"""RAG: retrieve catalog + documentation before grounded recommendation text."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

from src.app_logging import log_event
from src.rag.tone import format_explanation

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_GLOBS = ("docs/*.md", "model_card.md", "README.md")
RETRIEVAL_DIR = ROOT / "docs" / "retrieval"
SYNTHETIC_JSON = ROOT / "data" / "rag_sources.json"


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def load_synthetic_notes() -> List[Tuple[str, str]]:
    if not SYNTHETIC_JSON.is_file():
        return []
    rows = json.loads(SYNTHETIC_JSON.read_text(encoding="utf-8"))
    out = []
    for row in rows:
        blob = f"{' '.join(row.get('tags', []))} {row.get('text', '')}"
        out.append((row.get("id", "syn"), blob))
    return out


def build_document_corpus(songs: List[Dict]) -> List[Tuple[str, str]]:
    corpus: List[Tuple[str, str]] = []
    for path_pattern in DOCS_GLOBS:
        for path in ROOT.glob(path_pattern):
            if path.is_file():
                corpus.append((path.name, path.read_text(encoding="utf-8", errors="ignore")))
    if RETRIEVAL_DIR.is_dir():
        for path in RETRIEVAL_DIR.glob("*.md"):
            corpus.append((f"retrieval/{path.name}", path.read_text(encoding="utf-8", errors="ignore")))
    corpus.extend(load_synthetic_notes())
    for song in songs:
        blob = (
            f"{song['title']} {song['artist']} genre {song['genre']} mood {song['mood']} "
            f"energy {song['energy']} theme {song.get('lyrical_theme', '')} "
            f"{song.get('mood_detail', '')}"
        )
        corpus.append((f"song-{song['id']}", blob))
    return corpus


def build_index(corpus: List[Tuple[str, str]]) -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = {}
    for doc_id, text in corpus:
        for tok in set(tokenize(text)):
            index.setdefault(tok, []).append(doc_id)
    return index


def score_document(query_tokens: List[str], text: str) -> float:
    doc_tokens = set(tokenize(text))
    if not query_tokens:
        return 0.0
    hits = sum(1 for t in query_tokens if t in doc_tokens)
    return hits / max(len(query_tokens), 1)


class SongRAG:
    def __init__(self, songs: List[Dict]):
        self.songs = songs
        self.corpus = build_document_corpus(songs)
        self.text_by_id = {doc_id: text for doc_id, text in self.corpus}
        self.index = build_index(self.corpus)
        self.source_count = len(self.corpus)

    def retrieve(self, query: str, k: int = 4) -> List[Dict]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        candidate_ids: Dict[str, float] = {}
        for tok in q_tokens:
            for doc_id in self.index.get(tok, []):
                candidate_ids[doc_id] = candidate_ids.get(doc_id, 0) + 1

        scored: List[Tuple[str, float]] = []
        for doc_id, _ in candidate_ids.items():
            text = self.text_by_id[doc_id]
            scored.append((doc_id, score_document(q_tokens, text)))

        scored.sort(key=lambda x: (-x[1], x[0]))
        results = []
        for doc_id, rel in scored[:k]:
            snippet = self.text_by_id[doc_id][:280].replace("\n", " ")
            results.append({"id": doc_id, "score": round(rel, 3), "snippet": snippet})
        log_event("INFO", "rag", "retrieved chunks", query=query, count=len(results), sources=self.source_count)
        return results

    def grounded_summary(
        self,
        query: str,
        song: Dict,
        score_reasons: str,
        chunks: List[Dict],
        tone: str = "casual",
    ) -> str:
        cues = []
        for ch in chunks:
            if ch["id"].startswith("song-"):
                continue
            if any(t in ch["snippet"].lower() for t in tokenize(query)[:6]):
                cues.append(ch["snippet"][:120])
        policy = cues[0] if cues else "Content-based matching uses genre, mood, and energy from the catalog."
        return format_explanation(tone, query, song["title"], song["artist"], policy, score_reasons)