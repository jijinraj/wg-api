import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import Base
from app.core.time import utcnow
from app.core.formatting import iso

class VpnServer(Base):
    __tablename__ = "vpn_servers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    location_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)

    server_public_key: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)

    dns: Mapped[str] = mapped_column(String(255), nullable=False, default="1.1.1.1")
    allowed_ips: Mapped[str] = mapped_column(String(255), nullable=False, default="0.0.0.0/0, ::/0")
    ping_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "location_id": self.location_id,
            "label": self.label,
            "server_public_key": self.server_public_key,
            "endpoint": self.endpoint,
            "dns": self.dns,
            "allowed_ips": self.allowed_ips,
            "ping_url": self.ping_url,
            "is_active": self.is_active,
            "created_at": iso(self.created_at),
        }
