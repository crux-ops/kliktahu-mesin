# Riset Teknologi 26 September 2026 (Tahap 1)

> Semua keputusan upgrade (Tahap 2 bagian A-J) mengacu ke dokumen ini.
> Sumber dicantumkan per poin. AGEN.md mencatat keputusan final.

## 1. Tren motion graphics & editing edukasi 2026

- **Tipografi kinetik = karakter utama.** Kata bergerak mengikuti irama, bukan hiasan.
  Membantu penonton tanpa suara (banyak yang menonton muted).
  (criticatv.com, garagefarm.net, graphicdesignjunction.com)
- **Liquid glass, glitch/surealis, grain & tekstur handmade.** Lawan tampilan "AI generik
  yang terlalu poles". Tekstur kertas/film + grain = terasa manusiawi.
  (garagefarm.net, hatchstudios.com, graphicdesignjunction.com)
- **Vertical-first.** Shorts/Reels/TikTok menentukan desain: stiker, pop-up text,
  swipe transition, split screen. (graphicdesignjunction.com)
- **Hybrid 2D/2.5D + loop.** Kedalaman berlapis, akhir video menyambung ke awal.
  (garagefarm.net, hatchstudios.com)
- **Keputusan:** spek Bagian B di perintah pemilik SUDAH selaras tren. Tambahan: kata kunci
  kinetik dirancang ganda sebagai penolong penonton muted (pengganti subtitle yang dilarang).

## 2. Retensi YouTube Shorts 2026

- **Hook < 1 detik, tanpa intro logo.** Frame pertama = hook. (getkoro.app, prepublish.ai)
- **Beat baru tiap 2-3 detik** (cut, zoom, teks, SFX); open loop tiap 10-15 detik;
  tengah video wajib padat (zona drop-off terbesar). (prepublish.ai, shortzly.com,
  influencers-time.com)
- **Akhiri dengan loop**, bukan pamit. Target APV 70-85%, >100% via replay.
  CTA "follow" dilarang di 10 detik pertama. (prepublish.ai, getkoro.app)
- **Durasi:** sweet spot 15-45 detik; format explainer boleh lebih panjang asal tiap
  4 detik ada informasi baru. (getkoro.app, influencers-time.com)
- **Zona aman UI 2026 (1080x1920):** konten kritis di tengah 1080x1350; bahaya =
  bawah ~450 px (caption/judul), kanan ~15% (tombol aksi), kiri minimal 50 px dari tepi.
  (getkoro.app)
- **Keputusan QC (Bagian F):** margin kritis atas 180 / bawah 480 / kanan 160 / kiri 60 px;
  deteksi frame diam >1 detik = GAGAL; outro default ramah-loop; target durasi episode
  baru 45-75 detik (kompromi antara sweet spot dan kebutuhan explainer).

## 3. Versi pustaka (PyPI, dicek 26 Sep 2026) + kecocokan sandbox

Sandbox: Python 3.11.2, pip -> PyPI terbuka. Runner GitHub: Ubuntu + Python 3.12.

| Pustaka | Versi terbaru | Status sandbox | Catatan |
|---|---|---|---|
| skia-python | 144.0.post2 (Skia m144) | pip OK, import butuh libEGL sistem (tak ada root di sandbox) | workflow wajib `apt install libegl1 libgl1 libfontconfig1`; render CPU offscreen |
| faster-whisper | 1.2.1 | wheel cp311 manylinux tersedia (+ ctranslate2 4.8.2, onnxruntime 1.30.0) | word timestamps bawaan; tanpa token HF; tanpa diarization (tak perlu) |
| pedalboard | 0.9.25 | install + import OK | EQ, reverb, limiter (Spotify, paten aman) |
| pyloudnorm | 0.2.0 | install + import OK | ITU-R BS.1770 untuk -14 LUFS |
| numpy | 2.4.6 | OK | semua di atas kompatibel numpy 2.x |
| pillow | 12.3.0 | OK | utilitas saja (bukan renderer utama) |
| imageio-ffmpeg | 0.6.0 | OK | ffmpeg biner statis |
| scipy | 1.17.1 | install + import OK | filter/sintesis SFX |
| soundfile | 0.14.0 | install + import OK | baca/tulis WAV |
| librosa | 0.11.0 | tidak diuji | TIDAK DIPAKAI (pedalboard+scipy cukup, lebih ringan) |

- **Keputusan alignment (Bagian C): faster-whisper** (word_timestamps + VAD, model small,
  int8 CPU), BUKAN WhisperX. Alasan: WhisperX (wav2vec2 sub-100ms + diarization) jauh
  lebih berat dan butuh token HuggingFace untuk pyannote; kebutuhan kita (kunci animasi
  ke kata, 1 narator) terpenuhi faster-whisper yang MIT + ringan CPU.
  (localaimaster.com, vexascribe.com, whipscribe.com)

## 4. Rekomendasi upload YouTube terbaru

- **Codec:** H.264 High, progressive, CABAC, GOP tertutup = setengah fps, 2 B-frame,
  yuv420p, moov di depan (faststart), MP4. Audio AAC-LC 48 kHz stereo.
  (support.google.com/youtube/answer/1722171)
- **Bitrate SDR (referensi YouTube):** 1080p30 = 8 Mbps, 1080p60 = 12 Mbps,
  1440p30 = 16 Mbps, 1440p60 = 24 Mbps. Praktisi 2026 memakai di ATAS referensi
  (1080p60: 12-15, ada yang 25-30 untuk gerak cepat) agar tahan kompresi ulang.
  (support.google.com, ffmpeg-cookbook.com 2026, vid-crush.com, pixflow.net, sfxengine.com)
- **Loudness:** -14 LUFS terintegrasi (semua sumber sepakat). Audio di atasnya
  diturunkan otomatis oleh YouTube.
- **Keputusan encode (Bagian G):** Shorts 1080x1920@60 = VBR target **14 Mbps**
  (maks 18); Long 1080p30 = 10 Mbps; opsi 1440p30 = 20 Mbps (memicu codec VP9/AV1
  YouTube yang lebih bagus); AAC 256k 48 kHz; faststart; GOP=30 (60fps) / 15 (30fps).

## Sumber (URL langsung)

- https://www.criticatv.com/motion-graphics-trends-how-visual-storytelling-is-evolving-in-2026/
- https://garagefarm.net/blog/animation-trends-to-watch
- https://graphicdesignjunction.com/2026/01/video-and-motion-creative-trends-2026/
- https://hatchstudios.com/top-video-and-animation-trends-to-know-in-2026/
- https://getkoro.app/blog/youtube-shorts-dimensions
- https://getkoro.app/blog/create-youtube-shorts
- https://prepublish.ai/guides/youtube-shorts-retention
- https://shortzly.com/blog/short-form-video-retention-strategies
- https://www.influencers-time.com/youtube-shorts-discovery-structuring-hook-pacing-and-payoff/
- https://support.google.com/youtube/answer/1722171?hl=en
- https://ffmpeg-cookbook.com/en/articles/youtube-ffmpeg-settings/
- https://vid-crush.com/blog/best-video-settings-youtube/
- https://pixflow.net/blog/best-export-settings-youtube-premiere-pro/
- https://sfxengine.com/blog/best-export-settings-for-youtube
- https://localaimaster.com/blog/whisperx-guide
- https://vexascribe.com/whisperx
- https://whipscribe.com/tools/faster-whisper
- https://pypi.org/pypi/skia-python/json (144.0.post2, butuh libEGL + fontconfig di Linux)
