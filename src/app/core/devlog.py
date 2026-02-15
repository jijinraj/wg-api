# app/core/devlog.py
import logging

log = logging.getLogger("uvicorn")

def mask_secret(secret: str, head: int = 6, tail: int = 4) -> str:
    if not secret:
        return ""
    if len(secret) <= head + tail:
        return "*" * len(secret)
    return f"{secret[:head]}...{secret[-tail:]}"

def dev_log_secret(label: str, secret: str, **meta) -> None:
    """
    DEV-only structured log for secrets (masked).
    Example:
      dev_log_secret("REFRESH", token, user_id="...", expires_at="...")
    """
    masked = mask_secret(secret)
    extras = " ".join([f"{k}={v}" for k, v in meta.items() if v is not None])
    log.warning(f"[DEV {label}] {masked} {extras}".strip())
