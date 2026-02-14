"""
modules/admin/router.py — admin-only API routes for managing users and their VPN devices.

admin-only API endpoints.

This router exposes admin operations under the `/admin` prefix.
All routes are protected by `require_admin`, meaning the caller must:
1) be logged in with a valid JWT, and
2) have user.role == "admin".

Endpoints:
- GET  /admin/users
  Lists all users (safe fields only; never returns password hashes).
- POST /admin/users/{email}/approve
  Marks a user as beta-approved by email.
- GET  /admin/users/{user_id}/peers
  Lists all WireGuard peers/devices belonging to a user.
- DELETE /admin/peers/{peer_id}
  Force deletes a peer/device by peer id.

Uses:
- get_db() to get an AsyncSession per request.
- service layer functions (admin.service) for DB logic.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.formatting import iso
from app.core.security import require_admin
from app.db.session import get_db
from app.modules.admin.schemas import AdminUserUpdate, VpnServerCreate, VpnServerUpdate
from app.modules.admin.service import (
    list_users,
    approve_user_by_email,
    list_peers_for_user,
    force_delete_peer,
    create_vpn_server,
    update_vpn_server,
    delete_vpn_server,
    list_vpn_servers,
    update_user_admin,
    delete_user_admin,
)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")
async def users(admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    rows = await list_users(db)
    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "is_beta_approved": u.is_beta_approved,
                "is_email_verified": u.is_email_verified,
                "role": u.role,
                "created_at": iso(u.created_at),
            }
            for u in rows
        ]
    }

@router.post("/users/{email}/approve")
async def approve(email: str, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await approve_user_by_email(db, email)
    return {"ok": True}


@router.patch("/users/{user_id}")
async def patch_user(
    user_id: str,
    payload: AdminUserUpdate,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    u = await update_user_admin(db, user_id, payload)
    return {
        "id": u.id,
        "email": u.email,
        "is_beta_approved": u.is_beta_approved,
        "is_email_verified": u.is_email_verified,
        "role": u.role,
        "created_at": iso(u.created_at),
    }

@router.delete("/users/{user_id}")
async def remove_user(
    user_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await delete_user_admin(db, user_id)
    return {"ok": True}
    
@router.get("/users/{user_id}/peers")
async def user_peers(user_id: str, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    rows = await list_peers_for_user(db, user_id)
    return {
        "items": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "name": p.name,
                "public_key": p.public_key,
                "allowed_ip": p.allowed_ip,
                "location_id": p.location_id,
                "location_label": p.location_label,
                "created_at": iso(p.created_at),
            }
            for p in rows
        ]
    }

@router.delete("/peers/{peer_id}")
async def delete_peer(peer_id: str, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await force_delete_peer(db, peer_id)
    return {"ok": True}



# VPN Server Management Routes
@router.get("/vpn/servers")
async def get_vpn_servers(admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    rows = await list_vpn_servers(db)
    return {"items": [s.to_dict() for s in rows]}

@router.post("/vpn/servers")
async def add_vpn_server(
    payload: VpnServerCreate,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    s = await create_vpn_server(db, payload)
    return {
        "id": s.id,
        "location_id": s.location_id,
        "label": s.label,
        "endpoint": s.endpoint,
        "dns": s.dns,
        "allowed_ips": s.allowed_ips,
        "ping_url": s.ping_url,
        "is_active": s.is_active,
        "created_at": iso(s.created_at),
    }

@router.patch("/vpn/servers/{server_id}")
async def patch_vpn_server(
    server_id: str,
    payload: VpnServerUpdate,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    s = await update_vpn_server(db, server_id, payload)
    return s.to_dict()

@router.delete("/vpn/servers/{server_id}")
async def remove_vpn_server(
    server_id: str,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await delete_vpn_server(db, server_id)
    return {"ok": True}

