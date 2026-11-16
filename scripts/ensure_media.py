"""Create short demo .wav files for each catalog track (reproducible, offline)."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.recommender import load_songs
MEDIA = ROOT / "pwa" / "media"
CSV = ROOT / "data" / "songs.csv"

SAMPLE_RATE = 22050
DURATION_SEC = 2.0


def tone_wav(path: Path, frequency: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = int(SAMPLE_RATE * DURATION_SEC)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        for i in range(n_frames):
            t = i / SAMPLE_RATE
            envelope = min(1.0, t * 4) * max(0.0, 1.0 - (t / DURATION_SEC))
            sample = int(16000 * envelope * math.sin(2 * math.pi * frequency * t))
            w.writeframes(struct.pack("<h", sample))


def main() -> None:
    songs = load_songs(str(CSV))
    for song in songs:
        freq = 220 + (song["id"] * 37) % 520
        tone_wav(MEDIA / f"track_{song['id']}.wav", float(freq))
    print(f"Wrote {len(songs)} demo tracks to {MEDIA}")


if __name__ == "__main__":
    main()