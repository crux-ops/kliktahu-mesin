"""Uji logika murni Seksi E (tanpa TTS/jaringan; jalan lokal + CI)."""
import numpy as np
import pytest

from kt import voice as V

SR = 48000


def nada(f=140.0, dur=2.0, sr=SR, amp=0.5):
    t = np.arange(int(round(dur * sr))) / float(sr)
    return (amp * np.sin(2 * np.pi * f * t)).astype(np.float32)


def nada_gerbang(f=140.0, dur=8.0, sr=SR, periode=1.0, nyala=0.5):
    """Nada bergerbang (pola bicara kasar) + rentang nyala."""
    t = np.arange(int(round(dur * sr))) / float(sr)
    gate = ((t % periode) < nyala).astype(np.float32)
    x = (0.5 * np.sin(2 * np.pi * f * t) * gate).astype(np.float32)
    spans = [(a, a + nyala) for a in np.arange(0, dur, periode)]
    return x, spans


def test_hitung_kata():
    assert V.hitung_kata("a  b\nc") == 3
    assert V.hitung_kata("") == 0
    assert V.hitung_kata(V.AUDITION_TEXT) == 16


def test_ukur_pace():
    assert V.ukur_pace(16, 8.0) == pytest.approx(2.0)
    assert V.ukur_pace(0, 5.0) == 0.0


def test_batas_pace():
    assert not V.pace_ok(1.79)
    assert V.pace_ok(1.8)
    assert V.pace_ok(1.85)
    assert V.pace_ok(1.9)
    assert not V.pace_ok(1.91)


def test_ke_48k():
    x = nada(220.0, 1.0, 22050)
    y = V.ke_48k(x, 22050)
    assert len(y) == SR
    z = V.ke_48k(nada(dur=0.5), SR)
    assert len(z) == SR // 2


def test_regang_ke_pace():
    pytest.importorskip("pedalboard")
    x = nada(220.0, 2.0)
    y = V.regang_ke_pace(x, SR, 2.0, 1.85)
    assert len(y) == pytest.approx(len(x) * 2.0 / 1.85, rel=0.02)
    assert V.f0_median(y, SR) == pytest.approx(220.0, abs=5.0)  # nada terjaga
    assert np.array_equal(y, V.regang_ke_pace(x, SR, 2.0, 1.85))  # deterministik


def test_regang_identitas():
    pytest.importorskip("pedalboard")
    x = nada(dur=1.0)
    assert np.array_equal(V.regang_ke_pace(x, SR, 1.85, 1.85), x)


def test_lufs():
    pytest.importorskip("pyloudnorm")
    x, _ = nada_gerbang()
    assert V.ukur_lufs(x, SR) < 0.0
    y = V.normalisasi_lufs(x, SR)
    assert V.ukur_lufs(y, SR) == pytest.approx(-14.0, abs=0.1)
    assert np.array_equal(y, V.normalisasi_lufs(x, SR))


def test_lufs_sunyi():
    pytest.importorskip("pyloudnorm")
    assert V.ukur_lufs(np.zeros(4800, dtype=np.float32), SR) == float("-inf")


def test_jaga_puncak():
    panas = nada(440.0, 0.5, amp=0.95)
    y, p, s = V.jaga_puncak(panas)
    assert s and p == pytest.approx(-1.0) and V.puncak_db(y) <= -1.0
    dingin = nada(440.0, 0.5, amp=0.5)
    y2, p2, s2 = V.jaga_puncak(dingin)
    assert not s2 and np.array_equal(y2, dingin)


def _sinyal_celah():
    x = np.zeros(2 * SR, dtype=np.float32)
    x[int(0.3 * SR):int(1.7 * SR)] = nada(200.0, 1.4)
    x[int(0.60 * SR):int(0.62 * SR)] = 0.0  # 20 ms -> abaikan
    x[int(1.00 * SR):int(1.06 * SR)] = 0.0  # 60 ms -> celah
    return x


def test_celah_tanpa_rentang():
    qc = V.celah_hilang(_sinyal_celah(), SR)
    assert qc["awal_suara"] == pytest.approx(0.3, abs=0.02)
    assert qc["akhir_suara"] == pytest.approx(1.7, abs=0.02)
    assert len(qc["celah"]) == 1
    a, b, d = qc["celah"][0]
    assert (a, b) == (pytest.approx(1.0, abs=0.02),
                      pytest.approx(1.06, abs=0.02))
    assert d == pytest.approx(0.06, abs=0.02)
    assert qc["n_hilang"] == 0  # tanpa rentang tak bisa vonis


def test_celah_dengan_rentang():
    x = _sinyal_celah()
    qc = V.celah_hilang(x, SR, [(0.9, 1.2)])
    assert qc["n_hilang"] == 1 and qc["maks_hilang"] == pytest.approx(0.06, abs=0.02)
    qc2 = V.celah_hilang(x, SR, [(0.3, 0.5)])
    assert qc2["n_hilang"] == 0 and len(qc2["jeda"]) == 1
    # tepi kata (erosi 30 ms): tengah celah di luar inti -> jeda
    qc3 = V.celah_hilang(x, SR, [(0.5, 1.04)])
    assert qc3["n_hilang"] == 0 and len(qc3["jeda"]) == 1


def test_celah_sunyi():
    qc = V.celah_hilang(np.zeros(SR, dtype=np.float32), SR)
    assert qc["awal_suara"] is None and qc["celah"] == []


def test_f0():
    assert V.f0_median(nada(120.0, 1.0), SR) == pytest.approx(120.0, abs=3.0)
    assert V.f0_median(nada(220.0, 1.0), SR) == pytest.approx(220.0, abs=3.0)
    assert V.f0_median(np.zeros(SR, dtype=np.float32), SR) is None


def test_f0_oktaf():
    # tiruan suara pria: H1 lemah, harmonik kuat -> tetap ~130, bukan 260
    t = np.arange(2 * SR) / float(SR)
    x = (0.3 * np.sin(2 * np.pi * 130 * t)
         + 1.0 * np.sin(2 * np.pi * 260 * t)
         + 0.8 * np.sin(2 * np.pi * 390 * t)
         + 0.5 * np.sin(2 * np.pi * 520 * t)).astype(np.float32) / 2.6
    assert V.f0_median(x, SR) == pytest.approx(130.0, abs=8.0)
    # nada murni tak ikut terkoreksi turun
    assert V.f0_median(nada(220.0, 1.0), SR) == pytest.approx(220.0, abs=3.0)


def test_batas_lunak():
    panas = nada(440.0, 0.5, amp=1.5)
    y = V.batas_lunak(panas)
    assert V.puncak_db(y) <= -1.0 + 1e-9
    assert np.array_equal(y, V.batas_lunak(panas))
    dingin = nada(440.0, 0.5, amp=0.3)  # di bawah lutut -> tak tersentuh
    assert np.array_equal(V.batas_lunak(dingin), dingin)


def test_gender():
    assert V.tebak_gender(140.0) == "pria"
    assert V.tebak_gender(159.9) == "pria"
    assert V.tebak_gender(170.0) == "tak-pasti"
    assert V.tebak_gender(200.0) == "wanita"
    assert V.tebak_gender(None) == "tak-pasti"


def test_rantai_vo():
    pytest.importorskip("pedalboard")
    pytest.importorskip("pyloudnorm")
    x, spans = nada_gerbang(dur=8.0)  # 16 "kata" dalam 8 dtk -> pace 2,0
    faktor = 2.0 / 1.85
    spans_r = [(a * faktor, b * faktor) for a, b in spans]
    r = V.rantai_vo(x, SR, 16, spans_r)
    assert r["pace_awal"] == pytest.approx(2.0, abs=0.01)
    assert r["pace_akhir"] == pytest.approx(1.85, abs=0.03)
    assert r["lufs_akhir"] == pytest.approx(-14.0, abs=0.5)
    assert r["puncak_db"] <= -1.0
    assert r["f0_median"] == pytest.approx(140.0, abs=5.0)
    assert r["gender"] == "pria"
    assert r["qc"]["n_hilang"] == 0
    assert r["lolos"]
    r2 = V.rantai_vo(x, SR, 16, spans_r)
    assert np.array_equal(r["y"], r2["y"])
