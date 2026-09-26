#!/usr/bin/env python3
"""Utilitas bersama mesin KlikTahu v2.

Tiga tugas yang sebelumnya dikerjakan manual (dan sering lupa):
  1. preview_times() — menentukan titik waktu pratinjau dari timeline, bukan diketik tangan.
  2. ink_report()    — mengukur "tinta" (teks/bentuk kuat) di zona margin aman,
                       supaya cacat tepi seperti kredit sumber mepet / label terpotong
                       ketahuan sebelum render penuh.
  3. sheet()         — montase berlabel (adegan + waktu) untuk pemeriksaan mata.

Dipakai oleh render.py, check_layout.py, dan qc_mp4.py.
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.join(BASE, "fonts")

# margin aman kanvas 1080x1920 (piksel pada skala 1080 lebar)
SAFE_MARGIN = 40


def preview_times(tl, tail=True):
    """Titik waktu pratinjau otomatis: tengah VO tiap adegan + frame akhir."""
    lead = float(tl.get("lead_in", 0.6))
    out = []
    for sc in tl["scenes"]:
        vd = sc.get("vo_dur") or (sc["dur"] * 0.5)
        t = sc["start"] + lead + vd * 0.5
        t = min(t, sc["start"] + sc["dur"] - 0.15)
        out.append({"scene": sc["id"], "t": round(max(0.0, t), 3)})
    if tail:
        out.append({"scene": "akhir", "t": round(max(0.0, tl["total"] - 0.2), 3)})
    return out


def _is_ink(p, thr_dark=205, thr_sat=70):
    """Piksel kuat: gelap (teks) atau berwarna pekat (bentuk)."""
    mx, mn = max(p), min(p)
    return mx < thr_dark or (mx - mn > thr_sat and mx < 240)


def ink_report(img, margin=SAFE_MARGIN):
    """Hitung piksel tinta di zona margin. Kembalikan (jumlah, contoh_lokasi, sisi).

    `img` boleh PIL.Image atau path. Margin diskalakan otomatis bila gambar
    lebih besar dari 1080 (supersample).
    """
    if isinstance(img, str):
        img = Image.open(img)
    rgb = img.convert("RGB")
    w, h = rgb.size
    m = int(round(margin * w / 1080.0))
    px = rgb.load()
    step = max(1, int(round(3 * w / 1080.0)))
    hits, lokasi = 0, []
    sisi = {"atas": 0, "bawah": 0, "kiri": 0, "kanan": 0}
    for x in range(0, w, step):
        for y in range(0, m, step):
            if _is_ink(px[x, y]):
                hits += 1; sisi["atas"] += 1
                if len(lokasi) < 4: lokasi.append((x, y))
        for y in range(max(0, h - m), h, step):
            if _is_ink(px[x, y]):
                hits += 1; sisi["bawah"] += 1
                if len(lokasi) < 4: lokasi.append((x, y))
    for y in range(0, h, step):
        for x in range(0, m, step):
            if _is_ink(px[x, y]):
                hits += 1; sisi["kiri"] += 1
                if len(lokasi) < 4: lokasi.append((x, y))
        for x in range(max(0, w - m), w, step):
            if _is_ink(px[x, y]):
                hits += 1; sisi["kanan"] += 1
                if len(lokasi) < 4: lokasi.append((x, y))
    # normalisasi ke skala 1080 lebar supaya ambang tetap sama antar-supersample
    skala = (1080.0 / w) ** 2
    return int(round(hits * skala)), lokasi, sisi


def sheet(entries, out_path, cols=4, panel_w=330, label_h=44):
    """Montase berlabel. entries = [(path_gambar, label), ...] -> satu PNG.

    Label (adegan · waktu) digambar di atas tiap panel supaya adegan bermasalah
    langsung bisa ditunjuk tanpa menebak urutan.
    """
    imgs = []
    for path, label in entries:
        if not os.path.exists(path):
            continue
        im = Image.open(path).convert("RGB")
        ph = int(round(panel_w * im.height / im.width))
        imgs.append((im.resize((panel_w, ph), Image.LANCZOS), label))
    if not imgs:
        return None
    ph = imgs[0][0].height
    rows = (len(imgs) + cols - 1) // cols
    W_ = panel_w * cols
    H_ = (ph + label_h) * rows
    sh = Image.new("RGB", (W_, H_), (255, 255, 255))
    dr = ImageDraw.Draw(sh)
    try:
        f = ImageFont.truetype(os.path.join(FDIR, "Poppins-SemiBold.ttf"), 22)
    except Exception:
        f = ImageFont.load_default()
    for i, (im, label) in enumerate(imgs):
        cx, cy = (i % cols) * panel_w, (i // cols) * (ph + label_h)
        dr.rectangle([cx, cy, cx + panel_w - 1, cy + label_h - 1], fill=(246, 241, 232))
        dr.text((cx + 12, cy + label_h / 2), label, font=f, fill=(24, 24, 31), anchor="lm")
        sh.paste(im, (cx, cy + label_h))
        dr.rectangle([cx, cy + label_h, cx + panel_w - 1, cy + label_h + ph - 1],
                     outline=(205, 198, 186))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    sh.save(out_path)
    return out_path


if __name__ == "__main__":
    import json, sys
    tl = json.load(open(os.path.join(BASE, "timeline.json")))
    print("titik pratinjau otomatis:")
    for e in preview_times(tl):
        print(f"  {e['scene']:8s} t={e['t']:6.2f}s")
