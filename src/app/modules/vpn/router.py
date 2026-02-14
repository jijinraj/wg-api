"""
modules/vpn/router.py — lets users pick a VPN location and manage their own WireGuard devices (list/add/delete) after logging in.

VPN endpoints (locations + WireGuard peer self-management).

This router exposes VPN-related API routes under the `/vpn` prefix.

Public endpoints (no auth):
- GET /vpn/locations
  Returns available VPN locations from config.LOCATIONS (id, label, ping_url).
- GET /vpn/server-info?location_id=...
  Returns WireGuard server connection details for a location
  (server_public_key, endpoint, dns, allowed_ips). Returns 404 if unknown.

User endpoints (auth required via get_user):
- GET /vpn/me/peers
  Lists the logged-in user's WireGuard peers/devices.
- POST /vpn/me/peers
  Creates a new peer for the logged-in user (optional beta gate enforced here too).
- DELETE /vpn/me/peers/{peer_id}
  Deletes a peer owned by the logged-in user.

Notes:
- Uses get_db() to get an AsyncSession per request.
- Business logic (DB queries, IP allocation, ownership checks) lives in vpn.service.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_user
from app.db.session import get_db

from app.modules.vpn.schemas import (
    LocationListOut,
    ServerInfoOut,
    PeerCreateIn,
    PeerOut,
    PeerListOut,
)
from app.modules.vpn.service import (
    list_active_servers,
    get_server_by_location_id,
    list_peers_for_user,
    create_peer_for_user,
    delete_peer_for_user,
)

router = APIRouter(prefix="/vpn", tags=["vpn"])

@router.get("/locations", response_model=LocationListOut)
async def locations(db: AsyncSession = Depends(get_db)):
    rows = await list_active_servers(db)
    return {
        "items": [{"id": s.location_id, "label": s.label, "ping_url": s.ping_url or ""} for s in rows]
    }

@router.get("/server-info", response_model=ServerInfoOut)
async def server_info(location_id: str, db: AsyncSession = Depends(get_db)):
    loc = await get_server_by_location_id(db, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location")
    return {
        "server_public_key": loc.server_public_key,
        "endpoint": loc.endpoint,
        "dns": loc.dns,
        "allowed_ips": loc.allowed_ips,
    }

# User VPN self-management under VPN domain
@router.get("/me/peers", response_model=PeerListOut)
async def my_peers(user=Depends(get_user), db: AsyncSession = Depends(get_db)):
    rows = await list_peers_for_user(db, user.id)
    return {
        "items": [
            PeerOut(
                id=p.id,
                name=p.name,
                public_key=p.public_key,
                allowed_ip=p.allowed_ip,
                location_id=p.location_id,
                location_label=p.location_label,
            )
            for p in rows
        ]
    }

@router.post("/me/peers", response_model=PeerOut)
async def add_peer(data: PeerCreateIn, user=Depends(get_user), db: AsyncSession = Depends(get_db)):
    # (optional) enforce beta-approved here too, not just in login
    if not user.is_beta_approved:
        raise HTTPException(status_code=403, detail="Not approved for beta yet")

    p = await create_peer_for_user(
        db,
        user_id=user.id,
        name=data.name,
        public_key=data.public_key,
        location_id=data.location_id,
    )
    return PeerOut(
        id=p.id,
        name=p.name,
        public_key=p.public_key,
        allowed_ip=p.allowed_ip,
        location_id=p.location_id,
        location_label=p.location_label,
    )

@router.delete("/me/peers/{peer_id}")
async def remove_peer(peer_id: str, user=Depends(get_user), db: AsyncSession = Depends(get_db)):
    await delete_peer_for_user(db, user_id=user.id, peer_id=peer_id)
    return {"ok": True}
