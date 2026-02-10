import os
from pydantic import BaseModel

def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}

def _env_list(name: str, default: str = "*") -> list[str]:
    raw = os.getenv(name, default).strip()
    if raw == "*":
        return ["*"]
    return [x.strip() for x in raw.split(",") if x.strip()]

class Settings(BaseModel):
    JWT_SECRET: str = os.getenv("JWT_SECRET", "CHANGE_ME")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    JWT_EXP_MIN: int = int(os.getenv("JWT_EXP_MIN", str(60 * 24)))

    CORS_ORIGINS: list[str] = _env_list("CORS_ORIGINS", "*")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://wg:wgpass@localhost:5432/wg",
    )

    # Dev helper: allow memory users as fallback/seed
    ALLOW_MEMORY_USERS: bool = _env_bool("ALLOW_MEMORY_USERS", "true")

settings = Settings()

# Static for now; later move to DB (vpn module can manage)
LOCATIONS = [
    {
        "id": "de-fra",
        "label": "Germany (Frankfurt)",
        "server_public_key": "PUT_DE_SERVER_PUBLIC_KEY",
        "endpoint": "de.vpn.yourdomain.com:51820",
        "dns": "1.1.1.1",
        "allowed_ips": "0.0.0.0/0, ::/0",
        "ping_url": "instagram.com",
    },
    {
        "id": "uk-lon",
        "label": "United Kingdom (London)",
        "server_public_key": "PUT_UK_SERVER_PUBLIC_KEY",
        "endpoint": "uk.vpn.yourdomain.com:51820",
        "dns": "1.1.1.1",
        "allowed_ips": "0.0.0.0/0, ::/0",
        "ping_url": "facebook.com",
    },
]
