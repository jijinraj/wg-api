from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models_auth import RefreshToken


async def create_refresh_token(
    db: AsyncSession,
    *,
    user_id: str,
    token_hash: str,
    expires_at,
    ip: str | None = None,
    user_agent: str | None = None,
) -> RefreshToken:
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=datetime.utcnow(),
        revoked_at=None,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(rt)
    await db.flush()
    return rt


async def get_by_hash(db: AsyncSession, token_hash: str, *, for_update: bool = False) -> RefreshToken | None:
    q = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    if for_update:
        q = q.with_for_update()
    res = await db.execute(q)
    return res.scalar_one_or_none()


async def revoke(db: AsyncSession, token_hash: str) -> bool:
    rt = await get_by_hash(db, token_hash, for_update=True)
    if not rt:
        return False
    if rt.revoked_at is None:
        rt.revoked_at = datetime.utcnow()
    return True
