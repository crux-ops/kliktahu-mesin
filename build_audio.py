#!/usr/bin/env python3
"""Susun track audio final: hanya VO yang dijadwalkan (tanpa SFX, tanpa pemotongan)."""
import json, os, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg

BASE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "..", "build")
os.makedirs(BUILD, exist_ok=True)
OUT = os.path.join(BUILD, "audio.wav")
TARGET_PEAK_DB = -2.5   # sisa ruang untuk overshoot AAC (QC MP4 menolak peak > -0,1 dBFS)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stderr[-2000:]); sys.exit(1)
    return r


def peak_db(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels())
    return 20 * np.log10(np.abs(a.astype(np.float64).max() / 32768.0) + 1e-9)


def main():
    tl = json.load(open(os.path.join(BASE, "timeline.json")))
    total = tl["total"]
    adir = os.path.join(BASE, "audio_proc")
    tmp = os.path.join(BUILD, "audio_mix.wav")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    cmd = [FF, "-y"]
    for sc in tl["scenes"]:
        cmd += ["-i", os.path.join(adir, sc["id"] + ".wav")]
    cmd += ["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={total + 0.6:.3f}"]
    isil = len(tl["scenes"])
    parts = [f"[{isil}]atrim=0:{total + 0.6:.3f}[base]"]
    mix = ["[base]"]
    for i, sc in enumerate(tl["scenes"]):
        ms = int(round(sc["vo_at"] * 1000))
        parts.append(f"[{i}]adelay={ms}|{ms}[v{i}]")
        mix.append(f"[v{i}]")
    parts.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:dropout_transition=0[out]")
    run(cmd + ["-filter_complex", ";".join(parts), "-map", "[out]", "-ar", "48000", "-ac", "2", tmp])

    # gain statis (bukan loudnorm dinamis) + fade halus di akhir
    g = TARGET_PEAK_DB - peak_db(tmp)
    run([FF, "-y", "-i", tmp, "-af",
         f"volume={g:.2f}dB,alimiter=limit=0.97,afade=t=out:st={total - 0.45:.2f}:d=0.45",
         "-ar", "48000", "-ac", "2", OUT])

    # laporkan isi tiap slot supaya tidak ada VO yang terpotong / bertabrakan
    with wave.open(OUT) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, 2).mean(1) / 32768.0
    print(f"audio -> {OUT}  ({len(a)/sr:.2f}s, gain {g:+.1f}dB, peak {peak_db(OUT):.1f}dB)")
    hop = int(0.02 * sr)
    n = len(a) // hop
    rms = np.sqrt(np.array([(a[i*hop:(i+1)*hop]**2).mean() for i in range(n)]) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    print(f"{'scene':7s} {'VO mulai':>9s} {'VO akhir':>9s} {'ekor hening':>12s}  QC")
    langgar = []
    for sc in tl["scenes"]:
        s, e = int(sc["vo_at"] / 0.02), int((sc["vo_at"] + sc["vo_dur"]) / 0.02)
        seg = db[s:e]
        v = np.where(seg > -45)[0]
        if len(v) == 0:
            print(f"{sc['id']:7s} tidak ada suara?"); continue
        st, en = v[0]*0.02, v[-1]*0.02
        tail = sc["vo_dur"] - en
        nxt = next((x["start"] for x in tl["scenes"] if x["start"] > sc["start"]), None)
        gap = (nxt - (sc["vo_at"] + en)) if nxt else 99
        # syarat keras: VO tidak terpotong, mulai dekat lead_in, dan tidak bertabrakan
        fits = (sc["vo_at"] + en) <= (sc["start"] + sc["dur"] + 0.05)
        ok = tail > 0.045 and gap > 0.25 and st < 0.35 and fits
        if not ok:
            langgar.append(sc["id"] + (" (VO lewat batas scene)" if not fits else
                                       " (jeda sempit)" if gap <= 0.25 else " (potong/awal lambat)"))
        print(f"{sc['id']:7s} {st:8.2f}s {en:8.2f}s {tail:11.2f}s  {'OK' if ok else 'GAGAL'}"
              + (f"  jeda ke scene berikutnya {gap:.2f}s" if nxt else ""))

    # ringkas mutu audio final
    rms_all = 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9)
    pk = 20 * np.log10(np.abs(a).max() + 1e-9)
    print(f"level akhir: RMS keseluruhan {rms_all:.1f} dBFS, puncak {pk:.1f} dBFS")
    if langgar:
        print("AUDIO GAGAL:", ", ".join(langgar))
        sys.exit(1)
    print("AUDIO OK: semua VO utuh, tidak bertabrakan, tidak melewati batas scene ✔")


if __name__ == "__main__":
    main()
