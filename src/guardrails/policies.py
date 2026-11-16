"""URL, query, and playlist guardrails."""

from __future__ import annotations

import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from src.app_logging import log_event

BLOCKED_SCHEMES = {"javascript", "data", "file", "blob"}
ALLOWED_SCHEMES = {"https", "http"}

# Host patterns allowed for external encoders (expand in production with policy review)
ALLOWED_HOST_SUFFIXES = (
    "youtube.com",
    "youtu.be",
    "music.youtube.com",
    "soundcloud.com",
    "archive.org",
    "wikimedia.org",
    "cdn.pixabay.com",
    "files.freemusicarchive.org",
)

EXPLICIT_QUERY_PATTERNS = (
    re.compile(r"\bexplicit\b", re.I),
    re.compile(r"\bnsfw\b", re.I),
)


def validate_external_url(url: str) -> Tuple[bool, str, Dict]:
    """Return (ok, reason, meta) for streaming encoder chain."""
    url = (url or "").strip()
    if not url:
        log_event("WARNING", "guardrails", "empty URL rejected")
        return False, "URL is required.", {}

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme in BLOCKED_SCHEMES:
        log_event("WARNING", "guardrails", "blocked scheme", scheme=scheme)
        return False, f"Scheme '{scheme}' is not allowed.", {}
    if scheme not in ALLOWED_SCHEMES:
        return False, "Only http/https URLs are allowed.", {}

    host = (parsed.hostname or "").lower()
    if not host:
        return False, "Invalid host.", {}

    allowed = any(host == h or host.endswith("." + h) for h in ALLOWED_HOST_SUFFIXES)
    if host in {"127.0.0.1", "localhost"}:
        allowed = True

    if not allowed:
        log_event("WARNING", "guardrails", "host not on allowlist", host=host)
        return False, "Host is not on the streaming allowlist (compliance).", {"host": host}

    encoder_hints = classify_url(url)
    log_event("INFO", "guardrails", "URL approved", host=host, encoders=encoder_hints)
    return True, "OK", {"host": host, "encoder_hints": encoder_hints}


def classify_url(url: str) -> List[str]:
    """Suggested encoder order for a URL."""
    low = url.lower()
    if "youtube.com" in low or "youtu.be" in low:
        return ["iframe_embed", "video_element", "direct_audio", "fetch_blob"]
    if "soundcloud.com" in low:
        return ["iframe_embed", "direct_audio", "fetch_blob", "video_element"]
    if low.endswith((".mp3", ".wav", ".ogg", ".m4a", ".aac")):
        return ["direct_audio", "fetch_blob", "video_element", "iframe_embed"]
    return ["direct_audio", "fetch_blob", "video_element", "iframe_embed"]


def sanitize_discovery_query(query: str, block_explicit: bool = True) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    q = (query or "").strip()
    if block_explicit:
        for pat in EXPLICIT_QUERY_PATTERNS:
            if pat.search(q):
                warnings.append("Query flagged for explicit content policy; filtering catalog.")
                log_event("WARNING", "guardrails", "explicit query policy", query=q)
    return q, warnings


def enforce_focus_mode(songs: List[Dict], focus_mode: bool) -> List[Dict]:
    if not focus_mode:
        return songs
    filtered = [s for s in songs if not int(s.get("is_explicit", 0))]
    removed = len(songs) - len(filtered)
    if removed:
        log_event("INFO", "guardrails", "focus mode removed explicit tracks", removed=removed)
    return filtered