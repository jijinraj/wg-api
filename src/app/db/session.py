"""
sessions.py — connects backend to the database and gives each request a safe, temporary connection to use.

Async SQLAlchemy session setup (FastAPI-friendly)

- engine: async DB engine + connection pool (talks to DB via async driver, e.g. asyncpg)
- SessionLocal: factory that creates AsyncSession instances bound to the engine
- get_db(): FastAPI dependency that yields one session per request and auto-closes it

Notes:
- No auto-commit: call `await session.commit()` for writes (and `await session.rollback()` on errors)
- `expire_on_commit=False` keeps ORM objects usable after commit without implicit re-fetch
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
