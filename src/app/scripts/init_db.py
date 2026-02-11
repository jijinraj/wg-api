"""
scripts/init_db.py — creates your database tables from your SQLAlchemy models.

one-time DB table creation script.

This script connects to the database using the app's async engine and creates all tables
defined in SQLAlchemy models (Base.metadata) if they don't already exist.

- Uses `engine.begin()` to open a transactional connection.
- Uses `conn.run_sync(...)` because `Base.metadata.create_all` is a sync operation.
- Intended for quick local/dev setup (in production you typically use migrations like Alembic).
"""

import asyncio
from app.db.session import engine
from app.db.models import Base

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(main())
