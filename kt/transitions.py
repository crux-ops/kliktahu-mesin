"""19 transisi sinkron-SFX antar dua adegan.

Tiap fungsi: tx(canvas, img_a, img_b, t, seed, W, H).
img_a/img_b harus skia.Image tepat W x H (adegan pra-render).
Kontrak: t=0 -> A byte-persis, t=1 -> B byte-persis, tengah -> campuran.
TX_EVENTS: {nama: [(t01, jenis_sfx, gain)]} untuk disambung Seksi D.
"""
import math

import skia

from .canvas import argb, blur_paint, fill_paint
from .ease import clamp01, get as ease_get
from .rng import spawn


def _full(W, H):
    return skia.Rect.MakeXYWH(0.0, 0.0, float(W), float(H))


def _src(img):
    return skia.Rect.MakeXYWH(0.0, 0.0, float(img.width()), float(img.height()))


def _alpha_paint(a01):
    p = skia.Paint()
    p.setAntiAlias(True)
    p.setAlpha(int(round(255.0 * clamp01(a01))))
    return p


def _draw(canvas, img, x, y, a01=1.0):
    canvas.drawImage(img, float(x), float(y), paint=_alpha_paint(a01))


# ---------------- potong & larut ----------------

def tx_cut(c, ia, ib, t, seed, W, H):
    _draw(c, ia if t < 0.5 else ib, 0, 0)


def tx_fade(c, ia, ib, t, seed, W, H):
    u = ease_get("smooth")(t)
    _draw(c, ia, 0, 0)
    _draw(c, ib, 0, 0, u)


def _dip(c, ia, ib, t, seed, W, H, color):
    c.drawRect(_full(W, H), fill_paint(color))
    if t < 0.5:
        _draw(c, ia, 0, 0, 1.0 - ease_get("in_cubic")(t * 2.0))
    else:
        _draw(c, ib, 0, 0, ease_get("out_cubic")(t * 2.0 - 1.0))


def tx_dip_black(c, ia, ib, t, seed, W, H):
    _dip(c, ia, ib, t, seed, W, H, argb(255, 0, 0, 0))


def tx_dip_white(c, ia, ib, t, seed, W, H):
    _dip(c, ia, ib, t, seed, W, H, argb(255, 255, 255, 255))


# ---------------- usap & dorong ----------------

def _wipe(c, ia, ib, t, seed, W, H, edge):
    u = ease_get("in_out_cubic")(t)
    _draw(c, ia, 0, 0)
    if edge == "right":
        rect = skia.Rect.MakeXYWH(0, 0, W * u, H)
    elif edge == "left":
        rect = skia.Rect.MakeXYWH(W * (1 - u), 0, W * u, H)
    elif edge == "up":
        rect = skia.Rect.MakeXYWH(0, H * (1 - u), W, H * u)
    else:  # down
        rect = skia.Rect.MakeXYWH(0, 0, W, H * u)
    c.save()
    c.clipRect(rect, skia.ClipOp.kIntersect, True)
    _draw(c, ib, 0, 0)
    c.restore()


def tx_wipe_right(c, ia, ib, t, seed, W, H):
    _wipe(c, ia, ib, t, seed, W, H, "right")


def tx_wipe_left(c, ia, ib, t, seed, W, H):
    _wipe(c, ia, ib, t, seed, W, H, "left")


def tx_wipe_up(c, ia, ib, t, seed, W, H):
    _wipe(c, ia, ib, t, seed, W, H, "up")


def tx_wipe_down(c, ia, ib, t, seed, W, H):
    _wipe(c, ia, ib, t, seed, W, H, "down")


def tx_push_left(c, ia, ib, t, seed, W, H):
    u = ease_get("in_out_cubic")(t)
    _draw(c, ia, -W * u, 0)
    _draw(c, ib, W * (1.0 - u), 0)


# ---------------- zoom & putar ----------------

def _around(c, W, H, rot_deg=0.0, scale=1.0):
    c.translate(float(W) / 2.0, float(H) / 2.0)
    if rot_deg:
        c.rotate(float(rot_deg))
    if scale != 1.0:
        c.scale(float(scale), float(scale))
    c.translate(-float(W) / 2.0, -float(H) / 2.0)


def tx_zoom_in(c, ia, ib, t, seed, W, H):
    u = ease_get("out_cubic")(t)
    _draw(c, ia, 0, 0)
    c.save()
    _around(c, W, H, scale=0.35 + 0.65 * u)
    _draw(c, ib, 0, 0, min(1.0, u * 1.5))
    c.restore()


def tx_zoom_out(c, ia, ib, t, seed, W, H):
    u = ease_get("in_cubic")(t)
    _draw(c, ib, 0, 0)
    c.save()
    _around(c, W, H, scale=1.0 - 0.65 * u)
    _draw(c, ia, 0, 0, max(0.0, 1.0 - u * 1.2))
    c.restore()


def tx_spin_in(c, ia, ib, t, seed, W, H):
    u = ease_get("out_cubic")(t)
    _draw(c, ia, 0, 0)
    c.save()
    _around(c, W, H, rot_deg=160.0 * (1.0 - u), scale=0.4 + 0.6 * u)
    _draw(c, ib, 0, 0, min(1.0, u * 1.5))
    c.restore()


# ---------------- blur & iris ----------------

def tx_blur_dissolve(c, ia, ib, t, seed, W, H):
    u = ease_get("smooth")(t)
    c.drawImage(ia, 0, 0, paint=blur_paint(26.0 * u, int(255 * (1.0 - u))))
    c.drawImage(ib, 0, 0, paint=blur_paint(26.0 * (1.0 - u), int(255 * u)))


def _iris_radius(W, H):
    return math.hypot(float(W), float(H)) / 2.0 + 1.0


def tx_iris_open(c, ia, ib, t, seed, W, H):
    u = ease_get("in_out_cubic")(t)
    _draw(c, ia, 0, 0)
    p = skia.Path()
    p.addCircle(float(W) / 2.0, float(H) / 2.0, max(0.0, _iris_radius(W, H) * u))
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    _draw(c, ib, 0, 0)
    c.restore()


def tx_iris_close(c, ia, ib, t, seed, W, H):
    u = ease_get("in_out_cubic")(t)
    _draw(c, ib, 0, 0)
    p = skia.Path()
    p.addCircle(float(W) / 2.0, float(H) / 2.0,
                max(0.0, _iris_radius(W, H) * (1.0 - u)))
    c.save()
    c.clipPath(p, skia.ClipOp.kIntersect, True)
    _draw(c, ia, 0, 0)
    c.restore()


def tx_blinds(c, ia, ib, t, seed, W, H, n=8):
    u = ease_get("in_out_cubic")(t)
    _draw(c, ia, 0, 0)
    sh = float(H) / n
    for i in range(n):
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(0, i * sh, W * u, sh),
                   skia.ClipOp.kIntersect, True)
        _draw(c, ib, 0, 0)
        c.restore()


# ---------------- rusak-sinyal & piksel ----------------

def tx_glitch(c, ia, ib, t, seed, W, H, slices=12):
    env = math.sin(math.pi * clamp01(t))  # 0 di ujung, 1 di tengah
    if env < 1e-9:
        _draw(c, ia if t < 0.5 else ib, 0, 0)
        return
    base, other = (ia, ib) if t < 0.5 else (ib, ia)
    _draw(c, base, 0, 0)
    r = spawn(seed, "glitch")
    offs = [r.uniform(-1.0, 1.0) for _ in range(slices)]
    sh = float(H) / slices
    amp = float(W) * 0.06 * env
    for i, o in enumerate(offs):
        if abs(o) < 0.25:
            continue
        y0 = i * sh
        c.drawImageRect(other,
                        skia.Rect.MakeXYWH(0, y0, W, sh + 1.0),
                        skia.Rect.MakeXYWH(o * amp, y0, W, sh + 1.0),
                        skia.SamplingOptions())
    if env > 0.15:
        r2 = spawn(seed, "glitch-bar")
        bars = [argb(255, 255, 45, 85), argb(255, 45, 255, 255),
                argb(255, 255, 255, 255)]
        for _ in range(3):
            yy = r2.uniform(0, float(H))
            c.drawRect(skia.Rect.MakeXYWH(0, yy, W, max(2.0, H * 0.004)),
                       fill_paint(r2.choice(bars)))


def tx_pixelate(c, ia, ib, t, seed, W, H):
    u = ease_get("in_out_cubic")(t)
    _draw(c, ia, 0, 0)
    if u <= 0.0:
        return
    px = max(1, int(round(1.0 + (max(W, H) / 10.0 - 1.0) * (1.0 - u))))
    sw, sh = max(1, int(W) // px), max(1, int(H) // px)
    tmp = skia.Surface(sw, sh)
    tmp.getCanvas().drawImageRect(ib, _src(ib),
                                  skia.Rect.MakeXYWH(0, 0, sw, sh))
    tiny = tmp.makeImageSnapshot()
    p = skia.Paint()
    p.setAntiAlias(False)
    p.setAlpha(int(255 * u))
    c.drawImageRect(tiny, skia.Rect.MakeXYWH(0, 0, sw, sh), _full(W, H),
                    skia.SamplingOptions(skia.FilterMode.kNearest), p)


def tx_flash(c, ia, ib, t, seed, W, H):
    u = ease_get("smooth")(t)
    _draw(c, ia, 0, 0)
    _draw(c, ib, 0, 0, u)
    peak = 1.0 - abs(t * 2.0 - 1.0)
    a = int(255 * peak * peak)
    if a > 0:
        c.drawRect(_full(W, H), fill_paint(argb(a, 255, 255, 255)))


# ---------------- registri + titik sinkron SFX ----------------

TRANSITIONS = {
    "cut": (tx_cut, [(0.5, "pop", 0.8)]),
    "fade": (tx_fade, [(0.0, "swell", 0.4)]),
    "dip_black": (tx_dip_black, [(0.5, "thump", 0.7)]),
    "dip_white": (tx_dip_white, [(0.5, "snap", 0.5)]),
    "wipe_right": (tx_wipe_right, [(0.0, "whoosh", 0.8)]),
    "wipe_left": (tx_wipe_left, [(0.0, "whoosh", 0.8)]),
    "wipe_up": (tx_wipe_up, [(0.0, "whoosh", 0.8)]),
    "wipe_down": (tx_wipe_down, [(0.0, "whoosh", 0.8)]),
    "push_left": (tx_push_left, [(0.0, "whoosh", 0.9)]),
    "zoom_in": (tx_zoom_in, [(0.0, "whoosh", 0.8)]),
    "zoom_out": (tx_zoom_out, [(0.0, "sweep", 0.6)]),
    "spin_in": (tx_spin_in, [(0.0, "whoosh", 0.8)]),
    "blur_dissolve": (tx_blur_dissolve, [(0.0, "swell", 0.7)]),
    "iris_open": (tx_iris_open, [(0.0, "pop", 0.6)]),
    "iris_close": (tx_iris_close, [(1.0, "snap", 0.5)]),
    "blinds": (tx_blinds, [(0.0, "sweep", 0.7)]),
    "glitch": (tx_glitch, [(0.0, "zap", 0.8)]),
    "pixelate": (tx_pixelate, [(0.0, "sweep", 0.6)]),
    "flash": (tx_flash, [(0.5, "snap", 0.8)]),
}

TX_NAMES = list(TRANSITIONS)
TX_EVENTS = {k: v[1] for k, v in TRANSITIONS.items()}


def get_tx(name):
    try:
        return TRANSITIONS[name][0]
    except KeyError:
        raise ValueError(f"transisi tak dikenal: {name}")
