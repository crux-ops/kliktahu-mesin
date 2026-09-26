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


def batas_lunak(x, batas_db=PEAK_BATAS_DB, lutut_db=3.0):
    """Pembatas lunak: di bawah lutut tak tersentuh, puncak dibatasi halus.

    Perlu karena puncak global setelah normalisasi LUFS bisa > -1 dBFS
    (faktor kres ucapan); limiter siaran bekerja dengan cara yang sama.
    """
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    t = 10.0 ** (float(batas_db) / 20.0)
    k = 10.0 ** ((float(batas_db) - float(lutut_db)) / 20.0)
    a = np.abs(x).astype(np.float64)
    y = x.astype(np.float64).copy()
    over = a > k
    if np.any(over):
        y[over] = (np.sign(x[over])
                   * (k + (t - k) * np.tanh((a[over] - k) / (t - k))))
    return y.astype(np.float32)


def rantai_vo(x, sr_asal, n_kata, rentang_kata=None):
    """Rantai penuh: 48k -> pace -> -14 LUFS + limiter -> QC.

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
    if puncak_db(z) > 6.0:  # pengaman kasar (seharusnya tak terjadi)
        z, _, _ = jaga_puncak(z, 0.0)
    w = normalisasi_lufs(z, SR, TARGET_LUFS)
    for _ in range(3):
        w = batas_lunak(w)
        if (abs(ukur_lufs(w, SR) - TARGET_LUFS) <= TOL_LUFS
                and puncak_db(w) <= PEAK_BATAS_DB + 1e-9):
            break
        w = normalisasi_lufs(w, SR, TARGET_LUFS)
    w = batas_lunak(w)
    puncak = puncak_db(w)
    diskala = puncak_db(normalisasi_lufs(z, SR, TARGET_LUFS)) > PEAK_BATAS_DB
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


def kunci_seed_onnx(onnx_path, seed=SEED):
    """Tanam seed ke node acak ONNX (RandomNormal/dll) agar deterministik.

    VITS membangkitkan noise di dalam graf; tanpa seed, tiap render beda.
    Transformasi idempoten. Kembalikan jumlah node yang dikunci.
    """
    import onnx
    from onnx import helper
    ACAK = {"RandomNormal", "RandomUniform", "RandomNormalLike",
            "RandomUniformLike"}
    m = onnx.load(str(onnx_path))
    n = 0
    for node in m.graph.node:
        if node.op_type not in ACAK:
            continue
        for attr in node.attribute:
            if attr.name == "seed":
                attr.i = int(seed)
                break
        else:
            node.attribute.append(helper.make_attribute("seed", int(seed)))
        n += 1
    onnx.save(m, str(onnx_path))
    return n


def pastikan_piper(cache_dir):
    """Pastikan model Piper id setempat. Kembalikan {onnx, json, sr}."""
    d = os.path.join(str(cache_dir), "piper")
    os.makedirs(d, exist_ok=True)
    onnx = os.path.join(d, PIPER_VOICE + ".onnx")
    js = onnx + ".json"
    unduh_berkas(PIPER_URL + ".onnx", onnx, 10_000_000)
    unduh_berkas(PIPER_URL + ".onnx.json", js, 1000)
    n_acak = kunci_seed_onnx(onnx)
    print(f"piper node acak dikunci: {n_acak}", flush=True)
    with open(js, encoding="utf-8") as f:
        cfg = json.load(f)
    return {"onnx": onnx, "json": js,
            "sr": int(cfg["audio"]["sample_rate"])}


def muat_piper(onnx, js):
    """Muat suara Piper (CPU, 1 utas demi determinisme)."""
    import onnxruntime as ort
    from piper import PiperVoice
    voice = PiperVoice.load(str(onnx), str(js))
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    opts.inter_op_num_threads = 1
    voice.session = ort.InferenceSession(
        str(onnx), sess_options=opts, providers=["CPUExecutionProvider"])
    return voice


def sintesis_piper(voice, teks, sr, length_scale=None, seed=SEED):
    """Teks -> audio 48k via Piper. length_scale>1 = lebih lambat.

    normalize_audio=False: keluaran mentah model (tanpa kliping paksa ke
    skala penuh); rantai VO yang mengatur kenyaringan + puncak.
    """
    import random
    from piper import SynthesisConfig
    random.seed(seed)
    np.random.seed(seed % (2 ** 32))
    cfg = SynthesisConfig(length_scale=(None if length_scale is None
                                        else float(length_scale)),
                          normalize_audio=False)
    pot = []
    for c in voice.synthesize(str(teks), syn_config=cfg):
        pot.append(np.asarray(c.audio_int16_array, dtype=np.float32)
                   / 32768.0)
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


def _audio_ke_array(au):
    au = au or {}
    arr = au.get("array")
    if arr is None and au.get("bytes"):
        return _dekode_mp3(au["bytes"]), 48000
    return arr, int(au.get("sampling_rate") or 0)


def ambil_prompt(cache_dir):
    """Ambil 1 klip pria Indonesia (FLEURS, CC-BY-4.0) untuk prompt kandidat B.

    Common Voice tidak dipakai (repo HF kosong tanpa token). Pilih
    deterministik: cantum test/validation pertama berdurasi 2-12 dtk dengan
    F0 85-170 Hz. Kembalikan (path_wav_48k, meta).
    """
    from datasets import get_dataset_config_names, load_dataset
    d = os.path.join(str(cache_dir), "prompt")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, "prompt_pria.wav")
    meta_path = os.path.join(d, "prompt_pria.json")
    if os.path.exists(out) and os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            return out, json.load(f)
    repo = "google/fleurs"
    try:
        cfgs = get_dataset_config_names(repo)
    except Exception as e:
        raise RuntimeError(f"prompt {repo}: {type(e).__name__} {e}")
    cfg = "id_id" if "id_id" in cfgs else None
    if cfg is None:
        idmulai = sorted(c for c in cfgs if c.startswith("id"))
        if not idmulai:
            raise RuntimeError(f"prompt {repo}: tanpa config id")
        cfg = idmulai[0]
    for split in ("test", "validation"):
        try:
            ds = load_dataset(repo, cfg, split=split, streaming=True)
        except Exception as e:
            print(f"prompt {cfg}/{split} gagal: {e}", flush=True)
            continue
        for ex in ds:
            arr, au_sr = _audio_ke_array(ex.get("audio"))
            if arr is None or au_sr <= 0:
                continue
            arr = np.asarray(arr, dtype=np.float32).reshape(-1)
            dur = arr.size / au_sr
            if not 2.0 <= dur <= 12.0:
                continue
            a48 = ke_48k(arr, au_sr)
            f0 = f0_median(a48, SR)
            if f0 is None or not 85.0 <= f0 <= 170.0:
                continue
            meta = {"sumber": "fleurs", "lisensi": "CC-BY-4.0 Google",
                    "repo": f"{repo}/{cfg}", "split": split,
                    "kalimat": str(ex.get("transcription")
                                   or ex.get("sentence") or ""),
                    "gender": "pria(F0)", "sr_asal": au_sr, "dur_asal": dur,
                    "utt": str(ex.get("id") or ""), "f0": f0}
            tulis_wav_16(out, a48, SR)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=1)
            print(f"prompt: {repo}/{cfg}/{split} utt={meta['utt']}",
                  flush=True)
            return out, meta
    raise RuntimeError(f"prompt {repo}/{cfg}: tak ada klip pria (F0)")


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
