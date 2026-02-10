from fastapi import APIRouter

router = APIRouter(prefix="/ops", tags=["ops"])

@router.get("/health")
def health():
    return {"ok": True}
