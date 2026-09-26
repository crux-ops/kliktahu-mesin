"""Fungsi easing murni (tanpa Skia). f(0)=0, f(1)=1 untuk semua.

Monoton naik kecuali out_back/out_elastic (overshoot disengaja untuk pop).
t di luar [0,1] dijepit dulu.
"""
import math


def clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else float(t))


def linear(t):
    return clamp01(t)


def smooth(t):
    t = clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def in_quad(t):
    t = clamp01(t)
    return t * t


def out_quad(t):
    t = clamp01(t)
    return 1.0 - (1.0 - t) * (1.0 - t)


def in_out_quad(t):
    t = clamp01(t)
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0


def in_cubic(t):
    t = clamp01(t)
    return t * t * t


def out_cubic(t):
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 3


def in_out_cubic(t):
    t = clamp01(t)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def in_quart(t):
    t = clamp01(t)
    return t ** 4


def out_quart(t):
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 4


def in_out_quart(t):
    t = clamp01(t)
    if t < 0.5:
        return 8.0 * t ** 4
    return 1.0 - (-2.0 * t + 2.0) ** 4 / 2.0


def in_expo(t):
    t = clamp01(t)
    if t <= 0.0:
        return 0.0
    return 2.0 ** (10.0 * t - 10.0)


def out_expo(t):
    t = clamp01(t)
    if t >= 1.0:
        return 1.0
    return 1.0 - 2.0 ** (-10.0 * t)


def out_back(t, s=1.70158):
    t = clamp01(t)
    if t <= 0.0 or t >= 1.0:
        return t
    u = t - 1.0
    return 1.0 + (s + 1.0) * u ** 3 + s * u * u


def out_elastic(t, amp=1.0, period=0.3):
    t = clamp01(t)
    if t <= 0.0 or t >= 1.0:
        return t
    s = period / (2.0 * math.pi) * math.asin(1.0 / amp)
    return amp * 2.0 ** (-10.0 * t) * math.sin((t - s) * 2.0 * math.pi / period) + 1.0


EASE = {
    "linear": linear,
    "smooth": smooth,
    "in_quad": in_quad,
    "out_quad": out_quad,
    "in_out_quad": in_out_quad,
    "in_cubic": in_cubic,
    "out_cubic": out_cubic,
    "in_out_cubic": in_out_cubic,
    "in_quart": in_quart,
    "out_quart": out_quart,
    "in_out_quart": in_out_quart,
    "in_expo": in_expo,
    "out_expo": out_expo,
    "out_back": out_back,
    "out_elastic": out_elastic,
}

# Easing monoton (aman untuk wipe/clip yang butuh 0<=f<=1).
MONOTONIC = [k for k in EASE if k not in ("out_back", "out_elastic")]


def get(name):
    try:
        return EASE[name]
    except KeyError:
        raise ValueError(f"easing tak dikenal: {name}")
