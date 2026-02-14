"""
config.py — stores backend’s settings (JWT, CORS, DB) and the list of VPN server locations.

central app configuration (env-based settings + static VPN locations).

This file loads settings from environment variables (with safe defaults) and exposes them
via a `settings` object used across the backend.

- Helper functions:
  - _env_bool(): reads env vars like "true/1/yes/on" into a real boolean.
  - _env_list(): reads comma-separated env vars into a list (supports "*" = allow all).
- Settings (Pydantic):
  - JWT_SECRET / JWT_ALG / JWT_EXP_MIN: JWT signing + expiry configuration.
  - CORS_ORIGINS: allowed frontend origins for CORS.
  - DATABASE_URL: async SQLAlchemy connection string (e.g., postgresql+asyncpg).
  - ALLOW_MEMORY_USERS: dev flag to allow/seed in-memory users from memory.py.
- LOCATIONS: temporary hardcoded VPN server list (id, label, endpoint, DNS, etc.).
  Later this should move into the database so the VPN module can manage locations.
"""
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

log = logging.getLogger("uvicorn")

def _find_env_path() -> Path | None:
    """
    Searches upwards from this file to find: envs/.env
    This avoids brittle parents[3] assumptions when the folder structure changes.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        candidate = parent / "envs" / ".env"
        if candidate.exists():
            return candidate
    return None

ENV_PATH = _find_env_path()
if ENV_PATH:
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    # Only log (don’t print) to keep production clean
    log.info(f"Loaded ENV from: {ENV_PATH}")
else:
    log.warning("No envs/.env found. Using environment variables + defaults only.")

def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}

def _env_list(name: str, default: str = "*") -> list[str]:
    raw = os.getenv(name, default).strip()
    if raw == "*":
        return ["*"]
    return [x.strip() for x in raw.split(",") if x.strip()]

class Settings(BaseModel):
    ACCESS_TOKEN_EXP_MIN: int = int(os.getenv("ACCESS_TOKEN_EXP_MIN", "15"))
    REFRESH_TOKEN_EXP_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "14"))

    EMAIL_OTP_EXP_MIN: int = int(os.getenv("EMAIL_OTP_EXP_MIN", "10"))
    PASSWORD_RESET_EXP_MIN: int = int(os.getenv("PASSWORD_RESET_EXP_MIN", "15"))

    REQUIRE_EMAIL_VERIFIED: bool = _env_bool("REQUIRE_EMAIL_VERIFIED", "false")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "CHANGE_ME")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    JWT_EXP_MIN: int = int(os.getenv("JWT_EXP_MIN", str(60 * 24)))

    CORS_ORIGINS: list[str] = _env_list("CORS_ORIGINS", "*")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://myapp_user:pass@localhost:5432/myapp_db",
    )

    # Dev helper: allow memory users as fallback/seed
    # IMPORTANT: set ALLOW_MEMORY_USERS=false in prod.
    ALLOW_MEMORY_USERS: bool = _env_bool("ALLOW_MEMORY_USERS", "true")

    # Dev helper: expose extra ops/debug endpoints (NEVER enable in prod)
    DEV_MODE: bool = _env_bool("DEV_MODE", "false")

settings = Settings()
