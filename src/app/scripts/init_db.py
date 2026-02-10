import asyncio
from app.db.session import engine
from app.db.models import Base

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(main())
