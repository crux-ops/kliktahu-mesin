"""SAPUAN SEMENTARA (hapus setelah eksperimen): cari kalimat TTS-vs-Whisper terbaik."""
import shutil
import subprocess
import wave

import pytest

fw = pytest.importorskip("faster_whisper")  # noqa: F401

from kt.align import Aligner, coverage, words_of

KASUS = [
    ("S1", "id", "150", "Jantung memompa darah"),
    ("S2", "id", "150", "Jantung, memompa, darah."),
    ("S3", "id", "120", "Jantung memompa darah"),
    ("S4", "id", "150", "Matahari bersinar terang"),
    ("S5", "id", "150", "Air mengalir deras"),
    ("S6", "id", "150", "Burung terbang tinggi"),
    ("S7", "en", "150", "The heart pumps blood"),
    ("S8", None, "150", "Jantung memompa darah"),
]


def test_sapu_register(tmp_path):
    if shutil.which("espeak-ng") is None:
        pytest.skip("butuh espeak-ng (CI)")
    baris = []
    v = subprocess.run(["espeak-ng", "--voices=id"], capture_output=True, text=True)
    baris.append(f"SUARA-ID: {(v.stdout.strip().splitlines() or ['?'])[-1][:80]}")
    al = Aligner("base")
    for tag, voice, speed, kalimat in KASUS:
        wav = str(tmp_path / f"{tag}.wav")
        cmd = ["espeak-ng", "-s", speed, "-w", wav]
        if voice:
            cmd += ["-v", voice]
        cmd += [kalimat]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            baris.append(f"{tag} TTS-GAGAL {(r.stderr[-80:])}")
            continue
        with wave.open(wav, "rb") as f:
            dur = f.getnframes() / float(f.getframerate())
        ws = words_of(al.align(wav))
        c = coverage(kalimat, ws)
        dengar = "/".join(w.text for w in ws)[:90]
        baris.append(f"{tag} cov={c['cocok']}/{c['total']} {dur:.1f}s {dengar}")
    print("\n".join(baris))
    esc = [b.replace("%", "%25") for b in baris]
    print(f"::notice title=Sapu C::{'%0A'.join(esc)[:2000]}")
    assert False, "sapu selesai (lihat stdout di atas)"
