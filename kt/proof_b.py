"""Bukti Bagian B: montase gerak & transisi (JALANKAN HANYA DI GITHUB ACTIONS).

Menghasilkan: proof_b_final.png (1080x1920, ss=2) + proof_b_fast.png (0.25x).
Gagal bila dua render identik tidak sama persis.
"""
import argparse
import io
import os

import numpy as np
import skia
from PIL import Image

from . import ENGINE_VERSION
from .camera import Camera, make_shake
from .canvas import (Renderer, argb, fill_paint, hex_to_argb, star_path,
                     linear_gradient_paint)
from .cine import chromatic_aberration, letterbox
from .ease import EASE
from .motion import kinetic_pop, kinetic_rise, kinetic_words
from .spec import SHORTS
from .timeline import typewriter_text
from .transitions import TX_NAMES, get_tx

CREAM = hex_to_argb("#F6F1E8")
INK = hex_to_argb("#18181F")
DARK = hex_to_argb("#23232B")
ACCENT = hex_to_argb("#B2542A")
TEAL = hex_to_argb("#1F7A6D")
GOLD = hex_to_argb("#C9A227")
MUTED = argb(255, 150, 145, 135)


def scene_image(w, h, variant):
    """Adegan demo kecil -> skia.Image tepat w x h."""
    r = Renderer(int(w), int(h), ss=1.0)
    c = r.canvas
    if variant == "A":
        bg, fg, sx = "#B2542A", "#F6F1E8", 0.30
    else:
        bg, fg, sx = "#1F7A6D", "#C9A227", 0.70
    c.drawRect(skia.Rect.MakeXYWH(0, 0, w, h), fill_paint(hex_to_argb(bg)))
    c.drawCircle(w * sx, h * 0.5, min(w, h) * 0.22, fill_paint(hex_to_argb(fg)))
    c.drawPath(star_path(w * (1 - sx), h * 0.5, min(w, h) * 0.20,
                         min(w, h) * 0.09), fill_paint(hex_to_argb(fg)))
    r.text.draw_center(c, w / 2, h * 0.16, variant, "Poppins-Bold.ttf",
                       min(w, h) * 0.22, argb(255, 255, 255, 255))
    return r.surface.makeImageSnapshot()


def _cell_clip(c, x, y, w, h):
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h), skia.ClipOp.kIntersect, True)


def draw_easing_row(r, y):
    c, tc = r.canvas, r.text
    tc.draw_center(c, 540, y + 20, "EASING (kurva waktu)",
                   "Poppins-SemiBold.ttf", 32, INK)
    names = ["linear", "smooth", "out_cubic", "out_back"]
    cw, chh = 232, 140
    x0 = (1080 - (4 * cw + 3 * 16)) / 2
    yy = y + 44
    for i, name in enumerate(names):
        x = x0 + i * (cw + 16)
        c.drawRoundRect(skia.Rect.MakeXYWH(x, yy, cw, chh), 16, 16,
                        fill_paint(argb(255, 255, 255, 255)))
        pad = 18
        # petakan 0..1 ke tinggi kotak; overshoot (out_back) dijepit rapi
        pts = [(x + pad + (cw - 2 * pad) * k / 40,
                yy + chh - pad - (chh - 2 * pad)
                * min(1.0, max(0.0, EASE[name](k / 40))))
               for k in range(41)]
        path = skia.Path()
        path.moveTo(*pts[0])
        for px, py in pts[1:]:
            path.lineTo(px, py)
        p = skia.Paint()
        p.setAntiAlias(True)
        p.setColor(TEAL)
        p.setStyle(skia.Paint.Style.kStroke_Style)
        p.setStrokeWidth(5)
        c.drawPath(path, p)
        tc.draw_center(c, x + cw / 2, yy + chh + 24, name,
                       "Poppins-Regular.ttf", 24, INK)
    return yy + chh + 52


def draw_kinetic_row(r, y):
    c, tc = r.canvas, r.text
    tc.draw_center(c, 540, y + 20, "KINETIK TEKS",
                   "Poppins-SemiBold.ttf", 32, INK)
    cw, chh = 156, 124
    x0 = (1080 - (6 * cw + 5 * 12)) / 2
    yy = y + 44
    cells = ["rise 0.00", "rise 0.33", "rise 0.66", "rise 1.00",
             "words 0.5", "pop 0.6"]
    for i, label in enumerate(cells):
        x = x0 + i * (cw + 12)
        c.drawRoundRect(skia.Rect.MakeXYWH(x, yy, cw, chh), 14, 14,
                        fill_paint(DARK))
        _cell_clip(c, x, yy, cw, chh)
        cx = x + cw / 2
        if label.startswith("rise"):
            kinetic_rise(tc, c, cx, yy + chh / 2, "GERAK", "Poppins-Bold.ttf",
                         44, argb(255, 246, 241, 232), float(label[5:]))
        elif label.startswith("words"):
            kinetic_words(tc, c, cx, yy + chh / 2, "OTAK CERAH",
                          "Poppins-Bold.ttf", 24,
                          argb(255, 246, 241, 232), 0.5)
        else:
            kinetic_pop(tc, c, cx, yy + chh / 2, "POP!", "Poppins-Bold.ttf",
                        44, GOLD, 0.6)
        c.restore()
        tc.draw_center(c, cx, yy + chh + 22, label,
                       "Poppins-Regular.ttf", 22, INK)
    ty = yy + chh + 48
    for j, tt in enumerate((0.2, 0.5, 1.0)):
        s = typewriter_text("JANTUNG MEMOMPA", tt, cps=10.0)
        tc.draw_center(c, 540, ty + j * 36, f"ketik t={tt}: '{s}|'",
                       "Poppins-Regular.ttf", 28, INK)
    return ty + 3 * 36 + 14


def draw_tx_grid(r, y):
    c, tc = r.canvas, r.text
    tc.draw_center(c, 540, y + 20, f"TRANSISI TENGAH (19, t=0.5, seed 7)",
                   "Poppins-SemiBold.ttf", 32, INK)
    cols, cw, chh = 5, 187, 117
    x0 = (1080 - (cols * cw + (cols - 1) * 12)) / 2
    yy = y + 44
    ia, ib = scene_image(cw, chh, "A"), scene_image(cw, chh, "B")
    for i, name in enumerate(TX_NAMES):
        gx = x0 + (i % cols) * (cw + 12)
        gy = yy + (i // cols) * (chh + 40)
        c.drawRoundRect(skia.Rect.MakeXYWH(gx - 3, gy - 3, cw + 6, chh + 6),
                        10, 10, fill_paint(argb(255, 255, 255, 255)))
        _cell_clip(c, gx, gy, cw, chh)
        c.save()
        c.translate(gx, gy)
        get_tx(name)(c, ia, ib, 0.5, 7, cw, chh)
        c.restore()
        c.restore()
        tc.draw_center(c, gx + cw / 2, gy + chh + 20, name,
                       "Poppins-Regular.ttf", 20, INK)
    rows = (len(TX_NAMES) + cols - 1) // cols
    return yy + rows * (chh + 40) + 8


def draw_camera_row(r, y):
    c, tc = r.canvas, r.text
    tc.draw_center(c, 540, y + 18, "KAMERA VIRTUAL",
                   "Poppins-SemiBold.ttf", 32, INK)
    cw, chh = 317, 130
    x0 = (1080 - (3 * cw + 2 * 16)) / 2
    yy = y + 36
    img = scene_image(cw, chh, "A")
    shots = [("normal", Camera()),
             ("zoom 1.4 + geser", Camera(x=24, y=-10, zoom=1.4)),
             ("guncang t=0.5", None)]
    dx, dy, dr = make_shake(3)(0.5)
    shots[2] = ("guncang t=0.5", Camera(x=dx, y=dy, rot=dr))
    for i, (label, cam) in enumerate(shots):
        x = x0 + i * (cw + 16)
        _cell_clip(c, x, yy, cw, chh)
        c.save()
        c.translate(x, yy)
        cam.apply(c, cw, chh)
        p = skia.Paint()
        p.setAlpha(255)
        c.drawImage(img, 0, 0, paint=p)
        c.restore()
        c.restore()
        tc.draw_center(c, x + cw / 2, yy + chh + 22, label,
                       "Poppins-Regular.ttf", 22, INK)
    return yy + chh + 46


def _opaque_paint():
    p = skia.Paint()
    p.setAntiAlias(True)
    p.setAlpha(255)
    return p


def _skia_from_numpy(arr):
    buf = io.BytesIO()
    Image.fromarray(np.ascontiguousarray(arr), "RGB").save(buf, format="PNG")
    return skia.Image.MakeFromEncoded(buf.getvalue())


def draw_cine_row(r, y):
    c, tc = r.canvas, r.text
    tc.draw_center(c, 540, y + 18, "FINISHING SINEMATIK",
                   "Poppins-SemiBold.ttf", 32, INK)
    cw, chh = 317, 130
    x0 = (1080 - (3 * cw + 2 * 16)) / 2
    yy = y + 36
    base = scene_image(cw, chh, "B")
    # baca piksel adegan via PNG agar homogen dengan jalur produksi
    tmp = Renderer(cw, chh, ss=1.0)
    tmp.canvas.drawImage(base, 0, 0, paint=_opaque_paint())
    arr = np.array(tmp.to_pil())
    cells = [("asli", arr),
             ("letterbox", letterbox(arr, 0.18)),
             ("aberasi kromatik", chromatic_aberration(arr, 5.0))]
    for i, (label, a) in enumerate(cells):
        x = x0 + i * (cw + 16)
        c.drawImage(_skia_from_numpy(a), x, yy, paint=_opaque_paint())
        tc.draw_center(c, x + cw / 2, yy + chh + 22, label,
                       "Poppins-Regular.ttf", 22, INK)
    return yy + chh + 46


def draw_sheet(r: Renderer, seed: int):
    c, tc, W = r.canvas, r.text, r.w
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, r.h), fill_paint(CREAM))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, 150),
               linear_gradient_paint(0, 0, W, 150, hex_to_argb("#23232B"),
                                     hex_to_argb("#3A3A44")))
    tc.draw_center(c, W / 2, 62, "GERAK & TRANSISI (B)", "Poppins-Bold.ttf",
                   68, argb(255, 246, 241, 232))
    tc.draw_center(c, W / 2, 120, "19 transisi sinkron-SFX - kinetik - kamera",
                   "Poppins-Regular.ttf", 32, MUTED)
    y = 170
    y = draw_easing_row(r, y)
    y = draw_kinetic_row(r, y)
    y = draw_tx_grid(r, y)
    y = draw_camera_row(r, y)
    y = draw_cine_row(r, y)
    assert y < r.h - 30, f"montase meluap: {y} >= {r.h}"
    tc.draw_center(c, W / 2, r.h - 34, f"seed {seed} - engine v{ENGINE_VERSION}",
                   "Poppins-Regular.ttf", 28, MUTED)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="proof-b")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    seed = 7
    outs = []
    for name, ss, scale, fin in (("proof_b_final.png", 2.0, 1.0, seed),
                                 ("proof_b_fast.png", 1.0, 0.25, None)):
        r = Renderer(SHORTS.w, SHORTS.h, ss=ss, out_scale=scale)
        draw_sheet(r, seed)
        data = r.png_bytes(finish_seed=fin)
        p = os.path.join(a.outdir, name)
        open(p, "wb").write(data)
        outs.append((name, Renderer.sha256(data), len(data),
                     f"{int(SHORTS.w*scale)}x{int(SHORTS.h*scale)}"))
    r2 = Renderer(SHORTS.w, SHORTS.h, ss=2.0, out_scale=1.0)
    draw_sheet(r2, seed)
    h2 = Renderer.sha256(r2.png_bytes(finish_seed=seed))
    assert h2 == outs[0][1], f"render tidak deterministik: {h2} != {outs[0][1]}"
    for name, h, n, wh in outs:
        print(f"{name} {wh} {n} byte sha256={h}")
    print("deterministik OK (dua render final identik)")


if __name__ == "__main__":
    main()
