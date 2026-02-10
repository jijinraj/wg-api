from fastapi import HTTPException
from app.db.memory import PEERS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Peer 

async def next_allowed_ip(db: AsyncSession) -> str:
    res = await db.execute(select(Peer.allowed_ip))
    used = set(res.scalars().all())
    for i in range(10, 250):
        ip = f"10.8.0.{i}/32"
        if ip not in used:
            return ip
    raise HTTPException(status_code=400, detail="IP pool exhausted")