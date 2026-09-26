#!/usr/bin/env python3
"""Audit tata letak KlikTahu — mesin v2.

Dua lapis pemeriksaan, keduanya otomatis:

  A. Kartu teks (layout card/hero/compare/steps/defs): hitung apakah isi muat di
     dalam kartu seperti sebelumnya.
  B. Adegan diagram: RENDER tiap adegan lalu UKUR tinta di zona margin aman
     (informasi untuk elemen grafis yang memang sengaja penuh layar).

  C. AUDIT PRESISI: setiap elemen TEKS/PIL dicatat kotaknya oleh mesin v2, jadi
     teks yang menyentuh margin aman bisa ditunjuk beserta isinya — bukan menebak.

Pakai:
  python3 check_layout.py            # kartu + audit piksel semua adegan
  python3 check_layout.py --kartu    # hanya pemeriksaan kartu (cepat)
  KT_AUDIT_MAX=150 python3 check_layout.py   # ambang tinta margin (default 150)
"""
import importlib.util, json, os, shutil, sys, tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
spec = importlib.util.spec_from_file_location("r", os.path.join(BASE, "render.py"))
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
r.SS = 1.0
r.SHARPEN = 0.0
import mesin_util

CARD_TOP, CARD_BOT = 452, 1452
SAFE_BOT = CARD_BOT - 30
AUDIT_MAX = float(os.environ.get("KT_AUDIT_MAX", "150"))   # satuan: piksel tinta @1080 lebar
m = mesin_util.SAFE_MARGIN   # margin aman (px @1080 lebar)


def check_card(sc):
    for tsz in (74, 68, 62, 56, 50):
        f = r.font(r.FB, tsz); L = r.wrap(sc["title"], f, 700)
        if len(L) <= 2: break
    y = 744 + len(L) * r.tlh(f) * 1.1
    has_chip = bool(sc.get("stat"))
    res = 150 if has_chip else 20
    for bsz in (38, 35, 32, 29):
        fb = r.font(r.FM, bsz); B = r.wrap(sc["body"], fb, 815)
        if y + 20 + len(B) * r.tlh(fb) * 1.45 + res <= SAFE_BOT: break
    total = y + 20 + len(B) * r.tlh(fb) * 1.45 + res
    return total, SAFE_BOT, f"judul {tsz}pt/{len(L)} baris, badan {bsz}pt/{len(B)} baris"


def check_hero(sc):
    ft = r.font(r.FB, 60); L = r.wrap(sc["title"], ft, 700)[:2]
    num, unit = r.stat_parts(sc.get("stat", ""))
    fh = r.font(r.FB, 150)
    fbd = r.font(r.FM, 36); B = r.wrap(sc["body"], fbd, 800)[:3]
    bottom = 1195 + len(B) * r.tlh(fbd) * 1.42
    return bottom, SAFE_BOT, f"angka {num or '-'} {unit}, badan {len(B)} baris, " \
                             f"lebar angka {r.tw(num+' '+unit, fh):.0f}px (maks 900)"


def check_compare(sc):
    worst, detail = 0, []
    for key in ("left", "right"):
        blk = sc.get(key, {})
        tf = r.font(r.FB, 44); T = r.wrap(blk.get("title", ""), tf, 382)
        bf = r.font(r.FM, 34); B = r.wrap(blk.get("body", ""), bf, 382)[:5]
        y = 800 + len(T) * r.tlh(tf) * 1.1 + 14 + len(B) * r.tlh(bf) * 1.42
        worst = max(worst, y)
        detail.append(f"{key}: judul {len(T)} br, badan {len(B)} br")
    return worst, SAFE_BOT, " | ".join(detail)


def check_defs(sc):
    fterm = r.font(r.FB, 40)
    fmean = r.font(r.FM, 37)
    y, detail = 700, []
    for it in sc.get("items", [])[:3]:
        n = len(r.wrap(it.get("meaning", ""), fmean, 830))
        detail.append(f"{it.get('term','?')}: {n} br")
        y += 64 + 26 + n * r.tlh(fmean) * 1.4 + 32
    return y, SAFE_BOT, f"{len(sc.get('items', [])[:3])} istilah ({', '.join(detail)})"


def check_steps(sc):
    n = min(4, len(sc.get("items", [])))
    f = r.font(r.FM, 40)
    heights = [len(r.wrap(it, f, 700)) for it in sc.get("items", [])[:4]]
    return 700 + 158 * n, SAFE_BOT, f"{n} langkah, baris teks {heights}"


def audit_piksel(tl, content_by_id, samples=3):
    """Render tiap adegan pada beberapa waktu, ukur tinta di margin aman."""
    total, scenes, meta = tl["total"], tl["scenes"], tl.get("meta", {})
    lead = float(tl.get("lead_in", 0.6))
    # samakan keadaan global seperti saat render sungguhan (brand, badge, latar)
    r.META = meta
    r.BG_MOON = meta.get("bg_element") == "moon"
    r.BG_SUN = meta.get("bg_element") == "sun"
    r.BG_METEOR = meta.get("bg_element") == "meteor"
    tmpd = tempfile.mkdtemp(prefix="kt_audit_")
    hasil = []
    try:
        for sc in scenes:
            c = content_by_id.get(sc["id"], {})
            vd = sc.get("vo_dur") or sc["dur"] * 0.5
            ts = [sc["start"] + max(0.25, lead * 0.5),
                  min(sc["start"] + lead + vd * 0.5, sc["start"] + sc["dur"] - 0.2),
                  max(sc["start"] + 0.25, sc["start"] + sc["dur"] - 0.35)]
            ts = sorted(set(round(x, 2) for x in ts))[:samples]
            worst, sisi_worst, contoh = 0, {}, []
            for t in ts:
                p = os.path.join(tmpd, f"{sc['id']}_{t:.2f}.png")
                r.render_frame(t, total, scenes, meta, p)
                hits, lokasi, sisi = mesin_util.ink_report(p, mesin_util.SAFE_MARGIN)
                if hits > worst:
                    worst, sisi_worst, contoh = hits, sisi, lokasi
            hasil.append({"id": sc["id"], "visual": c.get("visual", "-"),
                          "tinta": worst, "sisi": sisi_worst, "lokasi": contoh,
                          "t": ts})
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    return hasil


def audit_teks(tl, content_by_id):
    """Presisi: catat kotak semua elemen teks/pil, laporkan yang menembus margin."""
    total, scenes, meta = tl["total"], tl["scenes"], tl.get("meta", {})
    r.diagrams.TRACK = True
    tmpd = tempfile.mkdtemp(prefix="kt_teks_")
    hasil = []
    try:
        for sc in scenes:
            r.diagrams.LAYOUT.clear()
            # akhir scene: kamera kembali z=1 sehingga koordinat apa adanya
            t = max(sc["start"] + 0.2, sc["start"] + sc["dur"] - 0.2)
            r.render_frame(t, total, scenes, meta, os.path.join(tmpd, sc["id"] + ".png"))
            entries = list(r.diagrams.LAYOUT)
            bad = []
            for e in entries:
                x0, y0, x1, y1 = e["x0"], e["y0"], e["x1"], e["y1"]
                sisi = []
                if x0 < m: sisi.append(("kiri", m - x0))
                if x1 > 1080 - m: sisi.append(("kanan", x1 - (1080 - m)))
                if y0 < m: sisi.append(("atas", m - y0))
                if y1 > 1920 - m: sisi.append(("bawah", y1 - (1920 - m)))
                if sisi:
                    e = dict(e); e["sisi"] = sisi
                    bad.append(e)
            hasil.append({"id": sc["id"], "n": len(entries), "bad": bad})
    finally:
        r.diagrams.TRACK = False
        shutil.rmtree(tmpd, ignore_errors=True)
    return hasil


def main():
    kartu_saja = "--kartu" in sys.argv
    tl = json.load(open(os.path.join(BASE, "timeline.json")))
    content = json.load(open(os.path.join(BASE, "content.json")))
    by_id = {s["id"]: s for s in content["scenes"]}
    gagal = 0

    print("=== A. Kelengkapan kartu ===")
    print(f"{'scene':7s} {'layout':8s} {'isi':>7s} {'batas':>6s}  status  keterangan")
    for sc in tl["scenes"]:
        c = by_id.get(sc["id"], {})
        if c.get("visual"):
            print(f"{sc['id']:7s} {'diagram':8s} {'-':>7s} {'-':>6s}  ->      "
                  f"'{c['visual']}' (diperiksa pada audit piksel di bawah)")
            continue
        if sc["type"] != "fact":
            continue
        lay = c.get("layout", "card")
        fn = {"card": check_card, "hero": check_hero, "compare": check_compare,
              "steps": check_steps, "defs": check_defs}[lay]
        used, limit, info = fn(c)
        ok = used <= limit
        gagal += 0 if ok else 1
        print(f"{sc['id']:7s} {lay:8s} {used:6.0f}px {limit:5d}px  "
              f"{'OK' if ok else 'LEBIH'}    {info}")
    if kartu_saja:
        print("\nHASIL:", "kartu muat ✔" if gagal == 0 else f"{gagal} kartu melebihi batas ✘")
        sys.exit(0 if gagal == 0 else 1)

    print(f"\n=== B. Audit piksel (grafis penuh layar — informasi) ===")
    hasil = audit_piksel(tl, by_id)
    for h in hasil:
        sisi = ", ".join(f"{k}={v}" for k, v in h["sisi"].items() if v) or "-"
        ket = "OK" if h["tinta"] <= AUDIT_MAX else "banyak grafis di tepi (sengaja)"
        print(f"  {h['id']:7s} {h['visual']:14s} tinta {h['tinta']:5d}  {ket}   sisi: {sisi}")

    print(f"\n=== C. Audit presisi elemen teks (margin aman {m}px) ===")
    hasil = audit_teks(tl, by_id)
    for h in hasil:
        if h["bad"]:
            for e in h["bad"][:6]:
                sisi = ", ".join(f"{k} {d:.0f}px" for k, d in e["sisi"])
                print(f"  {h['id']:7s} {e['kind']:9s} menembus margin: {sisi:22s} "
                      f"\"{e['text']}\"")
            gagal += len(h["bad"])
        else:
            print(f"  {h['id']:7s} {h['n']:3d} elemen teks/pil  semua di dalam margin aman  OK")

    print("\nHASIL:", "tata letak bersih ✔ (semua elemen teks di dalam margin aman)" if gagal == 0
          else f"{gagal} temuan perlu diperbaiki ✘")
    sys.exit(0 if gagal == 0 else 1)


if __name__ == "__main__":
    main()
