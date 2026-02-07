from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from argon2 import PasswordHasher
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import uuid

ph = PasswordHasher()
app = FastAPI()

LOCATIONS = [
    {
        "id": "de-fra",
        "label": "Germany (Frankfurt)",
        "server_public_key": "PUT_DE_SERVER_PUBLIC_KEY",
        "endpoint": "de.vpn.yourdomain.com:51820",
        "dns": "1.1.1.1",
        "allowed_ips": "0.0.0.0/0, ::/0",
    },
    {
        "id": "uk-lon",
        "label": "United Kingdom (London)",
        "server_public_key": "PUT_UK_SERVER_PUBLIC_KEY",
        "endpoint": "uk.vpn.yourdomain.com:51820",
        "dns": "1.1.1.1",
        "allowed_ips": "0.0.0.0/0, ::/0",
    },
]


class LocationOut(BaseModel):
    id: str
    label: str

class LocationListOut(BaseModel):
    items: list[LocationOut]

class ServerInfoOut(BaseModel):
    server_public_key: str
    endpoint: str
    dns: str
    allowed_ips: str


# CORS (adjust for your domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = "CHANGE_ME"
JWT_ALG = "HS256"
JWT_EXP_MIN = 60 * 24

# ----- In-memory store for MVP (replace with Postgres) -----
USERS = {
    "test@spartarocket.io": {
        "id": "u1",
        "email": "test@spartarocket.io",
        "password_hash": ph.hash("test1234"),

    }
}
PEERS = []  # {id,user_id,name,public_key,allowed_ip,created_at}

# Server info (your WG server details)
WG_SERVER_PUBLIC_KEY = "PUT_SERVER_PUBLIC_KEY_HERE"
WG_ENDPOINT = "vpn.yourdomain.com:51820"
WG_DNS = "1.1.1.1"
WG_ALLOWED_IPS = "0.0.0.0/0, ::/0"

# ----- Auth helpers -----
def make_token(user_id: str):
    exp = datetime.utcnow() + timedelta(minutes=JWT_EXP_MIN)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET, algorithm=JWT_ALG)

def require_user(auth: str = ""):
    # FastAPI gives headers via Depends usually; keep simple:
    raise NotImplementedError

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

def get_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        uid = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    for u in USERS.values():
        if u["id"] == uid:
            return u
    raise HTTPException(status_code=401, detail="User not found")

# ----- Schemas -----
class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    token: str

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

class ServerInfoOut(BaseModel):
    server_public_key: str
    endpoint: str
    dns: str
    allowed_ips: str

# ----- Endpoints -----
from argon2.exceptions import VerifyMismatchError

@app.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn):
    u = USERS.get(data.email.lower())
    try:
        ok = u is not None and ph.verify(u["password_hash"], data.password)
    except VerifyMismatchError:
        ok = False

    if not ok:
        raise HTTPException(status_code=401, detail="Wrong email or password")
    return {"token": make_token(u["id"])}

@app.get("/wg/server-info", response_model=ServerInfoOut)
def server_info():
    return {
        "server_public_key": WG_SERVER_PUBLIC_KEY,
        "endpoint": WG_ENDPOINT,
        "dns": WG_DNS,
        "allowed_ips": WG_ALLOWED_IPS,
    }

@app.get("/me/peers", response_model=PeerListOut)
def list_peers(user=Depends(get_user)):
    items = [
        PeerOut(**p) for p in PEERS if p["user_id"] == user["id"]
    ]
    return {"items": items}

def next_allowed_ip() -> str:
    # MVP allocator: 10.8.0.10 upwards
    used = set(p["allowed_ip"] for p in PEERS)
    for i in range(10, 250):
        ip = f"10.8.0.{i}/32"
        if ip not in used:
            return ip
    raise HTTPException(status_code=400, detail="IP pool exhausted")

@app.post("/me/peers", response_model=PeerOut)
def create_peer(data: PeerCreateIn, user=Depends(get_user)):
    loc = next((l for l in LOCATIONS if l["id"] == data.location_id), None)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location")
    peer_id = str(uuid.uuid4())
    allowed_ip = next_allowed_ip()

    peer = {
    "id": peer_id,
    "user_id": user["id"],
    "name": data.name.strip(),
    "public_key": data.public_key.strip(),
    "allowed_ip": allowed_ip,
    "location_id": data.location_id,
    "location_label": loc["label"],
    "created_at": datetime.utcnow().isoformat(),
}
    # TODO (production): apply peer to WireGuard server:
    # - wg set wg0 peer <public_key> allowed-ips <allowed_ip>
    # - persist to wg0.conf or your DB
    PEERS.append(peer)
    return PeerOut(**peer)

@app.delete("/me/peers/{peer_id}")
def delete_peer(peer_id: str, user=Depends(get_user)):
    idx = None
    for i, p in enumerate(PEERS):
        if p["id"] == peer_id and p["user_id"] == user["id"]:
            idx = i
            break
    if idx is None:
        raise HTTPException(status_code=404, detail="Peer not found")

    peer = PEERS.pop(idx)

    # TODO (production): remove from WireGuard server:
    # - wg set wg0 peer <public_key> remove
    return {"ok": True}

@app.get("/wg/locations", response_model=LocationListOut)
def wg_locations():
    return {"items": [{"id": l["id"], "label": l["label"]} for l in LOCATIONS]}

@app.get("/wg/server-info", response_model=ServerInfoOut)
def server_info(location_id: str):
    loc = next((l for l in LOCATIONS if l["id"] == location_id), None)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location")
    return {
        "server_public_key": loc["server_public_key"],
        "endpoint": loc["endpoint"],
        "dns": loc["dns"],
        "allowed_ips": loc["allowed_ips"],
    }
