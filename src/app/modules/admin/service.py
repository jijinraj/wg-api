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
import uuid

from fastapi import HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


from app.db.models import User, Peer
from app.db.models_vpn import VpnServer
from app.modules.admin.schemas import AdminUserUpdate,VpnServerCreate,VpnServerUpdate

# User-Admin Services
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
    
async def update_user_admin(db: AsyncSession, user_id: str, data: AdminUserUpdate) -> User:
    # 1) Check user exists
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    patch = {}

    # role validation (simple + strict)
    if data.role is not None:
        role = data.role.strip().lower()
        if role not in {"user", "admin"}:
            raise HTTPException(status_code=400, detail="Invalid role (must be 'user' or 'admin')")
        patch["role"] = role

    if data.is_beta_approved is not None:
        patch["is_beta_approved"] = bool(data.is_beta_approved)

    if data.is_email_verified is not None:
        patch["is_email_verified"] = bool(data.is_email_verified)

    if not patch:
        return u  # nothing to update

    await db.execute(update(User).where(User.id == user_id).values(**patch))
    await db.commit()

    # refresh and return
    res2 = await db.execute(select(User).where(User.id == user_id))
    return res2.scalar_one()


async def delete_user_admin(db: AsyncSession, user_id: str) -> None:
    # 1) Check user exists
    res = await db.execute(select(User).where(User.id == user_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # 2) Optional: cascade delete peers (recommended if no DB cascade is configured)
    # If your Peer.user_id has ON DELETE CASCADE in DB, you can remove this block.
    await db.execute(delete(Peer).where(Peer.user_id == user_id))

    # 3) Delete the user
    await db.execute(delete(User).where(User.id == user_id))
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


async def list_vpn_servers(db: AsyncSession) -> list[VpnServer]:
    res = await db.execute(select(VpnServer).order_by(VpnServer.created_at.desc()))
    return res.scalars().all()



async def update_vpn_server(db: AsyncSession, server_id: str, data: VpnServerUpdate) -> VpnServer:
    # Parse UUID safely
    try:
        server_uuid = uuid.UUID(server_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid server_id (must be UUID)")

    # 1) Check server exists
    res = await db.execute(select(VpnServer).where(VpnServer.id == server_uuid))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="VPN server not found")

    patch = {}

    if data.location_id is not None:
        new_location_id = data.location_id.strip().lower()
        if not new_location_id:
            raise HTTPException(status_code=400, detail="location_id cannot be empty")

        if new_location_id != s.location_id:
            res2 = await db.execute(select(VpnServer).where(VpnServer.location_id == new_location_id))
            if res2.scalar_one_or_none():
                raise HTTPException(status_code=409, detail="location_id already exists")
        patch["location_id"] = new_location_id

    if data.label is not None:
        v = data.label.strip()
        if not v:
            raise HTTPException(status_code=400, detail="label cannot be empty")
        patch["label"] = v

    if data.server_public_key is not None:
        v = data.server_public_key.strip()
        if not v:
            raise HTTPException(status_code=400, detail="server_public_key cannot be empty")
        patch["server_public_key"] = v

    if data.endpoint is not None:
        v = data.endpoint.strip()
        if not v:
            raise HTTPException(status_code=400, detail="endpoint cannot be empty")
        patch["endpoint"] = v

    if data.dns is not None:
        v = data.dns.strip()
        if not v:
            raise HTTPException(status_code=400, detail="dns cannot be empty")
        patch["dns"] = v

    if data.allowed_ips is not None:
        v = data.allowed_ips.strip()
        if not v:
            raise HTTPException(status_code=400, detail="allowed_ips cannot be empty")
        patch["allowed_ips"] = v

    if data.ping_url is not None:
        v = data.ping_url.strip()
        patch["ping_url"] = v if v else None

    if data.is_active is not None:
        patch["is_active"] = bool(data.is_active)

    if not patch:
        return s

    try:
        await db.execute(update(VpnServer).where(VpnServer.id == server_uuid).values(**patch))
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Update violates a constraint")

    res3 = await db.execute(select(VpnServer).where(VpnServer.id == server_uuid))
    return res3.scalar_one()

async def delete_vpn_server(db: AsyncSession, server_id: str) -> None:
    try:
        server_uuid = uuid.UUID(server_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid server_id (must be UUID)")

    res = await db.execute(select(VpnServer).where(VpnServer.id == server_uuid))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="VPN server not found")

    await db.execute(delete(VpnServer).where(VpnServer.id == server_uuid))
    await db.commit()
