"""Uji logika murni Bagian D (numpy saja; tanpa media). Boleh jalan lokal."""
import numpy as np
import pytest

from kt import sfx as sfx_mod

TUJUH = ["whoosh", "pop", "thump", "snap", "swell", "zap", "sweep"]


def test_registry_tujuh_jenis():
    assert sorted(sfx_mod.SFX) == sorted(TUJUH)
    try:
        sfx_mod.render_sfx("tidak_ada")
    except ValueError:
        pass
    else:
        raise AssertionError("harusnya ValueError")


def test_semua_deterministik_dan_valid():
    for kind in TUJUH:
        a = sfx_mod.render_sfx(kind, seed=7)
        b = sfx_mod.render_sfx(kind, seed=7)
        assert a.dtype == np.float32 and a.ndim == 1
        assert np.array_equal(a, b), kind
        assert np.all(np.isfinite(a)), kind
        assert float(np.max(np.abs(a))) <= 1.0, kind
        assert sfx_mod.rms(a) > 0.005, f"{kind} nyaris sunyi"
        assert abs(a[0]) < 1e-6 and abs(a[-1]) < 1e-6, f"{kind} tak fade"


def test_durasi_tepat_sampel():
    for kind, dur in [("whoosh", 0.45), ("pop", 0.2), ("zap", 0.33)]:
        y = sfx_mod.render_sfx(kind, dur=dur)
        assert y.size == round(dur * sfx_mod.SR), kind


def test_seed_berpengaruh_kecuali_nada_murni():
    for kind in ("whoosh", "pop", "snap", "swell", "zap"):
        a = sfx_mod.render_sfx(kind, seed=7)
        b = sfx_mod.render_sfx(kind, seed=8)
        assert not np.array_equal(a, b), kind
    for kind in ("thump", "sweep"):
        a = sfx_mod.render_sfx(kind, seed=7)
        b = sfx_mod.render_sfx(kind, seed=99)
        assert np.array_equal(a, b), kind


def test_sweep_dua_arah_dan_gain():
    naik = sfx_mod.render_sfx("sweep", dur=0.3, arah="naik")
    turun = sfx_mod.render_sfx("sweep", dur=0.3, arah="turun")
    assert not np.array_equal(naik, turun)
    g = sfx_mod.render_sfx("pop", gain=0.5)
    p = sfx_mod.render_sfx("pop", gain=1.0)
    assert np.allclose(g, p * 0.5, atol=1e-7)


def test_place_posisi_tepat():
    sr = sfx_mod.SR
    pop = sfx_mod.render_sfx("pop", dur=0.1)
    track = sfx_mod.place(1.0, [(0.5, pop, 1.0)], sr)
    assert track.size == sr
    i = int(0.5 * sr)
    assert np.allclose(track[i:i + pop.size], pop)
    assert (track[:i] == 0).all()
    assert (track[i + pop.size:] == 0).all()
    # tumpuk dua klip: dijumlah
    t2 = sfx_mod.place(1.0, [(0.0, pop, 1.0), (0.0, pop, 0.5)], sr)
    assert np.allclose(t2[:pop.size], pop * 1.5)
    # klip di luar trek: diabaikan aman
    t3 = sfx_mod.place(0.5, [(9.0, pop, 1.0)], sr)
    assert (t3 == 0).all()


def test_duck_menunduk_di_bawah_vo():
    sr = sfx_mod.SR
    sfx = sfx_mod.render_sfx("swell", dur=2.0)
    vo = np.zeros(2 * sr, dtype=np.float32)
    vo[sr // 2:sr] = 0.5  # VO aktif detik 0.5-1.0
    ducked, gains = sfx_mod.duck_under(sfx, vo, sr, release_ms=60.0)
    assert ducked.shape == sfx.shape and gains.shape == sfx.shape
    assert float(gains.min()) < 0.5 and float(gains.max()) > 0.95
    # wilayah VO: SFX melemah; luar VO: utuh
    dalam = slice(int(0.6 * sr), int(0.9 * sr))
    luar = slice(int(1.5 * sr), int(1.9 * sr))
    assert sfx_mod.rms(ducked[dalam]) < sfx_mod.rms(sfx[dalam]) * 0.6
    assert np.allclose(ducked[luar], sfx[luar], atol=0.02)
    # mulus anti-klik: loncatan gain kecil
    assert float(np.max(np.abs(np.diff(gains)))) < 0.05
    # deterministik + sunyi aman
    d2, g2 = sfx_mod.duck_under(sfx, vo, sr, release_ms=60.0)
    assert np.array_equal(ducked, d2) and np.array_equal(gains, g2)
    hening, gh = sfx_mod.duck_under(sfx, np.zeros_like(sfx), sr)
    assert np.allclose(hening, sfx, atol=0.02)


def test_puncak_db_dan_pcm16():
    assert sfx_mod.peak_db(np.zeros(100)) == -120.0
    assert abs(sfx_mod.peak_db(np.array([0.5, -0.5])) - (-6.0206)) < 1e-3
    raw = sfx_mod.to_pcm16(np.array([0.0, 1.0, -1.0], dtype=np.float32))
    assert len(raw) == 6
    assert list(np.frombuffer(raw, dtype=np.int16)) == [0, 32767, -32767]


def test_jenis_sfx_selaras_transisi_b():
    try:
        import skia  # noqa: F401
    except ImportError:
        pytest.skip("butuh Skia (stub lokal/CI)")
    from kt.transitions import TX_EVENTS
    butuh = set()
    for evs in TX_EVENTS.values():
        for _t, kind, _g in evs:
            butuh.add(kind)
    assert butuh <= set(sfx_mod.SFX), f"kurang: {butuh - set(sfx_mod.SFX)}"
