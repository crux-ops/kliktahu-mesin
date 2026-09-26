#!/usr/bin/env python3
"""Analisis kata kunci REAL-TIME untuk metadata KlikTahu.

Menarik saran pencarian langsung dari Google (web) dan YouTube, menyaring
kata kunci "tercemar" (lagu, karaoke, game Harvest Moon, dsb.), lalu menyusun
rekomendasi kata kunci + kerangka judul berdasarkan niat pencarian.

Pakai:
    python3 analisis_metadata.py --seeds "bulan purnama 26 september 2026" \
        "fenomena langit september 2026" "jadwal bulan purnama 2026" \
        --topik "Purnama Panen 26 September 2026" \
        --out laporan_purnama_sept2026.md
"""
import argparse, datetime, json, os, re, sys, time, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (compatible; KlikTahuResearch/1.0)"}

# kata kunci yang "membajak" topik: audiens musik/game, bukan audiens edukasi
BLOCK = [
    "karaoke", " cover", "cover ", "lagu", "dangdut", "koplo", "reggae", "rock",
    "madu", "sutena", "ksatria", "pinaka", "tours", "mang barna", "rhoma", "dedi mulyadi",
    " emulator", "ps1", "ps2", "ps3", "ps4", "ps5", "psp", "nintendo", "back to nature",
    "save the homeland", "android", "apk", "cheat", "gameplay", "walkthrough",
    "reog", "harga emas", "antam", "live reog",
]
# penanda niat pencarian -> dipakai untuk menyusun judul
INTENT = {
    "jadwal": "JADWAL", "tanggal": "TANGGAL", "kapan": "TANGGAL",
    "jam berapa": "JAM", "jam": "JAM",
    "nama": "NAMA", "apa itu": "PENGERTIAN", "adalah": "PENGERTIAN",
    "cara": "CARA", "hari ini": "HARI INI", "malam ini": "HARI INI",
    "dimana": "LOKASI", "di mana": "LOKASI", "arah": "LOKASI",
    "kenapa": "PENJELASAN", "mengapa": "PENJELASAN", "sebab": "PENJELASAN",
}


def suggest(q, ds=None, hl="id", gl="id", timeout=12):
    p = {"client": "firefox", "hl": hl, "gl": gl, "q": q}
    if ds:
        p["ds"] = ds
    url = "https://suggestqueries.google.com/complete/search?" + urllib.parse.urlencode(p)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))[1]
    except Exception as e:
        print(f"  ! gagal ({e}) untuk '{q}'", file=sys.stderr)
        return []


def bersih(lst):
    out = []
    for s in lst:
        low = " " + s.lower() + " "
        if any(b in low for b in BLOCK):
            continue
        out.append(s)
    return out


def intents_of(term):
    t = term.lower()
    return sorted({lbl for key, lbl in INTENT.items() if key in t})


def analisis(seeds, topik, out_path):
    rows, gabung = [], {}
    print(f"== analisis real-time: {datetime.datetime.now():%d %b %Y %H:%M} ==")
    for seed in seeds:
        web = suggest(seed)
        yt = suggest(seed, ds="yt")
        time.sleep(0.35)
        web_b, yt_b = bersih(web), bersih(yt)
        rows.append({"seed": seed, "web": web, "yt": yt, "web_bersih": web_b, "yt_bersih": yt_b})
        for term in web_b + yt_b:
            key = term.lower().strip()
            gabung.setdefault(key, {"term": term, "sumber": set(), "dari": set()})
            gabung[key]["sumber"].add("Google" if term in web_b else "YouTube")
            gabung[key]["dari"].add(seed)
    # skor: muncul di 2 mesin + lebih banyak seed + ada niat jelas
    skor = []
    for k, v in gabung.items():
        s = len(v["sumber"]) * 3 + min(len(v["dari"]), 3) + len(intents_of(k)) * 1.5
        if k.startswith(topik.split()[0].lower()):
            s += 0.5
        skor.append((s, v["term"], sorted(v["sumber"]), intents_of(k)))
    skor.sort(reverse=True)

    L = []
    L.append(f"# Analisis Kata Kunci Real-Time\n")
    L.append(f"**Topik:** {topik}  \n**Waktu tarik data:** {datetime.datetime.now():%d %B %Y, %H:%M} WIB  \n")
    L.append(f"**Mesin:** Google Autocomplete (hl=id) + YouTube Autocomplete (ds=yt)\n")
    for r in rows:
        L.append(f"\n## Seed: `{r['seed']}`")
        for nama, key_raw, key_bersih in [("Google (web)", "web", "web_bersih"),
                                          ("YouTube", "yt", "yt_bersih")]:
            L.append(f"\n**{nama}** — {len(r[key_raw])} saran, {len(r[key_bersih])} lolos saringan:")
            if not r[key_raw]:
                L.append("- _(tidak ada saran = permintaan pencarian untuk frasa ini masih tipis)_")
            for s in r[key_raw]:
                tanda = "❌ tercemar" if s not in r[key_bersih] else "✅"
                L.append(f"- {tanda} `{s}`")
    L.append("\n## Kata kunci paling berpotensi (setelah saringan + skor)\n")
    L.append("| skor | kata kunci | terlihat di | niat pencarian |")
    L.append("|---:|---|---|---|")
    for s, term, src, it in skor[:18]:
        L.append(f"| {s:.1f} | `{term}` | {', '.join(src)} | {', '.join(it) or '—'} |")
    peta = {}
    for s, term, src, it in skor:
        for i in it:
            peta.setdefault(i, []).append(term)
    L.append("\n## Peta niat pencarian -> dipakai untuk menyusun judul\n")
    if not peta:
        L.append("- _(tidak ada penanda niat; judul pakai kata kunci utama saja)_")
    for i, terms in sorted(peta.items(), key=lambda x: -len(x[1])):
        L.append(f"- **{i}** ({len(terms)} kueri): " + ", ".join(f"`{t}`" for t in terms[:5]))
    txt = "\n".join(L)
    with open(out_path, "w") as f:
        f.write(txt + "\n")
    print(f"laporan -> {out_path}")
    print(f"\ntop 8 kata kunci:")
    for s, term, src, it in skor[:8]:
        print(f"  {s:5.1f}  {term}   [{', '.join(src)}]  {', '.join(it) or '-'}")
    return skor, peta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", required=True)
    ap.add_argument("--topik", default="")
    ap.add_argument("--out", default=os.path.join(BASE, "laporan.md"))
    a = ap.parse_args()
    analisis(a.seeds, a.topik, a.out)
