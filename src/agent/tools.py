"""Named tools for multi-step agent traces (stretch: agentic workflow)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

from src.guardrails.policies import enforce_focus_mode, sanitize_discovery_query
from src.rag.retriever import SongRAG
from src.recommender import recommend_songs

ROOT = Path(__file__).resolve().parent.parent.parent
TRACE_FILE = ROOT / "logs" / "agent_traces.jsonl"

MIN_ACCEPTABLE_SCORE = 1.5


class AgentToolkit:
    def __init__(self, songs: List[Dict], rag: SongRAG):
        self.songs = songs
        self.rag = rag
        self.trace: List[Dict[str, Any]] = []

    def _record(self, tool: str, inp: Dict, out: Dict) -> Dict:
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "input": inp,
            "output": out,
        }
        self.trace.append(row)
        return out

    def tool_guard_query(self, query: str) -> Dict:
        cleaned, warnings = sanitize_discovery_query(query)
        return self._record("tool_guard_query", {"query": query}, {"cleaned": cleaned, "warnings": warnings})

    def tool_retrieve(self, query: str, k: int = 4) -> Dict:
        chunks = self.rag.retrieve(query, k=k)
        return self._record("tool_retrieve", {"query": query, "k": k}, {"chunks": chunks, "count": len(chunks)})

    def tool_rank(self, prefs: Dict, k: int, apply_diversity: bool = True) -> Dict:
        ranked = recommend_songs(prefs, self.songs, k=k, apply_diversity=apply_diversity)
        return self._record(
            "tool_rank",
            {"prefs": prefs, "k": k, "diversity": apply_diversity},
            {"top_score": ranked[0][1] if ranked else 0, "count": len(ranked), "ranked": ranked},
        )

    def tool_verify(self, top_score: float) -> Dict:
        passed = top_score >= MIN_ACCEPTABLE_SCORE
        return self._record(
            "tool_verify",
            {"top_score": top_score, "threshold": MIN_ACCEPTABLE_SCORE},
            {"passed": passed, "rerank_recommended": not passed},
        )

    def tool_focus_filter(self, song_dicts: List[Dict], focus: bool) -> Dict:
        filtered = enforce_focus_mode(song_dicts, focus)
        return self._record(
            "tool_focus_filter",
            {"focus": focus, "in_count": len(song_dicts)},
            {"out_count": len(filtered)},
        )

    def persist_trace(self, proposal_id: str, plan_steps: List[str]) -> None:
        TRACE_FILE.parent.mkdir(exist_ok=True)
        payload = {"proposal_id": proposal_id, "plan_steps": plan_steps, "tool_calls": self.trace}
        with TRACE_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")