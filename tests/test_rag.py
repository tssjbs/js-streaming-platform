from src.rag.retriever import SongRAG


def test_rag_grounded_summary_uses_retrieval():
    songs = [
        {
            "id": 2,
            "title": "Midnight Coding",
            "artist": "LoRoom",
            "genre": "lofi",
            "mood": "chill",
            "energy": 0.4,
            "lyrical_theme": "focus",
            "mood_detail": "nostalgic",
        }
    ]
    rag = SongRAG(songs)
    chunks = rag.retrieve("chill lofi focus", k=3)
    text = rag.grounded_summary("chill focus", songs[0], "genre match", chunks)
    assert "Midnight Coding" in text
    assert "chill" in text.lower() or "focus" in text.lower()