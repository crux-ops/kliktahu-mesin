"""Pustaka SFX sintetis murni numpy (tanpa musik/melodi/irama).

7 jenis sesuai titik sinkron Seksi B: whoosh, pop, thump, snap, swell, zap, sweep.
Semua 48 kHz mono float32, deterministik untuk (dur, seed) sama.
SFX bernada (thump/sweep) tidak memakai seed (disengaja, stabil nada).
"""
import numpy as np

from .rng import numpy_seed

SR = 48000
HEADROOM = 0.89  # puncak target ~ -1 dBFS


def _rng(seed, salt):
    return np.random.default_rng(numpy_seed(seed, salt))


def _n(dur, sr=SR):
    return max(1, int(round(float(dur) * sr)))


def envelope(n, attack=0.05, release=0.20):
    """Selubung raised-cosine: naik attack, turun release (fraksi durasi)."""
    n = int(n)
    env = np.ones(n, dtype=np.float64)
    na = max(1, min(n, int(round(n * float(attack)))))
    nr = max(1, min(n, int(round(n * float(release)))))
    if na > 1:
        t = np.linspace(0, np.pi / 2, na)
        env[:na] = np.sin(t) ** 2
    else:
        env[0] = 0.0
    if nr > 1:
        t = np.linspace(0, np.pi / 2, nr)
        env[n - nr:] = np.cos(t) ** 2
    else:
        env[-1] = 0.0
    return env.astype(np.float32)


def normalize_peak(x, peak=HEADROOM):
    """Skala ke puncak target; sunyi tetap sunyi."""
    x = np.asarray(x, dtype=np.float32)
    p = float(np.max(np.abs(x))) if x.size else 0.0
    if p <= 1e-9:
        return x.copy()
    return (x * (float(peak) / p)).astype(np.float32)


def peak_db(x, floor=-120.0):
    p = float(np.max(np.abs(np.asarray(x)))) if len(x) else 0.0
    if p <= 1e-9:
        return float(floor)
    return float(20.0 * np.log10(p))


def rms(x):
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(x * x)))


def sine_glide(n, f0, f1, sr=SR, curve="exp"):
    """Sinus geser nada tanpa klik (integrasi fase)."""
    n = int(n)
    if curve == "exp" and f0 > 0 and f1 > 0:
        f = f0 * (float(f1) / float(f0)) ** (np.arange(n) / max(1, n - 1))
    else:
        f = np.linspace(float(f0), float(f1), n)
    phase = np.cumsum(2.0 * np.pi * f / float(sr))
    return np.sin(phase).astype(np.float32)


def lowpass_sweep(x, sr, f0, f1, shape="up_down"):
    """Lowpass orde-1 dengan cutoff menyapu (loop sampel, deterministik)."""
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    u = np.arange(n) / max(1, n - 1)
    if shape == "up_down":
        k = np.sin(np.pi * u)
    elif shape == "up":
        k = u
    else:
        k = 1.0 - u
    fc = float(f0) + (float(f1) - float(f0)) * k
    a = 1.0 - np.exp(-2.0 * np.pi * np.clip(fc, 20.0, sr / 2 * 0.99) / float(sr))
    y = np.empty(n, dtype=np.float64)
    acc = 0.0
    for i in range(n):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y.astype(np.float32)


# ---------------- 7 generator SFX ----------------

def sfx_whoosh(dur=0.45, seed=7, sr=SR):
    n = _n(dur, sr)
    noise = _rng(seed, "whoosh").standard_normal(n).astype(np.float32)
    y = lowpass_sweep(noise, sr, 500.0, 6500.0, "up_down")
    return normalize_peak(y * envelope(n, 0.25, 0.35))


def sfx_pop(dur=0.12, seed=7, sr=SR):
    n = _n(dur, sr)
    body = sine_glide(n, 320.0, 75.0, sr)
    r = _rng(seed, "pop")
    click = r.standard_normal(n).astype(np.float32)
    k = np.zeros(n, dtype=np.float32)
    nk = max(1, int(sr * 0.008))
    k[:nk] = np.cos(np.linspace(0, np.pi / 2, nk)) ** 2
    y = body * 0.8 + click * k * 0.5
    return normalize_peak(y * envelope(n, 0.01, 0.55))


def sfx_thump(dur=0.35, seed=7, sr=SR):
    n = _n(dur, sr)
    y = sine_glide(n, 72.0, 38.0, sr)
    return normalize_peak(y * envelope(n, 0.01, 0.70))


def sfx_snap(dur=0.09, seed=7, sr=SR):
    n = _n(dur, sr)
    noise = _rng(seed, "snap").standard_normal(n).astype(np.float32)
    hp = noise - lowpass_sweep(noise, sr, 3000.0, 3000.0, "up")
    ring = np.sin(2 * np.pi * 2100.0 * np.arange(n) / sr).astype(np.float32)
    k = np.zeros(n, dtype=np.float32)
    nk = max(1, int(sr * 0.02))
    k[:nk] = np.cos(np.linspace(0, np.pi / 2, nk)) ** 2
    y = hp * 0.85 + ring * k * 0.25
    return normalize_peak(y * envelope(n, 0.01, 0.75))


def sfx_swell(dur=0.80, seed=7, sr=SR):
    n = _n(dur, sr)
    t = np.arange(n) / float(sr)
    # parsial inharmonik (tekstur, bukan akor): 173/271/389 Hz + noise
    y = (np.sin(2 * np.pi * 173.0 * t)
         + 0.6 * np.sin(2 * np.pi * 271.0 * t + 1.3)
         + 0.4 * np.sin(2 * np.pi * 389.0 * t + 2.1)).astype(np.float32)
    noise = _rng(seed, "swell").standard_normal(n).astype(np.float32)
    wash = lowpass_sweep(noise, sr, 900.0, 2400.0, "up") * 0.5
    trem = (0.75 + 0.25 * np.sin(2 * np.pi * 4.5 * t)).astype(np.float32)
    return normalize_peak((y * 0.5 + wash) * trem * envelope(n, 0.45, 0.40))


def sfx_zap(dur=0.25, seed=7, sr=SR):
    n = _n(dur, sr)
    r = _rng(seed, "zap")
    nstep = max(2, int(round(float(dur) / 0.03)))
    bounds = np.linspace(0, n, nstep + 1).astype(int)
    freqs = r.uniform(900.0, 4200.0, nstep)
    y = np.zeros(n, dtype=np.float32)
    phase = 0.0
    for i in range(nstep):
        a, b = bounds[i], bounds[i + 1]
        if b <= a:
            continue
        m = b - a
        ph = phase + 2 * np.pi * freqs[i] * np.arange(m) / float(sr)
        y[a:b] = np.sign(np.sin(ph)) * 0.6 + np.sin(ph) * 0.4
        phase = ph[-1] % (2 * np.pi)
    levels = 12.0
    y = np.round(y * levels) / levels  # bit-crush
    return normalize_peak(y.astype(np.float32) * envelope(n, 0.02, 0.45))


def sfx_sweep(dur=0.50, seed=7, sr=SR, arah="naik"):
    n = _n(dur, sr)
    if arah == "naik":
        y = sine_glide(n, 180.0, 4200.0, sr)
    else:
        y = sine_glide(n, 4200.0, 180.0, sr)
    res = np.sin(2 * np.pi * 90.0 * np.arange(n) / float(sr)).astype(np.float32)
    y = y * 0.85 + res * 0.15
    return normalize_peak(y * envelope(n, 0.08, 0.25))


SFX = {
    "whoosh": sfx_whoosh,
    "pop": sfx_pop,
    "thump": sfx_thump,
    "snap": sfx_snap,
    "swell": sfx_swell,
    "zap": sfx_zap,
    "sweep": sfx_sweep,
}


def render_sfx(kind, dur=None, seed=7, sr=SR, gain=1.0, **kw):
    """Render satu SFX: (jenis, durasi detik, seed) -> mono float32."""
    try:
        fn = SFX[kind]
    except KeyError:
        raise ValueError(f"SFX tak dikenal: {kind}")
    if dur is None:
        import inspect
        dur = inspect.signature(fn).parameters["dur"].default
    y = fn(float(dur), seed, sr, **kw)
    return (np.asarray(y, dtype=np.float32) * float(gain)).astype(np.float32)


# ---------------- susun & ducking ----------------

def place(dur_total, clips, sr=SR):
    """Susun klip [(t_detik, array, gain)] ke trek sepanjang dur_total."""
    n = _n(dur_total, sr)
    track = np.zeros(n, dtype=np.float32)
    for t, clip, g in clips:
        clip = np.asarray(clip, dtype=np.float32) * float(g)
        i = int(round(float(t) * sr))
        if i >= n or i + clip.size <= 0:
            continue
        a = max(0, i)
        b = min(n, i + clip.size)
        track[a:b] += clip[a - i:b - i]
    return track


def _follower(x, sr, attack_ms, release_ms, init=0.0):
    x = np.asarray(x, dtype=np.float64)
    aa = 1.0 - np.exp(-1.0 / (float(attack_ms) / 1000.0 * sr))
    ar = 1.0 - np.exp(-1.0 / (float(release_ms) / 1000.0 * sr))
    y = np.empty_like(x)
    acc = float(init)
    for i in range(x.size):
        k = aa if x[i] > acc else ar
        acc += k * (x[i] - acc)
        y[i] = acc
    return y


def duck_under(sfx, vo, sr=SR, floor=0.20, thresh_db=-45.0,
               attack_ms=8.0, release_ms=150.0):
    """Tundukkan SFX di bawah VO: kembalikan (ducked, kurva_gain).

    Saat VO aktif (di atas ambang), gain SFX -> floor; mulus anti-klik.
    """
    sfx = np.asarray(sfx, dtype=np.float32)
    vo = np.asarray(vo, dtype=np.float32)
    n = max(sfx.size, vo.size)
    s = np.zeros(n, dtype=np.float32)
    v = np.zeros(n, dtype=np.float32)
    s[:sfx.size] = sfx
    v[:vo.size] = vo
    env = _follower(np.abs(v), sr, attack_ms, release_ms)
    gate = env > (10.0 ** (float(thresh_db) / 20.0))
    target = np.where(gate, float(floor), 1.0)
    gains = _follower(target, sr, attack_ms, release_ms,
                      init=target[0]).astype(np.float32)
    return (s * gains).astype(np.float32), gains


def to_pcm16(x):
    """float32 [-1,1] -> bytes PCM 16-bit mono (untuk WAV stdlib)."""
    x = np.asarray(x, dtype=np.float64)
    pcm = (np.clip(x, -1.0, 1.0) * 32767.0).round().astype(np.int16)
    return pcm.tobytes()
