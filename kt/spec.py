"""Spesifikasi format + zona aman + preset encode (dari riset Tahap 1)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Format:
    name: str
    w: int
    h: int
    fps: int


SHORTS = Format("shorts", 1080, 1920, 60)
LONG1080 = Format("long1080", 1920, 1080, 30)
LONG1440 = Format("long1440", 2560, 1440, 30)

FORMATS = {f.name: f for f in (SHORTS, LONG1080, LONG1440)}


@dataclass(frozen=True)
class SafeZone:
    """Margin UI (px, skala format). Konten kritis tidak boleh masuk margin."""
    top: int
    bottom: int
    left: int
    right: int


# Zona aman Shorts 2026: tengah 1080x1350; bawah ~450 caption, kanan ~15% tombol.
SAFE_SHORTS = SafeZone(top=180, bottom=480, left=60, right=160)
SAFE_LONG = SafeZone(top=64, bottom=96, left=64, right=64)
SAFE = {"shorts": SAFE_SHORTS, "long1080": SAFE_LONG, "long1440": SAFE_LONG}


@dataclass(frozen=True)
class Encode:
    vcodec: str = "libx264"
    profile: str = "high"
    pix_fmt: str = "yuv420p"
    preset: str = "slow"
    tune: str = "animation"
    acodec: str = "aac"
    abitrate: str = "256k"
    ar: int = 48000
    # H.264 sesuai anjuran YouTube: CABAC, GOP tertutup = fps/2, 2 B-frame.
    bf: int = 2
    cabac: bool = True


@dataclass(frozen=True)
class EncodeTarget:
    fmt: str
    vbitrate: str
    maxrate: str
    bufsize: str
    gop: int
    level: str


# VBR target di atas referensi YouTube agar tahan kompresi ulang (riset Tahap 1).
ENCODE_TARGETS = {
    "shorts": EncodeTarget("shorts", "14M", "18M", "26M", 30, "4.2"),
    "long1080": EncodeTarget("long1080", "10M", "14M", "20M", 15, "4.1"),
    "long1440": EncodeTarget("long1440", "20M", "26M", "40M", 15, "5.0"),
}

LUFS_TARGET = -14.0
TRUE_PEAK_MAX = -1.0  # dBTP
