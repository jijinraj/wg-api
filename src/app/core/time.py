from datetime import datetime, timezone

def utcnow() -> datetime:
    """UTC-aware now() for DB defaults and runtime timestamps."""
    return datetime.now(timezone.utc)
