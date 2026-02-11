"""
memory.py — dev-only in-memory seed data for quick testing.

This file provides a temporary "fake DB" user so you can log in during development
without manually creating accounts in the real database.

- Uses Argon2 (PasswordHasher) to generate a secure password hash.
- USERS: a dict containing a pre-made test admin user:
  email: test@spartarocket.io
  password: endi
  role: admin
  (beta approved + email verified are set True to bypass checks)
- PEERS: legacy in-memory list for quick peer testing (not used by DB-backed routes).

Important:
- Passwords must be verified using:
    ph.verify(stored_hash, plain_password)
  Never compare password strings directly.
- Intended for development/testing only. Should be disabled in production
  unless explicitly allowed (e.g., via ALLOW_MEMORY_USERS=true).
"""

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
