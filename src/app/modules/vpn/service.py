"""
modules/vpn/service.py — manages VPN device records in the database and assigns each device a unique internal VPN IP.

VPN business logic (peer management + IP allocation).

This file contains the DB logic behind the VPN router:
- Location lookup uses the static LOCATIONS list (config.py) for now.
- Peer/device records are stored in the Peer table.
- Each new peer is assigned a unique tunnel IP from a simple IP pool.

Functions:
- get_location(location_id): returns the matching location dict from LOCATIONS or None.
- next_allowed_ip(db): finds the next unused IP in the pool (10.8.0.10–10.8.0.249)/32.
  Raises 400 if the pool is exhausted.
- list_peers_for_user(db, user_id): returns all peers owned by the user.
- create_peer_for_user(...): validates location, allocates allowed_ip, inserts a Peer row, commits, and returns it.
- delete_peer_for_user(db, user_id, peer_id): checks the peer exists and belongs to the user, then deletes it.

Notes:
- This currently updates only the database. Applying/removing peers on the actual WireGuard server
  is planned later (SSH/agent/API integration).
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Peer
from app.db.models_vpn import VpnServer


async def list_active_servers(db: AsyncSession) -> list[VpnServer]:
    res = await db.execute(
        select(VpnServer).where(VpnServer.is_active == True).order_by(VpnServer.label.asc())
    )
    return res.scalars().all()

async def get_server_by_location_id(db: AsyncSession, location_id: str) -> VpnServer | None:
    location_id = location_id.strip().lower()
    res = await db.execute(
        select(VpnServer).where(VpnServer.location_id == location_id, VpnServer.is_active == True)
    )
    return res.scalar_one_or_none()

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
    loc = await get_server_by_location_id(db, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location")

    allowed_ip = await next_allowed_ip(db)

    p = Peer(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=name.strip(),
        public_key=public_key.strip(),
        allowed_ip=allowed_ip,
        location_id=loc.location_id,
        location_label=loc.label,
        created_at=datetime.now(timezone.utc),
    )

    db.add(p)
    await db.commit()
    await db.refresh(p)

    # TODO later: apply peer to WG server for that location (ssh, agent, API, etc.)
    return p

async def delete_peer_for_user(db: AsyncSession, *, user_id: str, peer_id: str) -> None:
    res = await db.execute(select(Peer).where(Peer.id == peer_id, Peer.user_id == user_id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Peer not found")

    await db.execute(delete(Peer).where(Peer.id == peer_id))
    await db.commit()

    # TODO later: remove peer from WG server
