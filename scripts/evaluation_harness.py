#!/usr/bin/env python3
"""Stretch: evaluation harness — predefined inputs, pass/fail summary on stdout."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agent.orchestrator import StreamingAgent
from src.guardrails.policies import validate_external_url
from src.rag.tone import format_explanation, tones_differ

CSV = ROOT / "data" / "songs.csv"

CASES = [
    {
        "name": "discover_chill",
        "fn": "discover",
        "body": {"query": "chill lofi focus", "genre": "lofi", "mood": "chill", "energy": 0.38},
        "check": lambda o: o["confidence_score"] >= 0.8 and o["recommendations"][0]["genre"] == "lofi",
    },
    {
        "name": "discover_technical_tone",
        "fn": "discover",
        "body": {
            "query": "workout",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.85,
            "explain_tone": "technical",
        },
        "check": lambda o: "[technical]" in o["recommendations"][0]["explanation"],
    },
    {
        "name": "url_guard",
        "fn": "url",
        "url": "javascript:alert(1)",
        "check": lambda ok: not ok,
    },
    {
        "name": "tone_specialization",
        "fn": "tone",
        "check": lambda _: tones_differ(
            format_explanation("casual", "q", "T", "A", "policy", "reasons"),
            format_explanation("technical", "q", "T", "A", "policy", "reasons"),
        ),
    },
]


def run_pytest() -> tuple[int, int]:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, capture_output=True, text=True)
    import re

    passed = int(re.search(r"(\d+)\s+passed", proc.stdout).group(1)) if re.search(r"(\d+)\s+passed", proc.stdout) else 0
    failed = int(re.search(r"(\d+)\s+failed", proc.stdout).group(1)) if re.search(r"(\d+)\s+failed", proc.stdout) else 0
    return passed, failed


def main() -> int:
    agent = StreamingAgent(str(CSV))
    results = []
    failures = 0

    print("=== JS Streaming Music — Evaluation Harness ===\n")
    for case in CASES:
        ok = False
        detail = ""
        if case["fn"] == "discover":
            out = agent.discover(case["body"])
            ok = case["check"](out)
            detail = f"confidence={out.get('confidence_score')} tools={out.get('tool_trace_preview')}"
        elif case["fn"] == "url":
            ok, reason, _ = validate_external_url(case["url"])
            ok = case["check"](ok)
            detail = reason
        elif case["fn"] == "tone":
            ok = case["check"](None)
            detail = "casual vs technical differ"

        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        results.append({"case": case["name"], "status": status, "detail": detail})
        print(f"{status:4}  {case['name']:28}  {detail}")

    p, f = run_pytest()
    print(f"\npytest: {p} passed, {f} failed")
    print(f"cases: {len(results) - failures}/{len(results)} passed")

    out_path = ROOT / "docs" / "evaluation_harness_summary.json"
    out_path.write_text(
        json.dumps({"harness_cases": results, "pytest": {"passed": p, "failed": f}}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {out_path}")
    return 1 if failures or f else 0


if __name__ == "__main__":
    raise SystemExit(main())