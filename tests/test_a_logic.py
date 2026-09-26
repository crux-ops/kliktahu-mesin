"""Uji logika murni Bagian A (tanpa Skia, tanpa media). Boleh jalan lokal."""
import hashlib

from kt import ENGINE_VERSION
from kt import pool as pool_mod
from kt import rng as rng_mod
from kt import spec as spec_mod


def test_engine_version():
    assert ENGINE_VERSION == 3


def test_formats():
    assert (spec_mod.SHORTS.w, spec_mod.SHORTS.h, spec_mod.SHORTS.fps) == (1080, 1920, 60)
    assert (spec_mod.LONG1080.w, spec_mod.LONG1080.h, spec_mod.LONG1080.fps) == (1920, 1080, 30)
    assert (spec_mod.LONG1440.w, spec_mod.LONG1440.h, spec_mod.LONG1440.fps) == (2560, 1440, 30)


def test_safe_zones():
    s = spec_mod.SAFE_SHORTS
    assert (s.top, s.bottom, s.left, s.right) == (180, 480, 60, 160)
    assert s.top + s.bottom < spec_mod.SHORTS.h


def test_encode_targets():
    t = spec_mod.ENCODE_TARGETS["shorts"]
    assert t.vbitrate == "14M" and t.gop == 30 and t.level == "4.2"
    assert spec_mod.LUFS_TARGET == -14.0 and spec_mod.TRUE_PEAK_MAX == -1.0


def test_rng_deterministic():
    a = rng_mod.spawn(5, "x").random()
    b = rng_mod.spawn(5, "x").random()
    c = rng_mod.spawn(6, "x").random()
    assert a == b and a != c
    assert rng_mod.seed_for(1) != rng_mod.seed_for(1, "beda")


def _shard(i):
    return hashlib.sha256(f"frame-{i}".encode()).hexdigest()


def test_pool_order_and_determinism():
    r1 = pool_mod.render_range(_shard, 0, 12, jobs=3)
    r2 = pool_mod.render_range(_shard, 0, 12, jobs=1)
    assert r1 == r2
    assert r1[0] == _shard(0) and len(r1) == 12
    assert pool_mod.render_range(_shard, 5, 5, jobs=2) == []
