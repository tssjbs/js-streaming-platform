from pathlib import Path

from src.agent.orchestrator import StreamingAgent

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "songs.csv"


def test_agent_discover_returns_rag_and_pending_proposal():
    agent = StreamingAgent(str(CSV))
    out = agent.discover({"query": "chill lofi", "genre": "lofi", "mood": "chill", "energy": 0.38})
    assert out["status"] == "pending"
    assert out["recommendations"]
    assert out["rag_chunks"]
    assert "tool_retrieve" in " ".join(out["plan_steps"])


def test_human_in_the_loop_approve():
    agent = StreamingAgent(str(CSV))
    out = agent.discover({"genre": "pop", "mood": "happy", "energy": 0.85})
    pid = out["proposal_id"]
    res = agent.approve(pid)
    assert res["ok"]
    assert len(res["playlist"]) >= 1