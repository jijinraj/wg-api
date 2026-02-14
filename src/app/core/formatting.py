# app/core/formatting.py
from datetime import datetime
from typing import Optional, Union

def iso(dt: Optional[Union[datetime, str]]) -> Optional[str]:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()
