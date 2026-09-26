"""Bukti Bagian A: lembar uji renderer (JALANKAN HANYA DI GITHUB ACTIONS).

Menghasilkan: proof_final.png (1080x1920, ss=2) + proof_fast.png (pratinjau 0.25x).
Cetak sha256 + ukuran. Gagal bila dua render identik tidak sama persis.
"""
import argparse
import os

import skia

from . import ENGINE_VERSION
from .canvas import (Renderer, argb, fill_paint, glass_panel, hex_to_argb,
                     linear_gradient_paint, soft_shadow, star_path, stroke_paint,
                     finish_frame)
from .spec import SHORTS
from PIL import Image
import numpy as np

CREAM = hex_to_argb("#F6F1E8")
INK = hex_to_argb("#18181F")
ACCENT = hex_to_argb("#B2542A")
TEAL = hex_to_argb("#1F7A6D")
GOLD = hex_to_argb("#C9A227")


def draw_sheet(r: Renderer, seed: int):
    c = r.canvas
    W, H = r.w, r.h
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), fill_paint(CREAM))
    # kepala: gradien + judul
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 300),
               linear_gradient_paint(0, 0, W, 300, hex_to_argb("#23232B"), hex_to_argb("#3A3A44")))
    r.text.draw_center(c, W / 2, 120, "KLIKTAHU ENGINE v3", "Poppins-Bold.ttf", 84,
                       argb(255, 246, 241, 232))
    r.text.draw_center(c, W / 2, 210, "bukti renderer skia - deterministik", "Poppins-Regular.ttf", 40,
                       argb(255, 200, 195, 185))
    # kartu bayangan + lingkaran AA + bintang path
    soft_shadow(c, 80, 380, 920, 420, 48)
    c.drawRoundRect(skia.Rect.MakeXYWH(80, 380, 920, 420), 48, 48, fill_paint(argb(255, 255, 255, 255)))
    c.drawCircle(300, 625, 105, fill_paint(ACCENT))
    c.drawCircle(300, 625, 105, stroke_paint(INK, 6))
    c.drawPath(star_path(700, 625, 115, 48), fill_paint(GOLD))
    c.drawPath(star_path(700, 625, 115, 48), stroke_paint(INK, 5))
    r.text.draw_center(c, 540, 448, "ANTI-ALIASING + PATH", "Poppins-SemiBold.ttf", 36, INK)
    # panel kaca di atas pola warna
    for i, col in enumerate(["#B2542A", "#1F7A6D", "#3B4E8C", "#C9A227"]):
        c.drawRect(skia.Rect.MakeXYWH(80 + i * 230, 860, 230, 260), fill_paint(hex_to_argb(col)))
    glass_panel(r.surface, 140, 890, 800, 200, 40)
    r.text.draw_center(c, 540, 990, "LIQUID GLASS (blur + kilap tepi)", "Poppins-SemiBold.ttf", 34, INK)
    # teks multi-ukuran + rotasi
    r.text.draw_paragraph(c, 80, 1180, "Poppins Bold 96\nSemiBold 64 / Medium 44\nRegular 32 - badan teks",
                          "Poppins-Bold.ttf", 44, INK)
    c.save()
    c.translate(880, 1400)
    c.rotate(18)
    c.drawRoundRect(skia.Rect.MakeXYWH(-150, -60, 300, 120), 24, 24, fill_paint(TEAL))
    c.restore()
    r.text.draw_center(c, 880, 1400, "ROTASI", "Poppins-Bold.ttf", 40, argb(255, 255, 255, 255))
    # garis tipis + swatch
    for i in range(5):
        y = 1560 + i * 14
        c.drawLine(80, y, 1000, y, stroke_paint(argb(255 - i * 30, 24, 24, 31), 2))
    for i, col in enumerate([ACCENT, TEAL, GOLD, INK]):
        c.drawCircle(180 + i * 120, 1700, 44, fill_paint(col))
    r.text.draw_center(c, 540, 1820, f"seed {seed} - engine v{ENGINE_VERSION}",
                       "Poppins-Regular.ttf", 32, argb(255, 128, 122, 114))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="proof-a")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    seed = 7
    outs = []
    for name, ss, scale, fin in (("proof_final.png", 2.0, 1.0, seed),
                                 ("proof_fast.png", 1.0, 0.25, None)):
        r = Renderer(SHORTS.w, SHORTS.h, ss=ss, out_scale=scale)
        draw_sheet(r, seed)
        data = r.png_bytes(finish_seed=fin)
        p = os.path.join(a.outdir, name)
        open(p, "wb").write(data)
        outs.append((name, Renderer.sha256(data), len(data),
                     f"{int(SHORTS.w*scale)}x{int(SHORTS.h*scale)}"))
    # determinisme: render ulang final, hash harus identik
    r2 = Renderer(SHORTS.w, SHORTS.h, ss=2.0, out_scale=1.0)
    draw_sheet(r2, seed)
    h2 = Renderer.sha256(r2.png_bytes(finish_seed=seed))
    assert h2 == outs[0][1], f"render tidak deterministik: {h2} != {outs[0][1]}"
    for name, h, n, wh in outs:
        print(f"{name} {wh} {n} byte sha256={h}")
    print("deterministik OK (dua render final identik)")


if __name__ == "__main__":
    main()
