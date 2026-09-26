"""Bukti Bagian C: selaras kata espeak-ng -> faster-whisper (HANYA DI CI).

Menghasilkan: proof_c_final.png (1080x1920, ss=2) + proof_c_fast.png (0.25x).
Menegaskan: determinisme 2x selaras + liputan >= 50% + stempel monoton.
"""
import argparse
import os
from pathlib import Path

import skia

from . import ENGINE_VERSION
from .align import (Aligner, check_monotonic, coverage, normalize_token,
                    words_of)
from .canvas import (Renderer, argb, fill_paint, hex_to_argb,
                     linear_gradient_paint)
from .motion import with_alpha
from .spec import SHORTS

CREAM = hex_to_argb("#F6F1E8")
INK = hex_to_argb("#18181F")
DARK = hex_to_argb("#23232B")
ACCENT = hex_to_argb("#B2542A")
TEAL = hex_to_argb("#1F7A6D")
GOLD = hex_to_argb("#C9A227")
MUTED = argb(255, 150, 145, 135)

KALIMAT = "Jantung memompa darah ke seluruh tubuh."
MODEL = "base"
BATAS_LIPUTAN = 0.8  # terbukti sapu C3: 5/6 tanpa prompt
REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "fixtures" / "bicara-id.mp3"


def selaras_dan_periksa(wav_path):
    al = Aligner(MODEL)
    a = words_of(al.align(wav_path))
    b = words_of(al.align(wav_path))
    sa = [(w.text, round(w.start, 3), round(w.end, 3)) for w in a]
    sb = [(w.text, round(w.start, 3), round(w.end, 3)) for w in b]
    assert sa == sb, "selaras tak deterministik antar lari"
    assert a, "tak ada kata terselaras"
    assert check_monotonic(a), "stempel kata tak monoton"
    cov = coverage(KALIMAT, a)
    assert cov["rasio"] >= BATAS_LIPUTAN, f"liputan {cov} di bawah batas"
    dur = max(w.end for w in a) + 0.3
    return a, cov, dur


def _kartu(c, tc, x, y, w, label, teks, aksen):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, 118), 20, 20,
                    fill_paint(argb(255, 255, 255, 255)))
    tc.draw_center(c, x + 24 + tc.width(label, "Poppins-SemiBold.ttf", 26) / 2,
                   y + 34, label, "Poppins-SemiBold.ttf", 26, aksen)
    tc.draw_center(c, x + w / 2, y + 80, teks, "Poppins-Bold.ttf", 34, INK)
    return y + 118


def draw_sheet(r: Renderer, seed: int, words, cov, dur):
    c, tc, W = r.canvas, r.text, r.w
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, r.h), fill_paint(CREAM))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 150),
               linear_gradient_paint(0, 0, W, 150, hex_to_argb("#23232B"),
                                     hex_to_argb("#3A3A44")))
    tc.draw_center(c, W / 2, 62, "SINKRON KATA (C)", "Poppins-Bold.ttf",
                   68, argb(255, 246, 241, 232))
    tc.draw_center(c, W / 2, 120, f"suara neural ID -> faster-whisper {MODEL} int8",
                   "Poppins-Regular.ttf", 30, MUTED)
    y = 186
    y = _kartu(c, tc, 60, y, W - 120, "DIHARAPKAN", KALIMAT, TEAL) + 18
    didengar = " ".join(w.text for w in words) or "(hening)"
    if len(didengar) > 46:
        didengar = didengar[:45] + "..."
    y = _kartu(c, tc, 60, y, W - 120, "TERDENGAR", didengar, ACCENT) + 30
    # garis waktu kata
    tc.draw_center(c, W / 2, y + 20, f"GARIS WAKTU ({dur:.2f} detik)",
                   "Poppins-SemiBold.ttf", 32, INK)
    gx, gw, gy, gh = 60, W - 120, y + 48, 190
    c.drawRoundRect(skia.Rect.MakeXYWH(gx, gy, gw, gh), 18, 18, fill_paint(DARK))
    tmax = max(dur, max((w.end for w in words), default=1.0)) * 1.04
    pad = 26
    X = lambda t: gx + pad + (gw - 2 * pad) * (t / tmax)
    import math
    step = 0.5
    tt = 0.0
    while tt <= tmax + 1e-9:
        x = X(tt)
        c.drawRect(skia.Rect.MakeXYWH(x, gy + gh - 34, 2, 12),
                   fill_paint(argb(255, 120, 116, 110)))
        tc.draw_center(c, x, gy + gh - 12, f"{tt:.1f}",
                       "Poppins-Regular.ttf", 20, MUTED)
        tt += step
    for i, w in enumerate(words):
        x0, x1 = X(w.start), X(max(w.end, w.start + 0.02))
        box = skia.Rect.MakeXYWH(x0, gy + 26, max(10.0, x1 - x0), 64)
        c.drawRoundRect(box, 10, 10, fill_paint(with_alpha(TEAL, 0.45 + 0.55 * w.conf)))
        row = i % 2
        ly = gy + 26 + 64 + 26 + row * 30
        tok = normalize_token(w.text) or w.text
        if len(tok) > 12:
            tok = tok[:11] + "."
        tc.draw_center(c, min(max((x0 + x1) / 2, gx + 60), gx + gw - 60), ly,
                       tok, "Poppins-SemiBold.ttf", 24,
                       argb(255, 246, 241, 232))
    y = gy + gh + 30
    # pita liputan
    pct = cov["rasio"] * 100.0
    c.drawRoundRect(skia.Rect.MakeXYWH(60, y, W - 120, 120), 20, 20,
                    fill_paint(argb(255, 255, 255, 255)))
    tc.draw_center(c, W / 2, y + 48,
                   f"LIPUTAN {cov['cocok']}/{cov['total']} = {pct:.0f}%",
                   "Poppins-Bold.ttf", 52, TEAL if cov["rasio"] >= 0.7 else GOLD)
    tc.draw_center(c, W / 2, y + 94, "kecocokan urutan (LCS) vs kalimat",
                   "Poppins-Regular.ttf", 24, INK)
    y += 120 + 30
    # tabel kata
    tc.draw_center(c, W / 2, y + 18, "STEMPEL TIAP KATA",
                   "Poppins-SemiBold.ttf", 32, INK)
    y += 48
    tc.draw_center(c, 200, y + 16, "kata", "Poppins-SemiBold.ttf", 24, MUTED)
    tc.draw_center(c, 540, y + 16, "mulai - selesai", "Poppins-SemiBold.ttf", 24, MUTED)
    tc.draw_center(c, 880, y + 16, "yakin", "Poppins-SemiBold.ttf", 24, MUTED)
    y += 40
    for w in words[:14]:
        c.drawRect(skia.Rect.MakeXYWH(60, y, W - 120, 2),
                   fill_paint(argb(255, 220, 214, 204)))
        tok = normalize_token(w.text) or w.text
        tc.draw_center(c, 200, y + 24, tok[:16], "Poppins-Bold.ttf", 28, INK)
        tc.draw_center(c, 540, y + 24, f"{w.start:.2f} - {w.end:.2f}",
                       "Poppins-Regular.ttf", 28, INK)
        tc.draw_center(c, 880, y + 24, f"{w.conf:.2f}",
                       "Poppins-Regular.ttf", 28, INK)
        y += 46
    assert y < r.h - 40, f"lembar meluap: {y} >= {r.h}"
    tc.draw_center(c, W / 2, r.h - 70,
                   "2x selaras identik (ms) - monoton - stempel kata",
                   "Poppins-Regular.ttf", 26, MUTED)
    tc.draw_center(c, W / 2, r.h - 34, f"seed {seed} - engine v{ENGINE_VERSION}",
                   "Poppins-Regular.ttf", 28, MUTED)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="proof-c")
    ap.add_argument("--wav", default=None)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    seed = 7
    wav_path = a.wav or str(FIXTURE)
    assert os.path.exists(wav_path), f"audio hilang: {wav_path}"
    words, cov, dur = selaras_dan_periksa(wav_path)
    print(f"audio: {wav_path} ({dur:.2f}s)")
    for w in words:
        print(f"  {w.start:6.2f}-{w.end:6.2f} {w.conf:.2f} {w.text}")
    print(f"liputan: {cov['cocok']}/{cov['total']} = {cov['rasio']:.2f}")
    outs = []
    for name, ss, scale, fin in (("proof_c_final.png", 2.0, 1.0, seed),
                                 ("proof_c_fast.png", 1.0, 0.25, None)):
        r = Renderer(SHORTS.w, SHORTS.h, ss=ss, out_scale=scale)
        draw_sheet(r, seed, words, cov, dur)
        data = r.png_bytes(finish_seed=fin)
        p = os.path.join(a.outdir, name)
        open(p, "wb").write(data)
        outs.append((name, Renderer.sha256(data), len(data),
                     f"{int(SHORTS.w*scale)}x{int(SHORTS.h*scale)}"))
    r2 = Renderer(SHORTS.w, SHORTS.h, ss=2.0, out_scale=1.0)
    draw_sheet(r2, seed, words, cov, dur)
    h2 = Renderer.sha256(r2.png_bytes(finish_seed=seed))
    assert h2 == outs[0][1], f"render tidak deterministik: {h2} != {outs[0][1]}"
    for name, h, n, wh in outs:
        print(f"{name} {wh} {n} byte sha256={h}")
    print("deterministik OK (dua render final identik)")


if __name__ == "__main__":
    main()
