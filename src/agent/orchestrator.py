"""Agentic orchestration: plan → RAG → rank → verify → human-in-the-loop proposal."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.app_logging import log_event
from src.agent.tools import AgentToolkit
from src.guardrails.policies import sanitize_discovery_query
from src.rag.retriever import SongRAG
from src.recommender import load_songs

MIN_ACCEPTABLE_SCORE = 1.5
MAX_SCORE_REFERENCE = 6.0  # approximate ceiling for confidence normalization


@dataclass
class PlaylistProposal:
    id: str
    status: str  # pending | approved | rejected
    tracks: List[Dict[str, Any]]
    narrative: str
    plan_steps: List[str] = field(default_factory=list)
    rag_used: List[Dict] = field(default_factory=list)


class StreamingAgent:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.songs = load_songs(csv_path)
        self.rag = SongRAG(self.songs)
        self.pending: Dict[str, PlaylistProposal] = {}
        self.approved_playlist: List[Dict[str, Any]] = []

    def _prefs_from_body(self, body: Dict) -> Dict:
        return {
            "genre": body.get("genre") or body.get("favorite_genre") or "lofi",
            "mood": body.get("mood") or body.get("favorite_mood") or "chill",
            "energy": float(body.get("energy", body.get("target_energy", 0.4))),
            "likes_acoustic": bool(body.get("likes_acoustic", True)),
            "mood_detail": body.get("mood_detail"),
        }

    def discover(self, body: Dict) -> Dict:
        plan: List[str] = []
        toolkit = AgentToolkit(self.songs, self.rag)
        tone = str(body.get("explain_tone", "casual")).lower()
        focus = bool(body.get("focus_mode", True))
        k = int(body.get("k", 5))
        prefs = self._prefs_from_body(body)

        plan.append("Parse listener intent and taste profile")
        log_event("INFO", "agent", "discover start", prefs=prefs, query=body.get("query", ""))

        gq = toolkit.tool_guard_query(body.get("query", ""))
        query = gq["cleaned"]
        warnings = gq["warnings"]

        plan.append("Tool: tool_retrieve (multi-source RAG)")
        rag_out = toolkit.tool_retrieve(query or f"{prefs['mood']} {prefs['genre']} focus", k=5)
        rag_chunks = rag_out["chunks"]

        if query:
            for ch in rag_chunks:
                if ch["id"].startswith("song-"):
                    sid = ch["id"].split("-")[-1]
                    row = next((s for s in self.songs if str(s["id"]) == sid), None)
                    if row and row["genre"] not in (prefs.get("genre"), prefs.get("favorite_genre")):
                        prefs["mood_detail"] = row.get("mood_detail") or prefs.get("mood_detail")

        plan.append("Tool: tool_rank + tool_focus_filter")
        rank_out = toolkit.tool_rank(prefs, k=k, apply_diversity=True)
        ranked = rank_out["ranked"]
        toolkit.tool_focus_filter([t[0] for t in ranked], focus)

        top_score = ranked[0][1] if ranked else 0
        vrf = toolkit.tool_verify(top_score)
        reranked = False
        if vrf["rerank_recommended"]:
            plan.append("Tool: tool_rank (rerank, diversity off)")
            rank_out = toolkit.tool_rank(prefs, k=k, apply_diversity=False)
            ranked = rank_out["ranked"]
            top_score = ranked[0][1] if ranked else 0
            reranked = True
            toolkit.tool_verify(top_score)
            log_event("WARNING", "agent", "low confidence rerun", top_score=top_score, reranked=True)

        plan.append(f"Compose grounded explanations (tone={tone})")
        tracks = []
        for song, score, reasons in ranked:
            summary = self.rag.grounded_summary(query, song, reasons, rag_chunks, tone=tone)
            tracks.append(
                {
                    "id": song["id"],
                    "title": song["title"],
                    "artist": song["artist"],
                    "genre": song["genre"],
                    "mood": song["mood"],
                    "score": round(score, 2),
                    "explanation": summary,
                    "stream_url": f"/media/track_{song['id']}.wav",
                }
            )

        proposal_id = str(uuid.uuid4())[:8]
        narrative = (
            f"Proposed {len(tracks)} tracks for “{query or 'your vibe'}”. "
            "Approve to add them to your playlist (human-in-the-loop)."
        )
        proposal = PlaylistProposal(
            id=proposal_id,
            status="pending",
            tracks=tracks,
            narrative=narrative,
            plan_steps=plan,
            rag_used=rag_chunks,
        )
        self.pending[proposal_id] = proposal
        toolkit.persist_trace(proposal_id, plan)
        log_event("INFO", "agent", "proposal created", proposal_id=proposal_id, tracks=len(tracks))

        confidence = round(min(1.0, top_score / MAX_SCORE_REFERENCE), 2)
        passed = top_score >= MIN_ACCEPTABLE_SCORE
        log_event(
            "INFO",
            "agent",
            "confidence scored",
            confidence=confidence,
            top_score=top_score,
            passed=passed,
        )
        return {
            "proposal_id": proposal_id,
            "status": "pending",
            "warnings": warnings,
            "plan_steps": plan,
            "rag_chunks": rag_chunks,
            "recommendations": tracks,
            "narrative": narrative,
            "confidence_score": confidence,
            "explain_tone": tone,
            "rag_sources_indexed": self.rag.source_count,
            "tool_trace_preview": [t["tool"] for t in toolkit.trace],
            "verification": {
                "top_score": round(top_score, 2),
                "passed": passed,
                "reranked": reranked,
                "threshold": MIN_ACCEPTABLE_SCORE,
            },
        }

    def approve(self, proposal_id: str) -> Dict:
        prop = self.pending.get(proposal_id)
        if not prop:
            return {"error": "Unknown proposal"}
        if prop.status != "pending":
            return {"error": f"Proposal already {prop.status}"}
        prop.status = "approved"
        for t in prop.tracks:
            if not any(x["id"] == t["id"] for x in self.approved_playlist):
                self.approved_playlist.append(t)
        log_event("INFO", "agent", "human approved playlist", proposal_id=proposal_id)
        return {"ok": True, "playlist": self.approved_playlist}

    def reject(self, proposal_id: str) -> Dict:
        prop = self.pending.get(proposal_id)
        if not prop:
            return {"error": "Unknown proposal"}
        prop.status = "rejected"
        log_event("INFO", "agent", "human rejected playlist", proposal_id=proposal_id)
        return {"ok": True, "status": "rejected"}

    def get_playlist(self) -> List[Dict]:
        return list(self.approved_playlist)