# System design — JS Streaming Music

This document satisfies **Step 2 (Design and Architecture)**. The diagram is defined in **Mermaid source** below and in [`architecture.mmd`](architecture.mmd).

## Components

| Component | Role in codebase |
|-----------|------------------|
| **Retriever (RAG)** | `src/rag/retriever.py` — indexes catalog + docs, retrieves snippets before explanations |
| **Agent / orchestration** | `src/agent/orchestrator.py` — plans steps, calls RAG + recommender, creates pending proposals |
| **Guardrails** | `src/guardrails/policies.py` — query policy, URL allowlist, focus-mode filtering |
| **Recommender** | `src/recommender.py` + `scoring_strategies.py` — Module 3 ranking |
| **Evaluator** | Agent verification: minimum score threshold; re-rank without diversity if confidence is low |
| **Tester** | `tests/` + `tests/reliability/test_stability.py` — pytest + stability experiments |
| **PWA + player** | `pwa/` — human UI, playlist approve/reject, encoder fallback |

## Data flow (input → process → output)

1. **Input:** User taste profile, optional text query, or external URL from the PWA.
2. **Process:** Guardrails → agent orchestration → RAG retrieval → score/rank → evaluator → grounded explanations.
3. **Output:** JSON proposal (human approval required) or approved playlist; playback via local media or encoder chain; audit log entries.

## Where humans and testing check AI results

- **Human-in-the-loop:** Discover returns `pending` until the user **Approve** or **Reject** (`/api/playlist/approve`, `/api/playlist/reject`).
- **Automated verification:** Unit tests assert guardrails, RAG summaries, and agent proposals; reliability tests assert deterministic top-track ranking for fixed profiles.
- **Runtime logging:** `logs/js_streaming.log` and `GET /api/logs/recent` record agent steps and guardrail decisions.

## Diagram (Mermaid)

```mermaid
flowchart LR
  subgraph INPUT["1 · Input"]
    U[Listener in PWA]
    Q[Natural-language query + taste profile]
    EXT[External stream URL]
    U --> Q
    U --> EXT
  end

  subgraph PROCESS["2 · Process (API + AI)"]
    subgraph GR["Guardrails"]
      GQ[Query / policy checks]
      GU[URL allowlist + encoder hints]
    end

    subgraph AGENT["Agent / orchestration"]
      PLAN[Plan steps logged]
      ORCH[StreamingAgent.discover]
      PLAN --> ORCH
    end

    subgraph RAG["RAG retriever"]
      IDX[Index: songs.csv + docs]
      RET[Retrieve top-k snippets]
      IDX --> RET
    end

    subgraph REC["Recommender logic"]
      SCORE[Scoring strategies]
      RANK[Rank top-k + diversity]
      SCORE --> RANK
    end

    subgraph EVAL["Evaluator / verification"]
      VFY[Score threshold check]
      RERANK[Re-rank if low confidence]
      VFY -->|fail| RERANK
    end

    subgraph GEN["Grounded output"]
      NAR[Narrative explanations merge RAG + scores]
    end

    Q --> GQ --> ORCH
    EXT --> GU
    ORCH --> RET
    RET --> NAR
    ORCH --> SCORE
    RANK --> VFY
    VFY -->|pass| NAR
    RERANK --> NAR
  end

  subgraph OUTPUT["3 · Output"]
    PROP[Pending playlist proposal JSON]
    PLAY[Approved playlist + catalog playback]
    LOGS[(logs/js_streaming.log)]
    NAR --> PROP
    GU -->|allowed| ENC[4 encoders + auto-fallback]
    ENC --> PLAY
  end

  subgraph HUMAN["Human-in-the-loop"]
    APR[Approve proposal]
    REJ[Reject proposal]
    PROP --> APR
    PROP --> REJ
    APR --> PLAY
    REJ --> Q
  end

  subgraph TEST["Reliability & testing"]
    PYT[pytest: scoring, RAG, agent, guardrails]
    REL[reliability: stable top track across runs]
    PYT -.-> SCORE
    REL -.-> RANK
  end

  U <-->|REST JSON| ORCH
  ORCH --> LOGS
  GQ --> LOGS
  GU --> LOGS
```

## Optional preview

Export a PNG for slides or README from [Mermaid Live Editor](https://mermaid.live) by pasting `architecture.mmd`. Keep **this `.mmd` / `.md` source** in the repo for grading.