import logging
from datetime import datetime, timedelta
import secrets

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings
from app.core.security import make_refresh_token, hash_token
from app.db.models import User
from app.db.memory import USERS as MEM_USERS, ph

from app.db.models_auth import RefreshToken, EmailVerification, PasswordReset

log = logging.getLogger("uvicorn")


def _verify(password_hash: str, password: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    res = await db.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()


async def register(db: AsyncSession, email: str, password: str) -> User:
    email = email.strip().lower()

    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    if settings.ALLOW_MEMORY_USERS and email in MEM_USERS:
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    u = User(
        email=email,
        password_hash=ph.hash(password),
        role="user",
        is_beta_approved=False,
        is_email_verified=False,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)

    # Dev side-load memory (optional)
    if settings.ALLOW_MEMORY_USERS:
        MEM_USERS[email] = {
            "id": u.id,
            "email": u.email,
            "password_hash": u.password_hash,
            "created_at": datetime.utcnow().isoformat(),
            "is_beta_approved": u.is_beta_approved,
            "is_email_verified": u.is_email_verified,
            "provider": "password",
            "role": u.role,
        }

    return u


async def login(db: AsyncSession, email: str, password: str) -> tuple[User, str]:
    email = email.strip().lower()

    # 1) DB first
    u = await get_user_by_email(db, email)

    # 2) Memory fallback (dev only)
    if u is None and settings.ALLOW_MEMORY_USERS:
        mem = MEM_USERS.get(email)
        if not mem or not _verify(mem["password_hash"], password):
            raise HTTPException(status_code=401, detail="Wrong email or password")

        if not mem.get("is_beta_approved", False):
            raise HTTPException(status_code=403, detail="Not approved for beta yet")

        # seed into DB
        u = User(
            id=mem["id"],
            email=mem["email"],
            password_hash=mem["password_hash"],
            role=mem.get("role", "user"),
            is_beta_approved=mem.get("is_beta_approved", False),
            is_email_verified=mem.get("is_email_verified", False),
        )
        db.add(u)
        await db.commit()
        await db.refresh(u)

    if u is None or not _verify(u.password_hash, password):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    if not u.is_beta_approved:
        raise HTTPException(status_code=403, detail="Not approved for beta yet")

    if settings.REQUIRE_EMAIL_VERIFIED and not u.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    # Create refresh token row
    raw_refresh = make_refresh_token()
    rt = RefreshToken(
        user_id=u.id,
        token_hash=hash_token(raw_refresh),
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXP_DAYS),
    )
    db.add(rt)
    await db.commit()

    return u, raw_refresh


async def refresh(db: AsyncSession, refresh_token: str) -> User:
    token_hash = hash_token(refresh_token)

    res = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = res.scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if rt.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    if rt.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    res2 = await db.execute(select(User).where(User.id == rt.user_id))
    u = res2.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=401, detail="User not found")

    if not u.is_beta_approved:
        raise HTTPException(status_code=403, detail="Not approved for beta yet")

    if settings.REQUIRE_EMAIL_VERIFIED and not u.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    return u


async def issue_refresh_for_user(db: AsyncSession, user: User) -> str:
    raw_refresh = make_refresh_token()
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXP_DAYS),
    )
    db.add(rt)
    await db.commit()
    return raw_refresh


async def logout(db: AsyncSession, refresh_token: str) -> None:
    token_hash = hash_token(refresh_token)
    res = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = res.scalar_one_or_none()
    if not rt:
        # don’t leak whether token existed
        return

    if rt.revoked_at is None:
        rt.revoked_at = datetime.utcnow()
        await db.commit()


def _hash_otp(otp: str) -> str:
    # reuse sha256 hashing
    return hash_token(otp)


async def send_email_otp(db: AsyncSession, email: str) -> None:
    email = email.strip().lower()
    u = await get_user_by_email(db, email)
    if not u:
        # don’t leak
        return

    otp = f"{secrets.randbelow(900000) + 100000}"  # 6 digits
    otp_hash = _hash_otp(otp)

    rec = EmailVerification(
        user_id=u.id,
        otp_hash=otp_hash,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.EMAIL_OTP_EXP_MIN),
        is_used=False,
    )
    db.add(rec)
    await db.commit()

    # For now: print/log OTP
    log.warning(f"[DEV OTP] Email verification OTP for {email}: {otp} (expires in {settings.EMAIL_OTP_EXP_MIN} min)")


async def verify_email_otp(db: AsyncSession, email: str, otp: str) -> None:
    email = email.strip().lower()
    u = await get_user_by_email(db, email)
    if not u:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    otp_hash = _hash_otp(otp)

    res = await db.execute(
        select(EmailVerification)
        .where(
            EmailVerification.user_id == u.id,
            EmailVerification.otp_hash == otp_hash,
            EmailVerification.is_used == False,
        )
        .order_by(EmailVerification.created_at.desc())
    )
    rec = res.scalars().first()
    if not rec:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if rec.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    rec.is_used = True
    await db.execute(update(User).where(User.id == u.id).values(is_email_verified=True))
    await db.commit()


async def forgot_password(db: AsyncSession, email: str) -> None:
    email = email.strip().lower()
    u = await get_user_by_email(db, email)
    if not u:
        return

    token = secrets.token_urlsafe(32)
    rec = PasswordReset(
        user_id=u.id,
        token_hash=hash_token(token),
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXP_MIN),
        is_used=False,
    )
    db.add(rec)
    await db.commit()

    log.warning(f"[DEV RESET] Password reset token for {email}: {token} (expires in {settings.PASSWORD_RESET_EXP_MIN} min)")


async def reset_password(db: AsyncSession, email: str, token: str, new_password: str) -> None:
    email = email.strip().lower()
    u = await get_user_by_email(db, email)
    if not u:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    token_hash = hash_token(token)

    res = await db.execute(
        select(PasswordReset)
        .where(
            PasswordReset.user_id == u.id,
            PasswordReset.token_hash == token_hash,
            PasswordReset.is_used == False,
        )
        .order_by(PasswordReset.created_at.desc())
    )
    rec = res.scalars().first()
    if not rec:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    if rec.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired")

    rec.is_used = True
    await db.execute(update(User).where(User.id == u.id).values(password_hash=ph.hash(new_password)))
    await db.commit()
