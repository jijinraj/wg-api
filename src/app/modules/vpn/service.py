import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import LOCATIONS
from app.db.models import Peer

def get_location(location_id: str) -> dict | None:
    return next((l for l in LOCATIONS if l["id"] == location_id), None)

async def next_allowed_ip(db: AsyncSession) -> str:
    res = await db.execute(select(Peer.allowed_ip))
    used = set(res.scalars().all())
    for i in range(10, 250):
        ip = f"10.8.0.{i}/32"
        if ip not in used:
            return ip
    raise HTTPException(status_code=400, detail="IP pool exhausted")

async def list_peers_for_user(db: AsyncSession, user_id: str):
    res = await db.execute(select(Peer).where(Peer.user_id == user_id))
    return res.scalars().all()

async def create_peer_for_user(
    db: AsyncSession,
    *,
    user_id: str,
    name: str,
    public_key: str,
    location_id: str,
) -> Peer:
    loc = get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location")

    allowed_ip = await next_allowed_ip(db)

    p = Peer(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=name.strip(),
        public_key=public_key.strip(),
        allowed_ip=allowed_ip,
        location_id=location_id,
        location_label=loc["label"],
        created_at=datetime.utcnow().isoformat(),
    )

    db.add(p)
    await db.commit()
    await db.refresh(p)

    # TODO later:
    # apply peer to WG server for that location (ssh, agent, API, etc.)

    return p

async def delete_peer_for_user(db: AsyncSession, *, user_id: str, peer_id: str) -> None:
    res = await db.execute(select(Peer).where(Peer.id == peer_id, Peer.user_id == user_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Peer not found")

    await db.execute(delete(Peer).where(Peer.id == peer_id))
    await db.commit()

    # TODO later: remove peer from WG server
