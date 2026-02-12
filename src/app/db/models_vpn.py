import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models import Base  # wherever your Base is


def _uuid() -> str:
    return str(uuid.uuid4())

class VpnServer(Base):
    __tablename__ = "vpn_servers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # like "de-fra", "uk-lon" (must be unique)
    location_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)

    server_public_key: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)  # "de.vpn.yourdomain.com:51820"

    dns: Mapped[str] = mapped_column(String(255), nullable=False, default="1.1.1.1")
    allowed_ips: Mapped[str] = mapped_column(String(255), nullable=False, default="0.0.0.0/0, ::/0")
    ping_url: Mapped[str] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
