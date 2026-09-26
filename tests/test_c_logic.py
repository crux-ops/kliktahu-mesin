"""Uji logika murni Bagian C (tanpa model, tanpa media). Boleh jalan lokal."""
from kt.align import (Utterance, Word, check_monotonic, coverage,
                      normalize_token, utterances_to_srt, word_at_time,
                      words_in_range, words_of)


def _contoh():
    return [
        Utterance(0, 0.0, 1.2, "Jantung memompa", (
            Word("Jantung", 0.0, 0.5, 0.9),
            Word("memompa", 0.5, 1.2, 0.8))),
        Utterance(1, 1.5, 2.5, "darah merah", (
            Word("darah", 1.5, 2.0, 0.95),
            Word("merah", 2.0, 2.5, 0.7))),
    ]


def test_words_of_and_queries():
    ws = words_of(_contoh())
    assert [w.text for w in ws] == ["Jantung", "memompa", "darah", "merah"]
    assert word_at_time(ws, 0.25).text == "Jantung"
    assert word_at_time(ws, 1.3) is None  # jeda antar ujaran
    assert word_at_time(ws, 2.499).text == "merah"
    assert word_at_time(ws, 2.5) is None  # batas akhir eksklusif
    assert [w.text for w in words_in_range(ws, 0.4, 1.6)] == ["Jantung", "memompa", "darah"]
    assert words_in_range(ws, 9.0, 10.0) == []


def test_check_monotonic():
    assert check_monotonic(words_of(_contoh())) is True
    assert check_monotonic([Word("a", 1.0, 0.5)]) is False  # start > end
    assert check_monotonic([Word("a", 0.5, 1.0), Word("b", 0.0, 1.5)]) is False  # mundur
    assert check_monotonic([]) is True


def test_normalize_and_coverage():
    assert normalize_token("  Jantung,") == "jantung"
    assert normalize_token("MEMOMPA!") == "memompa"
    ws = words_of(_contoh())
    c = coverage("Jantung memompa darah merah", ws)
    assert (c["cocok"], c["total"], c["rasio"]) == (4, 4, 1.0)
    c2 = coverage("Jantung memompa darah merah muda", ws)
    assert (c2["cocok"], c2["total"]) == (4, 5)
    assert abs(c2["rasio"] - 0.8) < 1e-12
    c3 = coverage("apel jeruk", ws)
    assert (c3["cocok"], c3["rasio"]) == (0, 0.0)
    c4 = coverage("", [])
    assert c4["rasio"] == 1.0
    # urutan dibalik: LCS hanya 1 (tak dihitung penuh)
    rev = list(reversed(ws))
    c5 = coverage("Jantung memompa darah merah", rev)
    assert c5["cocok"] == 1


def test_srt_exact():
    srt = utterances_to_srt(_contoh())
    assert srt == ("1\n00:00:00,000 --> 00:00:01,200\nJantung memompa\n\n"
                   "2\n00:00:01,500 --> 00:00:02,500\ndarah merah\n")
    assert utterances_to_srt([]) == ""
