#!/usr/bin/env python3
"""Sapuan kata kunci besar: kumpulkan frasa, lalu peringkat per TEMA.

- Sumber: Google Autocomplete (hl=id) + YouTube Autocomplete (gl=id)
- Keluaran: analisis/klaster_besar.json (mentah) + tabel peringkat tema
"""
import json, re, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def sug(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=12) as r:
        txt = r.read().decode("utf-8", "ignore").strip()
    if txt.startswith("window.google.ac.h("):
        txt = txt[len("window.google.ac.h("):]
        txt = txt[: txt.rfind(")")]
    elif txt.startswith(")]}'"):
        txt = txt[4:].lstrip()
    data = json.loads(txt)
    if not isinstance(data, list) or len(data) < 2:
        return []
    out = []
    for s in data[1]:
        if isinstance(s, str):
            out.append(s)
        elif isinstance(s, list) and s and isinstance(s[0], str):
            out.append(s[0])
    return out


def g(q):
    time.sleep(0.22)
    try:
        return sug("https://suggestqueries.google.com/complete/search?client=firefox&hl=id&gl=id&q="
                   + urllib.parse.quote(q))
    except Exception:
        return []


def yt(q):
    time.sleep(0.22)
    try:
        return sug("https://suggestqueries-clients6.youtube.com/complete/search?client=youtube&ds=yt"
                   "&hl=id&gl=id&q=" + urllib.parse.quote(q))
    except Exception:
        return []


PREFIX = ("kenapa ", "kenapa ", "kenapa ")
AWALAN = ["lu", "di", "ka", "mi", "or", "ai", "bu", "ke", "ma", "pe", "ta", "si", "ha", "ge", "ku", "na"]
TOPIK = [
    "kenapa dinosaurus punah", "kenapa demam", "kenapa ngorok", "kenapa pesawat bisa terbang",
    "kenapa cegukan", "kenapa gunung meletus", "kenapa mimpi", "kenapa bulan berwarna merah",
    "kenapa kucing mengeong", "kenapa hujan", "kenapa gempa", "kenapa manusia menguap",
    "kenapa langit biru", "kenapa air laut asin", "kenapa es mengapung", "kenapa rambut memutih",
    "kenapa kita bermimpi", "kenapa jantung berdebar", "kenapa perut bunyi",
    "kenapa ponsel cepat panas", "kenapa baterai cepat habis", "kenapa internet lambat",
    "kenapa harga naik", "kenapa tidur mendengkur", "kenapa gigi berlubang", "kenapa kuping berdenging",
]
STOP = set("""yang dan di ke dari untuk pada dengan itu ini apa apakah kenapa bagaimana
saja aja tidak tak bukan bisa jadi ada adalah akan sudah belum lagi juga kalau kalo
sih deh ya kah nya lah pun per atau juga tapi oleh karena agar supaya buat sama
aku kamu kita kami mereka dia nya kita orang""".split())


def main():
    mentah = set()
    for a in AWALAN:
        for f in g("kenapa " + a) + yt("kenapa " + a) + yt(a):
            mentah.add(f.strip().lower())
    for t in TOPIK:
        for f in g(t) + yt(t):
            mentah.add(f.strip().lower())
    print(f"frasa unik: {len(mentah)}")

    # --- peringkat per TEMA: cari kata benda yang sering muncul lintas frasa ---
    kata = Counter()
    for f in mentah:
        for w in re.findall(r"[a-z]+", f):
            if w not in STOP and len(w) > 3:
                kata[w] += 1
    kandidat = [w for w, c in kata.items() if c >= 6]
    NIAT_POS = ("hari ini", "malam ini", "sekarang", "berbahaya", "bahaya", "aman", "kapan",
                "berapa", "cara", "apakah", "bisa", "kenapa")
    baris = []
    for w in kandidat:
        frasa = [f for f in mentah if re.search(r"\b" + re.escape(w) + r"\w*\b", f)]
        if len(frasa) < 6:
            continue
        niat = sum(1 for f in frasa if any(k in f for k in NIAT_POS))
        pendek = sum(1 for f in frasa if len(f.split()) <= 5)
        yt_ct = sum(1 for f in frasa if "kenapa" in f)
        skor = len(frasa) * 1.0 + pendek * 0.6 + niat * 0.8
        baris.append({"tema": w, "frasa": len(frasa), "pendek": pendek, "niat": niat,
                      "skor": round(skor, 1), "contoh": sorted(frasa)[:3]})
    baris.sort(key=lambda r: -r["skor"])
    print(f"\n{'skor':>7} {'frasa':>5} {'pendek':>6} {'niat':>5}  tema")
    for r in baris[:18]:
        print(f"{r['skor']:7.1f} {r['frasa']:5d} {r['pendek']:6d} {r['niat']:5d}  {r['tema']:16s} "
              f"{' | '.join(r['contoh'])[:66]}")
    json.dump({"total": len(mentah), "frasa": sorted(mentah), "peringkat": baris},
              open("/home/user/shorts/analisis/klaster_besar.json", "w"), ensure_ascii=False, indent=1)
    print("\ndisimpan: analisis/klaster_besar.json")


if __name__ == "__main__":
    main()
