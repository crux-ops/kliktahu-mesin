"""Uji model Bagian C (penuh di CI; lewati gracious bila tak ada model/binari)."""
import shutil
import subprocess
import wave

import numpy as np
import pytest

fw = pytest.importorskip("faster_whisper")  # noqa: F401

from kt.align import Aligner, check_monotonic, coverage, words_of

MODEL = "base"


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


def _durasi_wav(path):
    with wave.open(str(path), "rb") as f:
        return f.getnframes() / float(f.getframerate())


def _periksa_kata(wav, words):
    dur = _durasi_wav(wav)
    assert check_monotonic(words)
    for w in words:
        assert 0.0 <= w.start < w.end <= dur + 0.6, (w, dur)
        assert 0.0 <= w.conf <= 1.0


def test_sunyi_deterministik(tmp_path):
    wav = str(tmp_path / "sunyi.wav")
    _tulis_wav(wav, np.zeros(16000))
    al = Aligner(MODEL)
    a = words_of(al.align(wav))
    b = words_of(al.align(wav))
    assert _sidik(a) == _sidik(b)
    _periksa_kata(wav, a)


@pytest.mark.skipif(shutil.which("espeak-ng") is None, reason="butuh espeak-ng (CI)")
def test_espeak_indonesia_selaras(tmp_path):
    kalimat = "Jantung memompa darah"
    wav = str(tmp_path / "bicara.wav")
    r = subprocess.run(["espeak-ng", "-v", "id", "-s", "150", "-w", wav, kalimat],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-500:]
    al = Aligner(MODEL)
    a = words_of(al.align(wav))
    b = words_of(al.align(wav))
    assert len(a) >= 2, f"kata terlalu sedikit: {a}"
    assert _sidik(a) == _sidik(b)
    _periksa_kata(wav, a)
    c = coverage(kalimat, a)
    assert c["rasio"] >= 0.5, f"liputan rendah: {c} <- {a}"
