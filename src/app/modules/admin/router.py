from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_admin
from app.db.session import get_db
from app.modules.admin.service import (
    list_users,
    approve_user_by_email,
    list_peers_for_user,
    force_delete_peer,
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
                "created_at": u.created_at,
            }
            for u in rows
        ]
    }

@router.post("/users/{email}/approve")
async def approve(email: str, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await approve_user_by_email(db, email)
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
                "created_at": p.created_at,
            }
            for p in rows
        ]
    }

@router.delete("/peers/{peer_id}")
async def delete_peer(peer_id: str, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    await force_delete_peer(db, peer_id)
    return {"ok": True}
