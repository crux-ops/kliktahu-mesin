#!/usr/bin/env python3
"""Rapikan VO TANPA memotong isi kalimat.

Prinsip: hanya membuang keheningan di awal/akhir rekaman (dengan ambang sangat
rendah -50 dB supaya tidak menyentuh bunyi kata), lalu mempercepat sedikit.
Tidak ada loudnorm dinamis (bisa membuat awal kata terdengar aneh) dan tidak ada
pemotongan tengah kalimat seperti versi sebelumnya.

Setelah diproses, QC otomatis memastikan:
  * suara mulai <= 0.30 s dari awal klip
  * akhir klip benar-benar hening (bukan terpotong di tengah kata)
  * tidak ada clipping
"""
import os, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg

BASE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
SPEED = float(os.environ.get("SPEED", "1.15"))
# Kecepatan bicara seragam (kata/detik). Semua klip dijadikan sedatar mungkin:
# klip yang terlalu cepat diperlambat, klip yang lambat dipadatkan. Ini yang
# membuat narasi terdengar santai & rata, bukan sebagian cepat sebagian lambat.
TARGET_WPS = float(os.environ.get("TARGET_WPS", "1.90"))
ATEMPO_MIN, ATEMPO_MAX = float(os.environ.get("ATEMPO_MIN", "0.80")), float(os.environ.get("ATEMPO_MAX", "1.08"))
COMPRESS = os.environ.get("COMPRESS", "1") == "1"     # perataan kenyaringan lembut
BREATH = float(os.environ.get("BREATH", "0.16"))      # tambahan jeda antar kalimat (detik)
BREATH_MIN_GAP = float(os.environ.get("BREATH_MIN_GAP", "0.16"))
_SPEEDS = {}                    # pace khusus per adegan (dari content.json)


def load_speeds():
    """Adegan padat (angka/istilah) boleh dibaca lebih santai lewat field 'speed'."""
    global _SPEEDS
    try:
        import json
        c = json.load(open(os.path.join(BASE, "content.json")))
        for sc in c.get("scenes", []):
            v = sc.get("speed")
            if v:
                _SPEEDS[sc["id"]] = float(v)
    except Exception:
        pass


def scene_factor(fname):
    """Faktor relatif terhadap pace dasar 1,10 (1,07 = lebih santai, 1,13 = lebih rapat)."""
    return _SPEEDS.get(os.path.splitext(fname)[0], 1.10) / 1.10


TARGET_PEAK_DB = -1.5          # batas puncak (anti clipping)
TARGET_RMS_DB = float(os.environ.get("TARGET_RMS", "-20"))  # kenyaringan bicara (mesin v2)
FADE_IN, FADE_OUT = 0.010, 0.020   # fade mikro anti "klik"


def read_wav_mono(p):
    with wave.open(p) as w:
        sr = w.getframerate()
        n = w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype="<i2").reshape(-1, w.getnchannels()).mean(1)
    return a / 32768.0, sr


def max_db(p):
    a, _ = read_wav_mono(p)
    return 20 * np.log10(np.abs(a).max() + 1e-9)


def voice_rms_db(p, floor=-45.0, hop=0.01):
    """RMS bagian bersuara saja (mengabaikan keheningan) -> ukuran kenyaringan."""
    a, sr = read_wav_mono(p)
    h = max(1, int(hop * sr))
    fr = a[: len(a) // h * h].reshape(-1, h)
    rms = np.sqrt((fr ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    v = rms[db > floor]
    if v.size == 0:
        return -90.0
    return 20 * np.log10(np.sqrt((v ** 2).mean()) + 1e-9)


def fade_filter():
    """Fade mikro masuk/keluar (tanpa memotong isi): 10 ms awal, 20 ms akhir."""
    return (f"afade=t=in:st=0:d={FADE_IN},"
            f"areverse,afade=t=in:st=0:d={FADE_OUT},areverse")


def naskah_dur(sc_id, words_per_sec=None):
    """Perkiraan durasi naskah (untuk QC: klip tidak jauh lebih pendek/panjang)."""
    try:
        import json, os
        c = json.load(open(os.path.join(BASE, "content.json")))
        for sc in c["scenes"]:
            if sc["id"] == sc_id:
                return len(sc["vo"].split()) / (words_per_sec or TARGET_WPS)
    except Exception:
        pass
    return None


def trim_filter():
    """Potong keheningan saja (ambang rendah, sisa 0.12s), tanpa menyentuh kata."""
    return (
        "highpass=f=80,"
        "silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB:start_silence=0.06,"
        "areverse,"
        "silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB:start_silence=0.12,"
        "areverse"
    )


def speech_span(path):
    """(awal, akhir, durasi_bersuara) sebuah klip — dipakai menghitung kata/detik."""
    a, sr = read_wav_mono(path)
    hop = max(1, int(0.01 * sr))
    n = len(a) // hop
    if n < 2:
        return 0.0, 0.0, 0.0
    fr = a[: n * hop].reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1) + 1e-12) + 1e-9)
    v = np.where(db > -45)[0]
    if v.size == 0:
        return 0.0, 0.0, 0.0
    return v[0] * 0.01, v[-1] * 0.01, max(0.05, (v[-1] - v[0]) * 0.01)


def naskah_words(sc_id):
    try:
        import json, os
        c = json.load(open(os.path.join(BASE, "content.json")))
        for sc in c["scenes"]:
            if sc["id"] == sc_id:
                return len(sc["vo"].split())
    except Exception:
        pass
    return None


def add_breath(path, extra=None, min_gap=None, max_pauses=8):
    """Beri ruang napas: jeda alami di dalam klip dipanjangkan sedikit.

    Membuat narasi terdengar santai & bercerita TANPA mengubah kecepatan
    pengucapan satu kata pun (tidak ada kata yang dipercepat/dipotong).
    """
    extra = BREATH if extra is None else extra
    min_gap = BREATH_MIN_GAP if min_gap is None else min_gap
    if extra <= 0:
        return 0
    with wave.open(path) as w:
        sr, nch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype="<i2").reshape(-1, nch)
    mono = a.mean(1) / 32768.0
    hop = max(1, int(0.01 * sr))
    nfr = len(mono) // hop
    db = 20 * np.log10(np.sqrt((mono[: nfr * hop].reshape(nfr, hop) ** 2).mean(1) + 1e-12) + 1e-9)
    quiet = db < -42
    segs, i = [], 0
    while i < nfr:                      # rentetan hening di TENGAH klip saja
        if quiet[i]:
            j = i
            while j < nfr and quiet[j]:
                j += 1
            if i > 2 and j < nfr - 2 and (j - i) * 0.01 >= min_gap:
                segs.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    if not segs:
        return 0
    segs = segs[:max_pauses]
    pad = np.zeros((int(extra * sr), nch), dtype="<i2")
    out, prev = [], 0
    for s0, s1 in segs:
        out.append(a[prev:s1])
        out.append(pad)
        prev = s1
    out.append(a[prev:])
    b = np.concatenate(out).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(nch); w.setsampwidth(sw); w.setframerate(sr)
        w.writeframes(b.tobytes())
    return len(segs)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2000:]); sys.exit(1)
    return r


def main():
    ind = os.path.join(BASE, "audio")
    outd = os.path.join(BASE, "audio_proc")
    tmpd = os.path.join(BASE, "audio_tmp")
    os.makedirs(outd, exist_ok=True); os.makedirs(tmpd, exist_ok=True)
    tot_in = tot_out = 0.0
    load_speeds()
    if _SPEEDS:
        print("pace per adegan:", ", ".join(f"{k}={v:.2f}" for k, v in sorted(_SPEEDS.items())))
    rows = []
    for f in sorted(os.listdir(ind)):
        if not f.endswith(".wav"):
            continue
        src = os.path.join(ind, f)
        tmp = os.path.join(tmpd, f)
        dst = os.path.join(outd, f)
        # 1) trim keheningan (tetap kecepatan asli) — untuk mengukur irama bicara
        run([FF, "-y", "-i", src, "-af", trim_filter(), "-ar", "48000", "-ac", "2", tmp])
        # 2) hitung atempo klip ini supaya irama bicaranya seragam & santai
        st, en, sp = speech_span(tmp)
        w = naskah_words(f[:-4])
        env_key = "SPEED_" + f[:-4].upper()
        if env_key in os.environ:
            at = float(os.environ[env_key])
            wps_in = (w / sp) if (w and sp > 0.2) else 0.0
        elif w and sp > 0.2:
            wps_in = w / sp
            at = min(ATEMPO_MAX, max(ATEMPO_MIN, TARGET_WPS / wps_in))
        else:
            wps_in, at = 0.0, SPEED
        fac = scene_factor(f)                       # pace khusus adegan
        at = max(0.78, min(1.10, at * fac))
        wps_out = wps_in * at if wps_in else 0.0
        # 3) kenyaringan + perataan + atempo + fade
        pk = max_db(tmp)
        rms = voice_rms_db(tmp)
        g_rms = TARGET_RMS_DB - rms                 # dorongan menuju kenyaringan seragam
        g_rms_old = g_rms
        comp = "acompressor=threshold=-18dB:ratio=2.5:attack=8:release=140:makeup=1," if COMPRESS else ""
        tmp2 = os.path.join(tmpd, "c_" + f)
        run([FF, "-y", "-i", tmp, "-af", comp.rstrip(",") or "anull", "-ar", "48000", "-ac", "2", tmp2])
        pk = max_db(tmp2); rms = voice_rms_db(tmp2)          # ukur SETELAH perataan
        g = min(TARGET_RMS_DB - rms, TARGET_PEAK_DB - pk)
        run([FF, "-y", "-i", tmp2, "-af",
             f"volume={g:.2f}dB,alimiter=limit=0.98,atempo={at:.4f},{fade_filter()}",
             "-ar", "48000", "-ac", "2", dst])
        nbreath = add_breath(dst)                            # ruang napas antar kalimat
        di = wave.open(src).getnframes() / wave.open(src).getframerate()
        do = wave.open(dst).getnframes() / wave.open(dst).getframerate()
        tot_in += di; tot_out += do
        do = wave.open(dst).getnframes() / wave.open(dst).getframerate()
        rows.append((f, di, do, g, pk, rms, g_rms_old, at, wps_in, wps_out, nbreath))

    print(f"{'klip':12s} {'asli':>7s} {'proses':>7s} {'gain':>7s} {'RMS':>7s} {'akhir':>7s}   QC")
    ok_all = True
    for f, di, do, g, pk, rms_in, g_rms, at, wps_in, wps_out, nbreath in rows:
        a, sr = read_wav_mono(os.path.join(outd, f))
        hop = int(0.01 * sr)
        n = len(a) // hop
        rms = np.sqrt(np.array([(a[i * hop:(i + 1) * hop] ** 2).mean() for i in range(n)]) + 1e-12)
        db = 20 * np.log10(rms + 1e-9)
        voiced = np.where(db > -45)[0]
        start = voiced[0] * 0.01
        end = voiced[-1] * 0.01
        tail = do - end
        peak = 20 * np.log10(np.abs(a).max() + 1e-9)
        rms_out = voice_rms_db(os.path.join(outd, f))
        # QC: suara mulai cepat, ekor hening (tidak terpotong), tanpa clipping,
        #     dan kenyaringan mendekati target seragam
        qc = []
        if start > 0.30: qc.append(f"awal lambat({start:.2f}s)")
        if tail < 0.045: qc.append(f"EKOR TERPOTONG({tail:.2f}s)")
        if peak > -0.2: qc.append("clipping")
        if rms_out < TARGET_RMS_DB - 1.2: qc.append(f"kurang nyaring({rms_out:.1f}dB)")
        wps_end = (naskah_words(f[:-4]) / do) if naskah_words(f[:-4]) else 0.0
        if wps_end > TARGET_WPS + 0.15: qc.append(f"masih cepat({wps_end:.2f} kata/s)")
        # QC durasi hanya untuk naskah yang cukup panjang (klip pendek seperti
        # "Ikuti KlikTahu." punya jeda wajar, rasionya tidak bermakna)
        est = naskah_dur(f[:-4])
        if est and est >= 3.0:
            rasio = do / est
            if rasio < 0.70 or rasio > 1.62:      # klip lambat = wajar (narasi santai)
                qc.append(f"durasi {rasio:.2f}x naskah")
        ok_all &= not qc
        print(f"{f:12s} {di:6.2f}s {do:6.2f}s {g:+6.1f}dB {rms_in:6.1f} {rms_out:6.1f} "
              f"atempo {at:.2f} ({wps_in:.2f}->{wps_end:.2f} kata/s, {nbreath} jeda)   "
              f"{'OK (mulai %.2fs, ekor %.2fs, peak %.1f dB)' % (start, tail, peak) if not qc else '>>> ' + ', '.join(qc)}")
    print(f"TOTAL {tot_in:.1f}s -> {tot_out:.1f}s  pacing TARGET {TARGET_WPS:.2f} kata/s + napas {BREATH*1000:.0f}ms "
          f"(atempo {ATEMPO_MIN}-{ATEMPO_MAX})  RMS {TARGET_RMS_DB:.0f}dB peak {TARGET_PEAK_DB:.1f}dB "
          f"fade {FADE_IN*1000:.0f}/{FADE_OUT*1000:.0f}ms  kompresi={'on' if COMPRESS else 'off'}")
    print("QC:", "SEMUA KLIP BERSIH ✔" if ok_all else "ADA MASALAH ✘")


if __name__ == "__main__":
    main()
