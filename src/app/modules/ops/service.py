from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def db_ping(db: AsyncSession) -> None:
    """Raises if DB is unreachable."""
    await db.execute(text("SELECT 1"))

async def get_existing_tables(db: AsyncSession) -> set[str]:
    """Returns all table names in the `public` schema (PostgreSQL)."""
    res = await db.execute(
        text("""
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
        """)
    )
    return {row[0] for row in res.all()}

async def check_required_tables(db: AsyncSession, required: set[str]) -> dict:
    """
    Checks that all required tables exist.
    Returns a structured result (does not raise unless query fails).
    """
    existing = await get_existing_tables(db)
    missing = sorted(required - existing)
    present = sorted(required & existing)

    return {
        "required": sorted(required),
        "present": present,
        "missing": missing,
        "ok": len(missing) == 0,
    }

async def db_ready_check(db: AsyncSession) -> dict:
    """
    Composite check used by /ops/ready:
    - DB reachable
    - Required schema tables exist
    """
    await db_ping(db)

    required = {
    "users",
    "peers",
    "vpn_servers",
    "refresh_tokens",
    "email_verifications",
    "password_resets",
    }
    tables = await check_required_tables(db, required)

    return {
        "db": "up",
        "tables": tables,
        "ok": tables["ok"],
    }