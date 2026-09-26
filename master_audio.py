#!/usr/bin/env python3
"""Master audio Ep21 — versi "santai": VO tidak dipercepat (agar terasa tenang),
dinamikanya dibuat lebih rata (kompresor + limiter lembut), lalu dinaikkan ke level
broadcast. Output: build/audio_master.wav (48 kHz stereo) + laporan QC.
"""
import os, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg

BASE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "..", "build")
SRC = os.path.join(BUILD, "audio.wav")          # hasil build_audio.py (VO utuh)
os.makedirs(BUILD, exist_ok=True)
OUT = os.path.join(BUILD, "audio_master.wav")
TARGET_PEAK = -1.2     # dBTP kasar (dBFS) — aman untuk AAC YouTube
TARGET_LUFS = -14.0    # standar YouTube


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels())
    return a.astype(np.float64) / 32768.0, sr


def db(x):
    return 20 * np.log10(max(1e-9, x))


def main():
    tmp = os.path.join(BUILD, "_master_tmp.wav")
    # kompresor lembut 2 tahap + limiter: menjaga cerita tetap tenang tapi terdengar penuh
    chain = ("acompressor=threshold=-20dB:ratio=2.4:attack=14:release=260:makeup=2.2,"
             "acompressor=threshold=-12dB:ratio=1.6:attack=24:release=320:makeup=1.0,"
             "equalizer=f=6800:t=q:w=1.3:g=-1.6,"      # redam desis "s" agar tidak menusuk saat naskah padat
             "bass=g=1.0:f=110,"                        # sedikit kehangatan
             "treble=g=0.9:f=5200,"                     # kejernihan secukupnya
             "loudnorm=I=-14:TP=-1.3:LRA=8:print_format=none,"
             "alimiter=limit=0.985:attack=5:release=60")
    run([FF, "-y", "-i", SRC, "-af", chain, "-ar", "48000", "-ac", "2", tmp])
    a, sr = read(tmp)
    pk = np.abs(a).max()
    rms = np.sqrt((a ** 2).mean())
    # pastikan puncak tidak melewati target
    g = min(0.0, TARGET_PEAK - db(pk))
    if abs(g) > 0.05:
        a = np.clip(a * (10 ** (g / 20.0)), -1.0, 1.0)
    out = (a * 32767.0).astype("<i2")
    with wave.open(OUT, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(out.tobytes())
    pk2 = np.abs(a).max()
    print(f"master -> {os.path.normpath(OUT)}")
    print(f"  panjang {out.shape[0]/sr:.2f}s | RMS {db(rms):.1f} dBFS | puncak {db(pk2):.1f} dBFS "
          f"| gain akhir {g:+.2f} dB")
    # cek tidak ada clipping
    clip = int((np.abs(a) >= 0.9995).sum())
    print(f"  sample clipping: {clip}")
    if clip > 40:
        print("PERINGATAN: clipping terdeteksi")
        sys.exit(1)
    print("AUDIO MASTER OK ✔")


if __name__ == "__main__":
    main()
