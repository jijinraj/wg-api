from pydantic import BaseModel, Field
from typing import Optional



# VPNS Schemas
class VpnServerCreate(BaseModel):
    location_id: str = Field(min_length=2, max_length=64)
    label: str = Field(min_length=2, max_length=128)

    server_public_key: str = Field(min_length=20, max_length=128)
    endpoint: str = Field(min_length=3, max_length=255)

    dns: str = "1.1.1.1"
    allowed_ips: str = "0.0.0.0/0, ::/0"
    ping_url: str | None = None
    is_active: bool = True

class VpnServerUpdate(BaseModel):
    location_id: Optional[str] = None
    label: Optional[str] = None
    server_public_key: Optional[str] = None
    endpoint: Optional[str] = None
    dns: Optional[str] = None
    allowed_ips: Optional[str] = None
    ping_url: Optional[str] = None
    is_active: Optional[bool] = None


# Admin-User Schemas
class AdminUserUpdate(BaseModel):
    role: Optional[str] = None          # "user" | "admin"
    is_beta_approved: Optional[bool] = None
    is_email_verified: Optional[bool] = None