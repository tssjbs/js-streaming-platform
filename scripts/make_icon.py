"""Minimal PNG icon for PWA manifest (192x192)."""

from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pwa" / "icons" / "icon-192.png"


def png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def write_png(path: Path, w: int, h: int, rgb) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b""
    r, g, b = rgb
    for _ in range(h):
        raw += b"\x00" + bytes([r, g, b]) * w
    compressed = zlib.compress(raw, 9)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n"
    out += png_chunk(b"IHDR", ihdr)
    out += png_chunk(b"IDAT", compressed)
    out += png_chunk(b"IEND", b"")
    path.write_bytes(out)


if __name__ == "__main__":
    write_png(OUT, 192, 192, (155, 93, 229))
    print("Wrote", OUT)