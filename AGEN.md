# AGEN.md - Memori Proyek KlikTahu

> Dokumen hidup. Diperbarui setiap selesai satu bagian upgrade.
> Bahasa: Indonesia sederhana.

## Status proyek

- Repo: `crux-ops/kliktahu-mesin` (akun baru, repo publik).
- Tahap berjalan: **Tahap 0 SELESAI** - bersih-bersih warisan AI lama.
- Berikutnya: Tahap 1 (riset real-time), lalu Tahap 2 bagian A-J.
- Larangan: JANGAN membuat episode/video apa pun sampai pemilik memerintahkan.
- Semua render/pratinjau/sampel media HANYA di GitHub Actions. Tidak ada render di workspace chat.
- Uji logika murni tanpa media (syntax, import, matematika) boleh jalan lokal supaya tidak
  push beruntun; semua yang menghasilkan gambar/audio/video HANYA di GitHub.

## Aturan tetap (dari pemilik, jangan dilanggar)

1. TIDAK ADA KARAKTER: tanpa tokoh, maskot, wajah, figur kartun. Diagram organ tubuh boleh.
   Siluet polos tanpa wajah hanya untuk perbandingan ukuran.
2. Tanpa subtitle/caption berjalan. Tanpa musik (melodi/irama). Motion graphics, animasi,
   elemen, SFX, transisi harus ada dan lengkap.
3. 1 episode = 1 render = 1 rilis: semua aset lengkap sebelum render.
4. Satu suara narator pria bahasa Indonesia untuk semua episode. Audisi dulu dengan pemilik,
   lalu kunci ID suaranya di sini.
5. Fakta dari sumber kredibel. Topik sensitif/agama: jawab sainsnya, tidak menyerang keyakinan.
6. Tanpa dependensi berbayar/berlisensi tertutup. Semua aset bebas atau buatan sendiri.
7. Topik diblokir: kentut, ngiler, keringat & bau badan.
8. Permissions Actions minimal; tanpa aplikasi AI pihak ketiga lain; jangan push beruntun.

## ID suara narator

- Status: BELUM AUDISI. Audisi dengan pemilik sebelum episode pertama.

## Riwayat topik (judul episode lama - JANGAN DIULANG)

Dihapus pada Tahap 0 (26 Sep 2026):

- Ep23 - Kucing (judul persis hilang bersama akun lama)
- Ep24 - Kenapa Bulan Berwarna Merah?
- Ep25 - Kenapa Mimpi Cepat Lupa?
- Ep26 - Kenapa Dinosaurus Punah?

Diketahui pernah ada (file tidak ada di backup, informatif saja):

- Ep21 - Mimpi (dibahas + Ep25)
- Ep22 - Gempa

## Kemajuan upgrade

- [x] Tahap 0 (26 Sep 2026): hapus episodes/ep24-26, pustaka/Ep24-26, laporan & JSON analisis
      lama (18-19 Sep), script usang peringkat_topik.py. Diarahkan: tidak ada file DRAFT/PEMETA.
      longform/ lama DIPERTAHANKAN sampai pengganti lulus uji. analisis_mendalam.py dibuat
      mandiri (baca gabungan_frasa_2026-09-26.json), skor identik.
- [ ] Tahap 1: riset real-time (tren motion, retensi Shorts, versi pustaka, rekomendasi YouTube).
- [ ] A. Renderer (skia-python + deterministik + preview/final).
- [ ] B. Motion graphics & animasi (keyframe, kinetik, 15+ transisi, finishing sinematik).
- [ ] C. Sinkron kata (forced alignment word timestamps).
- [ ] D. SFX sintetis (tanpa musik) + ducking.
- [ ] E. Audio VO (pace 1,8-1,9 k/detik, -14 LUFS, QC isi hilang 30 ms).
- [ ] F. QC otomatis (zona aman UI, WCAG, frame diam, kedip, A/V sync, golden frame).
- [ ] G. Encode (H.264 High, bitrate riset terbaru, AAC 256k, faststart).
- [ ] H. Thumbnail 3 varian + METADATA 4 blok ASCII + komentar sematan.
- [ ] I. Mesin analisis pertumbuhan (autocomplete, trends, wiki, pesaing, velocity, hook).
- [ ] J. Otomasi GitHub Actions (Shorts 12 + Long 16 paralel, rilis otomatis, cron analisis).
- [ ] Demo 20 detik + laporan QC.

## Keputusan teknis

- (Tahap 0) File analisis 26 Sep (milik AI sesi ini, atas permintaan pemilik) DIPERTAHANKAN;
  yang dihapus hanya warisan AI lama. Koreksi bila pemilik ingin sebaliknya.
- (Tahap 0) longform/ lama dipertahankan sampai pengganti Tahap 2 lulus uji.
