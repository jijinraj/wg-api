from pydantic import BaseModel

class LocationOut(BaseModel):
    id: str
    label: str
    ping_url: str

class LocationListOut(BaseModel):
    items: list[LocationOut]

class ServerInfoOut(BaseModel):
    server_public_key: str
    endpoint: str
    dns: str
    allowed_ips: str

class PeerCreateIn(BaseModel):
    name: str
    public_key: str
    location_id: str

class PeerOut(BaseModel):
    id: str
    name: str
    public_key: str
    allowed_ip: str
    location_id: str
    location_label: str

class PeerListOut(BaseModel):
    items: list[PeerOut]
