#!/usr/bin/env python3
"""Renderer video Shorts 9:16 - terang & minimalis, animasi kinetik + ikon bergerak."""
import argparse, json, math, os, sys, time
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import diagrams
import mesin_util

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "..", "build")
FDIR = os.path.join(BASE, "fonts")
W, H = 1080, 1920
SS = float(os.environ.get("KT_SS", "2.0"))  # mesin v2: supersample default 2.0 (env KT_SS)
SHARPEN = float(os.environ.get("KT_SHARPEN", "45"))  # penajam tepi setelah downscale (0 = mati)
CREAM = (246, 241, 232)
INK = (24, 24, 31)
MUTED = (128, 122, 114)
WHITE = (255, 255, 255)
TRACK = (229, 222, 209)

FB, FS, FM, FR = "Poppins-Bold.ttf", "Poppins-SemiBold.ttf", "Poppins-Medium.ttf", "Poppins-Regular.ttf"
_F = {}


def font(name, size):
    k = (name, round(size, 1))
    if k not in _F:
        _F[k] = ImageFont.truetype(os.path.join(FDIR, name), max(8, int(round(size * SS))))
    return _F[k]


def S(v):
    return v * SS


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


def eo(t):
    t = clamp(t); return 1 - (1 - t) ** 3


def eio(t):
    t = clamp(t); return t * t * (3 - 2 * t)


def eob(t, c1=1.35):
    t = clamp(t); return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


def seg(t, a, b):
    """progress 0..1 untuk rentang [a,b]."""
    return clamp((t - a) / max(1e-6, b - a))


# ---------- teks ----------
_tmp = Image.new("RGB", (8, 8)); _td = ImageDraw.Draw(_tmp)


def tw(text, f):
    return _td.textlength(text, font=f) / SS


def tlh(f):
    a, d = f.getmetrics(); return (a + d) / SS


def tlayer(text, f, fill, alpha=1.0, pad=6):
    if alpha <= 0.01 or not text:
        return None
    w = int(_td.textlength(text, font=f)); h = int(tlh(f) * SS)
    p = int(pad * SS)
    lay = Image.new("RGBA", (max(1, w + 2 * p), max(1, h + 2 * p)), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((p, p), text, font=f, fill=tuple(fill) + (int(clamp(alpha) * 255),))
    return lay


def paste_c(base, cx, cy, text, f, fill, alpha=1.0, scale=1.0, dx=0.0, dy=0.0):
    if text and getattr(diagrams, "TRACK", False):
        w_ = tw(text, f); h_ = tlh(f)
        diagrams._note("render-c", cx + dx - w_ / 2, cy + dy - h_ / 2,
                       cx + dx + w_ / 2, cy + dy + h_ / 2, text)
    lay = tlayer(text, f, fill, alpha)
    if lay is None:
        return
    if abs(scale - 1) > 0.01:
        nw, nh = max(1, int(lay.width * scale)), max(1, int(lay.height * scale))
        lay = lay.resize((nw, nh), Image.BICUBIC)
    base.paste(lay, (int(S(cx + dx) - lay.width / 2), int(S(cy + dy) - lay.height / 2)), lay)


def paste_l(base, x, cy, text, f, fill, alpha=1.0, dx=0.0, dy=0.0):
    if text and getattr(diagrams, "TRACK", False):
        w_ = tw(text, f); h_ = tlh(f)
        diagrams._note("render-l", x + dx, cy + dy - h_ / 2, x + dx + w_, cy + dy + h_ / 2, text)
    lay = tlayer(text, f, fill, alpha)
    if lay is None:
        return 0
    base.paste(lay, (int(S(x + dx)), int(S(cy + dy) - lay.height / 2)), lay)
    return 1


def paste_tl(base, x, y, text, f, fill, alpha=1.0, dx=0.0, dy=0.0):
    if text and getattr(diagrams, "TRACK", False):
        w_ = tw(text, f); h_ = tlh(f)
        diagrams._note("render-tl", x + dx, y + dy, x + dx + w_, y + dy + h_, text)
    lay = tlayer(text, f, fill, alpha)
    if lay is None:
        return
    base.paste(lay, (int(S(x + dx)), int(S(y + dy))), lay)


def fit_size(name, text, size, maxw):
    """Perkecil ukuran font otomatis sampai teks muat dalam maxw."""
    f = font(name, size)
    w = tw(text, f)
    if w <= maxw:
        return size
    return size * (maxw / w)


def wrap(text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if tw(t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def rrect(base, x, y, w, h, r, fill=None, outline=None, width=2, alpha=1.0):
    """roundrect dengan alpha (dipakai untuk pill / chip)."""
    if alpha <= 0.01:
        return
    a = int(clamp(alpha) * 255)
    lay = Image.new("RGBA", (int(S(w)) + int(S(width)) * 2 + 4, int(S(h)) + int(S(width)) * 2 + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pad = int(S(width)) + 2
    d.rounded_rectangle([pad, pad, pad + int(S(w)), pad + int(S(h))], radius=S(r),
                        fill=(tuple(fill) + (a,)) if fill else None,
                        outline=(tuple(outline) + (a,)) if outline else None,
                        width=max(1, int(S(width))))
    base.paste(lay, (int(S(x) - pad), int(S(y) - pad)), lay)


def star4(d, cx, cy, r, color):
    k = 0.26
    d.polygon([(S(cx), S(cy - r)), (S(cx + k * r), S(cy - k * r)), (S(cx + r), S(cy)),
               (S(cx + k * r), S(cy + k * r)), (S(cx), S(cy + r)), (S(cx - k * r), S(cy + k * r)),
               (S(cx - r), S(cy)), (S(cx - k * r), S(cy - k * r))], fill=color)


def rot(pts, cx, cy, ang, k=1.0):
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for (x, y) in pts:
        dx, dy = (x - cx) * k, (y - cy) * k
        out.append((S(cx + dx * ca - dy * sa), S(cy + dx * sa + dy * ca)))
    return out


def line(base, p1, p2, color, width, cap_round=True):
    d = ImageDraw.Draw(base)
    d.line([S(p1[0]), S(p1[1]), S(p2[0]), S(p2[1])], fill=color, width=max(1, int(S(width))))
    if cap_round:
        r = width / 2.0
        d.ellipse([S(p1[0] - r), S(p1[1] - r), S(p1[0] + r), S(p1[1] + r)], fill=color)
        d.ellipse([S(p2[0] - r), S(p2[1] - r), S(p2[0] + r), S(p2[1] + r)], fill=color)


def circ(base, cx, cy, r, color):
    ImageDraw.Draw(base).ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=color)


def ring(base, cx, cy, r, color, width):
    ImageDraw.Draw(base).ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)],
                                 outline=color, width=max(1, int(S(width))))


def ell(base, x0, y0, x1, y1, fill=None, outline=None, width=3):
    ImageDraw.Draw(base).ellipse([S(x0), S(y0), S(x1), S(y1)], fill=fill, outline=outline,
                                 width=max(1, int(S(width))))


# ---------- ikon ----------
def ic_molecule(base, cx, cy, s, accent, p):
    n = 5
    pts = [(cx - 0.46 * s + i * (0.23 * s), cy + (0.07 * s) * math.sin(i * 1.5)) for i in range(n)]
    r = 0.075 * s
    for i in range(n - 1):
        f = seg(p, i / n, (i + 1) / n)
        if f <= 0:
            continue
        a, b = pts[i], pts[i + 1]
        m = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        line(base, a, m, mix(WHITE, accent, 0.55), 0.045 * s)
    for i in range(n):
        f = seg(p, i / n, i / n + 0.28)
        if f <= 0:
            continue
        rr = r * eob(f)
        c = mix(WHITE, accent, 0.95) if i < n - 1 else (193, 80, 46)
        circ(base, pts[i][0], pts[i][1], rr, c)
        if i == n - 1:
            circ(base, pts[i][0] - rr * 0.3, pts[i][1] - rr * 0.28, rr * 0.22, (150, 62, 36))
            circ(base, pts[i][0] + rr * 0.34, pts[i][1] + rr * 0.34, rr * 0.15, (150, 62, 36))
    # cincin orbit samar
    for i in range(3):
        a = 0.25 + i * 0.1
        ImageDraw.Draw(base).arc([S(cx - 0.5 * s), S(cy - 0.34 * s), S(cx + 0.5 * s), S(cy + 0.34 * s)],
                                 start=200 + i * 30, end=340 + i * 30, fill=mix(CREAM, accent, 0.25),
                                 width=max(1, int(S(2.2))))


def ic_sugar(base, cx, cy, s, accent, p, t):
    k = eob(p)
    ang = math.sin(t * 1.6) * 0.08
    top = [(cx, cy - 0.30 * s), (cx + 0.32 * s, cy - 0.13 * s), (cx, cy + 0.04 * s), (cx - 0.32 * s, cy - 0.13 * s)]
    left = [(cx - 0.32 * s, cy - 0.13 * s), (cx, cy + 0.04 * s), (cx, cy + 0.34 * s), (cx - 0.32 * s, cy + 0.17 * s)]
    right = [(cx + 0.32 * s, cy - 0.13 * s), (cx, cy + 0.04 * s), (cx, cy + 0.34 * s), (cx + 0.32 * s, cy + 0.17 * s)]
    d = ImageDraw.Draw(base)
    d.polygon(rot(left, cx, cy, ang, k), fill=mix(accent, WHITE, 0.05))
    d.polygon(rot(right, cx, cy, ang, k), fill=mix(accent, INK, 0.22))
    d.polygon(rot(top, cx, cy, ang, k), fill=mix(accent, WHITE, 0.62))
    for i, (dx, dy, ph) in enumerate([(-0.52, -0.42, 0.0), (0.5, -0.3, 1.1), (0.34, 0.46, 2.2), (-0.44, 0.34, 3.0)]):
        tw_ = seg(p, 0.35 + i * 0.1, 0.62 + i * 0.1) * (0.55 + 0.45 * abs(math.sin(t * 2.2 + ph)))
        if tw_ > 0.02:
            star4(d, cx + dx * s, cy + dy * s, 0.13 * s * tw_, mix(CREAM, accent, 0.75))


def ic_orbit(base, cx, cy, s, accent, p, t):
    circ(base, cx, cy, 0.115 * s, mix(accent, WHITE, 0.25))
    ring(base, cx, cy, 0.115 * s, accent, 0.022 * s)
    for i in range(3):
        rx, ry = (0.28 + i * 0.115) * s, (0.165 + i * 0.075) * s
        ImageDraw.Draw(base).ellipse([S(cx - rx), S(cy - ry), S(cx + rx), S(cy + ry)],
                                     outline=mix(CREAM, accent, 0.45), width=max(1, int(S(3.0))))
        if p > 0.12 + i * 0.16:
            a = t * (1.5 - i * 0.28) + i * 2.1
            px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
            rr = (0.055 - i * 0.008) * s * eob(seg(p, 0.12 + i * 0.16, 0.4 + i * 0.16))
            circ(base, px, py, max(0.5, rr), mix(accent, INK, 0.1 + 0.2 * i))
    # gelombang scan
    for i in range(2):
        q = seg(p, 0.3 + i * 0.3, 1.0 + i * 0.3)
        if 0 < q < 1:
            rr = 0.30 * s + 0.45 * s * q
            ImageDraw.Draw(base).ellipse([S(cx - rr), S(cy - rr * 0.62), S(cx + rr), S(cy + rr * 0.62)],
                                         outline=mix(CREAM, accent, 0.75 * (1 - q)), width=max(1, int(S(3.0))))


def ic_brain(base, cx, cy, s, accent, p, t):
    light = mix(WHITE, accent, 0.16)
    ImageDraw.Draw(base).ellipse([S(cx - 0.44 * s), S(cy - 0.31 * s), S(cx + 0.05 * s), S(cy + 0.31 * s)],
                                 fill=light, outline=accent, width=max(1, int(S(4.2))))
    ImageDraw.Draw(base).ellipse([S(cx - 0.05 * s), S(cy - 0.31 * s), S(cx + 0.44 * s), S(cy + 0.31 * s)],
                                 fill=light, outline=accent, width=max(1, int(S(4.2))))
    line(base, (cx, cy - 0.24 * s), (cx, cy + 0.24 * s), accent, 0.022 * s)
    nodes = [(-0.29, -0.15), (-0.13, 0.07), (0.07, -0.17), (0.24, 0.05), (-0.24, 0.19), (0.2, -0.06)]
    px = [(cx + dx * s, cy + dy * s) for dx, dy in nodes]
    for i in range(len(px) - 1):
        f = seg(p, 0.15 + i * 0.1, 0.4 + i * 0.1)
        if f > 0:
            a, b = px[i], px[i + 1]
            m = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            line(base, a, m, mix(WHITE, accent, 0.5), 0.016 * s)
    for i, (x, y) in enumerate(px):
        f = seg(p, 0.12 + i * 0.11, 0.34 + i * 0.11)
        if f > 0:
            pulse = 1 + 0.22 * math.sin(t * 4.5 + i)
            circ(base, x, y, 0.048 * s * eob(f) * pulse, mix(accent, INK, 0.12))


def ic_asteroid(base, cx, cy, s, accent, p, t):
    d = ImageDraw.Draw(base)
    n = 10
    base_r = 0.125 * s
    mult = [1.0, 0.82, 1.12, 0.9, 1.18, 0.86, 1.05, 0.92, 1.14, 0.88]
    ang0 = t * 0.9 + p * 0.6
    pts = []
    for i in range(n):
        a = ang0 + i * 2 * math.pi / n
        r = base_r * mult[i] * eob(p)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon([(S(x), S(y)) for x, y in pts], fill=mix(accent, WHITE, 0.45),
              outline=mix(accent, INK, 0.12), width=max(1, int(S(5))))
    for i, (dx, dy, rr) in enumerate([(-0.055, -0.045, 0.032), (0.062, 0.035, 0.026), (-0.012, 0.075, 0.02)]):
        if p > 0.4 + i * 0.12:
            circ(base, cx + dx * s, cy + dy * s, rr * s, mix(accent, INK, 0.22))
    # jejak gerak (koma kecil)
    for i in range(4):
        f = seg(p, 0.25 + i * 0.06, 0.5 + i * 0.06)
        if f > 0:
            circ(base, cx - 0.30 * s - i * 0.075 * s, cy + 0.26 * s + i * 0.055 * s, (0.030 - i * 0.005) * s * f,
                 mix(CREAM, accent, 0.35))
    # kilau
    for i, (dx, dy, ph) in enumerate([(0.46, -0.42, 0.4), (-0.42, -0.36, 1.9)]):
        q = abs(math.sin(t * 2.4 + ph))
        star4(d, cx + dx * s, cy + dy * s, 0.09 * s * q, mix(CREAM, accent, 0.7))


# ---------- ikon baru: penipuan AI ----------
def ic_wave(base, cx, cy, s, accent, p, t):
    """Gelombang suara beranimasi -> kloning suara."""
    d = ImageDraw.Draw(base)
    n = 7
    for i in range(n):
        x = cx + (i - (n - 1) / 2) * 0.125 * s
        a = (0.12 + 0.34 * abs(math.sin(t * 3.1 + i * 1.05))) * eob(seg(p, 0.1 + i * 0.07, 0.5 + i * 0.07))
        h = max(0.02, 0.46 * s * a)
        tone = mix(accent, WHITE, 0.10 + 0.45 * ((i * 2) % 3) / 2)
        d.rounded_rectangle([S(x - 0.035 * s), S(cy - h), S(x + 0.035 * s), S(cy + h)],
                            radius=S(0.035 * s), fill=tone)
    for i, ph in enumerate([0.2, 1.4, 2.6]):
        q = seg(p, 0.45 + i * 0.12, 0.85 + i * 0.12)
        if q > 0:
            star4(d, cx + (-0.46 + i * 0.46) * s, cy - 0.44 * s, 0.085 * s * q, mix(CREAM, accent, 0.72))


def ic_money(base, cx, cy, s, accent, p, t):
    """Uang kertas + panah turun -> kerugian."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    x0, y0, x1, y1 = cx - 0.52 * s, cy - 0.33 * s, cx + 0.16 * s, cy + 0.19 * s
    d.rounded_rectangle([S(x0), S(y0), S(x0 + (x1 - x0) * k), S(y1)], radius=S(0.05 * s),
                        fill=mix(WHITE, accent, 0.16), outline=accent, width=max(1, int(S(3.4))))
    if k > 0.9:
        d.ellipse([S(cx - 0.34 * s), S(cy - 0.15 * s), S(cx - 0.02 * s), S(cy + 0.02 * s)],
                  outline=accent, width=max(1, int(S(4))))
        d.line([S(cx - 0.48 * s), S(cy - 0.25 * s), S(cx - 0.48 * s), S(cy + 0.08 * s)],
               fill=mix(CREAM, accent, 0.4), width=max(1, int(S(3.4))))
        d.line([S(cx + 0.12 * s), S(cy - 0.25 * s), S(cx + 0.12 * s), S(cy + 0.08 * s)],
               fill=mix(CREAM, accent, 0.4), width=max(1, int(S(3.4))))
    q = seg(p, 0.35, 0.95)
    if q > 0:
        ink = mix(accent, INK, 0.15)
        ax, ay = cx + 0.46 * s, cy - 0.38 * s
        ln = 0.70 * s * eo(q)
        d.line([S(ax), S(ay), S(ax), S(ay + ln)], fill=ink, width=max(1, int(S(10))))
        d.polygon([(S(ax), S(ay + ln + 0.16 * s)), (S(ax - 0.11 * s), S(ay + ln - 0.04 * s)),
                   (S(ax + 0.11 * s), S(ay + ln - 0.04 * s))], fill=ink)
    for i, (dx, ph) in enumerate([(-0.54, 0.6), (-0.06, 1.8), (-0.30, 3.0)]):
        f = seg(p, 0.5 + i * 0.1, 1.05 + i * 0.1)
        if f > 0:
            circ(base, cx + dx * s, cy + 0.30 * s + 0.24 * s * f, 0.055 * s * (1 - 0.45 * f),
                 mix(accent, WHITE, 0.45))


def ic_key(base, cx, cy, s, accent, p, t):
    """Kunci -> kata sandi keluarga."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    r = 0.19 * s * k
    hx, hy = cx - 0.30 * s, cy
    d.ellipse([S(hx - r), S(hy - r), S(hx + r), S(hy + r)], outline=accent, width=max(1, int(S(8))),
              fill=mix(WHITE, accent, 0.14))
    x_start = hx + r
    x_end = x_start + (cx + 0.46 * s - x_start) * k
    d.line([S(x_start), S(hy), S(x_end), S(hy)], fill=accent, width=max(1, int(S(8))))
    if k > 0.85:
        for tx in (0.22, 0.36):
            d.line([S(cx + tx * s), S(hy), S(cx + tx * s), S(hy + 0.15 * s)], fill=accent,
                   width=max(1, int(S(8))))
    q = seg(p, 0.5, 0.95)
    if q > 0:
        star4(d, cx + 0.40 * s, cy - 0.34 * s, 0.10 * s * q, mix(CREAM, accent, 0.7))


def ic_phone(base, cx, cy, s, accent, p, t):
    """Telepon berbunyi + gelombang panggilan."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    pw, ph_ = 0.30 * s * k, 0.52 * s * k
    d.rounded_rectangle([S(cx - pw), S(cy - ph_), S(cx + pw), S(cy + ph_)], radius=S(0.10 * s),
                        fill=WHITE, outline=accent, width=max(1, int(S(5))))
    for i in range(4):
        amp = (0.05 + 0.06 * abs(math.sin(t * 3.4 + i * 1.3))) * s
        x = cx - 0.13 * s + i * 0.088 * s
        d.rounded_rectangle([S(x - 0.02 * s), S(cy - amp), S(x + 0.02 * s), S(cy + amp)],
                            radius=S(0.02 * s), fill=mix(accent, WHITE, 0.25))
    for i in range(3):
        q = seg(p, 0.3 + i * 0.14, 0.75 + i * 0.14)
        if q > 0:
            r = 0.40 * s + (0.30 * s) * q
            ImageDraw.Draw(base).arc([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], start=-58, end=58,
                                     fill=mix(accent, INK, 0.05 + 0.1 * i),
                                     width=max(1, int(S(5)))) 
            ImageDraw.Draw(base).arc([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], start=122, end=238,
                                     fill=mix(accent, INK, 0.05 + 0.1 * i),
                                     width=max(1, int(S(5))))


def ic_calendar(base, cx, cy, s, accent, p, t, text="26"):
    """Kalender + tanggal + cincin pengingat."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    w_, h_ = 0.40 * s, 0.38 * s
    x0, y0 = cx - w_, cy - h_
    d.rounded_rectangle([S(x0), S(y0), S(x0 + 2 * w_ * k), S(y0 + 2 * h_)], radius=S(0.06 * s),
                        fill=WHITE, outline=accent, width=max(1, int(S(4.5))))
    if k > 0.85:
        d.rounded_rectangle([S(x0), S(y0), S(x0 + 2 * w_), S(y0 + 0.12 * s)], radius=S(0.055 * s),
                            fill=mix(accent, WHITE, 0.15))
        fsz = fit_size(FB, text, 0.30 * s, (2 * w_ - 0.14 * s) * SS)
        paste_c(base, cx, cy + 0.10 * s, text, font(FB, fsz), mix(accent, INK, 0.15), 1.0)
        for dx in (-0.16, 0.16):
            d.line([S(cx + dx * s), S(y0 - 0.055 * s), S(cx + dx * s), S(y0 + 0.035 * s)],
                   fill=accent, width=max(1, int(S(8))))
    q = seg(p, 0.45, 1.0)
    if q > 0:
        rr = (0.52 + 0.30 * q) * s
        d.ellipse([S(cx - rr), S(cy - rr), S(cx + rr), S(cy + rr)],
                  outline=mix(CREAM, accent, 0.6 * (1 - q)), width=max(1, int(S(4))))


def ic_clock(base, cx, cy, s, accent, p, t):
    """Jam: jarum bergerak cepat -> jeda antar terbit yang pendek."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    r = 0.40 * s * k
    d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], fill=mix(WHITE, accent, 0.12),
              outline=accent, width=max(1, int(S(5))))
    for i in range(12):
        a = i * math.pi / 6
        d.line([S(cx + (r - 0.075 * s) * math.sin(a)), S(cy - (r - 0.075 * s) * math.cos(a)),
                S(cx + (r - 0.020 * s) * math.sin(a)), S(cy - (r - 0.020 * s) * math.cos(a))],
               fill=mix(CREAM, accent, 0.4), width=max(1, int(S(3))))
    ha = t * 1.5
    d.line([S(cx), S(cy), S(cx + 0.22 * s * math.sin(ha)), S(cy - 0.22 * s * math.cos(ha))],
           fill=mix(accent, INK, 0.1), width=max(1, int(S(7))))
    d.line([S(cx), S(cy), S(cx + 0.33 * s * math.sin(t * 0.35)), S(cy - 0.33 * s * math.cos(t * 0.35))],
           fill=accent, width=max(1, int(S(5))))
    circ(base, cx, cy, 0.04 * s, mix(accent, INK, 0.2))
    for i in range(2):
        q = seg(p, 0.4 + i * 0.22, 0.85 + i * 0.22)
        if q > 0:
            star4(d, cx + (-0.52 + i * 1.04) * s, cy - 0.44 * s, 0.09 * s * q, mix(CREAM, accent, 0.7))


def ic_padi(base, cx, cy, s, accent, p, t):
    """Setangkai padi/tanaman panen, tumbuh dari bawah."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    top = (cx + 0.06 * s, cy - 0.42 * s * k)
    bot = (cx - 0.10 * s, cy + 0.44 * s)
    pts = [(cx - 0.10 * s + (top[0] - (cx - 0.10 * s)) * u / 10,
            cy + 0.44 * s + (top[1] - (cy + 0.44 * s)) * u / 10) for u in range(11)]
    if k > 0.25:
        nline = max(2, int(len(pts) * eo(seg(p, 0, 0.9))))
        d.line([(S(pts[i][0]), S(pts[i][1])) for i in range(nline)],
               fill=mix(accent, INK, 0.25), width=max(1, int(S(7))))
        for i in range(1, 8):
            q = seg(p, 0.25 + i * 0.075, 0.55 + i * 0.075)
            if q <= 0:
                continue
            bx, by = pts[i]
            for sgn in (-1, 1):
                ex, ey = bx + sgn * 0.11 * s * q, by - 0.05 * s * q
                d.line([S(bx), S(by), S(ex), S(ey)], fill=mix(accent, INK, 0.30), width=max(1, int(S(4.5))))
                d.ellipse([S(ex - 0.055 * s), S(ey - 0.10 * s), S(ex + 0.055 * s), S(ey + 0.02 * s)],
                          fill=mix(accent, WHITE, 0.25) if sgn < 0 else accent)
    q = seg(p, 0.6, 1.1)
    if q > 0:
        for i in range(3):
            star4(d, cx + (0.30 + i * 0.16) * s, cy - 0.30 * s + i * 0.16 * s, 0.075 * s * q * (0.6 + 0.4 * math.sin(t * 2 + i)),
                  mix(CREAM, accent, 0.7))


def ic_moonrise(base, cx, cy, s, accent, p, t):
    """Bulan terbit di ujung garis horizon."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    r = 0.26 * s * k
    mx = cx + 0.10 * s
    my = cy - 0.10 * s - (0.26 * s) * (1 - eo(seg(p, 0, 1.1)))
    for i in range(3):
        rr = r * (1.25 + i * 0.32)
        d.ellipse([S(mx - rr), S(my - rr), S(mx + rr), S(my + rr)],
                  fill=mix(CREAM, accent, 0.06 + 0.04 * (2 - i)))
    d.ellipse([S(mx - r), S(my - r), S(mx + r), S(my + r)], fill=mix(WHITE, accent, 0.30),
              outline=mix(accent, INK, 0.05), width=max(1, int(S(3.4))))
    for (dx, dy, rr) in [(-0.09, -0.07, 0.055), (0.10, 0.02, 0.04), (-0.02, 0.13, 0.032)]:
        if k > 0.6:
            circ(base, mx + dx * s, my + dy * s, rr * s, mix(mix(WHITE, accent, 0.30), accent, 0.35))
    hy = cy + 0.42 * s
    d.line([S(cx - 0.46 * s), S(hy), S(cx + 0.46 * s), S(hy)], fill=mix(accent, INK, 0.15),
           width=max(1, int(S(6))))
    q = seg(p, 0.3, 0.95)
    if q > 0:
        ax, ay = cx - 0.34 * s, cy + 0.28 * s
        ln = 0.34 * s * eo(q)
        d.line([S(ax), S(ay + ln), S(ax), S(ay)], fill=mix(accent, INK, 0.2), width=max(1, int(S(7))))
        d.polygon([(S(ax), S(ay - 0.10 * s)), (S(ax - 0.09 * s), S(ay + 0.05 * s)), (S(ax + 0.09 * s), S(ay + 0.05 * s))],
                  fill=mix(accent, INK, 0.2))



def ic_shadow(base, cx, cy, s, accent, p, t):
    """Tongkat + bayangan yang menyusut sampai hilang (inti hari tanpa bayangan)."""
    d = ImageDraw.Draw(base)
    gy = cy + 0.34 * s
    d.line([S(cx - 0.50 * s), S(gy), S(cx + 0.50 * s), S(gy)], fill=mix(CREAM, INK, 0.16),
           width=max(1, int(S(5))))
    d.line([S(cx), S(gy), S(cx), S(cy - 0.34 * s)], fill=mix(accent, INK, 0.18), width=max(1, int(S(8))))
    circ(base, cx, gy - 0.46 * s + 0.46 * s, 0.001, mix(accent, WHITE, 0.2))
    # matahari tepat di atas tongkat
    sr = 0.085 * s
    circ(base, cx, cy - 0.50 * s, sr, mix(accent, WHITE, 0.20))
    for i in range(8):
        a = i * math.pi / 4 + t * 0.5
        r1, r2 = sr * 1.35, sr * 1.85
        d.line([S(cx + r1 * math.cos(a)), S(cy - 0.50 * s + r1 * math.sin(a)),
                S(cx + r2 * math.cos(a)), S(cy - 0.50 * s + r2 * math.sin(a))],
               fill=mix(accent, WHITE, 0.35), width=max(1, int(S(3))))
    # bayangan menyusut -> hilang -> kembali
    ph = (math.sin(t * 1.15 - math.pi / 2) + 1) / 2
    ln = (0.05 + 0.44 * ph) * s * eob(p)
    d.line([S(cx), S(gy), S(cx + ln), S(gy)], fill=mix(accent, INK, 0.46), width=max(1, int(S(8))))
    if ln < 0.11 * s:
        for i in range(3):
            star4(d, cx + (0.20 + i * 0.14) * s, gy - (0.18 + i * 0.10) * s,
                  0.085 * s * abs(math.sin(t * 3 + i)), mix(CREAM, accent, 0.8))


def ic_sun(base, cx, cy, s, accent, p, t):
    """Matahari + kepala pengamat tepat di bawahnya (titik zenit)."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    scy = cy - 0.16 * s
    r = 0.21 * s * k
    circ(base, cx, scy, r, mix(accent, WHITE, 0.28))
    for i in range(12):
        a = i * math.pi / 6 + t * 0.3
        r1, r2 = r * 1.18, r * 1.48
        d.line([S(cx + r1 * math.cos(a)), S(scy + r1 * math.sin(a)),
                S(cx + r2 * math.cos(a)), S(scy + r2 * math.sin(a))],
               fill=mix(accent, INK, 0.06), width=max(1, int(S(3.6))))
    # garis zenith ke kepala
    hy = cy + 0.30 * s
    dash = 0.055 * s
    y = scy + r * 1.5
    while y < hy - 0.14 * s:
        d.line([S(cx), S(y), S(cx), S(min(y + dash, hy - 0.14 * s))], fill=mix(CREAM, accent, 0.55),
               width=max(1, int(S(3))))
        y += dash * 2
    hr = 0.075 * s
    circ(base, cx, hy, hr, mix(WHITE, accent, 0.18))
    d.ellipse([S(cx - hr), S(hy - hr), S(cx + hr), S(hy + hr)], outline=accent, width=max(1, int(S(4))))
    d.arc([S(cx - hr * 1.5), S(hy - hr * 0.2), S(cx + hr * 1.5), S(hy + hr * 2.1)], start=200, end=340,
          fill=accent, width=max(1, int(S(4))))


def ic_warning(base, cx, cy, s, accent, p, t):
    """Segitiga peringatan + matahari kecil dicoret (jangan tatap Matahari)."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    w_, h_ = 0.46 * s * k, 0.40 * s * k
    pts = [(cx, cy - h_), (cx + w_, cy + h_ * 0.85), (cx - w_, cy + h_ * 0.85)]
    d.polygon([(S(x), S(y)) for x, y in pts], fill=mix(WHITE, accent, 0.15), outline=accent,
              width=max(1, int(S(6))))
    pulse = 1 + 0.05 * math.sin(t * 4.2)
    d.line([S(cx), S(cy - 0.12 * s), S(cx), S(cy + 0.13 * s)], fill=mix(accent, INK, 0.12),
           width=max(1, int(S(9) * pulse)))
    circ(base, cx, cy + 0.26 * s, 0.035 * s, mix(accent, INK, 0.12))
    sx, sy = cx + 0.42 * s, cy - 0.34 * s
    circ(base, sx, sy, 0.075 * s, mix(accent, WHITE, 0.30))
    d.line([S(sx - 0.11 * s), S(sy + 0.11 * s), S(sx + 0.11 * s), S(sy - 0.11 * s)],
           fill=mix(accent, INK, 0.30), width=max(1, int(S(4.5))))



def ic_comet(base, cx, cy, s, accent, p, t):
    """Komet: kepala terang + ekor debu memanjang (Komet Halley)."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    hx = cx + 0.30 * s
    hy = cy - 0.20 * s
    ang = math.radians(-152 + math.sin(t * 0.6) * 3)
    tl = (0.86 * s) * k
    # ekor: beberapa lapis semakin tipis
    for i, (wfac, alpha) in enumerate([(1.0, 0.18), (0.62, 0.34), (0.30, 0.55)]):
        tipx = hx + math.cos(ang) * tl
        tipy = hy + math.sin(ang) * tl
        perp = ang + math.pi / 2
        wdt = 0.20 * s * wfac
        d.polygon([(S(hx), S(hy)),
                   (S(tipx + math.cos(perp) * wdt), S(tipy + math.sin(perp) * wdt)),
                   (S(tipx - math.cos(perp) * wdt), S(tipy - math.sin(perp) * wdt))],
                  fill=mix(accent, WHITE, 0.72 - i * 0.18))
    hr = 0.115 * s * k
    circ(base, hx, hy, hr * 1.9, mix(CREAM, accent, 0.16))
    circ(base, hx, hy, hr, mix(accent, WHITE, 0.35))
    circ(base, hx - hr * 0.3, hy - hr * 0.3, hr * 0.42, mix(WHITE, accent, 0.05))
    # debu berkilau di sepanjang ekor
    for i in range(6):
        off = (i + 1) / 7.0
        q = seg(p, 0.35 + i * 0.07, 0.7 + i * 0.07)
        if q > 0:
            px = hx + math.cos(ang) * tl * off
            py = hy + math.sin(ang) * tl * off
            star4(d, px, py, (0.075 - i * 0.008) * s * q * (0.5 + 0.5 * abs(math.sin(t * 3 + i))),
                  mix(CREAM, accent, 0.75))


def ic_orion(base, cx, cy, s, accent, p, t):
    """Pola rasi Orion: sabuk tiga bintang + anggota badan."""
    d = ImageDraw.Draw(base)
    pts = {
        "kepala": (0.02, -0.44), "bahu_k": (-0.24, -0.28), "bahu_d": (0.22, -0.24),
        "sabuk1": (-0.07, -0.02), "sabuk2": (0.04, 0.00), "sabuk3": (0.14, 0.02),
        "kaki_k": (-0.20, 0.32), "kaki_d": (0.17, 0.34),
    }
    P = {n: (cx + dx * s, cy + dy * s) for n, (dx, dy) in pts.items()}
    edges = [("kepala", "bahu_k"), ("kepala", "bahu_d"), ("bahu_k", "sabuk1"), ("bahu_d", "sabuk3"),
             ("sabuk1", "sabuk2"), ("sabuk2", "sabuk3"), ("sabuk1", "kaki_k"), ("sabuk3", "kaki_d")]
    for i, (a, b) in enumerate(edges):
        q = seg(p, 0.10 + i * 0.06, 0.45 + i * 0.06)
        if q <= 0:
            continue
        p1, p2 = P[a], P[b]
        m = (p1[0] + (p2[0] - p1[0]) * q, p1[1] + (p2[1] - p1[1]) * q)
        line(base, p1, m, mix(CREAM, accent, 0.42), 0.014 * s)
    order = ["kepala", "bahu_k", "bahu_d", "kaki_k", "kaki_d", "sabuk1", "sabuk2", "sabuk3"]
    for i, n in enumerate(order):
        q = seg(p, 0.16 + i * 0.075, 0.42 + i * 0.075)
        if q <= 0:
            continue
        r = (0.052 if n.startswith("sabuk") else 0.044) * s * eob(q)
        tw = 0.82 + 0.18 * math.sin(t * 2.4 + i * 1.3)
        col = mix(accent, INK, 0.10) if n.startswith("sabuk") else mix(accent, WHITE, 0.35)
        if n == "bahu_k":
            col = mix((200, 90, 60), accent, 0.25)
        circ(base, P[n][0], P[n][1], r * tw, col)
    if p > 0.72:
        for i in range(2):
            star4(d, cx + (-0.44 + i * 0.88) * s, cy - 0.34 * s,
                  0.075 * s * abs(math.sin(t * 2 + i)), mix(CREAM, accent, 0.7))


def ic_moonset(base, cx, cy, s, accent, p, t):
    """Bulan terbenam di ufuk -> jendela gelap menjelang fajar."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    hy = cy + 0.36 * s
    my = cy - 0.24 * s + (0.44 * s) * eo(seg(p, 0.1, 1.5))
    r = 0.235 * s * k
    for i in range(3):
        rr = r * (1.22 + i * 0.26)
        d.ellipse([S(cx + 0.10 * s - rr), S(my - rr), S(cx + 0.10 * s + rr), S(my + rr)],
                  fill=mix(CREAM, accent, 0.05 + 0.035 * (2 - i)))
    d.ellipse([S(cx + 0.10 * s - r), S(my - r), S(cx + 0.10 * s + r), S(my + r)],
              fill=mix(WHITE, accent, 0.28), outline=mix(accent, INK, 0.06), width=max(1, int(S(3.4))))
    for (dx, dy, rr) in [(-0.08, -0.06, 0.05), (0.09, 0.03, 0.038), (-0.01, 0.12, 0.03)]:
        if k > 0.6:
            circ(base, cx + 0.10 * s + dx * s, my + dy * s, rr * s,
                 mix(mix(WHITE, accent, 0.28), accent, 0.32))
    d.line([S(cx - 0.46 * s), S(hy), S(cx + 0.46 * s), S(hy)], fill=mix(accent, INK, 0.16),
           width=max(1, int(S(6))))
    q = seg(p, 0.25, 0.9)
    if q > 0:
        ax, ay = cx - 0.34 * s, hy - 0.30 * s
        ln = 0.30 * s * eo(q)
        d.line([S(ax), S(ay), S(ax), S(ay + ln)], fill=mix(accent, INK, 0.22), width=max(1, int(S(7))))
        d.polygon([(S(ax), S(ay + ln + 0.12 * s)), (S(ax - 0.09 * s), S(ay + ln - 0.04 * s)),
                   (S(ax + 0.09 * s), S(ay + ln - 0.04 * s))], fill=mix(accent, INK, 0.22))
    for i in range(3):
        star4(d, cx + (-0.40 + i * 0.34) * s, cy - 0.44 * s,
              0.07 * s * abs(math.sin(t * 2.2 + i * 1.1)) * eo(seg(p, 0.5, 1.0)),
              mix(CREAM, accent, 0.7))



def ic_subduct(base, cx, cy, s, accent, p, t):
    """Lempeng samudra menunjam ke bawah lempeng benua + titik gempa dalam."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    # lempeng atas (benua)
    y0 = cy - 0.10 * s
    d.rounded_rectangle([S(cx - 0.52 * s), S(y0 - 0.20 * s), S(cx + 0.52 * s), S(y0 + 0.04 * s)],
                        radius=S(0.05 * s), fill=mix(WHITE, accent, 0.18), outline=accent,
                        width=max(1, int(S(4))))
    # lempeng samudra menyusup lalu menukik
    drop = 0.30 * s * eo(seg(p, 0.15, 1.2))
    pts = [(cx - 0.52 * s, y0 + 0.10 * s), (cx - 0.05 * s, y0 + 0.10 * s + drop * 0.15),
           (cx + 0.30 * s, y0 + 0.10 * s + drop * 0.55), (cx + 0.46 * s, y0 + 0.10 * s + drop)]
    d.line([(S(x), S(y)) for x, y in pts], fill=mix(accent, INK, 0.10), width=max(1, int(S(12))),
           joint="curve")
    for i in range(3):
        q = seg(p, 0.4 + i * 0.16, 0.8 + i * 0.16)
        if q > 0:
            rx = cx + (0.02 + i * 0.16) * s
            ry = y0 + 0.14 * s + (0.18 + i * 0.20) * s * k
            rr = (0.045 + i * 0.008) * s * q * (0.7 + 0.3 * math.sin(t * 3 + i))
            circ(base, rx, ry, rr, mix(accent, INK, 0.15))
    # panah gerak
    ax, ay = cx - 0.30 * s, y0 - 0.34 * s
    ln = 0.26 * s * eo(seg(p, 0.1, 0.8))
    if ln > 0:
        d.line([S(ax), S(ay), S(ax + ln), S(ay)], fill=mix(accent, INK, 0.25), width=max(1, int(S(9))))
        d.polygon([(S(ax + ln + 0.12 * s), S(ay)), (S(ax + ln), S(ay - 0.09 * s)), (S(ax + ln), S(ay + 0.09 * s))],
                  fill=mix(accent, INK, 0.25))


def ic_shield(base, cx, cy, s, accent, p, t):
    """Perisai + centang: aman dari tsunami."""
    d = ImageDraw.Draw(base)
    k = eob(p)
    w_ = 0.34 * s * k
    top = cy - 0.42 * s
    bot = cy + 0.44 * s
    pts = [(cx - w_, top), (cx + w_, top), (cx + w_, cy + 0.06 * s),
           (cx, bot), (cx - w_, cy + 0.06 * s)]
    d.polygon([(S(x), S(y)) for x, y in pts], fill=mix(WHITE, accent, 0.16), outline=accent,
              width=max(1, int(S(6))))
    q = seg(p, 0.35, 0.85)
    if q > 0:
        u = eo(q)
        p1 = (cx - 0.16 * s, cy - 0.02 * s)
        p2 = (cx - 0.03 * s, cy + 0.14 * s)
        p3 = (cx + 0.17 * s, cy - 0.20 * s)
        if u < 0.5:
            m = (p1[0] + (p2[0] - p1[0]) * (u / 0.5), p1[1] + (p2[1] - p1[1]) * (u / 0.5))
            d.line([S(p1[0]), S(p1[1]), S(m[0]), S(m[1])], fill=accent, width=max(1, int(S(11))))
        else:
            m = (p2[0] + (p3[0] - p2[0]) * ((u - 0.5) / 0.5), p2[1] + (p3[1] - p2[1]) * ((u - 0.5) / 0.5))
            d.line([S(p1[0]), S(p1[1]), S(p2[0]), S(p2[1])], fill=accent, width=max(1, int(S(11))))
            d.line([S(p2[0]), S(p2[1]), S(m[0]), S(m[1])], fill=accent, width=max(1, int(S(11))))
    if p > 0.8:
        star4(d, cx + 0.46 * s, cy - 0.36 * s, 0.09 * s * abs(math.sin(t * 2.4)), mix(CREAM, accent, 0.7))


ICONS = {"molecule": ic_molecule, "sugar": ic_sugar, "orbit": ic_orbit, "brain": ic_brain, "asteroid": ic_asteroid,
         "wave": ic_wave, "money": ic_money, "key": ic_key, "phone": ic_phone,
         "calendar": ic_calendar, "clock": ic_clock, "padi": ic_padi, "moonrise": ic_moonrise,
         "shadow": ic_shadow, "sun": ic_sun, "warning": ic_warning,
         "comet": ic_comet, "orion": ic_orion, "moonset": ic_moonset,
         "subduct": ic_subduct, "shield": ic_shield}




# ---------- upgrade mesin: teks kaya, angka bergerak, tata letak baru ----------
import re as _re

LAYOUT_LOG = {}


def split_hl(text, hl):
    """Pecah teks jadi segmen (teks, apakah_disorot) berdasarkan frasa hl."""
    if not hl:
        return [(text, False)]
    low, hlow = text.lower(), hl.lower()
    i = low.find(hlow)
    if i < 0:
        return [(text, False)]
    out = []
    if i > 0:
        out.append((text[:i], False))
    out.append((text[i:i + len(hl)], True))
    rest = text[i + len(hl):]
    if rest:
        out.append((rest, False))
    return out


def paste_tl_rich(base, x, y, text, f, base_col, hl_col, hl, alpha=1.0):
    """Gambar teks dengan satu frasa disorot warna aksen."""
    cx = x
    for seg_text, is_hl in split_hl(text, hl):
        col = hl_col if is_hl else base_col
        lay = tlayer(seg_text, f, col, alpha)
        if lay is not None:
            base.paste(lay, (int(S(cx)), int(S(y))), lay)
        cx += tw(seg_text, f)


def stat_parts(stat):
    """Pisah '368 KM' -> ('368', 'KM')."""
    m = _re.match(r"^\s*([\d][\d.,]*)\s*(.*)$", stat or "")
    if not m:
        return None, stat or ""
    return m.group(1), m.group(2).strip()


def count_str(num_str, prog):
    """Angka bergerak 0 -> nilai, mempertahankan gaya pemisah Indonesia."""
    try:
        if "," in num_str:
            whole, dec = num_str.split(",", 1)
            val = float(whole.replace(".", "") + "." + dec)
            cur = val * prog
            out = f"{cur:.{len(dec)}f}".replace(".", ",")
            if "." in whole:
                w = out.split(",")[0]
                out = f"{int(w):,}".replace(",", ".") + "," + out.split(",")[1]
            return out
        if "." in num_str:
            val = int(num_str.replace(".", ""))
            return f"{int(round(val * prog)):,}".replace(",", ".")
        return str(int(round(int(num_str) * prog)))
    except Exception:
        return num_str


# ---------- latar ----------
BLOBS = [(0.16, 0.20, 430, 0.0), (0.88, 0.52, 360, 1.9), (0.28, 0.86, 320, 3.4)]


BG_MOON = False
BG_SUN = False
BG_METEOR = False


def draw_meteor_bg(d, tg, accent):
    """Bintang berkelip + meteor melintas berkala."""
    for i in range(52):
        x = ((i * 137.508) % 1.0) * W
        y = ((i * 61.803) % 1.0) * H
        if y > 0.72 * H:
            continue
        size = 2.0 + ((i * 7) % 4) * 1.1
        tw = 0.22 + 0.55 * abs(math.sin(tg * (0.5 + (i % 5) * 0.22) + i))
        d.ellipse([S(x - size), S(y - size), S(x + size), S(y + size)],
                  fill=mix(CREAM, INK, 0.10 + 0.22 * tw))
    for i in range(6):
        x = ((i * 211.7) % 1.0) * W
        y = (0.06 + ((i * 97.3) % 1.0) * 0.34) * H
        tw = abs(math.sin(tg * 1.7 + i * 2.1))
        if tw > 0.35:
            star4(d, x, y, (10 + 8 * tw), mix(CREAM, accent, 0.55))
    period = 2.4
    for k in range(2):
        q = ((tg / period) + k * 0.5) % 1.0
        if 0.02 < q < 0.46:
            u = (q - 0.02) / 0.44
            x0 = (0.14 + k * 0.44) * W
            y0 = (0.10 + k * 0.14) * H
            ang = math.radians(33)
            L = 0.30 * W * eo(u)
            hx, hy = x0 + math.cos(ang) * L, y0 + math.sin(ang) * L
            tlx, tly = hx - math.cos(ang) * 0.11 * W, hy - math.sin(ang) * 0.11 * W
            a = math.sin(math.pi * u)
            d.line([S(tlx), S(tly), S(hx), S(hy)], fill=mix(CREAM, accent, 0.42 * a + 0.12),
                   width=max(1, int(S(4))))
            d.ellipse([S(hx - 6), S(hy - 6), S(hx + 6), S(hy + 6)], fill=mix(CREAM, accent, 0.85 * a + 0.1))


def draw_bg(img, d, tg, accent):
    if BG_METEOR:
        draw_meteor_bg(d, tg, accent)
    if BG_SUN:
        sx = 0.76 * W + math.sin(tg * 0.10) * 24
        sy = 0.215 * H + math.cos(tg * 0.12) * 18
        for i in range(3):
            rr = 240 * (1 + i * 0.20)
            d.ellipse([S(sx - rr), S(sy - rr), S(sx + rr), S(sy + rr)],
                      fill=mix(CREAM, accent, 0.030 + 0.020 * (2 - i)))
        d.ellipse([S(sx - 132), S(sy - 132), S(sx + 132), S(sy + 132)], fill=mix(CREAM, accent, 0.16))
        for i in range(16):
            a = i * math.pi / 8 + tg * 0.05
            r1, r2 = 150, 176 + 10 * math.sin(tg * 0.7 + i)
            d.line([S(sx + r1 * math.cos(a)), S(sy + r1 * math.sin(a)),
                    S(sx + r2 * math.cos(a)), S(sy + r2 * math.sin(a))],
                   fill=mix(CREAM, accent, 0.30), width=max(1, int(S(3))))
    if BG_MOON:
        mx = 0.74 * W + math.sin(tg * 0.10) * 26
        my = 0.235 * H + math.cos(tg * 0.13) * 20
        for i in range(3):
            rr = 210 * (1 + i * 0.22)
            d.ellipse([S(mx - rr), S(my - rr), S(mx + rr), S(my + rr)],
                      fill=mix(CREAM, accent, 0.030 + 0.022 * (2 - i)))
        d.ellipse([S(mx - 150), S(my - 150), S(mx + 150), S(my + 150)], fill=mix(CREAM, WHITE, 0.55))
        for (dx, dy, rr) in [(-52, -40, 30), (58, 12, 22), (-12, 74, 17), (34, -66, 13)]:
            d.ellipse([S(mx + dx - rr), S(my + dy - rr), S(mx + dx + rr), S(my + dy + rr)],
                      fill=mix(CREAM, accent, 0.10))
    for bx, by, br, ph in BLOBS:
        x = bx * W + math.sin(tg * 0.21 + ph) * 60
        y = by * H + math.cos(tg * 0.17 + ph) * 70
        d.ellipse([S(x - br), S(y - br), S(x + br), S(y + br)], fill=mix(CREAM, accent, 0.055))
    step = 94
    og = (tg * 7.0) % step
    dot = mix(CREAM, INK, 0.075)
    for j in range(-1, int(H / step) + 2):
        y = j * step + og
        for i in range(0, int(W / step) + 2):
            x = i * step + (step / 2 if j % 2 else 0)
            if x < W + 10:
                d.ellipse([S(x - 3.2), S(y - 3.2), S(x + 3.2), S(y + 3.2)], fill=dot)


def draw_header(img, d, sc, total, tg, accent, meta):
    # brand channel, selalu terlihat (zona aman: kiri atas)
    paste_l(img, 66, 92, meta.get("brand", "KlikTahu"), font(FB, 37), mix(CREAM, INK, 0.78), 1.0)
    d.ellipse([S(38), S(81), S(54), S(97)], fill=accent)
    label = meta.get("header_badge", "")
    if label:
        f = font(FS, 29)
        wid = tw(label, f) + 46
        rrect(img, W - 62 - wid, 66, wid, 52, 26, fill=mix(CREAM, INK, 0.9))
        paste_c(img, W - 62 - wid / 2, 92, label, f, WHITE, 1.0)
    # progress bar
    prog = clamp(tg / total)
    d.rectangle([0, 0, S(W), S(4)], fill=TRACK)
    d.rectangle([0, 0, S(W * prog), S(4)], fill=accent)


def caption_pill(img, sc, tl, accent):
    """Pill subtitle bawah."""
    caps = sc["captions"]
    cur = None
    for c in caps:
        if tl >= c["t"] - 0.01:
            cur = c
    if cur is None:
        return
    age = tl - cur["t"]
    a = eo(seg(age, 0, 0.16))
    dy = (1 - eo(seg(age, 0, 0.2))) * 14
    f = font(FS, 45)
    lines = wrap(cur["text"], f, 840)
    lh = tlh(f) * 1.14
    wid = max(tw(l, f) for l in lines) + 76
    hgt = lh * len(lines) + 44
    cy = 1646 + dy
    rrect(img, W / 2 - wid / 2, cy - hgt / 2, wid, hgt, 34, fill=mix(CREAM, INK, 0.94), alpha=a)
    for i, l in enumerate(lines):
        paste_c(img, W / 2, cy + (i - (len(lines) - 1) / 2) * lh, l, f, WHITE, a)


# ---------- kartu fakta (cached) ----------
_CARD_CACHE = {}


def card_layer(accent):
    key = accent
    if key in _CARD_CACHE:
        return _CARD_CACHE[key]
    x0, y0, cw, ch = 68, 452, 944, 1000
    pw = int(S(cw) + 120)
    ph = int(S(ch) + 120)
    lay = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ox, oy = 60, 60
    # shadow keras (sticker style)
    d.rounded_rectangle([ox + S(10), oy + S(12), ox + S(cw) + S(10), oy + S(ch) + S(12)],
                        radius=S(58), fill=mix(CREAM, INK, 0.30) + (255,))
    d.rounded_rectangle([ox, oy, ox + S(cw), oy + S(ch)], radius=S(58), fill=WHITE + (255,),
                        outline=mix(CREAM, INK, 0.14) + (255,), width=max(1, int(S(2.5))))
    _CARD_CACHE[key] = (lay, x0 - 60, y0 - 60)
    return _CARD_CACHE[key]


def paste_card(img, accent, dx=0.0, dy=0.0, alpha=1.0):
    lay, ox, oy = card_layer(accent)
    if alpha >= 0.995:
        img.paste(lay, (int(S(ox)) + int(S(dx)), int(S(oy)) + int(S(dy))), lay)
    else:
        a = lay.getchannel("A").point(lambda v: int(v * clamp(alpha)))
        img.paste(lay.convert("RGB"), (int(S(ox)) + int(S(dx)), int(S(oy)) + int(S(dy))), a)


# ---------- scene: fact ----------
def draw_fact(img, d, sc, tl, dur, tg):
    if sc.get("visual") in diagrams.VISUALS:
        accent = hexc(sc["accent"])
        fin = seg(tl, 0, 0.5)
        fout = seg(tl, dur - 0.36, dur)
        dy = (1 - eio(fin)) * 110 - eo(fout) * 70
        al = eo(seg(tl, 0, 0.34)) * (1 - eo(seg(tl, dur - 0.36, dur - 0.02)))
        diagrams.VISUALS[sc["visual"]](img, d, sc, tl, dur, tg, accent, al, dy)
        return
    layout = sc.get("layout", "card")
    if layout != "card":
        accent = hexc(sc["accent"])
        fin = seg(tl, 0, 0.5)
        fout = seg(tl, dur - 0.36, dur)
        dy = (1 - eio(fin)) * 110 - eo(fout) * 70
        al = eo(seg(tl, 0, 0.34)) * (1 - eo(seg(tl, dur - 0.36, dur - 0.02)))
        paste_card(img, accent, dy=dy, alpha=al)
        bp = seg(tl, 0.12, 0.5)
        if bp > 0:
            circ(img, 152, 556 + dy * 0.55, 10 * eob(bp), accent)
            paste_l(img, 180, 556 + dy * 0.55, sc.get("badge", ""), font(FS, 35),
                    mix(accent, INK, 0.10), bp * al)
        if layout == "hero":
            draw_fact_hero(img, d, sc, tl, dur, tg, accent, al, dy)
        elif layout == "compare":
            draw_fact_compare(img, d, sc, tl, dur, tg, accent, al, dy)
        elif layout == "steps":
            draw_fact_steps(img, d, sc, tl, dur, tg, accent, al, dy)
        elif layout == "defs":
            draw_fact_defs(img, d, sc, tl, dur, tg, accent, al, dy)
        else:
            draw_fact_hero(img, d, sc, tl, dur, tg, accent, al, dy)
        return

    accent = hexc(sc["accent"])
    light = mix(WHITE, accent, 0.12)
    fin = seg(tl, 0, 0.5)
    fout = seg(tl, dur - 0.36, dur)
    dy = (1 - eio(fin)) * 110 - eo(fout) * 70
    al = eo(seg(tl, 0, 0.34)) * (1 - eo(seg(tl, dur - 0.36, dur - 0.02)))
    paste_card(img, accent, dy=dy, alpha=al)
    # badge label (tanpa nomor)
    bp = seg(tl, 0.12, 0.5)
    if bp > 0:
        k = eob(bp)
        circ(img, 152, 556 + dy * 0.55, 10 * k, accent)
        paste_l(img, 180, 556 + dy * 0.55, sc["badge"], font(FS, 35), mix(accent, INK, 0.10), bp * al)
    # ikon — ditempatkan di KOTAK AMAN kartu supaya tidak menembus tepi/badge
    ip = seg(tl, 0.24, 1.25)
    if ip > 0 and sc.get("icon") in ICONS:
        fn = ICONS[sc["icon"]]
        isc = 268 if sc["icon"] in ("molecule", "asteroid", "money") else 244
        if sc["icon"] in ("shadow", "sun", "warning", "comet", "orion", "moonset", "subduct", "shield"):
            isc = 262
        # kotak aman: tepi dalam kartu (x 68..1012) dikurangi margin, dan tidak
        # boleh menimpa teks badge di baris atas
        cx_kartu, cw_kartu = 68, 944
        margin = 46
        bx_akhir = 0
        if sc.get("badge"):
            bx_akhir = 180 + tw(sc["badge"], font(FS, 35)) + 26
        while isc > 170:
            icon_kiri = (cx_kartu + cw_kartu - margin) - 0.52 * isc
            if icon_kiri >= bx_akhir:
                break
            isc -= 8
        icon_x = (cx_kartu + cw_kartu - margin) - 0.52 * isc
        icon_y = 452 + margin + 0.44 * isc
        kw = {}
        if sc["icon"] == "calendar":
            kw["text"] = sc.get("icon_text", "26")
        if sc["icon"] in ("sugar", "orbit", "brain", "asteroid", "wave", "money", "key", "phone",
                          "calendar", "clock", "padi", "moonrise", "shadow", "sun", "warning",
                          "comet", "orion", "moonset", "subduct", "shield"):
            fn(img, icon_x, icon_y + dy * 0.75, isc, accent, ip, tl, **kw)
        else:
            fn(img, icon_x, icon_y + dy * 0.75, isc, accent, ip)
    # garis aksen
    bp2 = eo(seg(tl, 0.26, 0.62))
    if bp2 > 0:
        d.rounded_rectangle([S(138), S(668 + dy * 0.8), S(138 + 118 * bp2), S(678 + dy * 0.8)],
                            radius=S(5), fill=accent)
    # --- tata letak adaptif: pastikan judul + body + chip tidak bertumpuk ---
    CARD_TOP, CARD_BOT = 452, 1452          # batas kartu
    TITLE_Y = 744
    SAFE_BOT = CARD_BOT - 30                # batas aman isi kartu
    # 1) pilih ukuran judul: maksimum 2 baris
    ft, lines, tsz = None, None, None
    for tsz_try in (74, 68, 62, 56, 50):
        f_try = font(FB, tsz_try)
        l_try = wrap(sc["title"], f_try, 700)
        if len(l_try) <= 2:
            ft, lines, tsz = f_try, l_try, tsz_try
            break
    if ft is None:
        tsz = 50; ft = font(FB, tsz); lines = wrap(sc["title"], ft, 700)[:3]
    # 2) pilih ukuran body yang muat di sisa ruang (sisakan 130px untuk chip)
    y_title_end = TITLE_Y + len(lines) * tlh(ft) * 1.1
    has_chip = bool(sc.get("stat"))
    reserve = 150 if has_chip else 20
    fbd, blines = None, None
    for bsz in (38, 35, 32, 29):
        f_try = font(FM, bsz)
        l_try = wrap(sc["body"], f_try, 815)
        if y_title_end + 20 + len(l_try) * tlh(f_try) * 1.45 + reserve <= SAFE_BOT:
            fbd, blines = f_try, l_try
            break
    if fbd is None:
        fbd = font(FM, 29); blines = wrap(sc["body"], fbd, 815)
    # judul
    y = TITLE_Y
    for i, l in enumerate(lines):
        q = seg(tl, 0.32 + i * 0.12, 0.74 + i * 0.12)
        if q > 0:
            paste_tl_rich(img, 138, y + (1 - eo(q)) * 30 + dy * 0.85, l, ft, INK, accent,
                          sc.get("title_hl", ""), q * al)
        y += tlh(ft) * 1.1
    # body
    y += 20
    for i, l in enumerate(blines):
        q = seg(tl, 0.66 + i * 0.11, 1.0 + i * 0.11)
        if q > 0:
            paste_tl_rich(img, 138, y + (1 - eo(q)) * 22 + dy * 0.9, l, fbd, MUTED, accent,
                          sc.get("body_hl", ""), q * al)
        y += tlh(fbd) * 1.45
    # chip statistik: selalu di bawah baris body terakhir
    if has_chip:
        q = seg(tl, 0.86, 1.18)
        if q > 0:
            k = eob(q)
            fst = font(FB, 46)
            wid = tw(sc["stat"], fst) + 76
            cx = 138 + wid / 2
            cy = min(SAFE_BOT - 46, max(y + 52, 1225)) + dy * 0.95
            rrect(img, cx - wid / 2, cy - 46 * k, wid, 92 * k, 46, fill=light, outline=accent,
                  width=2.5, alpha=q * al)
            paste_c(img, cx, cy, sc["stat"], fst, accent, q * al, scale=0.6 + 0.4 * k)




# --- layout: hero (satu angka jadi bintang) ---
def draw_fact_hero(img, d, sc, tl, dur, tg, accent, al, dy):
    ft = font(FB, 60)
    lines = wrap(sc["title"], ft, 700)[:2]
    y = 690
    for i, l in enumerate(lines):
        q = seg(tl, 0.28 + i * 0.12, 0.66 + i * 0.12)
        if q > 0:
            paste_tl_rich(img, 138, y + (1 - eo(q)) * 26 + dy * 0.85, l, ft, INK, accent,
                          sc.get("title_hl", ""), q * al)
        y += tlh(ft) * 1.1
    num, unit = stat_parts(sc.get("stat", ""))
    if num:
        prog = eo(seg(tl, 0.5, 1.5))
        shown = count_str(num, prog)
        fh = font(FB, 150)
        sz = min(150, 150 * min(1.0, 700 / max(1.0, tw(shown + " " + unit, fh))))
        fh = font(FB, sz)
        cy = 985
        k = eob(seg(tl, 0.45, 0.95))
        paste_c(img, W / 2, cy, shown, fh, accent, eo(seg(tl, 0.45, 0.9)) * al, scale=0.85 + 0.15 * k)
        if unit:
            paste_c(img, W / 2, cy + sz * 0.72, unit, font(FS, 44), mix(accent, INK, 0.25),
                    eo(seg(tl, 0.6, 1.05)) * al)
        # garis bawah angka
        q = seg(tl, 0.7, 1.1)
        if q > 0:
            wd = 240 * eo(q)
            d.rounded_rectangle([S(W / 2 - wd / 2), S(cy + sz * 0.95), S(W / 2 + wd / 2), S(cy + sz * 0.95 + 10)],
                                radius=S(5), fill=mix(accent, INK, 0.15))
    fbd = font(FM, 36)
    bl = wrap(sc["body"], fbd, 800)[:3]
    yy = 1195
    for i, l in enumerate(bl):
        q = seg(tl, 0.95 + i * 0.11, 1.3 + i * 0.11)
        if q > 0:
            paste_tl_rich(img, 138, yy + (1 - eo(q)) * 22 + dy * 0.9, l, fbd, MUTED, accent,
                          sc.get("body_hl", ""), q * al)
        yy += tlh(fbd) * 1.42


# --- layout: banding (dua kolom) ---
def draw_fact_compare(img, d, sc, tl, dur, tg, accent, al, dy):
    L = sc.get("left", {})
    R = sc.get("right", {})
    dh = S(545)
    d.line([dh, S(700 + dy * 0.8), dh, S(1300 + dy * 0.8)], fill=mix(CREAM, INK, 0.14), width=max(1, int(S(3))))
    for side, block, x0, x1, t0 in (("L", L, 138, 520, 0.30), ("R", R, 566, 948, 0.52)):
        hf = font(FS, 34)
        q = seg(tl, t0, t0 + 0.36)
        if q > 0:
            lab = block.get("label", "")
            wid = tw(lab, hf) + 40
            xx = x0 if side == "L" else x1 - wid
            rrect(img, xx, 700 + dy * 0.8 - 30, wid, 60, 30, fill=mix(WHITE, accent, 0.16),
                  outline=accent, width=2.2, alpha=q * al)
            paste_l(img, xx + 20, 700 + dy * 0.8, lab, hf, mix(accent, INK, 0.15), q * al)
        tf = font(FB, 44)
        yy = 800
        for i, l in enumerate(wrap(block.get("title", ""), tf, x1 - x0)):
            qq = seg(tl, t0 + 0.10 + i * 0.10, t0 + 0.42 + i * 0.10)
            if qq > 0:
                paste_tl(img, x0, yy + (1 - eo(qq)) * 22 + dy * 0.85, l, tf, INK, qq * al)
            yy += tlh(tf) * 1.1
        bf = font(FM, 34)
        yy += 14
        for i, l in enumerate(wrap(block.get("body", ""), bf, x1 - x0)[:5]):
            qq = seg(tl, t0 + 0.30 + i * 0.09, t0 + 0.66 + i * 0.09)
            if qq > 0:
                paste_tl_rich(img, x0, yy + (1 - eo(qq)) * 18 + dy * 0.9, l, bf, MUTED, accent,
                              block.get("hl", ""), qq * al)
            yy += tlh(bf) * 1.42


# --- layout: langkah-langkah bernomor ---
def draw_fact_steps(img, d, sc, tl, dur, tg, accent, al, dy):
    items = sc.get("items", [])[:4]
    yy = 700
    # jarak antar langkah menyesuaikan jumlahnya supaya kartu tidak menyisakan
    # ruang kosong besar (3 langkah -> lebih lega, 4 langkah -> rapat)
    n = max(1, len(items))
    gap = 158 if n >= 4 else min(280, max(158, (1360 - 700 - 96) / (n - 1)))
    for i, it in enumerate(items):
        t0 = 0.34 + i * 0.30
        q = seg(tl, t0, t0 + 0.5)
        if q > 0:
            k = eob(q)
            cyc = yy + 46 + dy * 0.85
            circ(img, 178, cyc, 38 * k, accent)
            paste_c(img, 178, cyc, str(i + 1), font(FB, 44), WHITE, q * al, scale=k)
            f = font(FM, 40)
            for j, l in enumerate(wrap(it, f, 700)):
                qq = seg(tl, t0 + 0.08 + j * 0.08, t0 + 0.42 + j * 0.08)
                if qq > 0:
                    paste_tl_rich(img, 244, cyc - tlh(f) * 0.5 + (1 - eo(qq)) * 18, l, f, INK, accent,
                                  sc.get("items_hl", ""), qq * al)
                cyc += tlh(f) * 1.35
            if i < len(items) - 1:
                d.line([S(178), S(yy + 96), S(178), S(yy + gap - 16)], fill=mix(CREAM, accent, 0.45),
                       width=max(1, int(S(3))))
        yy += gap



def draw_fact_defs(img, d, sc, tl, dur, tg, accent, al, dy):
    """Kamus mini: istilah (pill) + artinya, muncul satu per satu."""
    items = sc.get("items", [])[:3]
    yy = 700
    fterm = font(FB, 40)
    fmean = font(FM, 37)
    for i, it in enumerate(items):
        t0 = 0.30 + i * 0.34
        q = seg(tl, t0, t0 + 0.5)
        if q <= 0:
            continue
        k = eob(q)
        label = it.get("term", "")
        wpx = tw(label, fterm) + 60
        hpx = 64 * k
        rrect(img, 138, yy + dy * 0.85, wpx, hpx, 32, fill=mix(WHITE, accent, 0.15),
              outline=accent, width=2.4, alpha=q * al)
        paste_c(img, 138 + wpx / 2, yy + 32 + dy * 0.85, label, fterm,
                mix(accent, INK, 0.18), q * al, scale=0.86 + 0.14 * k)
        ym = yy + 64 + 26
        for j, l in enumerate(wrap(it.get("meaning", ""), fmean, 830)):
            qq = seg(tl, t0 + 0.12 + j * 0.08, t0 + 0.46 + j * 0.08)
            if qq > 0:
                paste_tl_rich(img, 138, ym + dy * 0.85, l, fmean, MUTED, accent,
                              it.get("hl", ""), qq * al)
            ym += tlh(fmean) * 1.4
        yy = ym + 32


# ---------- scene: intro ----------
def draw_intro(img, d, sc, tl, dur, tg):
    if sc.get("visual") in diagrams.VISUALS:
        accent = hexc(sc["accent"])
        al = 1 - eo(seg(tl, dur - 0.4, dur))
        diagrams.VISUALS[sc["visual"]](img, d, sc, tl, dur, tg, accent, al, 0.0)
        return
    accent = hexc(sc["accent"])
    fout = eo(seg(tl, dur - 0.4, dur))
    al = 1 - fout
    # badge atas
    q = seg(tl, 0.1, 0.45)
    if q > 0:
        f = font(FS, 33)
        wid = tw(sc["kicker"], f) + 78
        rrect(img, W / 2 - wid / 2, 438, wid, 62, 31, outline=accent, width=2.5, alpha=q * al)
        d.ellipse([S(W / 2 - wid / 2 + 30), S(462), S(W / 2 - wid / 2 + 44), S(476)], fill=accent)
        paste_c(img, W / 2 + 12, 469, sc["kicker"], f, mix(accent, INK, 0.25), q * al)
    # judul kinetik
    y = 632
    base_sizes = [128, 128, 196]
    offs = [(0, 0.18), (-96, 0.52), (0, 0.86)]
    for i, l in enumerate(sc["lines"]):
        fsz = fit_size(FB, l, base_sizes[i], 950)
        fnt = font(FB, fsz)
        dxo, t0 = offs[i]
        q = seg(tl, t0, t0 + 0.55)
        if q <= 0:
            continue
        k = eob(q)
        col = accent if i == 2 else INK
        if i == 2:
            paste_c(img, W / 2 + 6, y + fsz * 0.60, l, fnt, mix(CREAM, INK, 0.22), q * al, scale=k)
            paste_c(img, W / 2, y + fsz * 0.57, l, fnt, col, q * al, scale=k)
        else:
            paste_c(img, W / 2, y + (1 - k) * 46, l, fnt, col, q * al, scale=0.9 + 0.1 * k)
        y += [150, 150, 210][i]
    # roadmap (peta isi video) atau garis aksen
    road = sc.get("roadmap", [])
    if road:
        n = len(road)
        f = font(FS, 30)
        widths = [tw(x, f) + 52 for x in road]
        gap = 22
        total = sum(widths) + gap * (n - 1)
        x = W / 2 - total / 2
        for i, (label, wd) in enumerate(zip(road, widths)):
            t0 = 1.15 + i * 0.28
            q = seg(tl, t0, t0 + 0.45)
            if q > 0:
                k = eob(q)
                rrect(img, x, 1150 - 30 * k, wd, 60 * k, 30,
                      fill=mix(WHITE, accent, 0.14), outline=accent, width=2.2, alpha=q * al)
                paste_c(img, x + wd / 2, 1150, label, f, mix(accent, INK, 0.20), q * al, scale=0.85 + 0.15 * k)
            x += wd + gap
    else:
        q = seg(tl, 1.15, 1.6)
        if q > 0:
            wd = 300 * eo(q)
            d.rounded_rectangle([S(W / 2 - wd / 2), S(1130), S(W / 2 + wd / 2), S(1142)], radius=S(6), fill=accent)
    # kilau mengambang
    for (bx, by, r, ph) in [(214, 540, 15, 0.0), (884, 630, 12, 1.2), (176, 1075, 11, 2.4), (920, 1085, 16, 3.3)]:
        s_ = 0.6 + 0.4 * abs(math.sin(tg * 2.1 + ph))
        star4(d, bx, by + math.sin(tg * 0.9 + ph) * 12, r * s_, mix(CREAM, accent, 0.75))
    # label bawah
    q = seg(tl, 1.5, 1.9)
    if q > 0:
        paste_c(img, W / 2, 1272 if sc.get("roadmap") else 1230, sc.get("sub", ""), font(FM, 38),
                MUTED, q * al)


# ---------- scene: outro ----------
def draw_outro(img, d, sc, tl, dur, tg):
    accent = hexc(sc["accent"])
    al = 1 - eo(seg(tl, dur - 0.3, dur))
    sA = fit_size(FB, sc["lines"][0], 96, 900)
    fA = font(FB, sA)
    q = seg(tl, 0.08, 0.6)
    if q > 0:
        paste_c(img, W / 2, 656 + (1 - eob(q)) * 40, sc["lines"][0], fA, INK, q * al)
    sB = fit_size(FB, sc["lines"][1], 132, 980)
    fB = font(FB, sB)
    q = seg(tl, 0.3, 0.85)
    if q > 0:
        paste_c(img, W / 2, 656 + sA * 1.15 + sB * 0.75 + (1 - eob(q)) * 46, sc["lines"][1], fB, accent,
                q * al, scale=0.92 + 0.08 * eob(q))
    # tombol CTA
    q = seg(tl, 0.75, 1.35)
    if q > 0:
        k = eob(q)
        pulse = 1 + 0.035 * math.sin(tg * 5.2)
        wid, hgt = 520 * pulse, 136 * pulse
        cyc = 1066
        for i in range(3):
            rq = seg(tl, 0.9 + i * 0.5, 2.2 + i * 0.5)
            if 0 < rq < 1:
                rx, ry = wid / 2 + 60 * rq, hgt / 2 + 60 * rq
                ImageDraw.Draw(img).ellipse([S(W / 2 - rx), S(cyc - ry), S(W / 2 + rx), S(cyc + ry)],
                                            outline=mix(CREAM, accent, 0.55 * (1 - rq)), width=max(1, int(S(3))))
        rrect(img, W / 2 - wid / 2, cyc - hgt / 2, wid, hgt, 68, fill=mix(CREAM, INK, 0.92), alpha=q * al)
        paste_c(img, W / 2, cyc, sc["cta"], font(FB, 62), WHITE, q * al, scale=0.8 + 0.2 * k)
        # ikon panah naik
        ax, ay = W / 2 + tw(sc["cta"], font(FB, 62)) / 2 + 56, cyc
        d.line([S(ax), S(ay + 20), S(ax), S(ay - 20)], fill=accent, width=max(1, int(S(7))))
        d.polygon([(S(ax), S(ay - 34)), (S(ax - 18), S(ay - 8)), (S(ax + 18), S(ay - 8))], fill=accent)
    # wordmark channel: titik aksen + KlikTahu
    q = seg(tl, 1.05, 1.6)
    if q > 0:
        alp = eo(q) * al
        fw = font(FB, 74)
        name = META.get("brand", "KlikTahu")
        wtext = tw(name, fw)
        total_w = wtext + 42
        x0 = W / 2 - total_w / 2
        d.ellipse([S(x0), S(1188), S(x0 + 22), S(1210)], fill=accent)
        paste_l(img, x0 + 42, 1199 + (1 - eo(q)) * 18, name, fw, mix(CREAM, INK, 0.86), alp)
    q = seg(tl, 1.25, 1.7)
    if q > 0:
        paste_c(img, W / 2, 1320, sc["foot"], font(FM, 40), mix(CREAM, INK, 0.72), q * al)
        paste_c(img, W / 2, 1390, sc.get("foot2", ""), font(FR, 34), mix(CREAM, INK, 0.68), q * al)
    q = seg(tl, 1.5, 1.95)
    if q > 0:
        paste_c(img, W / 2, 1520, sc["src"], font(FR, 30), mix(CREAM, INK, 0.62), q * al)


# ---------- transisi ----------
def draw_streak(img, d, scenes, tg):
    for i in range(1, len(scenes)):
        st = scenes[i]["start"]
        a, b = st - 0.14, st + 0.20
        if a <= tg <= b:
            u = eio((tg - a) / (b - a))
            acc = hexc(scenes[i - 1]["accent"])
            yc = -0.22 * H + u * 1.42 * H
            hgt, skew = 0.16 * H, 90
            d.polygon([(0, S(yc - hgt / 2 + skew)), (S(W), S(yc - hgt / 2 - skew)),
                       (S(W), S(yc + hgt / 2 - skew)), (0, S(yc + hgt / 2 + skew))], fill=mix(acc, WHITE, 0.55))
            yc += hgt * 0.75
            d.polygon([(0, S(yc - hgt / 2 + skew)), (S(W), S(yc - hgt / 2 - skew)),
                       (S(W), S(yc + hgt / 2 - skew)), (0, S(yc + hgt / 2 + skew))], fill=acc)


# ---------- render ----------
META = {}



def _zoom_img(img, k, ax=0.5, ay=0.45):
    """Perbesar gambar k kali lalu potong kembali ke kanvas (dipakai kamera transisi)."""
    w, h = img.size
    nw, nh = int(round(w * k)), int(round(h * k))
    if k <= 1.001 or nw <= w or nh <= h:
        return img
    big = img.resize((nw, nh), Image.BICUBIC)
    x0 = int((nw - w) * ax)
    y0 = max(0, min(nh - h, int((nh - h) * ay)))
    return big.crop((x0, y0, x0 + w, y0 + h))


def _wipe_img(prev, new, p, soft=0.14):
    """Tirai lembut: adegan baru menyapu dari bawah ke atas dengan tepi bergradasi."""
    w, h = new.size
    edge = h * (1.0 - p)
    m = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(m)
    md.rectangle([0, int(edge), w, h], fill=255)
    band = max(2, int(soft * h))
    for i in range(band):
        y = int(edge) + i
        if 0 <= y < h:
            md.line([(0, y), (w, y)], fill=int(255 * (i / band)))
    return Image.composite(new, prev, m)


def _scene_index(tl, scenes):
    for i, s in enumerate(scenes):
        if tl < s["start"] + s["dur"] or s is scenes[-1]:
            return i
    return len(scenes) - 1


def _content_image(tl, total, scenes, meta):
    """Konten adegan saja (latar + diagram), sudah melewati kamera zoom-out.

    HUD (brand, lencana, progress bar) sengaja TIDAK digambar di sini, supaya saat
    transisi antar adegan HUD tetap tajam dan tidak ikut ter-blend.
    """
    img = Image.new("RGB", (int(S(W)), int(S(H))), CREAM)
    d = ImageDraw.Draw(img)
    i = _scene_index(tl, scenes)
    sc = scenes[i]
    t = tl - sc["start"]
    accent = hexc(sc["accent"])
    draw_bg(img, d, tl, accent)
    if sc["type"] == "fact":
        draw_fact(img, d, sc, t, sc["dur"], tl)
    elif sc["type"] == "intro":
        draw_intro(img, d, sc, t, sc["dur"], tl)
    else:
        draw_outro(img, d, sc, t, sc["dur"], tl)
    # kamera push: sedikit zoom-out tiap scene supaya frame terasa hidup
    prog = eio(clamp(t / max(0.1, sc["dur"])))
    z = 1.0 + 0.060 * (1.0 - prog)      # elemen tampil lebih besar di layar tegak
    w2, h2 = int(round(W * SS)), int(round(H * SS))
    cw, ch = int(round(w2 / z)), int(round(h2 / z))
    if cw < w2 or ch < h2:
        x0 = (w2 - cw) // 2
        y0 = int((h2 - ch) * 0.42)
        img = img.crop((x0, y0, x0 + cw, y0 + ch))
    return img


def _camera(img, k, dx, dy):
    """Gerakan kamera: dorong (zoom) + geser halus. Kualitas tetap 1:1 di tengah."""
    if abs(k - 1.0) < 0.004 and abs(dx) < 0.6 and abs(dy) < 0.6:
        return img
    w, h = img.size
    cw, ch = w / max(0.6, k), h / max(0.6, k)
    cx, cy = w / 2.0 + dx, h / 2.0 + dy
    x0 = min(max(0.0, cx - cw / 2), w - cw)
    y0 = min(max(0.0, cy - ch / 2), h - ch)
    return img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((w, h), Image.BICUBIC)


def _shake_amount(tl, scenes):
    """Goyangan kamera khusus adegan gempa (makin kuat lalu mereda)."""
    tot = 0.0
    for sc in scenes:
        amp = float(sc.get("shake") or 0.0)
        if amp <= 0:
            continue
        t = tl - sc["start"]
        if -0.4 < t < sc["dur"]:
            k = diagrams.esmooth(clamp((t - 0.15) / 0.55))
            fade = diagrams.esmooth(clamp(1.0 - (t - max(0.5, sc["dur"] * 0.45)) / max(0.6, sc["dur"] * 0.5)))
            tot = max(tot, amp * k * fade)
    return tot


_VIG_CACHE, _VIG_DARK, _GRAIN_CACHE = {}, {}, {}


def _vignette(img, amount=0.10):
    """Pinggiran lembut menggelap — memberi kedalaman sinematik (sangat halus).

    PENTING: mask dibuat dari gradasi RADIAL (elips), bukan dari persegi.
    Versi sebelumnya memakai cincin persegi, sehingga di layar 9:16 muncul
    bidang terang berbentuk kotak tegak di tengah frame (tampak seperti ponsel).
    """
    if amount <= 0.001:
        return img
    w, h = img.size
    key = (w, h, round(amount, 4))
    m = _VIG_CACHE.get(key)
    if m is None:
        import numpy as _np
        n = 256
        yy, xx = _np.mgrid[0:n, 0:n].astype("float32")
        cx = cy = (n - 1) / 2.0
        u = (xx - cx) / cx
        v = (yy - cy) / cy
        r = _np.sqrt(u * u + v * v) / 1.4142        # 0 di tengah, 1 di sudut
        k = _np.clip((r - 0.40) / 0.60, 0.0, 1.0) ** 1.5
        arr = (_np.clip(k * amount, 0.0, 1.0) * 255.0).astype("uint8")
        m = Image.fromarray(arr, "L").resize((w, h), Image.BICUBIC)
        _VIG_CACHE[key] = m
    dark = _VIG_DARK.get((w, h))
    if dark is None:
        dark = Image.new("RGB", (w, h), (18, 16, 26))
        _VIG_DARK[(w, h)] = dark
    return Image.composite(dark, img, m)


def _grain(img, amount=4.0, seed=7):
    """Butiran halus khas film — menyatukan elemen supaya tidak terasa datar."""
    if amount <= 0.1:
        return img
    w, h = img.size
    key = (w, h, round(amount, 3), seed)
    tiles = _GRAIN_CACHE.get(key)
    if tiles is None:
        import random as _r
        rnd = _r.Random(seed)
        sw, sh = max(2, w // 3), max(2, h // 3)
        tiles = []
        for _ in range(4):
            small = Image.new("L", (sw, sh))
            small.putdata([int(clamp(128 + rnd.gauss(0, amount * 6.0), 0, 255)) for _ in range(sw * sh)])
            t = small.resize((w, h), Image.BILINEAR)
            tiles.append(Image.merge("RGB", (t, t, t)))
        _GRAIN_CACHE[key] = tiles
    return Image.blend(img, tiles[int(time.time() * 24) % 4], amount / 90.0)


def _finish(img, tl, total, scenes, meta):
    """HUD + sapuan aksen + downscale + penajam — dijalankan setelah transisi."""
    i = _scene_index(tl, scenes)
    sc = scenes[i]
    accent = hexc(sc["accent"])
    cam = float(os.environ.get("KT_CAM", "1"))
    if cam > 0:
        # dorong perlahan sepanjang adegan + sisi bergantian supaya tidak monoton
        p = clamp((tl - sc["start"]) / max(0.4, sc["dur"]))
        k = 1.0 + float(os.environ.get("KT_CAM_ZOOM", "0.115")) * diagrams.esmooth(p)
        sgn = 1.0 if (i % 2 == 0) else -1.0
        amp = float(os.environ.get("KT_CAM_AMP", "11"))
        img = _camera(img, k, sgn * amp * (0.5 - diagrams.esmooth(p)), -amp * 0.35 * (0.5 - diagrams.esmooth(p)))
        sh = _shake_amount(tl, scenes)
        if sh > 0.01:
            img = _camera(img, 1.0, amp * 0.9 * sh * math.sin(tl * 37.0),
                          amp * 0.7 * sh * math.sin(tl * 29.0 + 1.1))
    d = ImageDraw.Draw(img)
    draw_header(img, d, sc, total, tl, accent, meta)
    draw_streak(img, d, scenes, tl)
    if img.size != (W, H):
        img = img.resize((W, H), Image.LANCZOS)
    if SHARPEN > 0:
        img = img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=int(round(SHARPEN)), threshold=3))
    # vignette + grain di resolusi akhir: lebih cepat dan butirannya tidak ikut mengecil
    img = _vignette(img, float(os.environ.get("KT_VIG", "0.10")))
    img = _grain(img, float(os.environ.get("KT_GRAIN", "3.6")))
    return img


_MP = {}


def _mp_init(total, scenes, meta, outdir, fps, ss, sharpen):
    """Siapkan proses pekerja: variabel global disalin apa adanya (fork)."""
    global SS, SHARPEN
    SS, SHARPEN = ss, sharpen
    diagrams.SS = ss
    _MP.update(total=total, scenes=scenes, meta=meta, outdir=outdir, fps=fps)


def _mp_one(i):
    render_frame(i / _MP["fps"], _MP["total"], _MP["scenes"], _MP["meta"],
                 os.path.join(_MP["outdir"], f"f_{i:05d}.png"))
    return i


def render_frame(tl, total, scenes, meta, out_path):
    """Frame: transisi antar adegan (fade/zoom/wipe/rise) + fade lembut di akhir."""
    img = _content_image(tl, total, scenes, meta)
    xf = float(os.environ.get("KT_XFADE", "0.45"))
    i = _scene_index(tl, scenes)
    st = scenes[i]["start"]
    if xf > 0.01 and i > 0 and tl < st + xf:
        # konten adegan sebelumnya dibekukan tepat di ujungnya, lalu berpindah ke adegan baru
        p = (tl - st) / xf
        k = diagrams.esmooth(p)
        mode = str(scenes[i].get("trans") or os.environ.get("KT_TRANS", "fade")).lower()
        prev = _content_image(max(0.0, st - 0.02), total, scenes, meta)
        if prev.size != img.size:
            prev = prev.resize(img.size, Image.BICUBIC)
        if mode == "zoom":
            img = Image.blend(_zoom_img(prev, 1.0 + 0.105 * k), img, min(1.0, 0.12 + 0.88 * k))
        elif mode == "wipe":
            img = _wipe_img(prev, img, k)
        elif mode == "rise":
            off = int((1.0 - k) * 0.07 * img.size[1])
            up = Image.new("RGB", img.size, CREAM)
            up.paste(img, (0, off))
            img = Image.blend(prev, up, min(1.0, 0.22 + 0.78 * k))
        else:
            img = Image.blend(prev, img, k)
    img = _finish(img, tl, total, scenes, meta)
    ef = float(os.environ.get("KT_ENDFADE", "0.40"))
    if ef > 0.01 and tl > total - ef:
        k = diagrams.esmooth((tl - (total - ef)) / ef)
        img = Image.blend(img, Image.new("RGB", img.size, CREAM), 0.9 * k)
    img.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", default=os.path.join(BASE, "timeline.json"))
    ap.add_argument("--outdir", default=os.path.join(BUILD, "frames"))
    ap.add_argument("--times", default="", help="waktu pratinjau dipisah koma; 'auto' = dari timeline")
    ap.add_argument("--range", default="")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--ss", type=float, default=float(os.environ.get("KT_SS", "2.0")))
    ap.add_argument("--sharpen", type=float, default=float(os.environ.get("KT_SHARPEN", "45")))
    ap.add_argument("--sheet", action="store_true",
                    help="setelah pratinjau, susun montase berlabel (build/prev_sheet.png)")
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("KT_JOBS", "1")),
                    help="jumlah proses paralel saat merender rentang penuh (default 1; KT_JOBS)")
    a = ap.parse_args()
    global SS, SHARPEN
    SS = a.ss
    SHARPEN = a.sharpen
    diagrams.SS = SS
    tl_data = json.load(open(a.timeline))
    scenes, total = tl_data["scenes"], tl_data["total"]
    meta = tl_data.get("meta", {})
    # --- jaga konsistensi: field visual SELALU diambil dari content.json terbaru ---
    cpath = os.path.join(BASE, "content.json")
    if os.path.exists(cpath):
        content = json.load(open(cpath))
        cby = {c["id"]: c for c in content.get("scenes", [])}
        asing = []
        for sc in scenes:
            c = cby.get(sc["id"])
            if not c:
                continue
            for k, v in c.items():
                if k in ("id", "type", "start", "dur", "vo_dur", "vo_at", "captions"):
                    continue
                if k not in sc or sc[k] != v:
                    asing.append(f"{sc['id']}.{k}")
                sc[k] = v
        for k, v in ({"header_badge": content.get("header_badge"),
                      "brand": content.get("channel", "KlikTahu"),
                      "bg_element": content.get("bg_element", "none")}).items():
            if v is not None:
                meta[k] = v
        if asing:
            print(f"[info] {len(asing)} field visual disegarkan dari content.json: "
                  f"{', '.join(asing[:8])}{' ...' if len(asing) > 8 else ''}")
    global META, BG_MOON, BG_SUN, BG_METEOR
    META = meta
    BG_MOON = meta.get("bg_element") == "moon"
    BG_SUN = meta.get("bg_element") == "sun"
    BG_METEOR = meta.get("bg_element") == "meteor"
    os.makedirs(a.outdir, exist_ok=True)
    t0 = time.time()
    if a.times:
        # 'auto' = titik pratinjau dihitung dari timeline (tiap adegan + frame akhir)
        if a.times.strip().lower() == "auto":
            waktu = mesin_util.preview_times(tl_data)
        else:
            waktu = [{"scene": "", "t": float(x)} for x in a.times.split(",")]
        hasil = []
        for e in waktu:
            ts = e["t"]
            p = os.path.join(a.outdir, f"t{ts:07.2f}.png")
            render_frame(ts, total, scenes, meta, p)
            label = f"{e['scene']}  {ts:.2f}s" if e.get("scene") else f"{ts:.2f}s"
            hasil.append((p, label))
            print("ok", p, f"{time.time()-t0:.1f}s", f"({label})")
        if a.sheet:
            out = os.path.join(BUILD, "prev_sheet.png")
            r = mesin_util.sheet(hasil, out)
            print(f"[+] montase pratinjau -> {os.path.normpath(out)}  ({len(hasil)} panel)")
        return
    if a.range:
        lo, hi = [int(x) for x in a.range.split(":")]
    else:
        lo, hi = 0, int(round(total * a.fps))
    jobs = max(1, int(a.jobs))
    if jobs > 1:
        import multiprocessing as mp
        ctx = mp.get_context("fork")
        n = hi - lo
        print(f"render {n} frame dengan {jobs} proses paralel", flush=True)
        with ctx.Pool(jobs, initializer=_mp_init,
                      initargs=(total, scenes, meta, a.outdir, a.fps, SS, SHARPEN)) as pool:
            done = 0
            for _ in pool.imap_unordered(_mp_one, range(lo, hi), chunksize=6):
                done += 1
                if done % 240 == 0 or done == n:
                    el = time.time() - t0
                    print(f"{done}/{n}  {el:.0f}s  eta {el/done*(n-done):.0f}s", flush=True)
    else:
        for i in range(lo, hi):
            render_frame(i / a.fps, total, scenes, meta, os.path.join(a.outdir, f"f_{i:05d}.png"))
            if i % 60 == 0:
                el = time.time() - t0
                done = i - lo + 1
                print(f"{i}/{hi}  {el:.0f}s  eta {el/done*(hi-i):.0f}s", flush=True)
    print("DONE frames", lo, hi, f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
