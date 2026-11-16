"""JS Streaming Platform — API + static PWA."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.agent.orchestrator import StreamingAgent
from src.app_logging import log_event, recent_events
from src.guardrails.policies import validate_external_url

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "songs.csv"
PWA = ROOT / "pwa"
(PWA / "media").mkdir(parents=True, exist_ok=True)
(PWA / "icons").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="JS Streaming Music", version="0.1.0")
agent = StreamingAgent(str(CSV))


class DiscoverBody(BaseModel):
    query: str = ""
    genre: str = "lofi"
    mood: str = "chill"
    energy: float = 0.4
    likes_acoustic: bool = True
    focus_mode: bool = True
    k: int = Field(default=5, ge=1, le=12)
    explain_tone: str = "casual"


class ProposalBody(BaseModel):
    proposal_id: str


class SourceBody(BaseModel):
    url: str


@app.on_event("startup")
def startup() -> None:
    import runpy

    runpy.run_path(str(ROOT / "scripts" / "ensure_media.py"), run_name="__main__")
    log_event("INFO", "server", "startup complete", catalog=len(agent.songs))


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "js-streaming-music",
        "tracks": len(agent.songs),
        "playlist_size": len(agent.get_playlist()),
        "features": ["rag", "agent", "guardrails", "hitl", "reliability_tests"],
    }


@app.get("/api/catalog")
def catalog():
    return {"songs": agent.songs}


@app.post("/api/discover")
def discover(body: DiscoverBody):
    try:
        return agent.discover(body.model_dump())
    except Exception as exc:
        log_event("ERROR", "server", "discover failed", error=str(exc))
        raise HTTPException(500, "Discover failed") from exc


@app.get("/api/playlist")
def playlist():
    return {"tracks": agent.get_playlist()}


@app.post("/api/playlist/approve")
def approve(body: ProposalBody):
    result = agent.approve(body.proposal_id)
    if result.get("error"):
        raise HTTPException(400, result["error"])
    return result


@app.post("/api/playlist/reject")
def reject(body: ProposalBody):
    result = agent.reject(body.proposal_id)
    if result.get("error"):
        raise HTTPException(400, result["error"])
    return result


@app.post("/api/sources/validate")
def validate_source(body: SourceBody):
    ok, reason, meta = validate_external_url(body.url)
    return {"ok": ok, "reason": reason, "meta": meta}


@app.get("/api/logs/recent")
def logs(limit: int = 40):
    return {"events": recent_events(limit)}


NO_STORE = {"Cache-Control": "no-store", "Pragma": "no-cache"}


@app.get("/")
def index():
    return FileResponse(PWA / "index.html", headers=NO_STORE)


@app.get("/clear.html")
def clear_sw():
    return FileResponse(PWA / "clear.html", headers=NO_STORE)


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(PWA / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(PWA / "sw.js", media_type="application/javascript")


if PWA.exists():
    app.mount("/css", StaticFiles(directory=PWA / "css"), name="css")
    app.mount("/js", StaticFiles(directory=PWA / "js"), name="js")
    app.mount("/media", StaticFiles(directory=PWA / "media"), name="media")
    app.mount("/icons", StaticFiles(directory=PWA / "icons"), name="icons")
    assets = PWA / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")


def main():
    import uvicorn

    uvicorn.run(
        "src.server:app",
        host="127.0.0.1",
        port=int(os.environ.get("JS_STREAM_PORT", "8790")),
        reload=False,
    )


if __name__ == "__main__":
    main()