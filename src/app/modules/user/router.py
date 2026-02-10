from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import make_token
from app.db.session import get_db

from app.modules.user.schemas import SignupIn, LoginIn, TokenOut, PublicUserOut
from app.modules.user.service import signup as signup_user, login as login_user

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/signup", response_model=PublicUserOut)
async def signup(data: SignupIn, db: AsyncSession = Depends(get_db)):
    u = await signup_user(db, data.email, data.password)
    return {
        "id": u.id,
        "email": u.email,
        "is_beta_approved": u.is_beta_approved,
        "is_email_verified": u.is_email_verified,
    }

@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    u = await login_user(db, data.email, data.password)
    return {"token": make_token(u.id)}
