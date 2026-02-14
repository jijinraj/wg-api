from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import make_access_token

from app.modules.auth.schemas import (
    RegisterIn, LoginIn, TokenPairOut,
    RefreshIn, LogoutIn,
    SendVerificationIn, VerifyEmailIn,
    ForgotPasswordIn, ResetPasswordIn
)
from app.modules.auth import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(payload: RegisterIn, db: AsyncSession = Depends(get_db)):
    u = await service.register(db, payload.email, payload.password)
    return {
        "id": u.id,
        "email": u.email,
        "is_beta_approved": u.is_beta_approved,
        "is_email_verified": u.is_email_verified,
        "role": u.role,
    }


@router.post("/login", response_model=TokenPairOut)
async def login(payload: LoginIn, db: AsyncSession = Depends(get_db)):
    u, refresh_token = await service.login(db, payload.email, payload.password)
    return {"access_token": make_access_token(u.id), "refresh_token": refresh_token}


@router.post("/refresh", response_model=TokenPairOut)
async def refresh(payload: RefreshIn, db: AsyncSession = Depends(get_db)):
    u = await service.refresh(db, payload.refresh_token)

    # rotate old refresh token
    await service.logout(db, payload.refresh_token)

    # issue new refresh token
    new_refresh = await service.issue_refresh_for_user(db, u)

    return {"access_token": make_access_token(u.id), "refresh_token": new_refresh}


@router.post("/logout")
async def logout(payload: LogoutIn, db: AsyncSession = Depends(get_db)):
    await service.logout(db, payload.refresh_token)
    return {"ok": True}


@router.post("/send-verification")
async def send_verification(payload: SendVerificationIn, db: AsyncSession = Depends(get_db)):
    await service.send_email_otp(db, payload.email)
    return {"ok": True}


@router.post("/verify-email")
async def verify_email(payload: VerifyEmailIn, db: AsyncSession = Depends(get_db)):
    await service.verify_email_otp(db, payload.email, payload.otp)
    return {"ok": True}


@router.post("/resend-verification")
async def resend_verification(payload: SendVerificationIn, db: AsyncSession = Depends(get_db)):
    await service.send_email_otp(db, payload.email)
    return {"ok": True}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordIn, db: AsyncSession = Depends(get_db)):
    await service.forgot_password(db, payload.email)
    return {"ok": True}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordIn, db: AsyncSession = Depends(get_db)):
    await service.reset_password(db, payload.email, payload.token, payload.new_password)
    return {"ok": True}