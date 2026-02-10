from argon2 import PasswordHasher

ph = PasswordHasher()

# Dev/test-only seed. If ALLOW_MEMORY_USERS=true, first login will seed into DB.
USERS = {
    "test@spartarocket.io": {
        "id": "u1",
        "email": "test@spartarocket.io",
        "password_hash": ph.hash("endi"),
        "created_at": "2026-02-10T00:00:00Z",
        "is_beta_approved": True,
        "is_email_verified": True,
        "provider": "password",
        "role": "admin",
    }
}

# Legacy list kept if you still want it for quick tests (not used by DB routes)
PEERS: list[dict] = []
