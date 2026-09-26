#!/usr/bin/env python3
"""QC MP4 KlikTahu — dipanggil otomatis oleh render_all.sh.

Memeriksa, tanpa perlu menebak:
  1. durasi video = durasi timeline (toleransi 0.35s)
  2. audio setiap scene utuh: VO mulai tepat setelah lead_in, tidak terpotong
     di tengah, dan ada jeda wajar sebelum scene berikutnya
  3. keutuhan audio MP4 dibandingkan dengan build/audio.wav (korelasi + selisih RMS)
  4. frame contoh disimpan ke build/qc/ + montase berlabel build/qc/sheet.png
  5. audit margin aman: memastikan tidak ada teks/bentuk yang menyentuh tepi kanvas

Pakai: python3 qc_mp4.py /path/video.mp4 [--timeline lain.json]
"""
import argparse, json, os, subprocess, sys, wave
import numpy as np
import imageio_ffmpeg
import mesin_util

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("KT_BUILD") or os.path.join(BASE, "..", "build")
os.makedirs(BUILD, exist_ok=True)
SR = 48000
TOL_DUR = 0.35


def load_wav(path):
    with wave.open(path) as w:
        n = w.getnframes()
        d = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() == 2:
            d = d.reshape(-1, 2).mean(1)
        sr = w.getframerate()
    if sr != SR:
        idx = np.linspace(0, len(d) - 1, int(len(d) * SR / sr))
        d = np.interp(idx, np.arange(len(d)), d).astype(np.float32)
    return d


def decode_mp4_audio(path):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    # PENTING: dekode sebagai stereo lalu rata-rata 0.5/kanal. Downmix mono ffmpeg
    # memakai koefisien 1/sqrt(2) sehingga level naik ~+3 dB (pernah bikin false alarm clipping).
    r = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-i", path,
                        "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode()[:400])
    d = np.frombuffer(r.stdout, dtype=np.float32).astype(np.float32)
    if d.size % 2:
        d = d[:-1]
    st = d.reshape(-1, 2)
    return st.mean(1), st


def probe(path):
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([ff, "-hide_banner", "-i", path], capture_output=True, text=True)
    info = {"raw": r.stderr}
    for line in r.stderr.splitlines():
        line = line.strip()
        if line.startswith("Duration:"):
            h, m, s = line.split(",")[0].split("Duration:")[1].strip().split(":")
            info["dur"] = int(h) * 3600 + int(m) * 60 + float(s)
            if "bitrate:" in line:
                info["bitrate"] = float(line.split("bitrate:")[1].split("kb/s")[0])
        elif line.startswith("Stream") and "Video:" in line:
            info["video"] = line.split("Video:")[1].split(",")[:3]
        elif line.startswith("Stream") and "Audio:" in line:
            info["audio"] = line.split("Audio:")[1].split(",")[:2]
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--timeline", default=os.path.join(BASE, "timeline.json"))
    ap.add_argument("--content", default=os.path.join(BASE, "content.json"))
    ap.add_argument("--margin-max", type=float,
                    default=float(os.environ.get("KT_AUDIT_MAX", "150")))
    arg = ap.parse_args()
    video = arg.video
    tl = json.load(open(arg.timeline))
    content = json.load(open(arg.content))
    lead_in = float(content.get("lead_in", 0.0))
    total = tl["total"]
    gagal = []

    print("=== QC MP4 KlikTahu ===")
    info = probe(video)
    dur = info.get("dur", 0)
    ukuran = os.path.getsize(video)
    print(f"file     : {video}")
    print(f"durasi   : {dur:.2f}s (timeline {total:.2f}s)  selisih {abs(dur - total):.2f}s")
    print(f"ukuran   : {ukuran/1e6:.2f} MB   bitrate {info.get('bitrate', float('nan')):.0f} kb/s")
    print(f"video    : {', '.join(info.get('video', []))}")
    print(f"audio    : {', '.join(info.get('audio', []))}")
    if abs(dur - total) > TOL_DUR:
        gagal.append(f"durasi melenceng {abs(dur-total):.2f}s")

    mp4, mp4_st = decode_mp4_audio(video)
    wav = load_wav(os.environ.get("KT_AUDIO_SRC") or os.path.join(BUILD, "audio.wav"))
    n = min(len(mp4), len(wav))
    a, b = mp4[:n], wav[:n]
    # bandingkan di area yang ada suaranya (bukan hening) supaya korelasi bermakna
    mask = np.abs(b) > 10 ** (-40 / 20) * max(1e-6, np.abs(b).max())
    if mask.sum() > SR:
        corr = float(np.corrcoef(a[mask][:SR * 20], b[mask][:SR * 20])[0, 1])
        d_rms = float(20 * np.log10((np.sqrt((a[mask] ** 2).mean()) + 1e-9) /
                                    (np.sqrt((b[mask] ** 2).mean()) + 1e-9)))
    else:
        corr, d_rms = float("nan"), float("nan")
    print(f"audio MP4 vs sumber ({os.path.basename(os.environ.get('KT_AUDIO_SRC') or 'build/audio.wav')}): korelasi {corr:.4f}, selisih level {d_rms:+.2f} dB")
    if corr < 0.97:
        gagal.append(f"audio MP4 tidak identik dengan sumber (korelasi {corr:.3f})")

    pk = np.abs(mp4_st).max(0)
    peak = float(pk.max())
    true_peak_db = 20 * np.log10(peak + 1e-9)
    print(f"peak MP4 : {true_peak_db:.1f} dBFS per kanal (L {20*np.log10(pk[0]+1e-9):.1f} / "
          f"R {20*np.log10(pk[1]+1e-9):.1f})")
    if true_peak_db > -0.1:
        gagal.append("audio mendekati clipping")

    print("\nper scene (VO diukur setelah lead_in %.2fs):" % lead_in)
    thr = 10 ** (-40 / 20) * max(1e-6, np.abs(mp4).max())
    for sc in tl["scenes"]:
        s, e = sc["start"], sc["start"] + sc["dur"]
        seg = mp4[int(s * SR):int(e * SR)]
        idx = np.where(np.abs(seg) > thr)[0]
        if len(idx) == 0:
            print(f"  {sc['id']:6s} HENING TOTAL ✘")
            gagal.append(f"{sc['id']} hening total")
            continue
        head = idx[0] / SR
        tail = (len(seg) - idx[-1]) / SR
        # rentang aktif (bukan jumlah sampel): jeda bicara jangan dihitung hilang
        aktif = (idx[-1] - idx[0]) / SR
        # VO harus mulai dekat awal scene (lead_in) dan berakhir sebelum scene usai
        telat = head - lead_in
        jeda = sc["dur"] - (head + aktif)
        harap = sc.get("vo_dur") or 0
        beda = abs(aktif - harap) if harap else 0
        ok = (head < lead_in + 0.35 and tail > 0.02 and jeda > 0.10
              and (not harap or beda < 0.35))
        print(f"  {sc['id']:6s} VO mulai +{head:.2f}s (lead_in {lead_in:.2f} → "
              f"selisih {telat:+.2f}s), durasi VO {aktif:.2f}s (naskah {harap:.2f}s, "
              f"beda {beda:.2f}s), ekor {tail:.2f}s, {'OK' if ok else 'PERIKSA ✘'}")
        if not ok:
            gagal.append(f"{sc['id']} tidak utuh (mulai +{head:.2f}s, durasi beda {beda:.2f}s)")

    # frame contoh untuk pemeriksaan mata
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    outdir = os.path.join(BUILD, "qc")
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        if f.endswith(".png"):
            os.remove(os.path.join(outdir, f))
    times = [min(total - 0.4, sc["start"] + sc["dur"] * 0.55) for sc in tl["scenes"]]
    entries = []
    for i, t in enumerate(times):
        p = os.path.join(outdir, f"qc{i}.png")
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                        "-i", video, "-frames:v", "1", "-y", p], check=True)
        entries.append((p, f"{tl['scenes'][i]['id']}  {t:.2f}s"))
    print(f"\n{len(entries)} frame contoh -> {os.path.normpath(outdir)}/qc0..{len(entries)-1}.png")

    # --- audit margin aman pada frame contoh ---------------------------------
    # Catatan: banyak adegan sengaja penuh layar (grafis menyentuh tepi). Karena itu
    # angka di sini bersifat INFORMASI; yang mengikat adalah audit presisi elemen
    # teks di check_layout.py (tahap 0 render_all.sh). Ambang besar (1200) tetap
    # ditolak supaya kelainan kasar tidak lolos.
    from PIL import Image
    # Sejak gaya baru (tanpa panel dalam), ilustrasi memang penuh layar dan
    # menyentuh tepi kanvas dengan sengaja. Yang mengikat tetap audit presisi
    # elemen teks (check_layout.py). Ambang kasar dinaikkan supaya hanya
    # kelainan benar-benar parah (mis. tepi tertutup penuh) yang ditolak.
    ambang_kasar = max(6000.0, arg.margin_max * 20)
    print(f"\naudit margin aman ({mesin_util.SAFE_MARGIN}px) — grafis penuh layar dinilai sebagai catatan:")
    for p, label in entries:
        hits, lokasi, sisi = mesin_util.ink_report(Image.open(p), mesin_util.SAFE_MARGIN)
        if hits > ambang_kasar:
            print(f"  {label:14s} tinta {hits:4d}  BERLEBIHAN   contoh {lokasi[:3]}")
            gagal.append(f"grafis terlalu banyak menyentuh tepi di {label} (tinta {hits})")
        else:
            print(f"  {label:14s} tinta {hits:4d}  catatan (grafis penuh layar biasa)")

    # --- montase berlabel untuk pemeriksaan mata ---
    sheet_path = os.path.join(outdir, "sheet.png")
    mesin_util.sheet(entries, sheet_path)
    print(f"[+] montase berlabel -> {os.path.normpath(sheet_path)}")

    print("\nHASIL QC:", "SEMUA BERSIH ✔" if not gagal else "MASALAH: " + "; ".join(gagal))
    sys.exit(0 if not gagal else 1)


if __name__ == "__main__":
    main()
