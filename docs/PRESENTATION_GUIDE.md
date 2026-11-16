# 5–7 minute presentation guide (Engineer's Pitch)

**Live demo URL:** http://127.0.0.1:8790/ (run `python -m src.server` first)

| Time | Slide | Say / show |
|------|-------|------------|
| 0:00 | Title | **JS Streaming Music** — applied AI from Module 3 VibeFinder |
| 0:30 | **Problem** | Listeners need explainable recommendations + safe streaming; black-box playlists are hard to trust |
| 1:30 | **Logic** | PWA → API → **RAG** (25 sources) → **agent tools** → rank → **confidence** → pending proposal |
| 2:30 | **Demo** | Home → Discover “chill lofi focus” → show RAG ids + explanation → **Approve** → playlist; optional external URL guardrail |
| 3:30 | **Reliability** | `confidence_score` 0.91; pytest 15/15; harness 4/4; guardrail blocks `javascript:` |
| 4:30 | **Reflection** | HITL + logs matter as much as scores; model_card ethics — point to GitHub README evidence |
| 5:30 | **Close** | Portfolio link; what I’d add next (mood penalties, larger catalog) |

### Optional Loom (~3 min screen capture)

1. Start server + open 8790  
2. Run discover + approve  
3. Show `docs/execution_evidence.txt` and architecture diagram  

Add link in README: `Loom: (paste URL here)`