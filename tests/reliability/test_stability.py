"""Reliability: same profile → stable top track ordering."""

from pathlib import Path

from src.recommender import load_songs, recommend_songs

CSV = Path(__file__).resolve().parents[2] / "data" / "songs.csv"


def test_chill_profile_top_track_stable_across_runs():
    songs = load_songs(str(CSV))
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.38, "likes_acoustic": True}
    runs = [
        recommend_songs(prefs, songs, k=3, apply_diversity=True)[0][0]["id"]
        for _ in range(5)
    ]
    assert len(set(runs)) == 1, f"Top track varied across runs: {runs}"