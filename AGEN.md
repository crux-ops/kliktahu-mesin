# AGEN.md - Memori Proyek KlikTahu

> Dokumen hidup. Diperbarui setiap selesai satu bagian upgrade.
> Bahasa: Indonesia sederhana.

## Status proyek

- Repo: `crux-ops/kliktahu-mesin` (akun baru, repo publik).
- Tahap berjalan: **Tahap 2D SELESAI** (26 Sep 2026). Berikutnya: Tahap 2E (audio VO + QC).
- Berikutnya: verifikasi bukti-A dari Actions, lalu Tahap 2B.
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

- Status: AUDISI BERJALAN. Kandidat A=piper id_ID-news_tts-medium (pria, MIT);
  B=chatterbox-id + prompt CV pria CC0 (Apache-2.0). Klip di bukti/2e-vo/ usai CI.

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
- [x] Tahap 1 (26 Sep 2026): riset real-time. Keputusan: pin skia-python 144.0.post2,
      faster-whisper 1.2.1 (bukan WhisperX), pedalboard 0.9.25, pyloudnorm 0.2.0,
      numpy 2.4.6, pillow 12.3.0, imageio-ffmpeg 0.6.0, scipy 1.17.1, soundfile 0.14.0;
      tanpa librosa. Zona aman QC: atas 180 / bawah 480 / kanan 160 / kiri 60 px.
      Encode: 1080p60 VBR 14 Mbps, 1080p30 10 Mbps, 1440p30 20 Mbps, AAC 256k,
      -14 LUFS, TP -1 dBTP. Target durasi episode baru 45-75 detik.
- [x] A. Renderer (26 Sep 2026): paket kt/ (spec, rng, pool, canvas, proof_a);
      13/13 uji hijau di CI; lembar bukti 1080x1920 deterministik di bukti/2a-renderer/;
      warna BGRA->RGBA terverifikasi; API Skia 144: Style kFill/kStroke_Style, drawImage paint=.
- [x] B. Motion graphics & animasi (26 Sep 2026): 15 easing, trek keyframe,
      kamera+guncang, kinetik (rise/pop/kata/ketik), 7 elemen, tilt pseudo-3D,
      19 transisi + titik sinkron SFX, letterbox + aberasi kromatik.
      28/28 uji hijau di CI; montase bukti/2b-motion/ deterministik.
      Pelajaran: MakeFromEncoded malas-decode -> wajib makeRasterImage selagi byte hidup.
- [x] C. Sinkron kata (26 Sep 2026): faster-whisper base int8 + VAD + stempel kata,
      Word/Utterance + kueri waktu + liputan LCS + SRT + prompt opsional.
      34/34 uji hijau di CI; bukti/2c-align/ deterministik (liputan 5/6=83%).
      Fixture: fixtures/bicara-id.mp3 (neural ID koma-jeda, 34KB).
      Pelajaran: espeak-ng id jelek (0/3); prompt transkrip 6/6 tapi ganda;
      koma-jeda 5/6 bersih -> dipakai + batas 0.8.
- [x] D. SFX sintetis + ducking (26 Sep 2026): 7 SFX numpy 48k selaras TX_EVENTS,
      place + duck_under sidechain + PCM16. 43/43 uji hijau di CI (9 D).
      bukti/2d-sfx/: gelombang berlabel + demo_sfx.wav + demo_duck.wav.
      Pelajaran: importorskip buta utk .so gagal-link (pakai try/except);
      follower gain wajib init=target[0] (anti fade awal).
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
