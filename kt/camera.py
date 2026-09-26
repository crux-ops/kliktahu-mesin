"""Kamera virtual 2D: geser/zoom/putar + guncangan ber-seed (deterministik).

apply(): bungkus gambar adegan di antara save()/restore() pemanggil.
Guncangan = jumlah sinus berfase acak-seed: mulus, deterministik, tanpa state.
"""
import math

from .rng import spawn


class Camera:
    """x, y = pusat pandang (px, relatif tengah); zoom; rot = derajat."""

    def __init__(self, x=0.0, y=0.0, zoom=1.0, rot=0.0):
        self.x, self.y = float(x), float(y)
        self.zoom = float(zoom)
        self.rot = float(rot)

    def apply(self, canvas, W, H):
        canvas.translate(float(W) / 2.0, float(H) / 2.0)
        canvas.scale(self.zoom, self.zoom)
        canvas.rotate(self.rot)
        canvas.translate(-float(W) / 2.0 - self.x, -float(H) / 2.0 - self.y)


def make_shake(seed, amp=12.0, freq=9.0, rot_amp=1.2):
    """Kembalikan fungsi guncang(t_detik) -> (dx, dy, drot). Deterministik."""
    r = spawn(0, f"guncang|{seed}")
    parts = [(r.uniform(0.7, 1.3), r.uniform(0, 2 * math.pi),
              r.uniform(0.7, 1.3), r.uniform(0, 2 * math.pi)) for _ in range(3)]
    pr = spawn(1, f"guncang-rot|{seed}")
    prot = [(pr.uniform(0.7, 1.3), pr.uniform(0, 2 * math.pi)) for _ in range(2)]

    def shake(t):
        t = float(t)
        dx = sum(math.sin(t * freq * fx + px) for fx, px, _, _ in parts) / 3.0
        dy = sum(math.sin(t * freq * fy + py) for _, _, fy, py in parts) / 3.0
        dr = sum(math.sin(t * freq * f + p) for f, p in prot) / 2.0
        return (dx * amp, dy * amp, dr * rot_amp)

    return shake


def impact_zoom(t, dur=0.45, peak=1.12):
    """Zoom hentakan: naik cepat ke peak lalu turun mulus (t detik sejak hentakan)."""
    from .ease import out_expo, in_out_cubic
    if t <= 0:
        return 1.0
    if t >= dur:
        return 1.0
    u = t / dur
    if u < 0.35:
        return 1.0 + (peak - 1.0) * out_expo(u / 0.35)
    return 1.0 + (peak - 1.0) * (1.0 - in_out_cubic((u - 0.35) / 0.65))
