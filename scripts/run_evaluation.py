"""Write parseable evaluation summary to docs/evaluation_results.json."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agent.orchestrator import StreamingAgent

CSV = ROOT / "data" / "songs.csv"
OUT = ROOT / "docs" / "evaluation_results.json"

PROFILES = [
    {"name": "chill_lofi", "body": {"query": "chill lofi focus", "genre": "lofi", "mood": "chill", "energy": 0.38}},
    {"name": "high_energy_pop", "body": {"genre": "pop", "mood": "happy", "energy": 0.85, "query": "workout"}},
    {"name": "niche_genre", "body": {"genre": "classical", "mood": "relaxed", "energy": 0.3, "query": ""}},
]


def main() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    passed = failed = 0
    import re

    m = re.search(r"(\d+)\s+passed", proc.stdout)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", proc.stdout)
    if m:
        failed = int(m.group(1))

    agent = StreamingAgent(str(CSV))
    runs = []
    confidences = []
    for p in PROFILES:
        out = agent.discover(p["body"])
        confidences.append(out["confidence_score"])
        runs.append(
            {
                "profile": p["name"],
                "top_title": out["recommendations"][0]["title"] if out["recommendations"] else None,
                "confidence_score": out["confidence_score"],
                "verification_passed": out["verification"]["passed"],
                "reranked": out["verification"]["reranked"],
            }
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "automated_tests": {
            "passed": passed,
            "failed": failed,
            "pytest_exit_code": proc.returncode,
        },
        "confidence_scores": {
            "average": round(sum(confidences) / len(confidences), 2) if confidences else 0,
            "min": min(confidences) if confidences else 0,
            "max": max(confidences) if confidences else 0,
            "by_profile": runs,
        },
        "logging": {
            "file": "logs/js_streaming.log",
            "api": "/api/logs/recent",
        },
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(json.dumps(payload["automated_tests"], indent=2))


if __name__ == "__main__":
    main()