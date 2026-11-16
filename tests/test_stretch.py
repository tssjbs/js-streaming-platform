"""Stretch feature checks: multi-source RAG, tone specialization, agent tools."""

from pathlib import Path

from src.agent.orchestrator import StreamingAgent
from src.agent.tools import AgentToolkit
from src.rag.retriever import SongRAG
from src.rag.tone import format_explanation, tones_differ

CSV = Path(__file__).resolve().parents[1] / "data" / "songs.csv"


def test_multi_source_rag_indexes_custom_docs():
    agent = StreamingAgent(str(CSV))
    assert agent.rag.source_count >= 22  # songs + readme + retrieval + synthetic
    chunks = agent.rag.retrieve("focus lofi coding", k=5)
    ids = {c["id"] for c in chunks}
    assert any("genre_guide" in i or "syn-focus" in i for i in ids)


def test_explain_tone_differs():
    song = {"title": "Library Rain", "artist": "Paper Lanterns"}
    casual = format_explanation("chill", "chill", song["title"], song["artist"], "lofi focus guide", "genre match")
    technical = format_explanation(
        "technical", "chill", song["title"], song["artist"], "lofi focus guide", "genre match"
    )
    assert tones_differ(casual, technical)
    assert "[technical]" in technical


def test_agent_tool_chain_runs():
    agent = StreamingAgent(str(CSV))
    out = agent.discover({"query": "chill lofi", "genre": "lofi", "mood": "chill", "energy": 0.38})
    assert "tool_retrieve" in out["tool_trace_preview"]
    assert "tool_rank" in out["tool_trace_preview"]
    assert "tool_verify" in out["tool_trace_preview"]