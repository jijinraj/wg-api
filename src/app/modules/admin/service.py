from fastapi import HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Peer

async def list_users(db: AsyncSession):
    res = await db.execute(select(User))
    return res.scalars().all()

async def approve_user_by_email(db: AsyncSession, email: str) -> None:
    email = email.strip().lower()
    res = await db.execute(select(User).where(User.email == email))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    await db.execute(update(User).where(User.email == email).values(is_beta_approved=True))
    await db.commit()

async def list_peers_for_user(db: AsyncSession, user_id: str):
    res = await db.execute(select(Peer).where(Peer.user_id == user_id))
    return res.scalars().all()

async def force_delete_peer(db: AsyncSession, peer_id: str) -> None:
    await db.execute(delete(Peer).where(Peer.id == peer_id))
    await db.commit()
