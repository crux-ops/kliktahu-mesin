#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# KlikTahu — render lokal (alur sama persis dengan GitHub Actions)
#
#   bash tools/run_local.sh ep26_dinosaurus_punah                  # render penuh
#   ONLY=preview bash tools/run_local.sh ep26_dinosaurus_punah     # pratinjau + audit saja
#   CHUNKS=6 JOBS=2 bash tools/run_local.sh ep26_dinosaurus_punah  # lebih ringan
#
# Render penuh lokal itu lambat (±1 jam untuk ±80 detik @60fps). Untuk hasil
# cepat, pakai GitHub Actions (workflow "Render Shorts (paralel)") — lihat README.
# ---------------------------------------------------------------------------
set -euo pipefail

EP="${1:?pakai: bash tools/run_local.sh <slug_episode>  (contoh: ep26_dinosaurus_punah)}"
ONLY="${ONLY:-full}"
CHUNKS="${CHUNKS:-4}"
JOBS="${JOBS:-2}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

[ -f "episodes/$EP/config.env" ] || { echo "episode tidak ditemukan: episodes/$EP/config.env"; exit 1; }
# shellcheck disable=SC1090
source "episodes/$EP/config.env"

echo "==> episode: $EP ($EPISODE_TITLE)"
echo "==> mode: $ONLY | chunks: $CHUNKS | jobs: $JOBS"

python3 -c "import PIL, numpy, imageio_ffmpeg" 2>/dev/null \
  || { echo "dependensi belum ada — pasang dulu: pip install -r requirements.txt"; exit 1; }

# ---- prep: audio -> timeline -> audio master (sama dengan job prep di Actions)
cp "episodes/$EP/content.json" .
mkdir -p audio audio_proc build
cp "episodes/$EP/audio_raw/"*.wav audio/
export KT_BUILD=build
SPEED="$SPEED" python3 process_audio.py | tail -12
MAXDUR="$MAXDUR" python3 build_timeline.py | tail -8
SPEED="$SPEED" python3 build_audio.py | tail -4
python3 master_audio.py | tail -3

# ---- audit tata letak (gagal cepat kalau ada masalah)
python3 check_layout.py | tail -12

if [ "$ONLY" = "preview" ]; then
  python3 render.py --times auto --ss "$SS" --sharpen "$SHARPEN" --sheet --outdir build/preview | tail -12
  echo "==> pratinjau selesai: build/prev_sheet.png + build/preview/"
  exit 0
fi

# ---- render penuh: potongan berurutan (masing-masing multi-proses)
TOTAL=$(python3 -c "import json;print(int(round(json.load(open('timeline.json'))['total']*$FPS)))")
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
export KT_JOBS="$JOBS"
mkdir -p parts
PER=$(( (TOTAL + CHUNKS - 1) / CHUNKS ))
: > list.txt
for (( C=0; C<CHUNKS; C++ )); do
  LO=$(( C * PER )); HI=$(( LO + PER ))
  [ "$HI" -gt "$TOTAL" ] && HI=$TOTAL
  [ "$LO" -ge "$TOTAL" ] && break
  echo "==> potongan $C: frame $LO..$((HI-1)) ($((HI-LO)) frame)"
  rm -rf frames; mkdir -p frames
  python3 render.py --fps "$FPS" --ss "$SS" --sharpen "$SHARPEN" --jobs "$JOBS" \
                    --range "$LO:$HI" --outdir frames
  "$FF" -y -loglevel error -framerate "$FPS" -start_number "$LO" -i frames/f_%05d.png \
        -frames:v "$((HI-LO))" -an -c:v libx264 -preset "$PRESET" -tune "$TUNE" \
        -b:v "$VBITRATE" -maxrate "$MAXRATE" -bufsize "$BUFSIZE" -pix_fmt yuv420p \
        -profile:v high -level 4.2 "parts/part_$C.mp4"
  echo "file parts/part_$C.mp4" >> list.txt
done

# ---- gabung + mux audio + QC (sama dengan job merge di Actions)
export KT_AUDIO_SRC=build/audio_master.wav
"$FF" -y -loglevel error -f concat -safe 0 -i list.txt -c copy video_master.mp4
"$FF" -y -loglevel error -i video_master.mp4 -i build/audio_master.wav \
      -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a "$ABITRATE" -ar 48000 \
      -movflags +faststart -shortest "${OUT_NAME}.mp4"
python3 qc_mp4.py "${OUT_NAME}.mp4" | tail -25

mkdir -p dist
cp "${OUT_NAME}.mp4" dist/
cp "episodes/$EP/METADATA.md" dist/ 2>/dev/null || true
cp "episodes/$EP/content.json" "dist/${OUT_NAME}_content.json"
du -h dist/*
echo "==> SELESAI: dist/${OUT_NAME}.mp4"
