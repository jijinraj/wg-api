from fastapi import APIRouter, HTTPException, Depends
from app.core.security import require_admin
from app.db.memory import USERS

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")
def list_users(admin=Depends(require_admin)):
    return {
        "items": [
            {
                "id": u["id"],
                "email": u["email"],
                "is_beta_approved": u.get("is_beta_approved", False),
                "is_email_verified": u.get("is_email_verified", False),
                "created_at": u.get("created_at"),
            }
            for u in USERS.values()
        ]
    }

@router.post("/users/{email}/approve")
def approve_user(email: str, admin=Depends(require_admin)):
    key = email.strip().lower()
    u = USERS.get(key)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u["is_beta_approved"] = True
    return {"ok": True}
