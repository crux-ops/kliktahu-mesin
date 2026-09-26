#!/usr/bin/env python3
"""Analisis mendalam KlikTahu: skor multi-sinyal dari data frasa terpadu.

Masukan: gabungan_frasa_2026-09-26.json (1.420 frasa unik + provenance Google/YouTube,
hasil penggabungan 4 sumber sapuan 18-19 Sep 2026; file sumber lama sudah dibersihkan
pada Tahap 0 upgrade mesin).

Skor per TOPIK (0-100, transparan):
  VOL    (30%) volume permintaan: frasa unik + bonus frasa pendek + bobot lama
  CERUK  (25%) kecocokan ceruk: sains + visual + evergreen (kurasi terdokumentasi)
  NIAT   (15%) penanda niat: bahaya/aman/cara/kapan/berapa/hari ini/dsb
  LINTAS (10%) lintas mesin: % frasa muncul di Google DAN YouTube
  TONTON (10%) niat menonton: % frasa dari YouTube
  BARU   (10%) belum dibahas di episode mana pun

Keluaran:
  gabungan_frasa_2026-09-26.json  frasa terpadu + provenance
  skor_topik_2026-09-26.json      peringkat topik + semua sinyal
  skor_niche_2026-09-26.json      peringkat niche (agregasi topik)
"""
import json, os, re
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))

STOP = set("""yang dan di ke dari untuk pada dengan itu ini apa apakah kenapa
bagaimana saja aja tidak tak bukan bisa jadi ada adalah akan sudah belum lagi juga
kalau kalo sih deh ya kah nya lah pun per atau juga tapi oleh karena agar supaya
buat sama aku kamu kita kami mereka dia orang anak baru lama kecil besar banyak
sedikit saat setelah sebelum ketika harus ingin mau masih terus cepat padahal
sering habis naik turun bunyi sakit perut terjadi kurang hilang mata warna enak
keluar masuk tidak tidak kalau jika sangat paling amat begitu begini sini situ
sana mana tiap setiap antara tanpa dalam luar atas bawah samping punya milik
lebih paling sangat sekali dua tiga empat lima enam tujuh delapan sembilan
sepuluh pertama kedua hari tahun bulan minggu malam pagi siang sore""".split())

NIAT = ("hari ini", "malam ini", "sekarang", "terbaru", "berbahaya", "bahaya",
        "aman", "kapan", "berapa", "cara", "apakah", "padahal", "tiba-tiba",
        "terus menerus", "tidak berhenti", "normal", "wajar")

# ---------------------------------------------------------------- topik
# sains : 0-3 mekanisme bisa dijelaskan tuntas dari nol (3 = terbaik)
# visual: 0-3 potensi visual diagram penuh layar (3 = terbaik)
# ever  : 0 abadi, 1 sedikit musiman, 2 berita/musiman kuat (penalti)
TOPIK = {
 # --- tubuh manusia ---
 "ngorok":        dict(label="Kenapa Orang Ngorok?", niche="tubuh", kw=r"ngorok|mendengkur|dengkur", sains=3, visual=2, ever=0, covered=None),
 "demam":         dict(label="Kenapa Demam Naik Turun?", niche="tubuh", kw=r"demam|panas\w*\s*badan|suhu\s*tubuh", sains=3, visual=2, ever=0, covered=None),
 "cegukan":       dict(label="Kenapa Cegukan Tidak Berhenti?", niche="tubuh", kw=r"cegukan|hikcup", sains=2, visual=2, ever=0, covered=None),
 "uban":          dict(label="Kenapa Uban Tidak Boleh Dicabut?", niche="tubuh", kw=r"\buban\b|rambut\s*(putih|memutih)|beruban", sains=3, visual=2, ever=0, covered=None),
 "menguap":       dict(label="Kenapa Kita Menguap (dan Menular)?", niche="tubuh", kw=r"menguap|kuap", sains=2, visual=1, ever=0, covered=None),
 "mata":          dict(label="Kenapa Mata Berkedip?", niche="tubuh", kw=r"\bmata\b|berkedip|kedutan|kelilipan", not_kw=r"bunga mekar", sains=2, visual=2, ever=0, covered=None),
 "perut":         dict(label="Kenapa Perut Bunyi?", niche="tubuh", kw=r"perut\s*bunyi|perut\s*keroncongan|bab\s*keras|lambung", sains=2, visual=1, ever=0, covered=None),
 "jantung":       dict(label="Kenapa Jantung Berdebar?", niche="tubuh", kw=r"jantung\s*berdebar|jantung\s*berdetak|detak\s*jantung|dada\s*berdebar", sains=3, visual=2, ever=0, covered=None),
 "telinga":       dict(label="Kenapa Telinga Berdenging?", niche="tubuh", kw=r"telinga\s*berdenging|kuping\s*berdenging|berdenging|tinnitus", sains=2, visual=1, ever=0, covered=None),
 "jari_keriput":  dict(label="Kenapa Jari Keriput Kena Air?", niche="tubuh", kw=r"keriput", sains=2, visual=1, ever=0, covered=None),
 "gigi":          dict(label="Kenapa Gigi Berlubang?", niche="tubuh", kw=r"gigi\s*berlubang|gigi\s*bolong|sakit\s*gigi|karies", sains=2, visual=2, ever=0, covered=None),
 "bersin":        dict(label="Kenapa Kita Bersin?", niche="tubuh", kw=r"\bbersin\b", sains=2, visual=1, ever=0, covered=None),
 "merinding":     dict(label="Kenapa Merinding?", niche="tubuh", kw=r"merinding|bulu\s*kuduk", sains=2, visual=1, ever=0, covered=None),
 "keringat":      dict(label="Kenapa Berkeringat?", niche="tubuh", kw=r"keringat|keringatan", sains=2, visual=1, ever=0, covered=None),
 "tidur":         dict(label="Kenapa Kita Butuh Tidur?", niche="tubuh", kw=r"\btidur\b|begadang|insomnia|mengantuk", not_kw=r"ngorok|mendengkur|dengkur|\bmimpi\b|bermimpi", sains=3, visual=1, ever=0, covered=None),
 "otak":          dict(label="Bagaimana Cara Kerja Otak?", niche="tubuh", kw=r"otak\b", not_kw=r"botak", sains=3, visual=3, ever=0, covered=None),
 "darah":         dict(label="Kenapa Darah Berwarna Merah?", niche="tubuh", kw=r"darah\b|golongan\s*darah|donor\s*darah", sains=3, visual=2, ever=0, covered=None),
 "nasi_basi":     dict(label="Kenapa Nasi Cepat Basi?", niche="tubuh", kw=r"nasi\s*(cepat\s*)?(basi|bau|kering)|nasi\s*di\s*(magic|meji)", not_kw=r"jamblang|nasida", sains=2, visual=1, ever=0, covered=None),
 "luka":          dict(label="Kenapa Luka Bisa Sembuh (dan Gatal)?", niche="tubuh", kw=r"\bluka\b", not_kw=r"lukaku|luka\s+(hati|diri|disini)|diatas\s+luka", sains=3, visual=2, ever=0, covered=None),
 "kencing":       dict(label="Kenapa Air Kencing Berwarna Kuning?", niche="tubuh", kw=r"kencing", sains=2, visual=1, ever=0, covered=None),
 "makan_ngantuk": dict(label="Kenapa Habis Makan Ngantuk?", niche="tubuh", kw=r"habis\s*makan|sesudah\s*makan|setelah\s*makan", sains=2, visual=1, ever=0, covered=None),
 "lutut":         dict(label="Kenapa Lutut Bunyi Krek?", niche="tubuh", kw=r"\blutut\b", not_kw=r"ayam|kepala\s*pundak", sains=2, visual=1, ever=0, covered=None),
 "tindihan":      dict(label="Kenapa Ketindihan Saat Tidur?", niche="tubuh", kw=r"tindih|sleep\s*paralysis|\berep\b", sains=3, visual=2, ever=0, covered=None),
 "mimpi":         dict(label="mimpi (SUDAH: Ep21, Ep25)", niche="tubuh", kw=r"\bmimpi\b|bermimpi", sains=3, visual=2, ever=0, covered="Ep21, Ep25"),
 # --- antariksa ---
 "lubang_hitam":  dict(label="Apa Itu Lubang Hitam?", niche="antariksa", kw=r"lubang\s*hitam|black\s*hole", not_kw=r"berlubang", sains=3, visual=3, ever=0, covered=None),
 "aurora":        dict(label="Aurora: Kenapa Langit Bisa Menyala?", niche="antariksa", kw=r"aurora", sains=3, visual=3, ever=0, covered=None),
 "matahari":      dict(label="Seberapa Besar & Panas Matahari?", niche="antariksa", kw=r"matahari\b", not_kw=r"pelangi|takut pada matahari", sains=3, visual=3, ever=0, covered=None),
 "bintang":       dict(label="Seberapa Banyak Bintang di Langit?", niche="antariksa", kw=r"bintang\b", not_kw=r"persib|spanyol|bendera|mengirim|film|kejora", sains=2, visual=2, ever=0, covered=None),
 "ufo":           dict(label="UFO & Alien: Apa Kata Sains?", niche="antariksa", kw=r"\bufo\b|alien\b", sains=1, visual=2, ever=0, covered=None),
 "meteor":        dict(label="Kenapa Ada Hujan Meteor?", niche="antariksa", kw=r"meteor|komet\b|asteroid|bintang\s*jatuh", sains=3, visual=3, ever=1, covered=None),
 "bulan":         dict(label="bulan (SUDAH: Ep24)", niche="antariksa", kw=r"\bbulan\b", sains=3, visual=3, ever=1, covered="Ep24"),
 "gerhana":       dict(label="Kenapa Terjadi Gerhana?", niche="antariksa", kw=r"gerhana", sains=3, visual=3, ever=1, covered=None),
 # --- bumi & cuaca ---
 "petir":         dict(label="Kenapa Petir Menyambar?", niche="bumi", kw=r"petir|halilintar|guntur|gledek", not_kw=r"gen\s*halilintar", sains=3, visual=3, ever=0, covered=None),
 "hujan":         dict(label="Kenapa Hujan Bikin Sakit (dan Ada Petir)?", niche="bumi", kw=r"\bhujan\b", sains=3, visual=2, ever=1, covered=None),
 "gunung":        dict(label="Kenapa Gunung Meletus?", niche="bumi", kw=r"gunung\s*(meletus|berapi)|letusan|lahar|magma", sains=3, visual=3, ever=1, covered=None),
 "pelangi":       dict(label="Bagaimana Pelangi Terbentuk?", niche="bumi", kw=r"pelangi", sains=2, visual=3, ever=0, covered=None),
 "awan":          dict(label="Kenapa Awan Tidak Jatuh?", niche="bumi", kw=r"\bawan\b", sains=2, visual=2, ever=0, covered=None),
 "gempa":         dict(label="gempa (SUDAH: Ep22)", niche="bumi", kw=r"\bgempa\b", sains=3, visual=3, ever=2, covered="Ep22"),
 "langit_biru":   dict(label="Kenapa Langit Biru?", niche="bumi", kw=r"langit\s*biru", sains=2, visual=2, ever=0, covered=None),
 # --- laut & misteri ---
 "laut_asin":     dict(label="Kenapa Air Laut Asin?", niche="laut", kw=r"laut\s*asin|air\s*laut", sains=3, visual=2, ever=0, covered=None),
 "palung":        dict(label="Sedalam Apa Palung Mariana?", niche="laut", kw=r"palung|mariana|laut\s*dalam|dasar\s*laut", sains=3, visual=3, ever=0, covered=None),
 "segitiga":      dict(label="Misteri Segitiga Bermuda", niche="laut", kw=r"segitiga\s*bermuda|bermuda", sains=1, visual=2, ever=0, covered=None),
 "tsunami":       dict(label="Kenapa Terjadi Tsunami?", niche="laut", kw=r"tsunami", not_kw=r"black\s*hole", sains=3, visual=3, ever=2, covered=None),
 # --- purba ---
 "dinosaurus":    dict(label="dinosaurus (SUDAH: Ep26)", niche="purba", kw=r"dinosaurus|dino\b", sains=3, visual=3, ever=0, covered="Ep26"),
 "megalodon":     dict(label="Megalodon: Benarkah Masih Hidup?", niche="purba", kw=r"megalodon|mosasaurus|hiu\s*purba", not_kw=r"fish|fisch|20\d\d", sains=2, visual=3, ever=0, covered=None),
 # --- hewan ---
 "kucing":        dict(label="kucing (SUDAH: Ep23)", niche="hewan", kw=r"kucing\b", sains=2, visual=2, ever=0, covered="Ep23"),
 "anjing":        dict(label="Kenapa Anjing Menggonggong Tengah Malam?", niche="hewan", kw=r"anjing\b|menggonggong", sains=2, visual=1, ever=0, covered=None),
 "burung":        dict(label="Kenapa Burung Bisa Terbang?", niche="hewan", kw=r"burung\b", not_kw=r"dara|hantu|garuda|lovebird", sains=3, visual=2, ever=0, covered=None),
 "ayam":          dict(label="Kenapa Ayam Berkokok Pagi Hari?", niche="hewan", kw=r"\bayam\b|berkokok", not_kw=r"ngorok|mendengkur|harga", sains=2, visual=1, ever=0, covered=None),
 "nyamuk":        dict(label="Kenapa Nyamuk Suka Menggigit?", niche="hewan", kw=r"nyamuk", sains=2, visual=1, ever=0, covered=None),
 # --- fisika ---
 "pesawat":       dict(label="Kenapa Pesawat Berat Bisa Terbang?", niche="fisika", kw=r"pesawat\b", sains=3, visual=3, ever=0, covered=None),
 "kapal":         dict(label="Kenapa Kapal Besi Tidak Tenggelam?", niche="fisika", kw=r"kapal\b|tenggelam", not_kw=r"\bes\b", sains=3, visual=3, ever=0, covered=None),
 "gravitasi":     dict(label="Apa Itu Gravitasi?", niche="fisika", kw=r"gravitasi", sains=3, visual=2, ever=0, covered=None),
 "es_mengapung":  dict(label="Kenapa Es Mengapung?", niche="fisika", kw=r"es\s*(mengapung|mencair|batu)|mengapung", sains=2, visual=2, ever=0, covered=None),
 "listrik":       dict(label="Dari Mana Listrik Berasal?", niche="fisika", kw=r"listrik\b", sains=3, visual=2, ever=0, covered=None),
 "bom_atom":      dict(label="Bagaimana Bom Atom Bekerja?", niche="fisika", kw=r"bom\s*atom|nuklir\b", sains=3, visual=3, ever=0, covered=None),
 # --- teknologi ---
 "baterai":       dict(label="Kenapa Baterai HP Cepat Habis?", niche="teknologi", kw=r"baterai|batre", sains=2, visual=1, ever=0, covered=None),
 "hp_panas":      dict(label="Kenapa HP Cepat Panas?", niche="teknologi", kw=r"ponsel\s*cepat\s*panas|hp\s*panas|hp\s*lemot|sinyal\s*hp|hp\s*hilang|memori\s*hp", sains=1, visual=1, ever=0, covered=None),
 "internet":      dict(label="Kenapa Internet Lambat?", niche="teknologi", kw=r"internet\s*lambat|wifi\b|sinyal\b", sains=1, visual=1, ever=0, covered=None),
 "ai":            dict(label="Apa Itu Kecerdasan Buatan (AI)?", niche="teknologi", kw=r"kecerdasan\s*buatan|\bai\b|artificial", not_kw=r"khodijah", sains=2, visual=2, ever=0, covered=None),
 "roket":         dict(label="Bagaimana Roket Mendarat?", niche="teknologi", kw=r"roket\b", sains=3, visual=3, ever=0, covered=None),
 # --- sejarah & misteri lokal ---
 "misteri_gunung":dict(label="Misteri Gunung Nusantara (Padang/Lawu/Merapi)", niche="misteri", kw=r"misteri\s*gunung|gunung\s*(padang|lawu|merapi|kawi|gede|welirang|ciremai|salak|slamet|tidar)", not_kw=r"episode|full", sains=1, visual=2, ever=0, covered=None),
 "piramida":      dict(label="Bagaimana Piramida Dibangun?", niche="misteri", kw=r"piramida|pisa\b|candi\b", not_kw=r"doraemon", sains=2, visual=3, ever=0, covered=None),
}

NICHE_LABEL = {"tubuh": "Tubuh manusia", "antariksa": "Luar angkasa",
               "bumi": "Bumi & cuaca", "laut": "Laut & misteri", "purba": "Purba",
               "hewan": "Hewan", "fisika": "Fisika dasar", "teknologi": "Teknologi",
               "misteri": "Sejarah & misteri"}


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def main():
    F = {}  # frasa -> {G:bool, Y:bool, seeds:set, niche:set, bobot:float}
    G = json.load(open(os.path.join(BASE, "gabungan_frasa_2026-09-26.json")))
    for f, e in G.items():
        F[f] = {"G": bool(e["G"]), "Y": bool(e["Y"]), "seeds": set(e["seeds"]),
                "niche": set(e["niche"]), "bobot": float(e["bobot"])}

    print(f"frasa unik gabungan: {len(F)}")
    gy = sum(1 for e in F.values() if e["G"] and e["Y"])
    print(f"  berprovenance GY: {gy}, hanya-G: {sum(1 for e in F.values() if e['G'] and not e['Y'])}, "
          f"hanya-Y: {sum(1 for e in F.values() if e['Y'] and not e['G'])}, "
          f"tanpa provenance: {sum(1 for e in F.values() if not e['G'] and not e['Y'])}")

    # ---- skor per topik ----
    hasil = []
    for tid, t in TOPIK.items():
        rx = re.compile(t["kw"])
        nx = re.compile(t["not_kw"]) if t.get("not_kw") else None
        fs = [(f, F[f]) for f in F if rx.search(f) and not (nx and nx.search(f))]
        if not fs:
            hasil.append({"id": tid, **{k: t[k] for k in ("label", "niche", "covered")},
                          "jml": 0, "pendek": 0, "gy": 0, "y": 0, "niat": 0, "prov": 0,
                          "seeds": 0, "bobot": 0.0, "sekolah": 0, "islam": 0,
                          "hibur": 0, "sains": t["sains"],
                          "visual": t["visual"], "ever": t["ever"], "top_frasa": []})
            continue
        jml = len(fs)
        pendek = sum(1 for f, e in fs if len(f.split()) <= 5)
        both = sum(1 for f, e in fs if e["G"] and e["Y"])
        y_ct = sum(1 for f, e in fs if e["Y"])
        niat = sum(1 for f, e in fs if any(k in f for k in NIAT))
        prov = sum(1 for f, e in fs if e["G"] or e["Y"])
        sekolah = sum(1 for f, e in fs if re.search(r"kelas\s*\d|\bips\b|pelajaran|jelaskan|\btugas\b", f))
        islam = sum(1 for f, e in fs if "menurut islam" in f)
        hibur = sum(1 for f, e in fs if re.search(r"jokes|gombal|meme|teka\s*teki|lucu|viral|joke", f))
        seeds = len({s for f, e in fs for s in e["seeds"]}) or 1
        bobot = round(sum(e["bobot"] for f, e in fs), 1)

        def rank(f, e):
            s = (3 if e["G"] and e["Y"] else 0) + (1 if e["Y"] else 0)
            s += max(0, 7 - len(f.split()))
            s += 1.5 if any(k in f for k in NIAT) else 0
            s += e["bobot"] * 0.3
            return s
        top = sorted(fs, key=lambda fe: -rank(*fe))[:12]

        hasil.append({"id": tid, "label": t["label"], "niche": t["niche"],
                      "covered": t["covered"], "jml": jml, "pendek": pendek,
                      "gy": both, "y": y_ct, "niat": niat, "seeds": seeds,
                      "bobot": bobot, "prov": prov, "sekolah": sekolah, "islam": islam,
                      "hibur": hibur, "sains": t["sains"], "visual": t["visual"],
                      "ever": t["ever"],
                      "top_frasa": [{"f": f, "G": e["G"], "Y": e["Y"]} for f, e in top]})

    # Imputasi jujur: 833 frasa sapuan besar tidak menyimpan provenance mesin.
    # Topik tanpa frasa berprovenance memakai rata-rata global (didokumentasikan
    # di laporan), bukan nol. Topik tanpa frasa sama sekali tetap nol.
    _pv = [e for e in F.values() if e["G"] or e["Y"]]
    G_LINTAS = sum(1 for e in _pv if e["G"] and e["Y"]) / (len(_pv) or 1) * 10
    G_TONTON = sum(1 for e in _pv if e["Y"]) / (len(_pv) or 1) * 10
    print(f"  imputasi global: LINTAS={G_LINTAS:.2f} TONTON={G_TONTON:.2f} dari {len(_pv)} frasa berprovenance")

    # normalisasi 0-10 per komponen
    mx_jml = max(h["jml"] for h in hasil) or 1
    mx_pdk = max(h["pendek"] for h in hasil) or 1
    mx_nyt = max(h["niat"] for h in hasil) or 1
    for h in hasil:
        vol = (h["jml"] / mx_jml * 6 + h["pendek"] / mx_pdk * 4)
        ceruk = ((h["sains"] / 3 * 6 + h["visual"] / 3 * 4) if h["jml"] else 0)
        if h["ever"] == 1: ceruk -= 1.0
        if h["ever"] == 2: ceruk -= 2.5
        ceruk = max(0, ceruk)
        niat10 = h["niat"] / mx_nyt * 10
        if h["jml"] == 0:
            lintas, tonton = 0.0, 0.0
        elif h["prov"] == 0:
            lintas, tonton = G_LINTAS, G_TONTON
        else:
            lintas = h["gy"] / h["prov"] * 10
            tonton = h["y"] / h["prov"] * 10
        baru = 0.0 if h["covered"] else 10.0
        skor = vol * 0.30 + ceruk * 0.25 + niat10 * 0.15 + lintas * 0.10 + tonton * 0.10 + baru * 0.10
        h.update({"VOL": round(vol, 2), "CERUK": round(ceruk, 2), "NIAT10": round(niat10, 2),
                  "LINTAS": round(lintas, 2), "TONTON": round(tonton, 2),
                  "skor": round(skor * 10, 1)})
    hasil.sort(key=lambda h: -h["skor"])
    json.dump(hasil, open(os.path.join(BASE, "skor_topik_2026-09-26.json"), "w"),
              ensure_ascii=False, indent=1)

    print(f"\n{'skor':>6} {'jml':>4} {'pdk':>4} {'gy':>3} {'Y':>3} {'niat':>4} {'C':>4} {'S':>2} {'I':>2} {'H':>2}  topik")
    for h in hasil[:40]:
        flag = "SUDAH" if h["covered"] else ""
        print(f"{h['skor']:6.1f} {h['jml']:4d} {h['pendek']:4d} {h['gy']:3d} {h['y']:3d} "
              f"{h['niat']:4d} {h['CERUK']:4.1f} {h['sekolah']:2d} {h['islam']:2d} {h['hibur']:2d}  {h['id']:14s} {flag}")

    # ---- agregasi niche ----
    niche = {}
    for h in hasil:
        n = niche.setdefault(h["niche"], {"frasa_set": set(), "topik": [], "skor": []})
        n["topik"].append(h["id"]); n["skor"].append(h["skor"])
        for t in h["top_frasa"]:
            n["frasa_set"].add(t["f"])
    nlist = []
    for nid, n in niche.items():
        unscored_covered = [h for h in hasil if h["niche"] == nid and not h["covered"]]
        nlist.append({"niche": nid, "label": NICHE_LABEL[nid],
                      "topik_ct": len(n["topik"]),
                      "skor_rata": round(sum(n["skor"]) / len(n["skor"]), 1),
                      "skor_max": round(max(n["skor"]), 1),
                      "top3": [h["id"] for h in sorted(unscored_covered, key=lambda x: -x["skor"])[:3]]})
    nlist.sort(key=lambda x: -(x["skor_rata"] + x["skor_max"]))
    json.dump(nlist, open(os.path.join(BASE, "skor_niche_2026-09-26.json"), "w"),
              ensure_ascii=False, indent=1)
    print("\n== NICHE ==")
    for n in nlist:
        print(f"  {n['label']:18s} rata={n['skor_rata']:5.1f} max={n['skor_max']:5.1f} top3={n['top3']}")

    # ---- sinyal liar: kata sering yang belum masuk topik mana pun ----
    rx_all = re.compile("|".join(f"(?:{t['kw']})" for t in TOPIK.values()))
    c = Counter()
    ex = {}
    for f in F:
        if rx_all.search(f):
            continue
        for w in re.findall(r"[a-z]+", f):
            if w not in STOP and len(w) > 3:
                c[w] += 1
                ex.setdefault(w, []).append(f)
    print("\n== SINYAL LIAR (kata sering di luar topik, kandidat baru) ==")
    for w, ct in c.most_common(25):
        if ct >= 4:
            print(f"  {w:14s} {ct:3d}x  ex: {sorted(set(ex[w]))[:2]}")


if __name__ == "__main__":
    main()
