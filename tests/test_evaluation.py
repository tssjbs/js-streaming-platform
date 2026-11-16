"""Reliability: confidence scoring, missing context, guardrail failures."""

from pathlib import Path

from src.agent.orchestrator import StreamingAgent
from src.guardrails.policies import validate_external_url
from src.rag.retriever import SongRAG

CSV = Path(__file__).resolve().parents[1] / "data" / "songs.csv"


def test_discover_exposes_confidence_score():
    agent = StreamingAgent(str(CSV))
    out = agent.discover(
        {"query": "chill lofi focus", "genre": "lofi", "mood": "chill", "energy": 0.38}
    )
    assert 0.0 <= out["confidence_score"] <= 1.0
    assert out["confidence_score"] >= 0.8
    assert out["verification"]["passed"] is True


def test_discover_empty_query_still_returns_recommendations():
    agent = StreamingAgent(str(CSV))
    out = agent.discover({"genre": "pop", "mood": "happy", "energy": 0.85, "query": ""})
    assert out["recommendations"]
    assert out["confidence_score"] > 0


def test_rag_missing_query_uses_profile_fallback():
    songs = load_songs_stub()
    rag = SongRAG(songs)
    chunks = rag.retrieve("", k=2)
    assert isinstance(chunks, list)


def test_invalid_url_blocked_with_reason():
    ok, reason, _ = validate_external_url("javascript:alert(1)")
    assert not ok
    assert reason


def load_songs_stub():
    agent = StreamingAgent(str(CSV))
    return agent.songs