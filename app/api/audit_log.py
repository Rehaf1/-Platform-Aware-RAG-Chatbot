import json
import logging
import time
from typing import Optional

logger = logging.getLogger("aptwatch.audit")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def log_chat_request(
    *,
    platform_id: str,
    tenant_id: str,
    user_id: str,
    user_role: Optional[str],
    grounded: bool,
    fallback_used: bool,
    num_citations: int,
    latency_ms: float,
) -> None:
    entry = {
        "event": "chat_request",
        "timestamp": time.time(),
        "platform_id": platform_id,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "user_role": user_role,
        "grounded": grounded,
        "fallback_used": fallback_used,
        "num_citations": num_citations,
        "latency_ms": round(latency_ms, 1),
    }
    logger.info(json.dumps(entry, ensure_ascii=False))