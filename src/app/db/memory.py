from argon2 import PasswordHasher

ph = PasswordHasher()

USERS = {
    "test@spartarocket.io": {
        "id": "u1",
        "email": "test@spartarocket.io",
        "password_hash": ph.hash("endi"),
        "created_at": "2026-02-10T00:00:00Z",
        "is_beta_approved": True,
        "is_email_verified": True,   # later you’ll set this after verify
        "provider": "password",      # later: "google"
        "role": "admin",              # later: "admin"
    }
}

PEERS: list[dict] = []
