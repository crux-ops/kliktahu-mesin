"""Audio VO Seksi E: pace 1,8-1,9 k/detik, -14 LUFS, QC isi-hilang 30 ms.

Fungsi murni (kata, pace, kenyaringan, celah, F0, rantai) deterministik dan
boleh diuji lokal. Fungsi TTS (Piper/Chatterbox), unduh model, dan ambil
prompt memakai impor malas dan HANYA boleh jalan di GitHub Actions
(butuh jaringan + CPU berat).
"""
import json
import math
import os
import urllib.request
import wave

import numpy as np

SR = 48000
TARGET_PACE = 1.85  # kata/detik tengah rentang seksi E
PACE_LO = 1.8
PACE_HI = 1.9
TARGET_LUFS = -14.0
TOL_LUFS = 0.5
PEAK_BATAS_DB = -1.0
GAP_MIN_S = 0.030  # >=30 ms di dalam kata = isi hilang
GAP_AMBANG_DB = -45.0
BINGKAI_S = 0.010
EROSI_S = 0.030  # tepi rentang kata diabaikan (toleransi stempel whisper)
SEED = 11

AUDITION_TEXT = ("Tahukah kamu? Gurita punya tiga jantung. "
                 "Dua berhenti saat berenang, satu memompa ke tubuh. "
                 "Keren, kan?")
# 16 kata -> ~8,6 detik pada 1,85 k/detik.

NARRATOR_ID = None  # dikunci usai audisi pemilik ("piper:..." / "chatterbox:...")

PIPER_VOICE = "id_ID-news_tts-medium"  # pria, MIT (Repology)
PIPER_URL = ("https://huggingface.co/rhasspy/piper-voices/resolve/main/"
             "id/id_ID/news_tts/medium/id_ID-news_tts-medium")
CHATTER_REPO = "grandhigh/Chatterbox-TTS-Indonesian"  # Apache-2.0
CHATTER_CKPT = "t3_cfg.safetensors"
CV_REPOS = ("mozilla-foundation/common_voice_17_0",
            "mozilla-foundation/common_voice_16_1",
            "mozilla-foundation/common_voice_15_0",
            "mozilla-foundation/common_voice_13_0")


# ---------------- fungsi murni ----------------

def hitung_kata(teks):
    """Jumlah kata (pisah spasi)."""
    return len(str(teks).split())


def ukur_pace(n_kata, dur_s):
    """Kata per detik."""
    return float(n_kata) / max(float(dur_s), 1e-9)


def pace_ok(pace):
    """Benar bila pace di dalam [1,8 ; 1,9]."""
    return PACE_LO <= float(pace) <= PACE_HI


def ke_48k(x, sr_asal):
    """Naik/turunkan laju cuplik ke 48 kHz (deterministik)."""
    from scipy.signal import resample_poly
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    sr_asal = int(sr_asal)
    if sr_asal == SR:
        return x.copy()
    g = math.gcd(SR, sr_asal)
    return resample_poly(x, SR // g, sr_asal // g).astype(np.float32)


def regang_ke_pace(x, sr, pace_ukur, pace_target=TARGET_PACE):
    """Regang waktu tanpa ubah nada agar pace -> target (pedalboard).

    faktor = pace_target/pace_ukur (faktor<1 = lebih lambat/panjang).
    """
    from pedalboard import time_stretch
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    faktor = float(pace_target) / float(pace_ukur)
    if abs(faktor - 1.0) < 1e-9:
        return x.copy()
    y = time_stretch(x, float(sr), faktor)
    return np.asarray(y, dtype=np.float32).reshape(-1)


def ukur_lufs(x, sr):
    """Kenyaringan terpadu LUFS (pyloudnorm). Sunyi -> -inf."""
    import pyloudnorm as pyln
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    if x.size == 0 or float(np.sqrt(np.mean(x * x))) < 1e-12:
        return float("-inf")
    return float(pyln.Meter(int(sr)).integrated_loudness(x))


def normalisasi_lufs(x, sr, target=TARGET_LUFS):
    """Skala audio ke target LUFS."""
    import pyloudnorm as pyln
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    y = pyln.normalize.loudness(x, ukur_lufs(x, sr), float(target))
    return np.asarray(y, dtype=np.float32).reshape(-1)


def puncak_db(x):
    """Puncak dBFS."""
    x = np.asarray(x).reshape(-1)
    p = float(np.max(np.abs(x))) if x.size else 0.0
    return 20.0 * math.log10(max(p, 1e-12))


def jaga_puncak(x, batas_db=PEAK_BATAS_DB):
    """Turunkan gain bila puncak > batas. Kembalikan (y, puncak_db, diskala)."""
    x = np.asarray(x, dtype=np.float32).reshape(-1).copy()
    p = puncak_db(x)
    if p <= float(batas_db):
        return x, p, False
    g = 10.0 ** ((float(batas_db) - p) / 20.0)
    return (x * g).astype(np.float32), float(batas_db), True


def bingkai_aktif(x, sr, ambang_db=GAP_AMBANG_DB, bingkai_s=BINGKAI_S):
    """Masker bingkai berenergi (di atas ambang). Kembalikan (masker, fpb)."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    fpb = max(1, int(round(float(bingkai_s) * int(sr))))
    n = x.size // fpb
    if n == 0:
        return np.zeros(0, dtype=bool), fpb
    rms = np.sqrt(np.mean(x[:n * fpb].reshape(n, fpb) ** 2, axis=1))
    db = 20.0 * np.log10(np.maximum(rms, 1e-12))
    return db > float(ambang_db), fpb


def _tengah_dalam_rentang(t, rentang, erosi=EROSI_S):
    for a, b in rentang:
        a, b = float(a), float(b)
        if a + erosi <= t < b - erosi:
            return True
    return False


def celah_hilang(x, sr, rentang_kata=None, ambang_db=GAP_AMBANG_DB,
                 min_s=GAP_MIN_S):
    """QC celah: sunyi >=30 ms DI DALAM batas suara.

    Tanpa rentang_kata: semua celah -> 'celah' (mentah).
    Dengan rentang_kata [(awal, akhir) dari whisper]: celah yang tengahnya
    jauh di dalam kata -> 'hilang' (GAGAL); selebihnya -> 'jeda' (info).
    """
    aktif, fpb = bingkai_aktif(x, sr, ambang_db)
    bdt = fpb / float(sr)
    out = {"awal_suara": None, "akhir_suara": None, "celah": [],
           "hilang": [], "jeda": [], "n_hilang": 0, "maks_hilang": 0.0}
    idx = np.flatnonzero(aktif)
    if idx.size == 0:
        return out
    i0, i1 = int(idx[0]), int(idx[-1])
    out["awal_suara"] = i0 * bdt
    out["akhir_suara"] = (i1 + 1) * bdt
    gaps = []
    j = i0
    while j <= i1:
        if not aktif[j]:
            k = j
            while k <= i1 and not aktif[k]:
                k += 1
            dur = (k - j) * bdt
            if dur + 1e-12 >= float(min_s):
                gaps.append((j * bdt, k * bdt, dur))
            j = k
        else:
            j += 1
    out["celah"] = gaps
    if rentang_kata:
        for g in gaps:
            tengah = (g[0] + g[1]) / 2.0
            key = ("hilang" if _tengah_dalam_rentang(tengah, rentang_kata)
                   else "jeda")
            out[key].append(g)
    out["n_hilang"] = len(out["hilang"])
    out["maks_hilang"] = max([g[2] for g in out["hilang"]] or [0.0])
    return out


def f0_median(x, sr, fmin=50.0, fmax=400.0):
    """Median F0 (autokorelasi, bingkai 30 ms/lompat 10 ms). None bila hening."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    sr = int(sr)
    fl = int(round(0.030 * sr))
    hop = int(round(0.010 * sr))
    if x.size < fl:
        return None
    lag_lo = max(1, int(round(sr / float(fmax))))
    lag_hi = min(fl - 1, int(round(sr / float(fmin))))
    aktif, fpb = bingkai_aktif(x, sr)
    vals = []
    nf = (x.size - fl) // hop + 1
    for i in range(nf):
        s = i * hop
        if s // fpb < len(aktif) and not aktif[s // fpb]:
            continue
        seg = x[s:s + fl]
        seg = seg - seg.mean()
        if float(np.sqrt(np.mean(seg * seg))) < 1e-4:
            continue
        ac = np.correlate(seg, seg, mode="full")[fl - 1:]
        if ac[0] < 1e-12:
            continue
        ac = ac / ac[0]
        k = int(np.argmax(ac[lag_lo:lag_hi + 1])) + lag_lo
        if ac[k] > 0.5:
            vals.append(sr / k)
    if len(vals) < 3:
        return None
    return float(np.median(vals))


def tebak_gender(f0):
    """Tebakan kasar dari F0: pria <160 Hz, wanita >180 Hz."""
    if f0 is None:
        return "tak-pasti"
    f0 = float(f0)
    if f0 < 160.0:
        return "pria"
    if f0 > 180.0:
        return "wanita"
    return "tak-pasti"


def rantai_vo(x, sr_asal, n_kata, rentang_kata=None):
    """Rantai penuh: 48k -> pace -> -14 LUFS -> jaga puncak -> QC.

    Kembalikan dict(y, pace_awal/akhir, lufs_masuk/akhir, puncak_db,
    diskala_puncak, qc, f0_median, gender, lolos, sr).
    """
    y = ke_48k(x, sr_asal)
    pace_awal = ukur_pace(n_kata, y.size / SR)
    faktor = 1.0
    z = y
    if not pace_ok(pace_awal):
        faktor = TARGET_PACE / pace_awal
        z = regang_ke_pace(y, SR, pace_awal, TARGET_PACE)
    pace_akhir = ukur_pace(n_kata, z.size / SR)
    lufs_masuk = ukur_lufs(z, SR)
    w = normalisasi_lufs(z, SR, TARGET_LUFS)
    w, puncak, diskala = jaga_puncak(w, PEAK_BATAS_DB)
    lufs_akhir = ukur_lufs(w, SR)
    qc = celah_hilang(w, SR, rentang_kata)
    f0 = f0_median(w, SR)
    lolos = (pace_ok(pace_akhir)
             and abs(lufs_akhir - TARGET_LUFS) <= TOL_LUFS
             and puncak <= PEAK_BATAS_DB + 1e-9
             and qc["n_hilang"] == 0)
    return {"y": w, "pace_awal": pace_awal, "pace_akhir": pace_akhir,
            "faktor_regang": faktor, "lufs_masuk": lufs_masuk,
            "lufs_akhir": lufs_akhir, "puncak_db": puncak,
            "diskala_puncak": diskala, "qc": qc, "f0_median": f0,
            "gender": tebak_gender(f0), "lolos": lolos, "sr": SR}


def tulis_wav_16(path, x, sr=SR):
    """Tulis mono PCM16."""
    from .sfx import to_pcm16
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(int(sr))
        f.writeframes(to_pcm16(x))


def baca_wav_16(path):
    """Baca WAV mono 16-bit -> (float32, sr)."""
    with wave.open(str(path), "rb") as f:
        assert f.getnchannels() == 1 and f.getsampwidth() == 2
        sr = f.getframerate()
        raw = f.readframes(f.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0, sr


# ---------------- TTS + unduh (HANYA Actions) ----------------

def unduh_berkas(url, path, min_byte=1000):
    """Unduh bila belum ada (lewati bila ukuran cukup)."""
    path = str(path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if os.path.exists(path) and os.path.getsize(path) >= min_byte:
        return path
    tmp = path + ".unduh"
    urllib.request.urlretrieve(url, tmp)
    if os.path.getsize(tmp) < min_byte:
        raise RuntimeError(f"unduhan kecil: {url}")
    os.replace(tmp, path)
    return path


def pastikan_piper(cache_dir):
    """Pastikan model Piper id setempat. Kembalikan {onnx, json, sr}."""
    d = os.path.join(str(cache_dir), "piper")
    os.makedirs(d, exist_ok=True)
    onnx = os.path.join(d, PIPER_VOICE + ".onnx")
    js = onnx + ".json"
    unduh_berkas(PIPER_URL + ".onnx", onnx, 10_000_000)
    unduh_berkas(PIPER_URL + ".onnx.json", js, 1000)
    with open(js, encoding="utf-8") as f:
        cfg = json.load(f)
    return {"onnx": onnx, "json": js,
            "sr": int(cfg["audio"]["sample_rate"])}


def muat_piper(onnx, js):
    """Muat suara Piper (CPU)."""
    from piper import PiperVoice
    return PiperVoice.load(str(onnx), str(js))


def sintesis_piper(voice, teks, sr, length_scale=None, seed=SEED):
    """Teks -> audio 48k via Piper. length_scale>1 = lebih lambat."""
    import random
    from piper import SynthesisConfig
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    cfg = None
    if length_scale is not None:
        cfg = SynthesisConfig(length_scale=float(length_scale))
    pot = []
    for c in voice.synthesize(str(teks), syn_config=cfg):
        pot.append(c.audio_int16_array().astype(np.float32) / 32768.0)
    if not pot:
        raise RuntimeError("piper tak mengeluarkan audio")
    return ke_48k(np.concatenate(pot), sr)


def muat_chatterbox(seed=SEED):
    """Muat Chatterbox-ID (CPU, 1 utas demi determinisme) + ckpt Indonesia."""
    import torch
    from chatterbox.tts import ChatterboxTTS
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file
    torch.manual_seed(seed)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    model = ChatterboxTTS.from_pretrained(device="cpu")
    ckpt = hf_hub_download(repo_id=CHATTER_REPO, filename=CHATTER_CKPT)
    model.t3.load_state_dict(load_file(ckpt, device="cpu"))
    return model


def sintesis_chatterbox(model, teks, prompt_wav, temperature=0.8, seed=SEED):
    """Teks -> audio 48k via Chatterbox-ID + prompt suara (CPU)."""
    import torch
    torch.manual_seed(seed)
    wav = model.generate(str(teks), audio_prompt_path=str(prompt_wav),
                         temperature=float(temperature))
    x = np.asarray(wav.squeeze(0).detach().cpu().numpy(), dtype=np.float32)
    return ke_48k(x, int(model.sr))


def ambil_prompt_cv(cache_dir):
    """Ambil 1 klip pria Common Voice (CC0) Indonesia ter-validasi.

    Pilih deterministik: cantum validasi pertama bergender pria, dur >=1 dtk.
    Kembalikan (path_wav_48k, meta).
    """
    from datasets import load_dataset
    d = os.path.join(str(cache_dir), "cv")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, "prompt_cv_pria.wav")
    meta_path = os.path.join(d, "prompt_cv_pria.json")
    if os.path.exists(out) and os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            return out, json.load(f)
    ds = None
    repo_pakai = None
    for repo in CV_REPOS:
        try:
            ds = load_dataset(repo, "id", split="validated", streaming=True)
            repo_pakai = repo
            break
        except Exception:
            ds = None
    if ds is None:
        raise RuntimeError("tak bisa membuka Common Voice: " + ",".join(CV_REPOS))
    PILIH = {"male", "masculine", "m", "pria", "laki-laki"}
    pilih = None
    for ex in ds:
        g = str(ex.get("gender") or "").strip().lower()
        if g not in PILIH:
            continue
        au = ex.get("audio") or {}
        arr = au.get("array")
        if arr is None and au.get("bytes"):
            arr = _dekode_mp3(au["bytes"])
            au_sr = 48000
        else:
            au_sr = int(au.get("sampling_rate") or 0)
        if arr is None or au_sr <= 0:
            continue
        arr = np.asarray(arr, dtype=np.float32).reshape(-1)
        if arr.size / au_sr < 1.0:
            continue
        pilih = {"repo": repo_pakai, "kalimat": str(ex.get("sentence") or ""),
                 "gender": g, "sr_asal": au_sr,
                 "dur_asal": arr.size / au_sr}
        tulis_wav_16(out, ke_48k(arr, au_sr), SR)
        break
    if pilih is None:
        raise RuntimeError("tak ada klip pria di Common Voice id")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(pilih, f, ensure_ascii=False, indent=1)
    return out, pilih


def _dekode_mp3(data):
    """Cadangan: dekode byte MP3 via imageio-ffmpeg -> mono float32 48k."""
    import imageio_ffmpeg
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(bytes(data))
        tmp = f.name
    try:
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        raw = subprocess.run(
            [exe, "-v", "error", "-i", tmp, "-ac", "1", "-ar", "48000",
             "-f", "f32le", "-"], capture_output=True, check=True).stdout
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    return np.frombuffer(raw, dtype=np.float32).copy()
