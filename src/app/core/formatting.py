from datetime import datetime
from typing import Optional

def iso(dt: Optional[datetime]) -> Optional[str]:
    """Safe ISO serializer for datetime fields."""
    return dt.isoformat() if dt else None
