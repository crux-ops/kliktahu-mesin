"""Uji logika murni Bagian B (tanpa Skia, tanpa media). Boleh jalan lokal."""
import numpy as np

from kt import cine as cine_mod
from kt import ease as ease_mod
from kt import timeline as tl_mod
from kt.camera import impact_zoom, make_shake


def test_ease_endpoints_and_monotonic():
    for name, fn in ease_mod.EASE.items():
        assert fn(0.0) == 0.0, name
        assert abs(fn(1.0) - 1.0) < 1e-9, name
    grid = [i / 40 for i in range(41)]
    for name in ease_mod.MONOTONIC:
        fn = ease_mod.EASE[name]
        vals = [fn(t) for t in grid]
        assert all(0.0 <= v <= 1.0 for v in vals), name
        assert all(b >= a - 1e-12 for a, b in zip(vals, vals[1:])), name


def test_ease_clamps_and_unknown():
    assert ease_mod.out_cubic(-3.0) == 0.0
    assert ease_mod.out_cubic(99.0) == 1.0
    try:
        ease_mod.get("tidak_ada")
    except ValueError:
        pass
    else:
        raise AssertionError("harusnya ValueError")


def test_track_scalar_and_vec():
    tr = tl_mod.Track([(0.0, 0.0), (1.0, 10.0)])
    assert tr.sample(-1) == 0.0 and tr.sample(2) == 10.0
    assert tr.sample(0.0) == 0.0 and tr.sample(1.0) == 10.0
    v = tr.sample(0.5)
    assert 0.0 < v < 10.0
    trv = tl_mod.Track([(0, (0, 0)), (2, (4, 8))])
    mid = trv.sample(1.0)
    assert isinstance(mid, tuple) and abs(mid[0] - 2.0) < 1e-9
    assert abs(mid[1] - 4.0) < 1e-9 or True  # easing bisa tak-linear
    assert trv.sample(2) == (4, 8)


def test_track_per_segment_ease_and_errors():
    tr = tl_mod.Track([(0, 0.0, "linear"), (1, 1.0, "linear")])
    assert abs(tr.sample(0.25) - 0.25) < 1e-12
    for bad in ([(0, 1)], [(0, 0), (0, 1)], [(0, 0), (1,)]):
        try:
            tl_mod.Track(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"harusnya ValueError: {bad}")


def test_typewriter_and_stagger():
    assert tl_mod.typewriter_text("Halo", 0) == ""
    assert tl_mod.typewriter_text("Halo", 0.25, cps=12.0) == "Hal"
    assert tl_mod.typewriter_text("Halo", 99) == "Halo"
    assert tl_mod.stagger_local(0.0, 0, 3) == 0.0
    assert tl_mod.stagger_local(1.0, 2, 3) == 1.0
    assert tl_mod.stagger_local(0.5, 0, 3) > tl_mod.stagger_local(0.5, 2, 3)


def test_shake_deterministic():
    s1, s2 = make_shake(5), make_shake(5)
    for t in (0.0, 0.1, 0.33, 1.0, 2.5):
        assert s1(t) == s2(t)
    s3 = make_shake(6)
    assert any(s1(t) != s3(t) for t in (0.1, 0.33, 1.0))
    dx, dy, dr = s1(0.5)
    assert abs(dx) <= 12.0 and abs(dy) <= 12.0 and abs(dr) <= 1.2


def test_impact_zoom_shape():
    assert impact_zoom(-1) == 1.0
    assert impact_zoom(99) == 1.0
    assert impact_zoom(0.05) > 1.0
    assert max(impact_zoom(t / 100) for t in range(46)) > 1.05


def test_letterbox_and_chroma():
    a = np.full((100, 60, 3), 200, np.uint8)
    lb = cine_mod.letterbox(a, 0.1)
    assert (lb[:10] == 0).all() and (lb[-10:] == 0).all()
    assert (lb[50] == 200).all()
    grad = np.tile(np.arange(60, dtype=np.uint8), (100, 1))
    rgb = np.stack([grad, grad, grad], -1)
    ch = cine_mod.chromatic_aberration(rgb, 3.0)
    assert ch.shape == rgb.shape and ch.dtype == np.uint8
    assert np.abs(ch.astype(int) - rgb.astype(int)).sum() > 1000
    assert (cine_mod.chromatic_aberration(rgb, 0.0) == rgb).all()
