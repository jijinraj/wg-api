"""
modules/ops/router.py — operational endpoints (health checks).

This router exposes lightweight endpoints under `/ops` used for monitoring and deployments.

- GET /ops/health:
  Simple health check that returns {"ok": True} to confirm the API process is running.
  Commonly used by uptime monitors, load balancers, and container orchestration probes.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/ops", tags=["ops"])

@router.get("/health")
def health():
    return {"ok": True}
