# app/core/time.py
from datetime import datetime, timezone

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def ensure_aware_utc(dt: datetime) -> datetime:
    # If DB gives naive datetime, treat it as UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
