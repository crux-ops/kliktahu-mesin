"""Uji Skia Bagian B (Gerak & Transisi). Semua assert di memori + hash."""
import numpy as np
import skia

from kt import motion as mo_mod
from kt import transitions as tx_mod
from kt.camera import Camera, make_shake
from kt.canvas import Renderer, argb, fill_paint, hex_to_argb, star_path

W, H = 256, 160


def _scene(bg, cx, cy, label):
    r = Renderer(W, H, ss=1.0)
    c = r.canvas
    c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), fill_paint(hex_to_argb(bg)))
    c.drawCircle(cx, cy, 34, fill_paint(hex_to_argb("#F6F1E8")))
    c.drawPath(star_path(W - cx, H - cy, 30, 13), fill_paint(hex_to_argb("#18181F")))
    r.text.draw_center(c, W / 2, 22, label, "Poppins-Bold.ttf", 24,
                       argb(255, 255, 255, 255))
    return r


def _snap(renderer):
    return renderer.surface.makeImageSnapshot()


def _render_tx(fn, ia, ib, t, seed=7):
    r = Renderer(W, H, ss=1.0)
    fn(r.canvas, ia, ib, t, seed, W, H)
    return r.png_bytes()


def test_registry_min_15_with_valid_events():
    assert len(tx_mod.TX_NAMES) >= 15
    kinds = {"whoosh", "pop", "thump", "snap", "swell", "zap", "sweep"}
    for name in tx_mod.TX_NAMES:
        evs = tx_mod.TX_EVENTS[name]
        assert len(evs) >= 1, name
        for t01, kind, gain in evs:
            assert 0.0 <= t01 <= 1.0 and kind in kinds and 0.0 < gain <= 1.0
    try:
        tx_mod.get_tx("tidak_ada")
    except ValueError:
        pass
    else:
        raise AssertionError("harusnya ValueError")


def test_all_transitions_endpoints_exact():
    ra, rb = _scene("#B2542A", 70, 90, "ADEGAN-A"), _scene("#1F7A6D", 90, 70, "ADEGAN-B")
    ba, bb = ra.png_bytes(), rb.png_bytes()
    ia, ib = _snap(ra), _snap(rb)
    assert ba != bb
    for name in tx_mod.TX_NAMES:
        fn = tx_mod.get_tx(name)
        assert _render_tx(fn, ia, ib, 0.0) == ba, f"{name}@0"
        assert _render_tx(fn, ia, ib, 1.0) == bb, f"{name}@1"


def test_all_transitions_mid_differs_and_deterministic():
    ra, rb = _scene("#B2542A", 70, 90, "ADEGAN-A"), _scene("#1F7A6D", 90, 70, "ADEGAN-B")
    ba, bb = ra.png_bytes(), rb.png_bytes()
    ia, ib = _snap(ra), _snap(rb)
    for name in tx_mod.TX_NAMES:
        fn = tx_mod.get_tx(name)
        m1 = _render_tx(fn, ia, ib, 0.5)
        m2 = _render_tx(fn, ia, ib, 0.5)
        assert m1 == m2, f"{name} tak deterministik"
        if name == "cut":
            assert m1 == bb  # potongan keras: tepat di tengah sudah B
        else:
            assert m1 != ba and m1 != bb, f"{name}@0.5 sama dengan ujung"


def _kinetic_bytes(fn_name, t, **kw):
    r = Renderer(W, H, ss=1.0)
    r.canvas.drawRect(skia.Rect.MakeXYWH(0, 0, W, H),
                      fill_paint(hex_to_argb("#23232B")))
    fn = getattr(mo_mod, fn_name)
    if fn_name.startswith("kinetic"):
        fn(r.text, r.canvas, W / 2, H / 2, "GERAK", "Poppins-Bold.ttf", 40,
           argb(255, 246, 241, 232), t, **kw)
    elif fn_name == "bar_wipe":
        fn(r.canvas, 28, H / 2 - 14, W - 56, 28, 14, t, hex_to_argb("#C9A227"))
    elif fn_name == "circle_pop":
        fn(r.canvas, W / 2, H / 2, 50, t, hex_to_argb("#B2542A"))
    elif fn_name == "ring_pulse":
        fn(r.canvas, W / 2, H / 2, 10, 60, t, hex_to_argb("#1F7A6D"))
    elif fn_name == "spin_path":
        fn(r.canvas, star_path(W / 2, H / 2, 46, 20), W / 2, H / 2, t,
           hex_to_argb("#C9A227"))
    return r.png_bytes()


def test_kinetic_all_change_and_deterministic():
    for fn_name in ("kinetic_rise", "kinetic_pop", "kinetic_words", "bar_wipe",
                    "circle_pop", "ring_pulse", "spin_path"):
        b0 = _kinetic_bytes(fn_name, 0.0)
        b1 = _kinetic_bytes(fn_name, 1.0)
        b1b = _kinetic_bytes(fn_name, 1.0)
        assert b0 != b1, fn_name
        assert b1 == b1b, f"{fn_name} tak deterministik"


def test_tilt_center_invariant_and_visible():
    m = mo_mod.tilt_matrix(W, H, 0.6, -0.4)
    cx, cy = m.mapXY(W / 2.0, H / 2.0)
    assert abs(cx - W / 2.0) < 1e-6 and abs(cy - H / 2.0) < 1e-6
    x0, _ = m.mapXY(0.0, 0.0)
    assert abs(x0) > 1e-3  # sudut ikut bergeser
    r0 = _scene("#B2542A", 70, 90, "A")
    b0 = r0.png_bytes()
    r1 = _scene("#B2542A", 70, 90, "A")
    mo_mod.draw_tilted(r1.canvas, lambda: None, W, H, 0.0, 0.0)
    assert r1.png_bytes() == b0  # tilt nol = identik
    r2 = _scene("#B2542A", 70, 90, "A")
    # gambar ulang miring: render adegan ke citra lalu gambar miring
    img = _snap(_scene("#B2542A", 70, 90, "A"))
    r3 = Renderer(W, H, ss=1.0)
    r3.canvas.drawRect(skia.Rect.MakeXYWH(0, 0, W, H),
                       fill_paint(hex_to_argb("#23232B")))

    def _isi():
        r3.canvas.drawImage(img, 0, 0, paint=_opaque())
    mo_mod.draw_tilted(r3.canvas, _isi, W, H, 0.8, 0.5)
    assert r3.png_bytes() != b0
    assert mo_mod.flip_cos(0.0) == 1.0
    assert abs(mo_mod.flip_cos(0.5)) < 1e-9
    assert mo_mod.flip_cos(1.0) == -1.0
    assert mo_mod.parallax_offsets([0.0, 0.5, 1.0], 40.0) == [0.0, 20.0, 40.0]


def _opaque():
    p = skia.Paint()
    p.setAntiAlias(True)
    p.setAlpha(255)
    return p


def test_proof_sheet_deterministic_small():
    # Regresi: montase B harus byte-identik antar render (pernah goyang
    # karena citra malas-decode MakeFromEncoded + byte sementara).
    from kt.proof_b import draw_sheet
    outs = []
    for _ in range(2):
        r = Renderer(1080, 1920, ss=1.0, out_scale=0.125)
        draw_sheet(r, 7)
        outs.append(r.png_bytes())
    assert outs[0] == outs[1]


def test_camera_apply_deterministic():
    def _shot(cam, sh=None):
        r = Renderer(W, H, ss=1.0)
        r.canvas.drawRect(skia.Rect.MakeXYWH(0, 0, W, H),
                          fill_paint(hex_to_argb("#F6F1E8")))
        r.canvas.drawCircle(60, 60, 30, fill_paint(hex_to_argb("#B2542A")))
        img = _snap(r)
        r2 = Renderer(W, H, ss=1.0)
        r2.canvas.save()
        if sh is not None:
            dx, dy, dr = sh
            cam2 = Camera(cam.x + dx, cam.y + dy, cam.zoom, cam.rot + dr)
        else:
            cam2 = cam
        cam2.apply(r2.canvas, W, H)
        r2.canvas.drawImage(img, 0, 0, paint=_opaque())
        r2.canvas.restore()
        return r2.png_bytes()

    base = _shot(Camera())
    assert _shot(Camera()) == base
    assert _shot(Camera(x=30, zoom=1.2)) != base
    shk = make_shake(3)(0.5)
    assert _shot(Camera(), shk) != base
    assert _shot(Camera(), make_shake(3)(0.5)) == _shot(Camera(), shk)
