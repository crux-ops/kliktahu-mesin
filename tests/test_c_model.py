"""Uji model Bagian C (penuh di CI; butuh unduhan model sekali)."""
import wave
from pathlib import Path

import numpy as np
import pytest

fw = pytest.importorskip("faster_whisper")  # noqa: F401

from kt.align import Aligner, check_monotonic, coverage, words_of

MODEL = "base"
REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "fixtures" / "bicara-id.mp3"
KALIMAT = "Jantung memompa darah ke seluruh tubuh."
BATAS = 0.8  # terbukti sapu C3: 5/6 tanpa prompt


def _tulis_wav(path, data, sr=16000):
    data = np.asarray(data, dtype=np.float32)
    pcm = (np.clip(data, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())


def _sidik(words):
    return [(w.text, round(w.start, 3), round(w.end, 3)) for w in words]


def test_sunyi_deterministik(tmp_path):
    wav = str(tmp_path / "sunyi.wav")
    _tulis_wav(wav, np.zeros(16000))
    al = Aligner(MODEL)
    a = words_of(al.align(wav))
    b = words_of(al.align(wav))
    assert _sidik(a) == _sidik(b)
    assert check_monotonic(a)
    for w in a:
        assert 0.0 <= w.start < w.end <= 1.6
        assert 0.0 <= w.conf <= 1.0


def test_fixture_indonesia_selaras():
    assert FIXTURE.exists(), f"fixture hilang: {FIXTURE}"
    al = Aligner(MODEL)
    a = words_of(al.align(str(FIXTURE)))
    b = words_of(al.align(str(FIXTURE)))
    assert len(a) >= 4, f"kata terlalu sedikit: {a}"
    assert _sidik(a) == _sidik(b)
    assert check_monotonic(a)
    for w in a:
        assert 0.0 <= w.start < w.end <= 30.0
        assert 0.0 <= w.conf <= 1.0
    c = coverage(KALIMAT, a)
    assert c["rasio"] >= BATAS, f"liputan rendah: {c} <- {a}"
