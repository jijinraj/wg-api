"""
modules/user/router.py — provides the signup and login API endpoints and returns a login token for authenticated requests.

user-facing API endpoints (signup + login).

This router exposes normal user actions under the `/user` prefix.

Endpoints:
- POST /user/signup
  Creates a new user account (delegates to user.service.signup) and returns a safe public user response.
- POST /user/login
  Validates email/password (delegates to user.service.login) and returns a JWT token created by make_token().

Notes:
- Uses get_db() to get an AsyncSession per request.
- Response models (PublicUserOut, TokenOut) ensure we never return sensitive fields like password_hash.
- The JWT token returned from /login should be sent on future requests as:
  Authorization: Bearer <token>
"""
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
