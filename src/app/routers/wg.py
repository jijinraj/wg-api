from fastapi import APIRouter, HTTPException
from app.core.config import LOCATIONS
from app.models.schemas import LocationListOut, ServerInfoOut

router = APIRouter(prefix="/wg", tags=["wireguard"])

@router.get("/locations", response_model=LocationListOut)
def wg_locations():
    return {"items": [{"id": l["id"], "label": l["label"], "ping_url": l["ping_url"]} for l in LOCATIONS]}

@router.get("/server-info", response_model=ServerInfoOut)
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
