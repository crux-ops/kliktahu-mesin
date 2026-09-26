"""SAPUAN-3 SEMENTARA (hapus setelah eksperimen): prompt + jeda koma."""
import os
import shutil
import subprocess

import pytest

fw = pytest.importorskip("faster_whisper")  # noqa: F401

from kt.align import Aligner, coverage, words_of

KAL = "Jantung memompa darah ke seluruh tubuh."
KAL_KOMA = "Jantung, memompa, darah, ke, seluruh, tubuh."


def test_sapu_tiga(tmp_path):
    if shutil.which("espeak-ng") is None:
        pytest.skip("butuh espeak-ng (CI)")
    out = []
    al = Aligner("base")

    def lapor(tag, wav, prompt=None):
        ws = words_of(al.align(wav, prompt=prompt))
        c = coverage(KAL, ws)
        dengar = "/".join(w.text for w in ws)[:90]
        out.append(f"{tag} cov={c['cocok']}/{c['total']} {dengar}")
        return c["cocok"]

    lapor("BASIS", "fixtures/bicara-id.mp3")
    lapor("BASIS+P", "fixtures/bicara-id.mp3", prompt=KAL)
    mp3 = str(tmp_path / "koma.mp3")
    r = subprocess.run(["edge-tts", "--voice", "id-ID-ArdiNeural",
                        "--text", KAL_KOMA, "--write-media", mp3],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        out.append(f"KOMA-TTS gagal rc={r.returncode}")
    else:
        s_plain = lapor("KOMA", mp3)
        s_prom = lapor("KOMA+P", mp3, prompt=KAL)
        if max(s_plain, s_prom) >= 5 and os.environ.get("GITHUB_EVENT_NAME") == "push":
            shutil.copy(mp3, "fixtures/bicara-id.mp3")
            subprocess.run(["git", "config", "user.name",
                            "github-actions[bot]"], check=True)
            subprocess.run(["git", "config", "user.email",
                            "41898282+github-actions[bot]@users.noreply.github.com"],
                           check=True)
            subprocess.run(["git", "add", "fixtures/bicara-id.mp3"], check=True)
            subprocess.run(["git", "commit", "-q", "-m",
                            "Fixture C: suara koma-jeda [skip ci]"], check=True)
            p = subprocess.run(["git", "push", "origin",
                                "HEAD:arena/01a0dda8-kliktahu-mesin"],
                               capture_output=True, text=True)
            out.append(f"PUSH rc={p.returncode} {'OK' if not p.returncode else p.stderr[-60:]}")
    print("\n".join(out))
    esc = [b.replace("%", "%25") for b in out]
    print(f"::notice title=Sapu C3::{'%0A'.join(esc)[:2000]}")
    assert False, "sapu3 selesai (lihat stdout di atas)"
