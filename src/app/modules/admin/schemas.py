from pydantic import BaseModel, Field



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