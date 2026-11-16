# JS Streaming Music — Applied AI System

**Portfolio project (AI110 final)** · Extends the **Module 3 Music Recommender Simulation** into a full-stack, responsible AI product: streaming PWA, retrieval-augmented recommendations, agent orchestration, human approval, guardrails, and automated reliability checks.

### Portfolio

| Item | Link / location |
|------|------------------|
| **GitHub (submit here)** | `https://github.com/jeanrussosaus/<your-repo-name>` — push this folder when ready |
| **Live demo (local)** | http://127.0.0.1:8790/ after `python -m src.server` |
| **Execution evidence (graded)** | This README § below + [`docs/execution_evidence.txt`](docs/execution_evidence.txt) |
| **5–7 min talk track** | [`docs/PRESENTATION_GUIDE.md`](docs/PRESENTATION_GUIDE.md) |
| **Loom walkthrough (optional)** | _Add URL here after recording_ |

### What this project says about me as an AI engineer

I build **auditable** applied AI: retrieval and ranking are wired into the product path, not bolted on as a demo script. I default to **human-in-the-loop** when automation affects user playlists, **guardrails and logging** when inputs can be abused, and **pytest + harnesses** when someone needs to grade or hire without watching a video. I’m comfortable evolving a small Module 3 ranker into a full PWA and defending trade-offs (template+RAG vs. opaque LLM, allowlisted URLs vs. open scraping) in a model card.

---

## Presentation and portfolio — reproducible execution evidence (required)

Graders can verify the system **without video** by running the commands below. Captured output is also committed as [`docs/execution_evidence.txt`](docs/execution_evidence.txt) (regenerate anytime).

### Start the server

```bash
cd js-streaming-platform
source .venv/bin/activate
export JS_STREAM_PORT=8790
python -m src.server
```

### Case A — End-to-end health + features list

**Command:**

```bash
curl -sS http://127.0.0.1:8790/api/health | python3 -m json.tool
```

**Output:**

```json
{
  "ok": true,
  "service": "js-streaming-music",
  "tracks": 18,
  "playlist_size": 0,
  "features": ["rag", "agent", "guardrails", "hitl", "reliability_tests"]
}
```

### Case B — AI behavior (RAG + agent + confidence)

**Input:**

```bash
curl -sS -X POST http://127.0.0.1:8790/api/discover \
  -H 'Content-Type: application/json' \
  -d '{"query":"chill lofi focus","genre":"lofi","mood":"chill","energy":0.38,"k":2}'
```

**Output (abridged — key fields):**

```json
{
  "proposal_id": "c98dccaf",
  "status": "pending",
  "confidence_score": 0.91,
  "rag_sources_indexed": 25,
  "tool_trace_preview": [
    "tool_guard_query",
    "tool_retrieve",
    "tool_rank",
    "tool_focus_filter",
    "tool_verify"
  ],
  "rag_chunk_ids": ["README.md", "model_card.md", "song-2", "song-4"],
  "top_recommendation": {
    "title": "Library Rain",
    "genre": "lofi",
    "score": 5.46,
    "explanation": "For \"chill lofi focus\", we used curator notes (...syn-focus-rule...) to suggest Library Rain..."
  },
  "verification": { "top_score": 5.46, "passed": true, "threshold": 1.5 }
}
```

Shows **RAG** (multi-source chunks), **agent tools**, **grounded explanation**, and **verification**.

### Case C — Human-in-the-loop (approve playlist)

**Input** (use `proposal_id` from Case B):

```bash
curl -sS -X POST http://127.0.0.1:8790/api/playlist/approve \
  -H 'Content-Type: application/json' \
  -d '{"proposal_id": "c98dccaf"}'
```

**Output (abridged):**

```json
{
  "ok": true,
  "playlist": [
    { "title": "Library Rain", "genre": "lofi", "score": 5.46 },
    { "title": "Midnight Coding", "genre": "lofi", "score": 4.92 }
  ]
}
```

Playlist updates **only** after approval (reject leaves library unchanged — test in UI or API).

### Case D — Guardrail (reliability / safety)

**Input:**

```bash
curl -sS -X POST http://127.0.0.1:8790/api/sources/validate \
  -H 'Content-Type: application/json' \
  -d '{"url":"javascript:alert(1)"}'
```

**Output:**

```json
{
  "ok": false,
  "reason": "Scheme 'javascript' is not allowed.",
  "meta": {}
}
```

### Case E — Automated evaluation harness

**Commands:**

```bash
pytest -q
python scripts/evaluation_harness.py
```

**Output:**

```text
15 passed in 0.05s
PASS  discover_chill                confidence=0.91 tools=[...]
PASS  discover_technical_tone       confidence=0.74 tools=[...]
PASS  url_guard                     Scheme 'javascript' is not allowed.
PASS  tone_specialization           casual vs technical differ
pytest: 15 passed, 0 failed
cases: 4/4 passed
```

To refresh evidence after code changes: run the curl commands in Cases A–D while the server is on **8790**, then `pytest -q` and `python scripts/evaluation_harness.py`, and save the combined output to **`docs/execution_evidence.txt`** (a current copy is already in the repo).

---

## Original project (Modules 1–3)

**Name:** **Music Recommender Simulation** (*VibeFinder 1.0*) — from  
`ai110-module3show-musicrecommendersimulation-starter` (CodePath Module 3).

**Original goals:** Load a small tagged song catalog from CSV, score each track against a listener’s stated **genre, mood, and energy**, rank the top five matches, and print **plain-English reasons** in the terminal. It taught **content-based filtering** and transparent scoring—not a black-box neural recommender.

**Original capabilities:** `src/recommender.py` + scoring strategies, diversity penalties, CLI demo profiles, and pytest for ranking behavior. That core is still the ranking engine inside this final system.

---

## Title and summary — what this project does and why it matters

**JS Streaming Music** is an installable **progressive web app** that lets listeners browse a catalog, play local demo audio, request **AI-curated playlists** from natural language, and stream **allowlisted external URLs** with automatic encoder fallback.

**Why it matters:** Real music products must combine **recommendation logic**, **safety policy**, and **human oversight**. This project shows end-to-end design: the same scores from VibeFinder now run behind an API, explanations are **grounded in retrieved documentation** (RAG), proposals stay **pending until the user approves them**, and tests plus logs make behavior **auditable**—skills directly relevant to applied ML and trustworthy AI roles.

---

## Architecture overview

Data moves in three stages (**input → process → output**):

1. **Input** — Taste profile + optional query from the PWA, or an external stream URL.
2. **Process** — Guardrails → **StreamingAgent** (orchestration) → **RAG retriever** → VibeFinder scoring/ranking → **evaluator** (confidence threshold / re-rank) → grounded explanations.
3. **Output** — Pending playlist JSON (human-in-the-loop), approved library, playback (local WAV or 4 encoders), structured logs.

```
Listener → Guardrails → Agent → RAG + Recommender → Evaluator → Proposal → [Approve/Reject] → Playlist
```

Full **Mermaid source** (required for submission): [`diagrams/architecture.mmd`](diagrams/architecture.mmd)  
Narrated version: [`diagrams/architecture.md`](diagrams/architecture.md)

| Component | Location |
|-----------|----------|
| RAG retriever | `src/rag/retriever.py` |
| Agent / orchestration | `src/agent/orchestrator.py` |
| Guardrails | `src/guardrails/policies.py` |
| Recommender (Module 3) | `src/recommender.py`, `src/scoring_strategies.py` |
| API + static PWA | `src/server.py`, `pwa/` |
| Tests | `tests/`, `tests/reliability/test_stability.py` |

---

## Setup instructions

**Prerequisites:** Python 3.10+ (tested on 3.13), macOS/Linux/Windows.

1. **Clone and enter the project**

   ```bash
   cd js-streaming-platform
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate          # macOS / Linux
   # .venv\Scripts\Activate.ps1       # Windows PowerShell
   ```

3. **Install dependencies**

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run tests** (verifies recommender, RAG, agent, guardrails, reliability)

   ```bash
   python scripts/make_icon.py
   pytest
   ```

5. **Start the server**

   ```bash
   export JS_STREAM_PORT=8790   # optional; default is 8790
   python -m src.server
   ```

   Or double-click **`Start JS Streaming Music.command`** (macOS).

6. **Open the app**

   - PWA: **http://127.0.0.1:8790/**
   - Health check: **http://127.0.0.1:8790/api/health**

   **Note:** Use port **8790**, not 8765. An old service worker from another app on 8765 can show the wrong UI; use `http://127.0.0.1:8765/clear.html` once if needed, then stay on 8790.

7. **Optional — terminal-only VibeFinder (Module 3 CLI)**

   ```bash
   python -m src.main
   ```

---

## Sample interactions

These examples show the **integrated AI pipeline** (not side scripts). Run them while the server is up.

### Example 1 — Discover with RAG + agent (pending human approval)

**Input** (`POST /api/discover`):

```json
{
  "query": "chill lofi focus",
  "genre": "lofi",
  "mood": "chill",
  "energy": 0.38,
  "likes_acoustic": true,
  "k": 3
}
```

**Output (abridged):** `status: "pending"`, `proposal_id`, `plan_steps` (parse → RAG → score → verify → compose), `rag_chunks` from README/model card/songs, and `recommendations` with **grounded explanations**, e.g. top track *Library Rain* with score **5.46** and narrative citing retrieved catalog notes—not a generic template alone.

Approve in the UI or:

```bash
curl -X POST http://127.0.0.1:8790/api/playlist/approve \
  -H 'Content-Type: application/json' \
  -d '{"proposal_id": "<id from discover>"}'
```

### Example 2 — Guardrails on external stream URL

**Input** (`POST /api/sources/validate`):

```json
{ "url": "https://www.youtube.com/watch?v=abc" }
```

**Output:**

```json
{
  "ok": true,
  "reason": "OK",
  "meta": {
    "host": "www.youtube.com",
    "encoder_hints": ["iframe_embed", "video_element", "direct_audio", "fetch_blob"]
  }
}
```

The PWA tries encoders in order until playback succeeds.

**Blocked input example:** `javascript:alert(1)` → `ok: false`, scheme rejected (logged in `logs/js_streaming.log`).

### Example 3 — Module 3 CLI ranking (baseline recommender)

**Input:** Chill profile via built-in demo in `src/main.py` (`genre=lofi`, `mood=chill`, `energy=0.38`).

**Output (typical top line):** *Library Rain* / *Midnight Coding* with reason strings such as `genre match (+2.0); mood match (+1.0); energy similarity (+1.46); acoustic bonus (+0.5)`.

Run: `python -m src.main`

---

## Design decisions and trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| Extend **VibeFinder** instead of a new domain | Meets “evolve Modules 1–3” requirement; ranking stays explainable | Still content-based; no collaborative filtering |
| **Template + RAG grounding** for explanations vs. paid LLM API | Reproducible, no API keys, auditable text | Less fluent prose than a large language model |
| **Human-in-the-loop** before playlist commit | Reduces blind trust in automated rankings | Extra click; slower than auto-add |
| **URL allowlist** + encoder fallback | Compliance and resilient playback | Many legitimate streams are blocked until allowlist grows |
| **FastAPI + static PWA** | Single command to demo for employers | Not a production CDN or mobile native app |
| **Synthetic WAV tones** per track | Offline, reproducible media | Not real mastered audio |

---

## Reliability and evaluation (Step 4)

**Summary:** **12 / 12** `pytest` cases passed. Discover **confidence scores averaged 0.79** (0.71–0.91 on three profiles). **Guardrails + logging** record blocked URLs and low-confidence re-ranks; **human checklist: 6 / 7 pass** (offline catalog message is partial fail). Accuracy of top picks improved after **verification threshold**, **URL allowlist**, and **focus-mode** filtering.

| Mechanism | Where |
|-----------|--------|
| Automated tests | `pytest` → `tests/` |
| Confidence score | `confidence_score` + `verification` in `POST /api/discover` |
| Logging | `logs/js_streaming.log`, `GET /api/logs/recent` |
| Human evaluation table | [`model_card.md` §7.5](model_card.md) |
| JSON results | [`docs/evaluation_results.json`](docs/evaluation_results.json) — refresh: `python scripts/run_evaluation.py` |

### Human evaluation (excerpt)

| Test input | Evaluation criteria | Result |
|------------|---------------------|--------|
| `chill lofi focus` discover | Top tracks match lofi/chill; grounded explanations | Pass |
| `javascript:` URL | Rejected safely | Pass |
| Empty query discover | Returns recommendations without crash | Pass |
| Approve vs reject playlist | Library updates only on approve | Pass |

Full table and confidence breakdown: **model_card §7.5**.

---

## Testing summary (development notes)

**What worked**

- `pytest` (12 tests): recommender, guardrails, RAG, agent, evaluation, reliability stability.
- End-to-end: Home → Discover → Approve → Library; bottom player for catalog audio.
- Structured evaluation export for grading (`docs/evaluation_results.json`).

**What didn’t / limitations**

- External **fetch_blob** encoder often fails on CORS-heavy URLs.
- Empty or vague queries produce **less specific** RAG snippets (still functional).
- Small catalog (18 songs) limits diversity (model card §6).

**What we learned**

- Exposing **`confidence_score`** makes weak matches visible before humans approve.
- Parseable logs and JSON beat demo-only proof for portfolio review.

---

## Reflection (brief)

Building this final system showed how **Module 3 transparency** (explicit scoring reasons) scales into a product only when paired with **retrieval, policy, and human gates**. The surprising part was how much UX trust depends on *where* approval happens—not on fancier math alone.

**Graded responsible-AI reflection (Step 5)** — limitations, misuse prevention, testing surprises, AI collaboration (accepted vs. changed suggestions): **[`model_card.md` §10](model_card.md)**.

---

## Additional documentation

- [**Model Card**](model_card.md) — bias, evaluation, responsible use  
- [**Final project brief**](docs/FINAL_PROJECT_BRIEF.md)  
- [**AI interaction log**](ai_interactions.md) — stretch / tooling notes  
- **Legacy deep-dive** on VibeFinder scoring: see model card §5 and `src/scoring_strategies.py`

---

## Optional stretch features (+8 rubric)

| Feature | Implementation | How to verify |
|---------|----------------|---------------|
| **RAG enhancement** | `docs/retrieval/`, `data/rag_sources.json` merged into index | `pytest tests/test_stretch.py` — before/after in model_card §7.6.1 |
| **Agentic enhancement** | `src/agent/tools.py`, traces in **`logs/agent_traces.jsonl`** | See **`ai_interactions.md`** |
| **Tone specialization** | `explain_tone`: `casual` \| `technical` on discover API | `POST /api/discover` with `"explain_tone": "technical"` |
| **Evaluation harness** | `python scripts/evaluation_harness.py` | PASS/FAIL table + `docs/evaluation_harness_summary.json` |

```bash
python scripts/evaluation_harness.py
python scripts/run_evaluation.py
```

---

## License / context

Course portfolio project for AI110. Separate from work repos (`tssjbs`, Elpis Express). Intended public GitHub: **`jeanrussosaus`** when submitted.