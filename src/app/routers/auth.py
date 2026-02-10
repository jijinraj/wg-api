from fastapi import APIRouter, HTTPException,Depends
from argon2.exceptions import VerifyMismatchError
from app.db.memory import USERS, ph
from app.db.session import get_db
from app.core.security import make_token
from app.models.schemas import LoginIn, TokenOut
from datetime import datetime, timezone
import uuid
from app.models.schemas import SignupIn, PublicUserOut

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    email = data.email.strip().lower()

    res = await db.execute(select(User).where(User.email == email))
    u = res.scalar_one_or_none()

    try:
        ok = u is not None and ph.verify(u.password_hash, data.password)
    except VerifyMismatchError:
        ok = False

    if not ok:
        raise HTTPException(status_code=401, detail="Wrong email or password")

    # beta gate
    # try:
    #     ok = u is not None and ph.verify(u["password_hash"], data.password)
    # except VerifyMismatchError:
    #     ok = False
        
    # if not u.get("is_beta_approved"):
    #     raise HTTPException(status_code=403, detail="Not approved for beta yet")

    # # later, when you implement email verification, uncomment this:
    # # if not u.get("is_email_verified"):
    # #     raise HTTPException(status_code=403, detail="Email not verified")
    # #     
    # if not ok:
    #     raise HTTPException(status_code=401, detail="Wrong email or password")
    # return {"token": make_token(u["id"])}

    if not u.is_beta_approved:
        raise HTTPException(status_code=403, detail="Not approved for beta yet")

    return {"token": make_token(u.id)}


@router.post("/signup", response_model=PublicUserOut)
def signup(data: SignupIn):
    email = data.email.strip().lower()

    if email in USERS:
        raise HTTPException(status_code=409, detail="Email already registered")

    # basic password sanity (keep simple for MVP)
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": ph.hash(data.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_beta_approved": False,     # gate
        "is_email_verified": False,    # later gate
        "provider": "password",
        "role": "user",
    }

    USERS[email] = user

    # TODO later:
    # 1) create email verification token
    # 2) send email via SES/Resend/Mailgun, etc.

    return {
        "id": user["id"],
        "email": user["email"],
        "is_beta_approved": user["is_beta_approved"],
        "is_email_verified": user["is_email_verified"],
    }