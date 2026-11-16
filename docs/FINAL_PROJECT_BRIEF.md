# JS Streaming Platform — Applied AI System (AI110 Final)

**Working title:** JS Streaming Platform  
**Evolution of:** Module 3 — Music Recommender Simulation (VibeFinder)  
**Base repo:** `tssjbs/ai110-module3show-musicrecommendersimulation-starter`  
**Agent pattern reference:** `codepath/ai110-module4tinker-docubot-starter`  
**GitHub:** https://github.com/tssjbs/js-streaming-platform (`tssjbs` / jeanrussosaus@gmail.com) — separate from Elpis (`elpisexpressadmin-svg`)  
**Local workspace:** `AI110/AI1110/js-streaming-platform`

## Problem (Engineer's Pitch)

Listeners want a **friendly streaming-style PWA** that builds **playlists**, surfaces **personalized recommendations** from a song catalog, and can **encode / play from approved external sources**—without opaque black-box ranking. The system must explain *why* each track was suggested and let a **human approve** changes before they hit the playlist.

## Product surface (PWA)

| Area | Intent |
|------|--------|
| Home / Now playing | Friendly UI, installable PWA (`manifest` + service worker) |
| Playlists | Create, reorder, save local + server-backed state |
| Discover | Recommendation flow from taste profile + RAG over song/docs metadata |
| Sources menu | User supplies external URLs / embed codes; **guardrails** validate before playback |
| Review queue | **Human-in-the-loop** — approve or reject agent-proposed playlist edits |

## Applied AI components (rubric alignment)

| Term | Planned implementation |
|------|-------------------------|
| **RAG** | Retrieve song rows + `model_card.md` / catalog notes; ground natural-language explanations |
| **Agent** | Orchestrator plans: profile → retrieve → score → propose playlist diff → await approval |
| **Orchestration** | Python modules: `rag/`, `agent/`, `recommender.py`, API layer for PWA |
| **Guardrails** | Block unsafe external URLs, profanity in queries, energy/genre policy for “focus mode” |
| **Bias** | Document content-based bias; diversity penalty (existing stretch); audit log |
| **Risk / compliance** | Model card, data sourcing, no real DRM bypass; explicit allowlist for external media |
| **Human-in-the-loop** | UI + API: pending recommendations until user confirms |
| **Verification** | Unit tests on scoring; schema checks on catalog |
| **Reliability testing** | `tests/reliability/` — fixed profiles → expected top-k stability |

## Architecture

See `diagrams/architecture.mmd` (required Mermaid source).

## Folder layout (target)

```
js-streaming-platform/
  assets/           # screenshots, architecture PNG exports
  diagrams/         # architecture.mmd (required)
  data/             # songs.csv
  docs/             # this brief + API notes for RAG
  pwa/              # installable front-end
  src/
    recommender.py  # Module 3 core (keep)
    agent/          # planner + HITL hooks (Module 4/5 style)
    rag/            # retrieval over catalog + docs
    guardrails/     # policy checks
  tests/
    test_recommender.py
    reliability/
```

## Next inputs from you

1. CodePath **step-by-step** instructions (we implement in order).  
2. Screenshot / rubric for **PowerPoint pitch** (Problem, Logic, Reliability, Reflection — 4 min demo + 1 min feedback).  
3. ~~Create repo and push~~ — live at **tssjbs/js-streaming-platform**.

## Environment

```bash
cd "/Users/jeansaus/Desktop/Appdev &  Cyber 2026/AI110/AI1110/js-streaming-platform"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```