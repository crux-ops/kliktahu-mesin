"""Finishing sinematik di aras piksel numpy (RGB uint8). Deterministik."""
import numpy as np


def letterbox(arr, ratio=0.06, color=(0, 0, 0)):
    """Bilah hitam atas-bawah setebal ratio*tinggi. Kembalikan salinan baru."""
    a = np.array(arr, copy=True)
    h = a.shape[0]
    b = int(round(h * float(ratio)))
    if b > 0:
        a[:b, :, :] = color
        a[h - b:, :, :] = color
    return a


def _shift_hold(a, dx):
    """Geser kanal 2D sejauh dx kolom; tepi diisi tetangga (tanpa wrap)."""
    dx = int(round(dx))
    if dx == 0:
        return a
    out = np.empty_like(a)
    if dx > 0:
        out[:, dx:] = a[:, :-dx]
        out[:, :dx] = a[:, :1]
    else:
        out[:, :dx] = a[:, -dx:]
        out[:, dx:] = a[:, -1:]
    return out


def chromatic_aberration(arr, px=2.0, vertical=False):
    """Aberasi kromatik: kanal R dan B digeser berlawanan (±px)."""
    a = np.asarray(arr)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    if vertical:
        r2 = _shift_hold(r.T, px).T
        b2 = _shift_hold(b.T, -px).T
    else:
        r2 = _shift_hold(r, px)
        b2 = _shift_hold(b, -px)
    return np.stack([r2, g, b2], axis=-1)
