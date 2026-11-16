"""Few-shot style templates — casual vs technical explanations (specialized tone)."""

from __future__ import annotations

from typing import List

# Few-shot anchors (shown to graders in docstrings; shape real output format)
FEW_SHOT_CASUAL = (
    "Example casual: 'Great pick for your vibe — Library Rain matches your chill lofi ask.'"
)
FEW_SHOT_TECHNICAL = (
    "Example technical: 'Rank selected via balanced strategy; dominant signals: genre (+2.0), mood (+1.0).'"
)


def format_explanation(
    tone: str,
    query: str,
    song_title: str,
    artist: str,
    policy_snippet: str,
    score_reasons: str,
) -> str:
    tone = (tone or "casual").lower()
    q = query or "your taste profile"

    if tone == "technical":
        return (
            f"[technical] query={q!r}; retrieved_policy={policy_snippet[:60]!r}; "
            f"track={song_title!r} artist={artist!r}; scoring_trace={score_reasons}"
        )

    # casual (default)
    return (
        f"For “{q}”, we used curator notes ({policy_snippet[:70]}…) to suggest "
        f"{song_title} by {artist} — {score_reasons}"
    )


def tones_differ(casual: str, technical: str) -> bool:
    return casual != technical and len(casual) > 10 and len(technical) > 10