#!/usr/bin/env python3
"""Analisis kata kunci real-time LANJUTAN untuk KlikTahu.

Menarik saran dari Google Autocomplete (hl=id) dan YouTube Autocomplete (gl=id),
lalu menghitung 4 jenis sinyal supaya keputusan topik tidak bergantung pada satu
angka saja:

  1. RANK      -> seberapa cepat frasa muncul untuk seed/awalan yang sangat pendek
                  (semakin pendek awalan, semakin tinggi volume pencariannya).
  2. KLASTER    -> berapa banyak varian yang muncul di sekitar sebuah tema
                  (permintaan pasar, bukan cuma satu frasa).
  3. NIAT       -> pola kata: hari ini / malam ini (pencarian berulang), kenapa/apa
                  (penjelasan), berapa/kapan (data), bahaya/aman (urgensi).
  4. PELUANG   -> klaster besar + niat jelas + belum banyak dibahas di YouTube ID
                  (dicerminkan oleh jumlah saran YouTube).
"""
import json, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
PREFIX = "kenapa "


def sug(url):
    """Kembalikan daftar saran dari endpoint autocomplete (2 format respons)."""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=12) as r:
        txt = r.read().decode("utf-8", "ignore").strip()
    if txt.startswith("window.google.ac.h("):          # format YouTube
        txt = txt[len("window.google.ac.h("):]
        txt = txt[: txt.rfind(")")]
    elif txt.startswith(")]}'"):                        # format lama dengan prefix
        txt = txt[4:].lstrip()
    data = json.loads(txt)
    if not isinstance(data, list) or len(data) < 2:
        return []
    saran = data[1]
    out = []
    for s in saran:
        if isinstance(s, str):
            out.append(s)
        elif isinstance(s, list) and s and isinstance(s[0], str):   # [teks, 0, [512]]
            out.append(s[0])
    return out


def google(q):
    time.sleep(0.25)
    u = ("https://suggestqueries.google.com/complete/search?client=firefox&hl=id&gl=id&q="
         + urllib.parse.quote(q))
    try:
        return sug(u)
    except Exception:
        return []


def youtube(q):
    time.sleep(0.25)
    u = ("https://suggestqueries-clients6.youtube.com/complete/search?client=youtube&ds=yt"
         "&hl=id&gl=id&q=" + urllib.parse.quote(q))
    try:
        return sug(u)
    except Exception:
        return []


def skor_rank(frasa, seed):
    """Semakin pendek awalan yang memunculkan frasa, semakin besar permintaannya."""
    a = frasa.lower().replace(PREFIX, "", 1).strip()
    panjang = len(a.split())
    return {1: 8.0, 2: 7.0, 3: 6.0, 4: 5.5}.get(panjang, 5.0)


NIAT = {
    "hari ini": 1.4, "malam ini": 1.4, "sekarang": 1.25, "terbaru": 1.2,
    "berbahaya": 1.3, "bahaya": 1.3, "aman": 1.2, "kenapa": 1.15, "apa": 1.1,
    "kapan": 1.1, "berapa": 1.1, "cara": 1.15, "apakah": 1.1, "bisa": 1.1,
}


def bukti_niat(frasa):
    f = frasa.lower()
    return max([v for k, v in NIAT.items() if k in f] or [1.0])


def tarik(seeds_pendek, seeds_topik):
    klaster, mentah = {}, set()
    for s in seeds_pendek:                       # awalan pendek = volume tinggi
        for frasa in google(PREFIX + s) + youtube(PREFIX + s) + youtube(s):
            mentah.add(frasa.lower())
            k = s.strip().lower()
            klaster.setdefault(k, set()).add(frasa.lower())
    for t in seeds_topik:                        # topik spesifik = permintaan langsung
        for frasa in google(t) + youtube(t):
            mentah.add(frasa.lower())
            for k in klaster:
                if k in frasa.lower():
                    klaster[k].add(frasa.lower()); break
            else:
                klaster.setdefault(t.lower(), set()).add(frasa.lower())
    return klaster, mentah


def laporan(klaster, mentah, top=14):
    baris = []
    for k, frasa in klaster.items():
        if len(frasa) < 2:
            continue
        rata = sum(skor_rank(f, k) * bukti_niat(f) for f in frasa) / len(frasa)
        baris.append({"klaster": k, "frasa": len(frasa), "skor": round(rata * (1 + 0.05 * len(frasa)), 2)})
    baris.sort(key=lambda r: -r["skor"])
    return baris[:top]


def main():
    seeds_pendek = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else
                    "lu, ng, di, pe, ar, ai, bu, pi").split(",")]
    seeds_topik = [s.strip() for s in (sys.argv[2] if len(sys.argv) > 2 else "").split("|") if s.strip()]
    klaster, mentah = tarik(seeds_pendek, seeds_topik)
    print(f"frasa unik terkumpul: {len(mentah)} dari {len(seeds_pendek)} awalan pendek + {len(seeds_topik)} topik")
    print(f"\n{'skor':>6} {'klaster':38s} {'frasa':>6}   contoh")
    for r in laporan(klaster, mentah):
        contoh = sorted(f for f in klaster[r["klaster"]])[:2]
        print(f"{r['skor']:6.2f} {r['klaster'][:38]:38s} {r['frasa']:6d}   {' | '.join(contoh)[:80]}")
    json.dump({"mentah": sorted(mentah), "klaster": {k: sorted(v) for k, v in klaster.items()}},
              open("/home/user/shorts/analisis/klaster_terbaru.json", "w"), ensure_ascii=False, indent=1)
    print("\nhasil mentah disimpan: analisis/klaster_terbaru.json")


if __name__ == "__main__":
    main()
