#!/usr/bin/env python3
"""Peringkat TOPIK (bukan kata umum) dari hasil sapuan_besar.json.

Menghitung untuk setiap topik:
  - jml   : jumlah frasa unik yang menyebut topik itu (ukuran permintaan)
  - kuat  : frasa yang muncul dari awalan sangat pendek (indikasi volume besar)
  - niat  : frasa dengan penanda niat (hari ini, bahaya, cara, kapan, berapa)
  - sains : kecocokan dengan ceruk channel KlikTahu (mekanisme, bisa dijelaskan tuntas)
Skor  = jml + kuat*0.7 + niat*0.9 + sains*3
"""
import json, re
from collections import Counter

D = json.load(open("/home/user/shorts/analisis/klaster_besar.json"))
frasa = D["frasa"]

UMUM = set("""terus cepat padahal sering habis naik turun bunyi sakit perut terjadi kurang hilang
mata warna jadi enak keluar masuk tidak bisa kenapa apa cara orang anak baru lama
kecil besar banyak sedikit saat setelah sebelum ketika kalau kalo sih deh ya kah
harus ingin mau sudah belum masih juga lagi dari untuk pada dengan itu ini
""".split())

SAINS = {   # ceruk KlikTahu: mekanisme yang bisa dijelaskan tuntas & evergreen
    "dinosaurus": 3, "mimpi": 3, "bulan": 2.5, "gempa": 3, "gunung": 2.5, "hujan": 2.5,
    "petir": 2.5, "langit": 2.5, "pesawat": 2.5, "cegukan": 2, "ngorok": 2, "tidur": 2,
    "demam": 2, "kucing": 2, "jantung": 2, "darah": 2.5, "otak": 3, "mata": 2,
    "rambut": 1.5, "gigi": 1.5, "kuping": 1.5, "air": 2, "laut": 2.5, "es": 2,
    "baterai": 1.5, "hp": 1.5, "ponsel": 1.5, "internet": 1.5, "matahari": 3, "bintang": 3,
    "lubang": 2.5, "hitam": 1.5, "harga": 1, "api": 2, "asap": 2, "rokok": 1.5,
}
NIAT_POS = ("hari ini", "malam ini", "sekarang", "berbahaya", "bahaya", "aman", "kapan",
            "berapa", "cara", "apakah", "bisa", "padahal")

kata = Counter()
for f in frasa:
    for w in re.findall(r"[a-z]+", f):
        if len(w) > 3 and w not in UMUM:
            kata[w] += 1
kandidat = [w for w, c in kata.items() if c >= 8 and w not in UMUM]

baris = []
for w in kandidat:
    fs = [f for f in frasa if re.search(r"\b" + re.escape(w) + r"\w*\b", f)]
    if len(fs) < 8:
        continue
    kuat = sum(1 for f in fs if len(f.split()) <= 5)
    niat = sum(1 for f in fs if any(k in f for k in NIAT_POS))
    sains = SAINS.get(w, 0)
    skor = len(fs) + kuat * 0.7 + niat * 0.9 + sains * 3
    baris.append({"topik": w, "jml": len(fs), "kuat": kuat, "niat": niat, "sains": sains,
                  "skor": round(skor, 1), "contoh": sorted(fs)[:4]})
baris.sort(key=lambda r: -r["skor"])
print(f"{'skor':>7} {'jml':>4} {'kuat':>5} {'niat':>5} {'sains':>5}  topik")
for r in baris[:16]:
    print(f"{r['skor']:7.1f} {r['jml']:4d} {r['kuat']:5d} {r['niat']:5d} {r['sains']:5.1f}  {r['topik']:12s} "
          f"{' | '.join(r['contoh'])[:70]}")
json.dump(baris, open("/home/user/shorts/analisis/peringkat_topik.json", "w"), ensure_ascii=False, indent=1)
print("\ndisimpan: analisis/peringkat_topik.json")
