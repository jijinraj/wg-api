"""
models.py — defines what our database tables look like and how the backend stores users and their VPN devices.

This file describes the structure (schema) of the database using SQLAlchemy ORM models.

- Base: shared ORM base class used by all models.
- User: `users` table for authentication and account management
  (email, password_hash, role, beta/verification flags).
- Peer: `peers` table for WireGuard devices linked to a user via `user_id` (ForeignKey).

Notes:
- IDs are auto-generated UUID strings.
- `email` is unique and indexed for fast login lookups.
- `created_at` currently uses a String with DB default `now()` 
  (can be upgraded to proper DateTime later).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, ForeignKey, DateTime

class Base(DeclarativeBase):
    pass

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    is_beta_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="user")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

class Peer(Base):
    __tablename__ = "peers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    public_key: Mapped[str] = mapped_column(String, nullable=False)
    allowed_ip: Mapped[str] = mapped_column(String, nullable=False)

    location_id: Mapped[str] = mapped_column(String, nullable=False)
    location_label: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
