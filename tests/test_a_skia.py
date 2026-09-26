"""Uji Skia Bagian A (HANYA DI GITHUB ACTIONS). Semua assert di memori + hash."""
import numpy as np
import skia

from kt import pool as pool_mod
from kt.canvas import (Renderer, argb, blur_paint, fill_paint, finish_frame,
                       glass_panel, hex_to_argb, linear_gradient_paint,
                       soft_shadow, star_path)
from kt.spec import SHORTS


def _mini(seed_px=0):
    r = Renderer(320, 200, ss=1.0)
    c = r.canvas
    c.drawRect(skia.Rect.MakeXYWH(0, 0, 320, 200), fill_paint(hex_to_argb("#F6F1E8")))
    c.drawCircle(80 + seed_px, 100, 50, fill_paint(hex_to_argb("#B2542A")))
    c.drawPath(star_path(230, 100, 60, 26), fill_paint(hex_to_argb("#1F7A6D")))
    r.text.draw_center(c, 160, 30, "UJI", "Poppins-Bold.ttf", 28, argb(255, 24, 24, 31))
    return r


def test_typeface_and_measure():
    r = Renderer(100, 100, ss=1.0)
    w = r.text.width("Halo Dunia", "Poppins-Bold.ttf", 40)
    assert w > 100
    assert len(r.text._fonts) >= 1  # cache terisi


def test_determinism_bytes_identical():
    assert _mini().png_bytes() == _mini().png_bytes()


def test_different_content_different_bytes():
    assert _mini().png_bytes() != _mini(seed_px=40).png_bytes()


def test_blur_shadow_glass_change_pixels():
    base = np.array(_mini().to_pil()).astype(int)
    r = _mini()
    soft_shadow(r.canvas, 10, 10, 100, 60, 12)
    s1 = np.array(r.to_pil()).astype(int)
    assert np.abs(s1 - base).sum() > 1000
    r2 = _mini()
    glass_panel(r2.surface, 150, 40, 140, 120, 24)
    s2 = np.array(r2.to_pil()).astype(int)
    assert np.abs(s2 - base).sum() > 1000
    r3 = _mini()
    r3.canvas.drawRect(skia.Rect.MakeXYWH(0, 0, 320, 200),
                       linear_gradient_paint(0, 0, 0, 200, argb(80, 0, 0, 0), argb(0, 0, 0, 0)))
    s3 = np.array(r3.to_pil()).astype(int)
    assert np.abs(s3 - base).sum() > 1000


def test_supersample_and_preview_sizes():
    assert _mini().to_pil().size == (320, 200)
    r = Renderer(320, 200, ss=2.0)
    assert (r.pw, r.ph) == (640, 400)
    assert r.to_pil().size == (320, 200)
    rp = Renderer(320, 200, ss=1.0, out_scale=0.25)
    assert rp.to_pil().size == (80, 50)


def test_finish_deterministic_and_visible():
    a = np.array(_mini().to_pil())
    f1 = finish_frame(a, 7)
    f2 = finish_frame(a, 7)
    f3 = finish_frame(a, 8)
    assert (f1 == f2).all()
    assert np.abs(f1.astype(int) - a.astype(int)).sum() > 1000
    assert not (f1 == f3).all()


def _frame_hash(i):
    r = Renderer(160, 100, ss=1.0)
    r.canvas.drawRect(skia.Rect.MakeXYWH(0, 0, 160, 100),
                      fill_paint(hex_to_argb("#F6F1E8")))
    r.canvas.drawCircle(20 + i * 5, 50, 18, fill_paint(hex_to_argb("#B2542A")))
    return Renderer.sha256(r.png_bytes())


def test_pool_skia_order_and_determinism():
    r1 = pool_mod.render_range(_frame_hash, 0, 8, jobs=2)
    r2 = pool_mod.render_range(_frame_hash, 0, 8, jobs=1)
    assert r1 == r2 and len(set(r1)) == 8
