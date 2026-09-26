"""Bukti Bagian D: SFX sintetis + ducking (JALANKAN HANYA DI GITHUB ACTIONS).

Menghasilkan: proof_d_final.png (1080x1920, ss=2) + proof_d_fast.png +
demo_sfx.wav (7 SFX berurutan) + demo_duck.wav (bed VO + SFX ditundukkan).
Gagal bila render tak deterministik / puncak > -0.9 dBFS.
"""
import argparse
import os
import wave

import numpy as np
import skia

from . import ENGINE_VERSION
from .canvas import (Renderer, argb, fill_paint, hex_to_argb,
                     linear_gradient_paint)
from .sfx import (SR, SFX, duck_under, normalize_peak, peak_db, place,
                  render_sfx, rms, to_pcm16)
from .spec import SHORTS

CREAM = hex_to_argb("#F6F1E8")
INK = hex_to_argb("#18181F")
DARK = hex_to_argb("#23232B")
ACCENT = hex_to_argb("#B2542A")
TEAL = hex_to_argb("#1F7A6D")
GOLD = hex_to_argb("#C9A227")
MUTED = argb(255, 150, 145, 135)

KIND_ORDER = ["whoosh", "pop", "thump", "snap", "swell", "zap", "sweep"]
SEED = 7


def bed_vo(dur=4.0, sr=SR):
    """Bed pengganti VO: dengung 140 Hz berpintu suku-kata (SINTETIS, bukan suara)."""
    n = int(round(dur * sr))
    t = np.arange(n) / float(sr)
    tone = (np.sin(2 * np.pi * 140.0 * t)
            + 0.4 * np.sin(2 * np.pi * 280.0 * t)
            + 0.2 * np.sin(2 * np.pi * 420.0 * t)).astype(np.float32)
    gate = np.zeros(n, dtype=np.float32)
    for a, b in ((0.2, 0.45), (0.7, 1.05), (1.3, 1.7),
                 (1.9, 2.3), (2.6, 2.95), (3.2, 3.6)):
        gate[int(a * sr):int(b * sr)] = 1.0
    hann = np.hanning(min(n, int(sr * 0.01)) + 2).astype(np.float32)
    gate = np.convolve(gate, hann / hann.sum(), mode="same")
    gate = np.clip(gate, 0.0, 1.0).astype(np.float32)
    return normalize_peak(tone * gate * 0.5, 0.70)


def tulis_wav(path, x, sr=SR):
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(to_pcm16(x))


def draw_wave(c, x, y, w, h, data, color):
    c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), 12, 12, fill_paint(DARK))
    p = fill_paint(color)
    n = int(data.size)
    if n == 0:
        return
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


def draw_gain_curve(c, x, y, w, h, gains):
    gains = np.asarray(gains, dtype=np.float64)
    cols = max(2, int(w))
    idx = (np.arange(cols) * gains.size / cols).astype(int)
    path = skia.Path()
    for j in range(cols):
        px = x + j
        py = y + h - 6 - float(gains[idx[j]]) * (h - 12)
        if j == 0:
            path.moveTo(px, py)
        else:
            path.lineTo(px, py)
    p = skia.Paint()
    p.setAntiAlias(True)
    p.setColor(GOLD)
    p.setStyle(skia.Paint.Style.kStroke_Style)
    p.setStrokeWidth(3)
    c.drawPath(path, p)


def draw_sheet(r, seed, clips, vo, sfx_bed, ducked, gains):
    c, tc, W = r.canvas, r.text, r.w
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, r.h), fill_paint(CREAM))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 150),
               linear_gradient_paint(0, 0, W, 150, hex_to_argb("#23232B"),
                                     hex_to_argb("#3A3A44")))
    tc.draw_center(c, W / 2, 62, "SFX SINTETIS (D)", "Poppins-Bold.ttf",
                   68, argb(255, 246, 241, 232))
    tc.draw_center(c, W / 2, 120, "7 SFX numpy 48kHz - tanpa musik - ducking",
                   "Poppins-Regular.ttf", 30, MUTED)
    y = 172
    for kind, data in clips:
        tc.draw_center(c, W / 2, y + 14,
                       f"{kind}  {data.size / SR:.2f}s  "
                       f"peak {peak_db(data):.1f}dB  rms {rms(data):.3f}",
                       "Poppins-SemiBold.ttf", 24, INK)
        draw_wave(c, 60, y + 30, W - 120, 72, data, TEAL)
        y += 30 + 72 + 12
    y += 8
    tc.draw_center(c, W / 2, y + 16, "DUCKING DI BAWAH BED VO SINTETIS",
                   "Poppins-SemiBold.ttf", 30, INK)
    y += 40
    for label, data, col in (("bed VO sintetis (pengganti)", vo, ACCENT),
                             ("SFX kering", sfx_bed, TEAL),
                             ("SFX ditundukkan + kurva gain", ducked, TEAL)):
        tc.draw_center(c, W / 2, y + 14, label, "Poppins-SemiBold.ttf", 24, INK)
        draw_wave(c, 60, y + 30, W - 120, 72, data, col)
        if gains is not None and label.startswith("SFX ditundukkan"):
            draw_gain_curve(c, 60, y + 30, W - 120, 72, gains)
        y += 30 + 72 + 12
    y += 6
    red = rms(sfx_bed) / max(1e-9, rms(ducked))
    tc.draw_center(c, W / 2, y + 20,
                   f"reduksi ducking {20 * np.log10(red):.1f} dB (rms) - "
                   f"puncak campuran {peak_db(vo + ducked):.1f} dBFS",
                   "Poppins-Regular.ttf", 26, INK)
    assert y + 60 < r.h - 60, f"lembar meluap: {y} >= {r.h}"
    tc.draw_center(c, W / 2, r.h - 70,
                   "2x render identik - puncak <= -0.9 dBFS - deterministik",
                   "Poppins-Regular.ttf", 26, MUTED)
    tc.draw_center(c, W / 2, r.h - 34, f"seed {seed} - engine v{ENGINE_VERSION}",
                   "Poppins-Regular.ttf", 28, MUTED)


def build_all():
    """Render semua aset D. Kembalikan dict deterministik."""
    clips = [(k, render_sfx(k, seed=SEED)) for k in KIND_ORDER]
    for k, d in clips:  # determinisme tiap SFX
        assert np.array_equal(d, render_sfx(k, seed=SEED)), k
        assert peak_db(d) <= -0.9, f"{k} puncak {peak_db(d):.2f}dB"
    gap = np.zeros(int(0.25 * SR), dtype=np.float32)
    demo_parts = []
    for _, d in clips:
        demo_parts += [d, gap]
    demo_sfx = np.concatenate(demo_parts)
    vo = bed_vo(4.0)
    sfx_bed = place(4.0, [
        (0.30, render_sfx("whoosh", seed=SEED), 0.9),
        (1.00, render_sfx("pop", seed=SEED), 0.9),
        (1.80, render_sfx("thump", seed=SEED), 0.9),
        (2.50, render_sfx("sweep", seed=SEED), 0.8),
        (3.30, render_sfx("zap", seed=SEED), 0.8),
    ])
    ducked, gains = duck_under(sfx_bed, vo)
    mix = normalize_peak(vo + ducked)
    assert peak_db(mix) <= -0.9
    return {"clips": clips, "vo": vo, "sfx_bed": sfx_bed,
            "ducked": ducked, "gains": gains, "mix": mix,
            "demo_sfx": demo_sfx}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="proof-d")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    seed = SEED
    b = build_all()
    for kind, data in b["clips"]:
        print(f"  {kind:7s} {data.size / SR:5.2f}s peak {peak_db(data):6.1f}dB "
              f"rms {rms(data):.3f}")
    wavs = []
    for name, key in (("demo_sfx.wav", "demo_sfx"), ("demo_duck.wav", "mix")):
        p = os.path.join(a.outdir, name)
        tulis_wav(p, b[key])
        wav_bytes = open(p, "rb").read()
        p2 = os.path.join(a.outdir, name + ".tmp")
        tulis_wav(p2, b[key])
        assert open(p2, "rb").read() == wav_bytes, f"{name} tak deterministik"
        os.remove(p2)
        wav_dur = b[key].size / SR
        print(f"{name} {wav_dur:.2f}s {len(wav_bytes)} byte")
        wavs.append(name)
    _ = wavs
    outs = []
    for name, ss, scale, fin in (("proof_d_final.png", 2.0, 1.0, seed),
                                 ("proof_d_fast.png", 1.0, 0.25, None)):
        r = Renderer(SHORTS.w, SHORTS.h, ss=ss, out_scale=scale)
        draw_sheet(r, seed, b["clips"], b["vo"], b["sfx_bed"], b["ducked"],
                   b["gains"])
        data = r.png_bytes(finish_seed=fin)
        p = os.path.join(a.outdir, name)
        open(p, "wb").write(data)
        outs.append((name, Renderer.sha256(data), len(data),
                     f"{int(SHORTS.w*scale)}x{int(SHORTS.h*scale)}"))
    r2 = Renderer(SHORTS.w, SHORTS.h, ss=2.0, out_scale=1.0)
    draw_sheet(r2, seed, b["clips"], b["vo"], b["sfx_bed"], b["ducked"],
               b["gains"])
    h2 = Renderer.sha256(r2.png_bytes(finish_seed=seed))
    assert h2 == outs[0][1], f"render tidak deterministik: {h2} != {outs[0][1]}"
    for name, h, n, wh in outs:
        print(f"{name} {wh} {n} byte sha256={h}")
    print("deterministik OK (dua render final identik)")


if __name__ == "__main__":
    main()
