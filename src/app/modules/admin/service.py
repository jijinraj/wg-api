"""
modules/admin/service.py — admin-side database actions (service layer).

This file contains the database logic used by the admin router. The router should stay thin
(HTTP request/response), while this service layer runs SQLAlchemy queries and commits changes.

Functions:
- list_users(db): returns all users.
- approve_user_by_email(db, email): normalizes email, verifies the user exists, then sets
  is_beta_approved=True (raises 404 if not found).
- list_peers_for_user(db, user_id): returns all WireGuard peers/devices for the given user_id.
- force_delete_peer(db, peer_id): verifies the peer exists, then deletes it (raises 404 if not found).

Notes:
- `await db.commit()` is required for updates/deletes to persist in the database.
- Email normalization uses strip().lower() to avoid case/spacing mismatches.
- The delete function includes a 404 existence check so the API doesn't silently succeed on invalid IDs.
"""

from fastapi import HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, Peer
from app.db.models_vpn import VpnServer
from app.modules.admin.schemas import VpnServerCreate

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
    # 1) Check existence
    res = await db.execute(select(Peer).where(Peer.id == peer_id))
    peer = res.scalar_one_or_none()
    if not peer:
        raise HTTPException(status_code=404, detail="Peer not found")

    # 2) Delete + commit
    await db.execute(delete(Peer).where(Peer.id == peer_id))
    await db.commit()


# VPN Server Services
async def create_vpn_server(db: AsyncSession, data: VpnServerCreate) -> VpnServer:
    # normalize
    location_id = data.location_id.strip().lower()

    # ensure unique location_id
    res = await db.execute(select(VpnServer).where(VpnServer.location_id == location_id))
    existing = res.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="location_id already exists")

    server = VpnServer(
        location_id=location_id,
        label=data.label.strip(),
        server_public_key=data.server_public_key.strip(),
        endpoint=data.endpoint.strip(),
        dns=data.dns.strip(),
        allowed_ips=data.allowed_ips.strip(),
        ping_url=data.ping_url.strip() if data.ping_url else None,
        is_active=data.is_active,
    )

    db.add(server)
    await db.commit()
    await db.refresh(server)
    return server