"""Trek keyframe murni: [(t, nilai, easing?)] -> sample(t).

Nilai boleh skalar (int/float) atau tuple/list angka sama panjang.
t di luar rentang dijepit ke ujung (hold).
"""
from .ease import get as ease_get


def _lerp(a, b, u):
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        if len(a) != len(b):
            raise ValueError("panjang nilai keyframe beda")
        cls = tuple if isinstance(a, tuple) else list
        return cls(x + (y - x) * u for x, y in zip(a, b))
    return a + (b - a) * u


class Track:
    """Satu trek animasi. keys: urutan (t, nilai) atau (t, nilai, nama_easing)."""

    def __init__(self, keys, ease_default="smooth"):
        if len(keys) < 2:
            raise ValueError("butuh >= 2 keyframe")
        norm = []
        for k in keys:
            if len(k) == 2:
                t, v = k
                e = ease_default
            elif len(k) == 3:
                t, v, e = k
            else:
                raise ValueError(f"keyframe salah bentuk: {k}")
            norm.append((float(t), v, e))
        norm.sort(key=lambda k: k[0])
        for i in range(1, len(norm)):
            if norm[i][0] <= norm[i - 1][0]:
                raise ValueError("waktu keyframe harus naik tegas")
        self.keys = norm

    def sample(self, t):
        t = float(t)
        if t <= self.keys[0][0]:
            return self.keys[0][1]
        if t >= self.keys[-1][0]:
            return self.keys[-1][1]
        for i in range(1, len(self.keys)):
            t0, v0, _ = self.keys[i - 1]
            t1, v1, e1 = self.keys[i]
            if t <= t1:
                u = (t - t0) / (t1 - t0)
                return _lerp(v0, v1, ease_get(e1)(u))
        return self.keys[-1][1]  # tak terjangkau

    @property
    def t_start(self):
        return self.keys[0][0]

    @property
    def t_end(self):
        return self.keys[-1][0]


def typewriter_text(text, t, cps=12.0):
    """Kembalikan potongan teks efek ketikan pada detik t (cps = huruf/detik)."""
    n = int(float(t) * float(cps) + 1e-9)
    if n <= 0:
        return ""
    return text[:n]


def stagger_local(t, index, count, overlap=0.5):
    """Waktu lokal [0,1] anggota ke-index dari total count (efek beruntun).

    overlap 0 = satu-satu berurutan, 1 = semua serentak.
    """
    if count <= 1:
        return max(0.0, min(1.0, float(t)))
    span = 1.0 - overlap
    start = (index / (count - 1)) * span
    width = 1.0 - span
    if width <= 0.0:
        return max(0.0, min(1.0, float(t)))
    return max(0.0, min(1.0, (float(t) - start) / width))
