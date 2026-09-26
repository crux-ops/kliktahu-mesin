"""Gerak Skia: kinetik teks, elemen bentuk, pseudo-3D. Semua deterministik.

t selalu ternormalisasi [0,1] (dijepit bila keluar).
"""
import math

import skia

from .canvas import argb, fill_paint, stroke_paint
from .ease import clamp01, get as ease_get
from .timeline import stagger_local


def with_alpha(color, a01):
    """Kembalikan warna ARGB dengan alfa diskala a01 (0 transparan - 1 utuh)."""
    a01 = clamp01(a01)
    a = (int(color) >> 24) & 0xFF
    return ((int(round(a * a01)) & 0xFF) << 24) | (int(color) & 0xFFFFFF)


# ---------------- kinetik teks ----------------

def kinetic_rise(tc, canvas, cx, cy, text, name, size, color, t,
                 dist=70.0, ease="out_cubic"):
    """Teks naik dari bawah + memudar masuk."""
    u = ease_get(ease)(t)
    yy = float(cy) + float(dist) * (1.0 - u)
    tc.draw_center(canvas, float(cx), yy, text, name, float(size),
                   with_alpha(color, u))


def kinetic_pop(tc, canvas, cx, cy, text, name, size, color, t, ease="out_back"):
    """Teks membesar berlebih (overshoot) + memudar masuk."""
    u = ease_get(ease)(t)
    s = 0.4 + 0.6 * u
    a = clamp01(t * 2.5)
    if s <= 0.01 or a <= 0.0:
        return
    canvas.save()
    canvas.translate(float(cx), float(cy))
    canvas.scale(s, s)
    tc.draw_center(canvas, 0.0, 0.0, text, name, float(size),
                   with_alpha(color, a))
    canvas.restore()


def kinetic_words(tc, canvas, cx, cy, text, name, size, color, t,
                  dist=50.0, overlap=0.5):
    """Kata-per-kata naik beruntun (stagger), rata tengah keseluruhan."""
    words = str(text).split()
    if not words:
        return
    widths = [tc.width(w, name, size) for w in words]
    sp = tc.width(" ", name, size)
    x = float(cx) - (sum(widths) + sp * (len(words) - 1)) / 2.0
    for i, (w, ww) in enumerate(zip(words, widths)):
        lt = stagger_local(t, i, len(words), overlap)
        u = ease_get("out_cubic")(lt)
        yy = float(cy) + float(dist) * (1.0 - u)
        tc.draw_center(canvas, x + ww / 2.0, yy, w, name, float(size),
                       with_alpha(color, u))
        x += ww + sp


# ---------------- elemen bentuk ----------------

def bar_wipe(canvas, x, y, w, h, r, t, color, ease="in_out_cubic"):
    """Bilah tumbuh dari kiri (radius disesuaikan tinggi)."""
    u = ease_get(ease)(t)
    ww = float(w) * u
    if ww <= 0.5:
        return
    rr = min(float(r), float(h) / 2.0)
    canvas.drawRoundRect(skia.Rect.MakeXYWH(float(x), float(y), ww, float(h)),
                         rr, rr, fill_paint(color))


def circle_pop(canvas, cx, cy, rmax, t, color, ease="out_back",
               ring=None, ring_w=0.0):
    """Lingkaran meletus + memudar masuk; opsional cincin tepi."""
    u = ease_get(ease)(t)
    rr = float(rmax) * max(0.0, u)
    a = clamp01(t * 3.0)
    if rr <= 0.5 or a <= 0.0:
        return
    canvas.drawCircle(float(cx), float(cy), rr,
                      fill_paint(with_alpha(color, a)))
    if ring is not None and ring_w > 0:
        canvas.drawCircle(float(cx), float(cy), rr,
                          stroke_paint(with_alpha(ring, a), float(ring_w)))


def ring_pulse(canvas, cx, cy, r0, r1, t, color, width=6.0, ease="out_cubic"):
    """Cincin mengembang sambil memudar (denyut)."""
    u = ease_get(ease)(t)
    rr = float(r0) + (float(r1) - float(r0)) * u
    a = 1.0 - u
    if rr <= 0.5 or a <= 0.01:
        return
    canvas.drawCircle(float(cx), float(cy), rr,
                      stroke_paint(with_alpha(color, a), float(width)))


def spin_path(canvas, path, cx, cy, t, color, turns=1.0, ease="out_cubic"):
    """Path berputar masuk + membesar dari 0.3x + memudar."""
    u = ease_get(ease)(t)
    deg = 360.0 * float(turns) * (1.0 - u)
    s = 0.3 + 0.7 * u
    a = clamp01(t * 2.0)
    if s <= 0.01 or a <= 0.0:
        return
    canvas.save()
    canvas.translate(float(cx), float(cy))
    canvas.rotate(deg)
    canvas.scale(s, s)
    canvas.translate(-float(cx), -float(cy))
    canvas.drawPath(path, fill_paint(with_alpha(color, a)))
    canvas.restore()


# ---------------- pseudo-3D ----------------

def tilt_matrix(W, H, rx, ry, amount=0.0009):
    """Matriks miring perspektif semu di sekitar tengah kanvas.

    rx/ry -1..1 (positif = sisi kanan/bawah menjauh). Titik tengah invarian.
    """
    cx, cy = float(W) / 2.0, float(H) / 2.0
    m = skia.Matrix()
    m.setPerspX(float(rx) * float(amount))
    m.setPerspY(float(ry) * float(amount))
    m.preTranslate(-cx, -cy)
    m.postTranslate(cx, cy)
    return m


def draw_tilted(canvas, draw_fn, W, H, rx, ry, amount=0.0009):
    """Gambar draw_fn() dengan kemiringan perspektif semu."""
    canvas.save()
    canvas.concat(tilt_matrix(W, H, rx, ry, amount))
    draw_fn()
    canvas.restore()


def flip_cos(t):
    """Skala-X efek flip kartu: 1 -> 0 -> -1 (muka ganti di t=0.5)."""
    return math.cos(math.pi * clamp01(t))


def parallax_offsets(depths, travel):
    """Offset tiap lapis untuk paralaks (depth 0 jauh - 1 dekat)."""
    return [float(d) * float(travel) for d in depths]
