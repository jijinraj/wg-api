"""
memory.py — dev-only in-memory seed data for quick testing.
...
"""
import uuid

from datetime import datetime, timezone
from argon2 import PasswordHasher

ph = PasswordHasher()

def now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

USERS = {
    "test@spartarocket.io": {
        "id": str(uuid.uuid4()),  # ok for dev; can be uuid string too if you prefer
        "email": "test@spartarocket.io",
        "password_hash": ph.hash("endi"),
        "created_at": now_z(),
        "is_beta_approved": True,
        "is_email_verified": True,
        "provider": "password",
        "role": "admin",
    }
}

PEERS: list[dict] = []
