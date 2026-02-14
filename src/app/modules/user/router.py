"""
modules/user/router.py — user account/profile endpoints (NOT auth).

Auth lives in /auth/*
VPN device management lives in /vpn/* (peers)

This module will later contain:
- profile
- preferences
- billing/customer metadata
- etc.
"""

from fastapi import APIRouter, Depends
from app.core.security import get_user
from app.core.formatting import iso

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me")
async def me(user=Depends(get_user)):
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_beta_approved": user.is_beta_approved,
        "is_email_verified": user.is_email_verified,
        "created_at": iso(user.created_at),
    }