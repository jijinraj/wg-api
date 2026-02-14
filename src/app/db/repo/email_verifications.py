from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models_auth import EmailVerification


async def create_otp(
    db: AsyncSession,
    *,
    user_id: str,
    otp_hash: str,
    expires_at,
) -> EmailVerification:
    rec = EmailVerification(
        user_id=user_id,
        otp_hash=otp_hash,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        is_used=False,
    )
    db.add(rec)
    await db.flush()
    return rec


async def find_latest_valid(
    db: AsyncSession,
    *,
    user_id: str,
    otp_hash: str,
) -> EmailVerification | None:
    res = await db.execute(
        select(EmailVerification)
        .where(
            EmailVerification.user_id == user_id,
            EmailVerification.otp_hash == otp_hash,
            EmailVerification.is_used == False,
        )
        .order_by(EmailVerification.created_at.desc())
    )
    return res.scalars().first()


async def mark_used(db: AsyncSession, rec: EmailVerification) -> None:
    rec.is_used = True
