import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, ForeignKey, text

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    is_beta_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="user")

    # keep string for now (works); later you can convert to DateTime properly
    created_at: Mapped[str] = mapped_column(String, server_default=text("now()"))

class Peer(Base):
    __tablename__ = "peers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    public_key: Mapped[str] = mapped_column(String, nullable=False)
    allowed_ip: Mapped[str] = mapped_column(String, nullable=False)

    location_id: Mapped[str] = mapped_column(String, nullable=False)
    location_label: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[str] = mapped_column(String, server_default=text("now()"))
