"""
security.py — creates and checks login tokens, and it blocks routes unless the user is logged in (or is an admin).

JWT auth helpers + route protection dependencies.

This file handles authentication and authorization for the API.

- security = HTTPBearer(): reads "Authorization: Bearer <token>" from requests.
- make_token(user_id): creates a signed JWT containing:
  - sub = user_id (who the token belongs to)
  - exp = expiry time (based on settings.JWT_EXP_MIN)
- get_user(): FastAPI dependency that:
  1) extracts the Bearer token
  2) verifies/decodes it using JWT_SECRET + JWT_ALG
  3) fetches the User from the database using the `sub` claim
  4) returns the User or raises 401 if invalid/missing
- require_admin(): dependency that allows only users with role == "admin" (otherwise 403).

Used in routes like:
  user: User = Depends(get_user)
  admin: User = Depends(require_admin)
"""
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User

security = HTTPBearer()

def make_token(user_id: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXP_MIN)
    return jwt.encode({"sub": user_id, "exp": exp}, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

async def get_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        uid = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    res = await db.execute(select(User).where(User.id == uid))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(user: User = Depends(get_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
