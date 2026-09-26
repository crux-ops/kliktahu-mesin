"""Renderer Skia: kanvas vektor deterministik + cache + finishing numpy.

Aturan: semua yang acak memakai seed eksplisit (kt.rng). Tanpa jam/waktu.
Latar selalu opak (byte premul Skia = straight untuk alfa 255).
"""
import hashlib
import io
import os

import numpy as np
import skia
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
FONTS = os.path.join(REPO, "fonts")


def argb(a, r, g, b):
    return skia.ColorSetARGB(int(a), int(r), int(g), int(b))


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hex_to_argb(h, a=255):
    r, g, b = hex_to_rgb(h)
    return argb(a, r, g, b)


def fill_paint(color, aa=True):
    p = skia.Paint()
    p.setColor(color)
    p.setAntiAlias(aa)
    p.setStyle(skia.Paint.Style.kFill_Style)
    return p


def stroke_paint(color, width, aa=True):
    p = skia.Paint()
    p.setColor(color)
    p.setAntiAlias(aa)
    p.setStyle(skia.Paint.Style.kStroke_Style)
    p.setStrokeWidth(float(width))
    return p


def linear_gradient_paint(x0, y0, x1, y1, c0, c1):
    p = skia.Paint()
    p.setAntiAlias(True)
    pts = [skia.Point(float(x0), float(y0)), skia.Point(float(x1), float(y1))]
    p.setShader(skia.GradientShader.MakeLinear(pts, [c0, c1], [0.0, 1.0],
                                               skia.TileMode.kClamp))
    return p


def blur_paint(sigma, alpha=255):
    p = skia.Paint()
    p.setAntiAlias(True)
    p.setAlpha(int(alpha))
    p.setImageFilter(skia.ImageFilters.Blur(float(sigma), float(sigma),
                                            skia.TileMode.kClamp, None))
    return p


def rrect_of(x, y, w, h, r):
    rr = skia.RRect()
    rr.setRectXY(skia.Rect.MakeXYWH(float(x), float(y), float(w), float(h)),
                 float(r), float(r))
    return rr


class TextCache:
    """Cache typeface + font Skia. Kunci: (nama_file, ukuran)."""

    def __init__(self, font_dir=FONTS):
        self.font_dir = font_dir
        self._faces = {}
        self._fonts = {}

    def face(self, name):
        if name not in self._faces:
            tf = skia.Typeface.MakeFromFile(os.path.join(self.font_dir, name))
            if tf is None:
                raise RuntimeError(f"fon tidak bisa dibuka: {name}")
            self._faces[name] = tf
        return self._faces[name]

    def font(self, name, size):
        key = (name, round(float(size), 2))
        if key not in self._fonts:
            f = skia.Font(self.face(name), float(size))
            f.setSubpixel(True)
            self._fonts[key] = f
        return self._fonts[key]

    def width(self, text, name, size):
        return float(self.font(name, size).measureText(text))

    def draw_center(self, canvas, cx, cy, text, name, size, color):
        """Teks rata tengah (cx, cy = titik tengah visual). Kembalikan lebar."""
        f = self.font(name, size)
        m = f.getMetrics()
        w = float(f.measureText(text))
        baseline = float(cy) - (float(m.fAscent) + float(m.fDescent)) / 2.0
        canvas.drawString(text, float(cx) - w / 2.0, baseline, f, fill_paint(color))
        return w

    def draw_paragraph(self, canvas, x, y, text, name, size, color, lh=1.25):
        """Multi-baris rata kiri dari (x, y). Kembalikan y akhir."""
        f = self.font(name, size)
        m = f.getMetrics()
        step = (float(m.fDescent) - float(m.fAscent)) * float(lh)
        yy = float(y) - float(m.fAscent)
        for line in text.split("\n"):
            canvas.drawString(line, float(x), yy, f, fill_paint(color))
            yy += step
        return yy


def soft_shadow(canvas, x, y, w, h, r, dy=14, sigma=22, alpha=110):
    """Bayangan lembut: sprite hitam kecil digambar buram (tanpa saveLayer)."""
    pad = int(sigma * 3 + dy + 8)
    sw, sh = max(2, int(w + pad * 2)), max(2, int(h + pad * 2))
    tmp = skia.Surface(sw, sh)
    tc = tmp.getCanvas()
    tc.drawRoundRect(skia.Rect.MakeXYWH(pad, pad, w, h), r, r,
                     fill_paint(argb(255, 0, 0, 0)))
    snap = tmp.makeImageSnapshot()
    canvas.drawImage(snap, x - pad, y - pad + dy, paint=blur_paint(sigma, alpha))


def glass_panel(surface, x, y, w, h, r, blur=22, tint=(255, 255, 255, 46),
                gloss=(255, 255, 255, 110)):
    """Liquid Glass: jepret latar -> buram -> klip panel -> kilap tepi."""
    canvas = surface.getCanvas()
    snap = surface.makeImageSnapshot()
    canvas.save()
    canvas.clipRRect(rrect_of(x, y, w, h, r), skia.ClipOp.kIntersect, True)
    canvas.drawImage(snap, 0, 0, paint=blur_paint(blur))
    tr, tg, tb, ta = tint[0], tint[1], tint[2], tint[3]
    canvas.drawRect(skia.Rect.MakeXYWH(x, y, w, h), fill_paint(argb(ta, tr, tg, tb)))
    canvas.restore()
    rect = skia.Rect.MakeXYWH(x, y, w, h)
    gr, gg, gb, ga = gloss[0], gloss[1], gloss[2], gloss[3]
    canvas.drawRoundRect(rect, r, r, stroke_paint(argb(ga, gr, gg, gb), 3))


def star_path(cx, cy, r_out, r_in, n=5, rot=-90.0):
    import math
    p = skia.Path()
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180.0 / n)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    return p


def _snapshot_to_pil(surface, target_w, target_h):
    img = surface.makeImageSnapshot()
    # Jalur 1: bytes mentah langsung (tercepat).
    try:
        raw = img.tobytes()
        w, h = img.width(), img.height()
        pil = Image.frombytes("RGBA", (w, h), raw)
    except Exception:
        pil = None
    # Jalur 2: ronde PNG via SkData + PIL (paling kompatibel).
    if pil is None:
        try:
            data = img.encodeToData()
            if data is not None:
                pil = Image.open(io.BytesIO(bytes(data))).convert("RGBA")
        except Exception:
            pil = None
    # Jalur 3: baca memori Pixmap via ctypes (cadangan terakhir).
    if pil is None:
        import ctypes
        pm = skia.Pixmap()
        if not img.peekPixels(pm):
            raise RuntimeError("gagal membaca piksel snapshot Skia")
        w, h, row = pm.width(), pm.height(), pm.rowBytes()
        buf = ctypes.string_at(pm.addr(), h * row)
        wide = np.frombuffer(buf, dtype=np.uint8).reshape(h, row)
        arr = wide[:, :w * 4].reshape(h, w, 4)
        pil = Image.fromarray(arr.copy(), "RGBA")
    w, h = pil.size
    if (w, h) != (target_w, target_h):
        pil = pil.resize((target_w, target_h), Image.LANCZOS)
    return pil.convert("RGB")


def finish_frame(arr, seed, vignette=0.16, grain=2.2, grade=0.10):
    """Finishing numpy deterministik: grading S-curve + vinyet + grain film."""
    from .rng import numpy_seed
    a = arr.astype(np.float32)
    x = np.linspace(0, 1, 256, dtype=np.float32)
    lut = (x + grade * (x * (1 - x) * (x - 0.5) * 4.0)).clip(0, 1)
    a = lut[(a / 255.0 * 255).astype(np.int32)] * 255.0
    H, W, _ = a.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx / max(1, W - 1) - 0.5) * 2.0
    dy = (yy / max(1, H - 1) - 0.5) * 2.0
    mask = 1.0 - vignette * np.clip(dx * dx + dy * dy, 0, 1) ** 1.5
    a *= mask[..., None]
    rng = np.random.default_rng(numpy_seed(seed, "grain"))
    a += rng.normal(0, grain, a.shape).astype(np.float32)
    return np.clip(a, 0, 255).astype(np.uint8)


class Renderer:
    """Kanvas logis W x H. ss = supersampling, out_scale = mode pratinjau."""

    def __init__(self, w, h, ss=2.0, out_scale=1.0):
        self.w, self.h = int(w), int(h)
        self.ss = float(ss)
        self.out_scale = float(out_scale)
        self.pw = max(1, int(round(w * ss * out_scale)))
        self.ph = max(1, int(round(h * ss * out_scale)))
        self.surface = skia.Surface(self.pw, self.ph)
        self.canvas = self.surface.getCanvas()
        self.canvas.scale(ss * out_scale, ss * out_scale)
        self.text = TextCache()

    def clear(self, color):
        self.canvas.drawColor(color)

    def to_pil(self):
        tw = max(1, int(round(self.w * self.out_scale)))
        th = max(1, int(round(self.h * self.out_scale)))
        return _snapshot_to_pil(self.surface, tw, th)

    def png_bytes(self, finish_seed=None):
        pil = self.to_pil()
        if finish_seed is not None:
            pil = Image.fromarray(finish_frame(np.array(pil), finish_seed), "RGB")
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
