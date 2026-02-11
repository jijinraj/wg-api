"""
modules/vpn/schemas.py — defines the JSON formats for VPN locations, server connection info, and user devices (WireGuard peers).

request/response models for the VPN API.

These Pydantic models define the JSON structure for VPN endpoints:
- LocationOut / LocationListOut: output format for listing VPN locations.
- ServerInfoOut: output format for WireGuard server connection details for a location.
- PeerCreateIn: input format for creating a WireGuard peer/device (name, public_key, location_id).
- PeerOut / PeerListOut: output format for returning peer/device details (including allowed_ip and location label).

FastAPI uses these models to validate input, serialize output, and generate API docs.
"""
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
