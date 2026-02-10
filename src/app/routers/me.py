import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_user
from app.core.config import LOCATIONS
from app.db.memory import PEERS
from app.models.schemas import PeerCreateIn, PeerOut, PeerListOut
from app.services.peers import next_allowed_ip
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import Peer


router = APIRouter(prefix="/me", tags=["me"])

@router.get("/peers", response_model=PeerListOut)
async def list_peers(user=Depends(get_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Peer).where(Peer.user_id == user.id))
    rows = res.scalars().all()
    return {"items": [PeerOut(**{
        "id": p.id,
        "name": p.name,
        "public_key": p.public_key,
        "allowed_ip": p.allowed_ip,
        "location_id": p.location_id,
        "location_label": p.location_label
    }) for p in rows]}

@router.post("/peers", response_model=PeerOut)
def create_peer(data: PeerCreateIn, user=Depends(get_user)):
    loc = next((l for l in LOCATIONS if l["id"] == data.location_id), None)
    if not loc:
        raise HTTPException(status_code=404, detail="Unknown location")

    peer = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": data.name.strip(),
        "public_key": data.public_key.strip(),
        "allowed_ip": next_allowed_ip(),
        "location_id": data.location_id,
        "location_label": loc["label"],
        "created_at": datetime.utcnow().isoformat(),
    }

    # TODO: apply peer to WG server for that location
    PEERS.append(peer)
    return PeerOut(**peer)

@router.delete("/peers/{peer_id}")
def delete_peer(peer_id: str, user=Depends(get_user)):
    idx = next((i for i, p in enumerate(PEERS) if p["id"] == peer_id and p["user_id"] == user["id"]), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Peer not found")

    PEERS.pop(idx)
    # TODO: remove from WG server
    return {"ok": True}
