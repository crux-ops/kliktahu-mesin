"""SAPUAN-2 SEMENTARA (hapus setelah eksperimen): mbrola + edge-tts neural."""
import shutil
import subprocess

import pytest

fw = pytest.importorskip("faster_whisper")  # noqa: F401

from kt.align import Aligner, coverage, words_of

KAL = "Jantung memompa darah ke seluruh tubuh."


def test_sapu_dua(tmp_path):
    if shutil.which("espeak-ng") is None:
        pytest.skip("butuh espeak-ng (CI)")
    out = []
    al = Aligner("base")

    def lapor(tag, wav):
        ws = words_of(al.align(wav))
        c = coverage(KAL, ws)
        dengar = "/".join(w.text for w in ws)[:80]
        out.append(f"{tag} cov={c['cocok']}/{c['total']} {dengar}")

    v = subprocess.run(["espeak-ng", "--voices"], capture_output=True, text=True)
    ids = [l.strip()[:50] for l in v.stdout.splitlines()
           if " id" in f" {l} " or "/id" in l or "ndonesia" in l]
    out.append("SUARA: " + (" | ".join(ids)[:180] if ids else "tak-ada"))
    m = subprocess.run(["sudo", "apt-get", "install", "-y", "mbrola-id1"],
                       capture_output=True, text=True)
    out.append(f"MBROLA-APT rc={m.returncode}")
    if m.returncode == 0:
        mb = str(tmp_path / "mb.wav")
        r = subprocess.run(["espeak-ng", "-v", "mb/mb-id1", "-s", "150",
                            "-w", mb, KAL], capture_output=True, text=True)
        if r.returncode == 0:
            lapor("MB", mb)
        else:
            out.append(f"MB-TTS gagal {r.stderr[-80:]}")
    try:
        import edge_tts  # noqa: F401
        mp3 = str(tmp_path / "edge.mp3")
        r = subprocess.run(["edge-tts", "--voice", "id-ID-ArdiNeural",
                            "--text", KAL, "--write-media", mp3],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            lapor("EDGE", mp3)
            import os
            os.makedirs("fixtures", exist_ok=True)
            shutil.copy(mp3, "fixtures/bicara-id.mp3")
            out.append("EDGE disimpan fixtures/bicara-id.mp3")
            if os.environ.get("GITHUB_EVENT_NAME") == "push":
                subprocess.run(["git", "config", "user.name",
                                "github-actions[bot]"], check=True)
                subprocess.run(["git", "config", "user.email",
                                "41898282+github-actions[bot]@users.noreply.github.com"],
                               check=True)
                subprocess.run(["git", "add", "fixtures/bicara-id.mp3"], check=True)
                subprocess.run(["git", "commit", "-q", "-m",
                                "Fixture C: suara neural ID [skip ci]"], check=True)
                p = subprocess.run(["git", "push", "origin",
                                    "HEAD:arena/01a0dda8-kliktahu-mesin"],
                                   capture_output=True, text=True)
                out.append(f"PUSH rc={p.returncode} "
                           f"{p.stderr[-80:] if p.returncode else 'OK'}")
            else:
                out.append("PUSH lewati (bukan event push)")
        else:
            out.append(f"EDGE gagal rc={r.returncode} {r.stderr[-100:]}")
    except ImportError:
        out.append("EDGE tak-terpasang")
    except subprocess.TimeoutExpired:
        out.append("EDGE timeout")
    print("\n".join(out))
    esc = [b.replace("%", "%25") for b in out]
    print(f"::notice title=Sapu C2::{'%0A'.join(esc)[:2000]}")
    assert False, "sapu2 selesai (lihat stdout di atas)"
