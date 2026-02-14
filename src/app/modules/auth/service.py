import logging
from datetime import datetime, timedelta, timezone
import secrets

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings
from app.core.security import make_refresh_token, hash_token
from app.db.memory import USERS as MEM_USERS, ph

from app.db.repo import users as users_repo
from app.db.repo import sessions as sessions_repo
from app.db.repo import email_verifications as ev_repo
from app.db.repo import password_resets as pr_repo

log = logging.getLogger("uvicorn")


def _verify(password_hash: str, password: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _hash_otp(otp: str) -> str:
    return hash_token(otp)


async def register(db: AsyncSession, email: str, password: str):
    email = email.strip().lower()

    existing = await users_repo.get_by_email(db, email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    if settings.ALLOW_MEMORY_USERS and email in MEM_USERS:
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    async with db.begin():
        u = await users_repo.create_user(
            db,
            email=email,
            password_hash=ph.hash(password),
            role="user",
            is_beta_approved=False,
            is_email_verified=False,
        )

    # Dev side-load memory (optional)
    if settings.ALLOW_MEMORY_USERS:
        MEM_USERS[email] = {
            "id": u.id,
            "email": u.email,
            "password_hash": u.password_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_beta_approved": u.is_beta_approved,
            "is_email_verified": u.is_email_verified,
            "provider": "password",
            "role": u.role,
        }

    return u


async def login(db: AsyncSession, email: str, password: str):
    email = email.strip().lower()

    u = await users_repo.get_by_email(db, email)

    # Memory fallback (dev only)
    if u is None and settings.ALLOW_MEMORY_USERS:
        mem = MEM_USERS.get(email)
        if not mem or not _verify(mem["password_hash"], password):
            raise HTTPException(status_code=401, detail="Wrong email or password")

        if not mem.get("is_beta_approved", False):
            raise HTTPException(status_code=403, detail="Not approved for beta yet")

        # seed into DB
        async with db.begin():
            u = await users_repo.create_user(
                db,
                email=mem["email"],
                password_hash=mem["password_hash"],
                role=mem.get("role", "user"),
                is_beta_approved=mem.get("is_beta_approved", False),
                is_email_verified=mem.get("is_email_verified", False),
            )

    if u is None or not _verify(u.password_hash, password):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    if not u.is_beta_approved:
        raise HTTPException(status_code=403, detail="Not approved for beta yet")

    if settings.REQUIRE_EMAIL_VERIFIED and not u.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    raw_refresh = make_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXP_DAYS)

    async with db.begin():
        await sessions_repo.create_refresh_token(
            db,
            user_id=u.id,
            token_hash=hash_token(raw_refresh),
            expires_at=expires_at,
            ip=None,
            user_agent=None,
        )

    return u, raw_refresh


async def refresh_rotate(db: AsyncSession, refresh_token: str):
    """
    Atomic refresh rotation:
    - validate refresh token row
    - revoke it
    - issue a new refresh token row
    All in ONE transaction so the user never loses session due to partial failures.
    """
    old_hash = hash_token(refresh_token)

    async with db.begin():
        rt = await sessions_repo.get_by_hash(db, old_hash, for_update=True)
        if not rt:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if rt.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Refresh token revoked")

        if rt.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token expired")

        u = await users_repo.get_by_id(db, rt.user_id)
        if not u:
            raise HTTPException(status_code=401, detail="User not found")

        if not u.is_beta_approved:
            raise HTTPException(status_code=403, detail="Not approved for beta yet")

        if settings.REQUIRE_EMAIL_VERIFIED and not u.is_email_verified:
            raise HTTPException(status_code=403, detail="Email not verified")

        # revoke old
        rt.revoked_at = datetime.now(timezone.utc)

        # issue new
        new_raw = make_refresh_token()
        new_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXP_DAYS)
        await sessions_repo.create_refresh_token(
            db,
            user_id=u.id,
            token_hash=hash_token(new_raw),
            expires_at=new_expires,
            ip=None,
            user_agent=None,
        )

    return u, new_raw


async def logout(db: AsyncSession, refresh_token: str) -> None:
    token_hash = hash_token(refresh_token)
    async with db.begin():
        await sessions_repo.revoke(db, token_hash)
    # intentionally silent on missing token


async def send_email_otp(db: AsyncSession, email: str) -> None:
    email = email.strip().lower()
    u = await users_repo.get_by_email(db, email)
    if not u:
        return  # don't leak

    otp = f"{secrets.randbelow(900000) + 100000}"  # 6 digits
    otp_hash = _hash_otp(otp)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.EMAIL_OTP_EXP_MIN)

    async with db.begin():
        await ev_repo.create_otp(db, user_id=u.id, otp_hash=otp_hash, expires_at=expires_at)

    log.warning(f"[DEV OTP] Email verification OTP for {email}: {otp} (expires in {settings.EMAIL_OTP_EXP_MIN} min)")


async def verify_email_otp(db: AsyncSession, email: str, otp: str) -> None:
    email = email.strip().lower()
    u = await users_repo.get_by_email(db, email)
    if not u:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    otp_hash = _hash_otp(otp)

    async with db.begin():
        rec = await ev_repo.find_latest_valid(db, user_id=u.id, otp_hash=otp_hash)
        if not rec:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if rec.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP expired")

        await ev_repo.mark_used(db, rec)
        await users_repo.set_email_verified(db, u.id, True)


async def forgot_password(db: AsyncSession, email: str) -> None:
    email = email.strip().lower()
    u = await users_repo.get_by_email(db, email)
    if not u:
        return

    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_EXP_MIN)

    async with db.begin():
        await pr_repo.create_reset(db, user_id=u.id, token_hash=token_hash, expires_at=expires_at)

    log.warning(f"[DEV RESET] Password reset token for {email}: {token} (expires in {settings.PASSWORD_RESET_EXP_MIN} min)")


async def reset_password(db: AsyncSession, email: str, token: str, new_password: str) -> None:
    email = email.strip().lower()
    u = await users_repo.get_by_email(db, email)
    if not u:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    token_hash = hash_token(token)

    async with db.begin():
        rec = await pr_repo.find_latest_valid(db, user_id=u.id, token_hash=token_hash)
        if not rec:
            raise HTTPException(status_code=400, detail="Invalid reset token")

        if rec.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Reset token expired")

        await pr_repo.mark_used(db, rec)
        await users_repo.set_password_hash(db, u.id, ph.hash(new_password))


async def issue_refresh_for_user(db: AsyncSession, user) -> str:
    """
    Kept for compatibility if you call it elsewhere.
    (Not used by /auth/refresh anymore.)
    """
    raw_refresh = make_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXP_DAYS)
    async with db.begin():
        await sessions_repo.create_refresh_token(
            db,
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            expires_at=expires_at,
            ip=None,
            user_agent=None,
        )
    return raw_refresh


async def refresh(db: AsyncSession, refresh_token: str):
    """
    Kept only if some old code calls it.
    Prefer refresh_rotate().
    """
    u, _new = await refresh_rotate(db, refresh_token)
    return u
