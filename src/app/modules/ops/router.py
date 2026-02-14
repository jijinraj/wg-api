"""
modules/ops/router.py — operational endpoints (health/readiness checks).

This router exposes lightweight endpoints under `/ops` used for monitoring and deployments.

- GET /ops/health:
  Simple health check that returns {"ok": True} to confirm the API process is running.
- GET /ops/db/ready:
  Checks database connectivity (SELECT 1).
- GET /ops/ready:
  Checks database connectivity + verifies required tables exist (schema readiness).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.ops.service import db_ping, db_ready_check
from app.core.config import settings


router = APIRouter(prefix="/ops", tags=["ops"])

@router.get("/health")
def health():
    return {"ok": True}

@router.get("/db/ready")
async def db_ready(db: AsyncSession = Depends(get_db)):
    try:
        await db_ping(db)
        return {"ok": True, "db": "up"}
    except Exception:
        raise HTTPException(status_code=503, detail="DB unavailable")

@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        result = await db_ready_check(db)
        if not result["ok"]:
            raise HTTPException(status_code=503, detail=result)
        return result
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="DB unavailable")

@router.get("/version")
def version():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}