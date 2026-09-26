"""Bukti Bagian E: audisi 2 narator + rantai VO (HANYA DI GITHUB ACTIONS).

Kandidat A: Piper id_ID-news_tts-medium (pria, MIT, 22050 Hz).
Kandidat B: Chatterbox-TTS-Indonesian + prompt Common Voice pria CC0.
Hasil: demo_vo_piper.wav + demo_vo_chatterbox.wav (48k PCM16, pace 1,8-1,9,
-14 LUFS, puncak <= -1 dBFS) + prompt_cv_pria.wav + proof_e_final.png.
Gagal bila: render tak deterministik, QC di luar batas, isi hilang,
liputan whisper < 100%, atau gender keluaran bukan pria.
"""
import argparse
import hashlib
import os
import shutil

import numpy as np
import skia

from . import ENGINE_VERSION
from .align import Aligner, coverage, words_of
from .canvas import (Renderer, argb, fill_paint, hex_to_argb,
                     linear_gradient_paint)
from .spec import SHORTS
from . import voice as V

CREAM = hex_to_argb("#F6F1E8")
INK = hex_to_argb("#18181F")
DARK = hex_to_argb("#23232B")
ACCENT = hex_to_argb("#B2542A")
TEAL = hex_to_argb("#1F7A6D")
GOLD = hex_to_argb("#C9A227")
MUTED = argb(255, 150, 145, 135)

SEED = V.SEED


def sha8(data):
    return hashlib.sha256(bytes(data)).hexdigest()[:8]


def draw_wave(c, x, y, w, h, data, color):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), 12, 12, fill_paint(DARK))
    n = int(np.asarray(data).size)
    if n == 0:
        return
    p = fill_paint(color)
    cols = max(1, int(w))
    idx = (np.arange(cols + 1) * n / cols).astype(int)
    for j in range(cols):
        seg = data[idx[j]:idx[j + 1]]
        if seg.size == 0:
            continue
        mn, mx = float(seg.min()), float(seg.max())
        y1 = y + h / 2 - mx * h / 2
        y2 = y + h / 2 - mn * h / 2
        c.drawRect(skia.Rect.MakeXYWH(x + j, min(y1, y2), 1.0,
                                      max(1.0, abs(y2 - y1))), p)
    c.drawRect(skia.Rect.MakeXYWH(x, y + h / 2 - 1, w, 2),
               fill_paint(argb(90, 255, 255, 255)))


def panel_stat_lines(tag, nama, r, qc, lip, det, h8, sr_asal, extra=()):
    qc0 = r["qc"]
    awal = qc0["awal_suara"] or 0.0
    akhir = qc0["akhir_suara"] or 0.0
    f0 = r["f0_median"]
    lines = [
        f"suara {nama} | sr asal {sr_asal} Hz -> 48000 Hz",
        f"dur {r['y'].size / V.SR:.2f}s | pace {r['pace_awal']:.2f} "
        f"-> {r['pace_akhir']:.2f} k/dtk (regang x{r['faktor_regang']:.3f})",
        f"LUFS {r['lufs_masuk']:.1f} -> {r['lufs_akhir']:.2f} "
        f"(target -14) | puncak {r['puncak_db']:.1f} dBFS",
        f"F0 median {f0:.0f} Hz -> {r['gender']} | "
        f"suara {awal:.2f}-{akhir:.2f}s" if f0 else
        f"F0 tak-terbaca -> {r['gender']}",
        f"liputan whisper {lip['cocok']}/{lip['total']} | "
        f"hilang {qc['n_hilang']} | jeda {len(qc['jeda'])}",
        f"sha8 {h8} | 2x render {'identik' if det else 'BEDA'}",
    ]
    lines.extend(extra)
    vonis = ("LOLOS" if det and r["lolos"] and qc["n_hilang"] == 0
             and lip["rasio"] == 1.0 and r["gender"] == "pria" else "GAGAL")
    lines.append(f"vonis {tag}: {vonis}")
    _ = tag
    return lines, vonis


def draw_sheet(r, aud, stat_a, stat_b, qc_lines):
    c, tc, W = r.canvas, r.text, r.w
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, r.h), fill_paint(CREAM))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 150),
               linear_gradient_paint(0, 0, W, 150, hex_to_argb("#23232B"),
                                     hex_to_argb("#3A3A44")))
    tc.draw_center(c, W / 2, 62, "AUDIO VO + AUDISI (E)", "Poppins-Bold.ttf",
                   64, argb(255, 246, 241, 232))
    tc.draw_center(c, W / 2, 120,
                   "pace 1,8-1,9 k/dtk - -14 LUFS - QC isi-hilang 30 ms",
                   "Poppins-Regular.ttf", 28, MUTED)
    y = 172
    for judul, stats, y_audio, col in stat_a, stat_b:
        _ = y_audio
        tc.draw_center(c, W / 2, y + 16, judul, "Poppins-SemiBold.ttf", 30, INK)
        draw_wave(c, 60, y + 34, W - 120, 110, stats["y"], col)
        tc.draw_paragraph(c, 60, y + 152, "\n".join(stats["lines"]),
                          "Poppins-Regular.ttf", 24, INK, lh=1.3)
        y += 152 + int(len(stats["lines"]) * 24 * 1.3) + 18
    y += 6
    tc.draw_center(c, W / 2, y + 16, "QC ISI-HILANG (whisper base + celah)",
                   "Poppins-SemiBold.ttf", 30, INK)
    tc.draw_paragraph(c, 60, y + 46, "\n".join(qc_lines),
                      "Poppins-Regular.ttf", 24, INK, lh=1.3)
    y += 46 + int(len(qc_lines) * 24 * 1.3) + 20
    assert y + 90 < r.h, f"lembar meluap: {y} >= {r.h}"
    tc.draw_center(c, W / 2, r.h - 70, aud["kaki1"],
                   "Poppins-Regular.ttf", 26, MUTED)
    tc.draw_center(c, W / 2, r.h - 34, aud["kaki2"],
                   "Poppins-Regular.ttf", 26, MUTED)


def selaras(aligner, wav_path):
    uts = aligner.align(str(wav_path), language="id", beam=5, vad=True,
                        prompt=None)
    words = words_of(uts)
    spans = [(w.start, w.end) for w in words]
    return words, spans, coverage(V.AUDITION_TEXT, words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="proof-e")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    cache = os.path.join(os.path.expanduser("~"), ".cache", "kliktahu")
    n_kata = V.hitung_kata(V.AUDITION_TEXT)
    print(f"teks audisi: {n_kata} kata", flush=True)

    # --- A: Piper ---
    pp = V.pastikan_piper(cache)
    print(f"piper: {V.PIPER_VOICE} sr={pp['sr']}", flush=True)
    voice = V.muat_piper(pp["onnx"], pp["json"])
    mentah = V.sintesis_piper(voice, V.AUDITION_TEXT, pp["sr"], None)
    pace_mentah = V.ukur_pace(n_kata, mentah.size / V.SR)
    if V.pace_ok(pace_mentah):
        length_scale = None
    else:
        length_scale = min(2.0, max(0.5, pace_mentah / V.TARGET_PACE))
    print(f"piper pace mentah {pace_mentah:.2f} length_scale={length_scale}",
          flush=True)
    a1 = V.sintesis_piper(voice, V.AUDITION_TEXT, pp["sr"], length_scale)
    a2 = V.sintesis_piper(voice, V.AUDITION_TEXT, pp["sr"], length_scale)
    det_a = bool(np.array_equal(a1, a2))
    rA = V.rantai_vo(a1, V.SR, n_kata)
    pA = os.path.join(a.outdir, "demo_vo_piper.wav")
    V.tulis_wav_16(pA, rA["y"])
    print(f"A pace {rA['pace_akhir']:.2f} LUFS {rA['lufs_akhir']:.2f} "
          f"puncak {rA['puncak_db']:.1f} F0 {rA['f0_median']} det={det_a}",
          flush=True)

    # --- B: Chatterbox-ID + prompt CV pria ---
    prompt_path, prompt_meta = V.ambil_prompt_cv(cache)
    xp, _ = V.baca_wav_16(prompt_path)
    f0p = V.f0_median(xp, V.SR)
    print(f"prompt {prompt_meta['repo'].split('/')[-1]} "
          f"dur={prompt_meta['dur_asal']:.1f}s F0={f0p}", flush=True)
    print(f"kalimat prompt: {prompt_meta['kalimat'][:80]}", flush=True)
    model = V.muat_chatterbox()
    print("chatterbox dimuat, sintesis 1/2...", flush=True)
    b1 = V.sintesis_chatterbox(model, V.AUDITION_TEXT, prompt_path)
    print("sintesis 2/2...", flush=True)
    b2 = V.sintesis_chatterbox(model, V.AUDITION_TEXT, prompt_path)
    det_b = bool(np.array_equal(b1, b2))
    rB = V.rantai_vo(b1, V.SR, n_kata)
    pB = os.path.join(a.outdir, "demo_vo_chatterbox.wav")
    V.tulis_wav_16(pB, rB["y"])
    shutil.copy(prompt_path, os.path.join(a.outdir, "prompt_cv_pria.wav"))
    print(f"B pace {rB['pace_akhir']:.2f} LUFS {rB['lufs_akhir']:.2f} "
          f"puncak {rB['puncak_db']:.1f} F0 {rB['f0_median']} det={det_b}",
          flush=True)

    # --- QC selaras whisper pada berkas final ---
    al = Aligner(model="base", cache_dir=os.path.join(cache, "whisper"))
    _, spansA, lipA = selaras(al, pA)
    _, spansB, lipB = selaras(al, pB)
    qcA = V.celah_hilang(rA["y"], V.SR, spansA)
    qcB = V.celah_hilang(rB["y"], V.SR, spansB)
    print(f"liputan A {lipA['cocok']}/{lipA['total']} hilang={qcA['n_hilang']} "
          f"jeda={len(qcA['jeda'])}", flush=True)
    print(f"liputan B {lipB['cocok']}/{lipB['total']} hilang={qcB['n_hilang']} "
          f"jeda={len(qcB['jeda'])}", flush=True)

    hA = sha8(open(pA, "rb").read())
    hB = sha8(open(pB, "rb").read())
    repo_pendek = prompt_meta["repo"].split("/")[-1]
    kal = prompt_meta["kalimat"]
    kal = kal if len(kal) <= 42 else kal[:42] + "..."
    linesA, vonisA = panel_stat_lines("A", V.PIPER_VOICE + " (MIT)", rA, qcA,
                                      lipA, det_a, hA, pp["sr"])
    sumber = prompt_meta.get("sumber", "cv")
    linesB, vonisB = panel_stat_lines(
        "B", "chatterbox-id (Apache-2.0)", rB, qcB, lipB, det_b, hB,
        int(model.sr), extra=[f"prompt {sumber} {repo_pendek} F0 {f0p:.0f} Hz",
                              f'"{kal}"'] if f0p else
        [f"prompt {sumber} {repo_pendek}", f'"{kal}"'])
    stat_a = ("A. PIPER id_ID-news_tts-medium (pria, MIT)",
              {"y": rA["y"], "lines": linesA}, TEAL)
    stat_b = ("B. CHATTERBOX-ID + prompt Common Voice pria (CC0)",
              {"y": rB["y"], "lines": linesB}, ACCENT)
    qc_lines = [
        f"A liputan {lipA['cocok']}/{lipA['total']} hilang {qcA['n_hilang']} "
        f"jeda {len(qcA['jeda'])} | B liputan {lipB['cocok']}/{lipB['total']} "
        f"hilang {qcB['n_hilang']} jeda {len(qcB['jeda'])}",
        "ambang: celah >=30 ms di dalam kata (bingkai 10 ms, -45 dBFS,",
        "erosi tepi kata 30 ms). Jeda antar kalimat = info, bukan gagal.",
        "B diberi cap-air Perth bawaan chatterbox (tak terdengar).",
        'Teks: "Tahukah kamu? Gurita punya tiga jantung. Dua',
        'berhenti saat berenang, satu memompa ke tubuh. Keren, kan?"',
    ]
    aud = {"kaki1": f"deterministik 2x: A {'ya' if det_a else 'TIDAK'} "
                    f"B {'ya' if det_b else 'TIDAK'} - seed {SEED}",
           "kaki2": f"pemilik pilih A/B -> kunci NARRATOR_ID - engine v{ENGINE_VERSION}"}

    for name, ss, scale, fin in (("proof_e_final.png", 2.0, 1.0, SEED),
                                 ("proof_e_fast.png", 1.0, 0.25, None)):
        r = Renderer(SHORTS.w, SHORTS.h, ss=ss, out_scale=scale)
        draw_sheet(r, aud, stat_a, stat_b, qc_lines)
        data = r.png_bytes(finish_seed=fin)
        open(os.path.join(a.outdir, name), "wb").write(data)
        print(f"{name} {len(data)} byte sha256={Renderer.sha256(data)}",
              flush=True)
    r2 = Renderer(SHORTS.w, SHORTS.h, ss=2.0, out_scale=1.0)
    draw_sheet(r2, aud, stat_a, stat_b, qc_lines)
    h2 = Renderer.sha256(r2.png_bytes(finish_seed=SEED))
    h1 = Renderer.sha256(open(os.path.join(a.outdir, "proof_e_final.png"),
                              "rb").read())
    assert h2 == h1, "lembar E tak deterministik"

    # --- vonis akhir (gagal = seksi berhenti, artefak tetap diunggah) ---
    assert det_a, "kandidat A tak deterministik"
    assert det_b, "kandidat B tak deterministik (seed cpu)"
    for tag, r, qc, lip in (("A", rA, qcA, lipA), ("B", rB, qcB, lipB)):
        assert V.pace_ok(r["pace_akhir"]), f"{tag} pace {r['pace_akhir']:.2f}"
        assert abs(r["lufs_akhir"] - V.TARGET_LUFS) <= V.TOL_LUFS, \
            f"{tag} LUFS {r['lufs_akhir']:.2f}"
        assert r["puncak_db"] <= V.PEAK_BATAS_DB, f"{tag} puncak"
        assert r["gender"] == "pria", f"kandidat {tag} gender {r['gender']}"
        assert qc["n_hilang"] == 0, f"{tag} isi hilang {qc['n_hilang']}"
        assert lip["rasio"] == 1.0, \
            f"{tag} liputan {lip['cocok']}/{lip['total']}"
    print(f"2E OK: vonis A={vonisA} B={vonisB}", flush=True)


if __name__ == "__main__":
    main()
