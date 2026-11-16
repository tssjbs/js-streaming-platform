"""Structured application logging for guardrails and agent steps."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "js_streaming.log"

_ring: List[Dict[str, Any]] = []
_ring_lock = threading.Lock()
_MAX_RING = 200


@dataclass
class LogEvent:
    level: str
    component: str
    message: str
    detail: Dict[str, Any] = field(default_factory=dict)
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _configure_root() -> logging.Logger:
    logger = logging.getLogger("js_streaming")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


LOGGER = _configure_root()


def log_event(
    level: str,
    component: str,
    message: str,
    **detail: Any,
) -> LogEvent:
    event = LogEvent(level=level.upper(), component=component, message=message, detail=detail)
    payload = asdict(event)
    with _ring_lock:
        _ring.append(payload)
        if len(_ring) > _MAX_RING:
            del _ring[: len(_ring) - _MAX_RING]
    line = f"[{component}] {message}"
    if detail:
        line += " | " + json.dumps(detail, default=str)
    if level.upper() == "ERROR":
        LOGGER.error(line)
    elif level.upper() == "WARNING":
        LOGGER.warning(line)
    else:
        LOGGER.info(line)
    return event


def recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    with _ring_lock:
        return list(_ring[-limit:])