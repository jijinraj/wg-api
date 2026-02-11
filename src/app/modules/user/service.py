"""
modules/user/service.py — the signup/login logic, checks passwords securely, and (in dev mode) can use a memory test user and seed it into the database.

user auth logic (signup/login) + optional dev memory fallback.

This file contains the core business logic for user accounts:
- Password hashing/verification uses Argon2 (ph.hash / ph.verify).
- DB is the main source of truth for users.
- Optional dev feature: when ALLOW_MEMORY_USERS=true, we can:
  - block duplicate signup if the email exists in memory seed
  - allow login using memory users if not found in DB
  - "seed" that memory user into the DB on first successful login (to make future behavior consistent)

Functions:
- _verify(hash, password): verifies a plain password against an Argon2 hash.
- get_user_by_email(db, email): fetches a user from DB or returns None.
- create_db_user(db, ...): inserts a user into DB and commits.
- signup(db, email, password): validates input, hashes password, creates user in DB,
  and optionally mirrors it into MEM_USERS for dev convenience.
- login(db, email, password): checks DB first; if missing and dev mode enabled,
  falls back to memory user, verifies password, enforces beta gate, and seeds into DB.

Notes:
- Password checks must use `ph.verify(stored_hash, plain_password)` (never compare strings).
- Beta access is enforced via `is_beta_approved` (returns 403 if not approved).
- Email verification is planned later (is_email_verified check is currently commented).
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings
from app.db.models import User
from app.db.memory import USERS as MEM_USERS, ph

def _verify(password_hash: str, password: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    res = await db.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()

async def create_db_user(
    db: AsyncSession,
    *,
    user_id: str,
    email: str,
    password_hash: str,
    role: str = "user",
    is_beta_approved: bool = False,
    is_email_verified: bool = False,
) -> User:
    u = User(
        id=user_id,
        email=email,
        password_hash=password_hash,
        role=role,
        is_beta_approved=is_beta_approved,
        is_email_verified=is_email_verified,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u

async def signup(db: AsyncSession, email: str, password: str) -> User:
    email = email.strip().lower()

    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    if settings.ALLOW_MEMORY_USERS and email in MEM_USERS:
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user_id = str(uuid.uuid4())
    password_hash = ph.hash(password)

    u = await create_db_user(
        db,
        user_id=user_id,
        email=email,
        password_hash=password_hash,
        role="user",
        is_beta_approved=False,   # beta gate
        is_email_verified=False,  # email gate later
    )

    # Dev side-load (easy to disable by ALLOW_MEMORY_USERS=false)
    if settings.ALLOW_MEMORY_USERS:
        MEM_USERS[email] = {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_beta_approved": False,
            "is_email_verified": False,
            "provider": "password",
            "role": "user",
        }

    # TODO later reminders:
    # 1) create email verification token
    # 2) send email via SES/Resend/Mailgun, etc.
    # 3) google signin: store provider + google_sub

    return u

async def login(db: AsyncSession, email: str, password: str) -> User:
    email = email.strip().lower()

    # 1) DB first
    u = await get_user_by_email(db, email)

    # 2) Memory fallback (dev only)
    if u is None and settings.ALLOW_MEMORY_USERS:
        mem = MEM_USERS.get(email)
        if not mem:
            raise HTTPException(status_code=401, detail="Wrong email or password")

        if not _verify(mem["password_hash"], password):
            raise HTTPException(status_code=401, detail="Wrong email or password")

        if not mem.get("is_beta_approved", False):
            raise HTTPException(status_code=403, detail="Not approved for beta yet")

        # Seed into DB so everything becomes consistent
        u = await create_db_user(
            db,
            user_id=mem["id"],
            email=mem["email"],
            password_hash=mem["password_hash"],
            role=mem.get("role", "user"),
            is_beta_approved=mem.get("is_beta_approved", False),
            is_email_verified=mem.get("is_email_verified", False),
        )
        return u

    if u is None:
        raise HTTPException(status_code=401, detail="Wrong email or password")

    if not _verify(u.password_hash, password):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    if not u.is_beta_approved:
        raise HTTPException(status_code=403, detail="Not approved for beta yet")

    # later:
    # if not u.is_email_verified: raise HTTPException(status_code=403, detail="Email not verified")

    return u
