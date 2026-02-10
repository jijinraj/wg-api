import os
from pydantic import BaseModel


class Settings(BaseModel):
    JWT_SECRET: str = os.getenv("JWT_SECRET", "CHANGE_ME")
    JWT_ALG: str = "HS256"
    JWT_EXP_MIN: int = 60 * 24
    CORS_ORIGINS: list[str] = ["*"]
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://wg:wgpass@localhost:5432/wg",
    )

settings = Settings()

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
