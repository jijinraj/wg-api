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
