from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models_auth import PasswordReset

async def create_reset(
    db: AsyncSession,
    *,
    user_id: str,
    token_hash: str,
    expires_at,
) -> PasswordReset:
    rec = PasswordReset(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(rec)
    await db.flush()
    return rec

async def find_latest_valid(db: AsyncSession, *, user_id: str, token_hash: str) -> PasswordReset | None:
    res = await db.execute(
        select(PasswordReset)
        .where(
            PasswordReset.user_id == user_id,
            PasswordReset.token_hash == token_hash,
            PasswordReset.is_used == False,
        )
        .order_by(PasswordReset.created_at.desc())
    )
    return res.scalars().first()

async def mark_used(db: AsyncSession, rec: PasswordReset) -> None:
    rec.is_used = True
