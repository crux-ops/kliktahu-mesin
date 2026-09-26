# KlikTahu — Mesin Render (Shorts + Long-form)

Mesin pembuat video edukasi KlikTahu:

- **Shorts** 1080×1920 · 60 fps — dari naskah VO + diagram kinetik (`episodes/`,
  `render.py`, `diagrams.py`). Render cepat via **GitHub Actions paralel**.
- **Long-form** 1920×1080 — animatic/storyboard bergerak 16:9 (`longform/`).
- **Riset topik** — sapuan kata kunci Google/YouTube Autocomplete (`analisis/`).
- **Pustaka** — metadata + teks siap tempel per episode (`pustaka/`).

## Struktur

```
.github/workflows/render.yml       render Shorts paralel (prep → render ×N → merge)
.github/workflows/preview.yml      cek cepat: 8 frame + montase (±1 menit)
.github/workflows/render-longform.yml  animatic 16:9
episodes/<slug>/
    content.json                   naskah + setelan per adegan (badge, aksen, visual, VO)
    config.env                     FPS, supersampling, bitrate, jumlah potongan, dll.
    audio_raw/*.wav                klip voice over (intro, f1..f6, outro)
    METADATA.md                    judul, deskripsi, tag, peta adegan
longform/<slug>/                   episode 16:9 (content.json + config.env + audio_raw/)
analisis/                          riset kata kunci + peringkat topik
pustaka/<episode>/                 METADATA.md + SIAP_TEMPEL.md per episode rilis
engine (root repo)                 render.py · diagrams.py · build_*.py · process_audio.py
                                   master_audio.py · qc_mp4.py · check_layout.py · mesin_util.py
tools/run_local.sh                 jalankan alur yang sama di komputer sendiri
```

## Cara render Shorts di GitHub Actions (disarankan)

1. Buka repo → tab **Actions** → **Render Shorts (paralel)** → **Run workflow**.
2. Isi: `episode` = slug folder (mis. `ep26_dinosaurus_punah`), `chunks` = `12`,
   `jobs` = `4`, lalu **Run workflow**.
3. Tunggu ±6–10 menit. Hasilnya muncul di:
   - **Artifacts** → `final-KlikTahu_Ep26_...` (mp4 + metadata)
   - **Releases** → otomatis dibuat, video bisa langsung diunduh

Atau dari terminal (pakai [GitHub CLI](https://cli.github.com), sudah login):

```bash
gh workflow run render.yml -f episode=ep26_dinosaurus_punah -f chunks=12 -f jobs=4
gh run watch                              # pantau sampai selesai
```

Ingin pratinjau dulu tanpa render penuh? Jalankan workflow
**Pratinjau cepat (QC visual)** — keluar montase 8 frame berlabel.

## Kenapa cepat

| | 1 proses lokal | GitHub Actions |
|---|---|---|
| Proses | 1 inti, urut | `chunks` (12) job paralel × `jobs` (4) proses per job |
| ±4.800 frame | ±68 menit | ±5–8 menit |
| Memori | terbatas di satu mesin | terbagi ke 12 mesin |

Setiap potongan langsung di-encode dengan setelan **sama** (`preset slow`,
`tune animation`, bitrate dari `config.env`), lalu digabung tanpa re-encode
(`concat -c copy`) — kualitas identik dengan render satu proses (frame hasil
paralel sudah diuji **bit-identical**).

## Menambah episode Shorts baru

1. Buat `episodes/<slug>/` → salin `content.json` + `config.env` dari episode
   sebelumnya sebagai template.
2. Taruh klip VO ke `audio_raw/` (nama: `intro.wav, f1..f6.wav, outro.wav` —
   sesuaikan dengan `id` adegan di `content.json`).
3. Sesuaikan `SPEED` (tempo VO santai ±1,10–1,13) dan `OUT_NAME`.
4. `ONLY=preview bash tools/run_local.sh <slug>` untuk cek tata letak,
   lalu render penuh via Actions.

## Menjalankan lokal (opsional)

```bash
pip install -r requirements.txt
bash tools/run_local.sh ep26_dinosaurus_punah                 # render penuh
ONLY=preview bash tools/run_local.sh ep26_dinosaurus_punah    # cuma pratinjau + audit tata letak
CHUNKS=6 JOBS=2 bash tools/run_local.sh ep26_dinosaurus_punah # lebih ringan
```

Catatan: render penuh lokal itu lambat (±1 jam). Pratinjau lokal + render penuh
di Actions adalah alur normal.

## Long-form 16:9

```bash
python3 longform/render_longform.py --episode ep01_besar_tapi_miskin --preview
python3 longform/render_longform.py --episode ep01_besar_tapi_miskin --render   # animatic mp4
```

atau via Actions → workflow **Render YouTube Long-form 16:9**. Detail:
`longform/README.md`.

## Riset topik berikutnya

```bash
python3 analisis/sapuan_besar.py     # tarik frasa autocomplete (butuh internet)
python3 analisis/analisis_mendalam.py  # gabung + skor 54 topik + 9 niche
```

Hasil terakhir: `analisis/HASIL_ANALISIS_TERBARU.md` (antrean Ep27-Ep36).
Paket metadata siap pakai: `analisis/PAKET_METADATA.md`.

## Catatan kualitas

- Shorts: 1080×1920 · 60 fps · H.264 high@4.2 · bitrate per `config.env`
- Supersampling 1,5× + penajam → teks & garis tetap tajam
- Audio: VO dinormalisasi, kompresor 2 lapis, loudnorm −14 LUFS, limiter, 0 clipping
- QC otomatis sebelum unggah: durasi, kesinkronan VO per adegan, margin aman
  elemen teks, dan korelasi audio MP4 vs master
