from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    res = await db.execute(select(User).where(User.email == email))
    return res.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: str) -> User | None:
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password_hash: str,
    role: str = "user",
    is_beta_approved: bool = False,
    is_email_verified: bool = False,
) -> User:
    u = User(
        email=email,
        password_hash=password_hash,
        role=role,
        is_beta_approved=is_beta_approved,
        is_email_verified=is_email_verified,
    )
    db.add(u)
    await db.flush()  # assigns PK without committing
    # await db.refresh(u)
    return u


async def set_email_verified(db: AsyncSession, user_id: str, verified: bool = True) -> None:
    await db.execute(update(User).where(User.id == user_id).values(is_email_verified=verified))


async def set_password_hash(db: AsyncSession, user_id: str, password_hash: str) -> None:
    await db.execute(update(User).where(User.id == user_id).values(password_hash=password_hash))
