"""Sinkron kata-per-kata (forced alignment) via faster-whisper CPU int8.

Deterministik: temperature=0, beam tetap, tanpa sampling.
Impor faster-whisper malas (hanya di Aligner) agar fungsi murni bisa
diuji tanpa dependensi berat.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Word:
    text: str
    start: float  # detik
    end: float
    conf: float = 1.0  # 0..1


@dataclass(frozen=True)
class Utterance:
    id: int
    start: float
    end: float
    text: str
    words: tuple = field(default_factory=tuple)


class Aligner:
    """Model whisper cepat. model: tiny/base/small/...; unduh sekali dari HF."""

    def __init__(self, model="base", device="cpu", compute_type="int8",
                 cache_dir=None):
        from faster_whisper import WhisperModel
        kw = dict(model_size_or_path=model, device=device,
                  compute_type=compute_type)
        if cache_dir:
            kw["download_root"] = cache_dir
        self.model_name = model
        self._m = WhisperModel(**kw)

    def align(self, audio, language="id", beam=5, vad=True):
        """Selaraskan audio -> daftar Utterance berisi Word ber-stempel waktu."""
        segments, _info = self._m.transcribe(
            audio, language=language, beam_size=int(beam), temperature=0.0,
            word_timestamps=True, vad_filter=bool(vad))
        out = []
        for i, s in enumerate(segments):
            ws = tuple(
                Word(str(w.word).strip(), float(w.start), float(w.end),
                     float(w.probability))
                for w in (s.words or ()))
            out.append(Utterance(int(i), float(s.start), float(s.end),
                                 str(s.text).strip(), ws))
        return out


# ---------------- fungsi murni ----------------

def words_of(utterances):
    """Gabungkan semua kata dari daftar Utterance (urut)."""
    out = []
    for u in utterances:
        out.extend(u.words)
    return out


def word_at_time(words, t):
    """Kata yang sedang terucap pada detik t (start <= t < end), atau None."""
    t = float(t)
    for w in words:
        if w.start <= t < w.end:
            return w
    return None


def words_in_range(words, t0, t1):
    """Kata yang bersinggungan dengan [t0, t1)."""
    t0, t1 = float(t0), float(t1)
    return [w for w in words if w.start < t1 and w.end > t0]


def check_monotonic(words):
    """Benar bila tiap kata start<end dan start tak-pernah mundur."""
    prev = -1e-9
    for w in words:
        if not (w.start < w.end):
            return False
        if w.start < prev - 1e-9:
            return False
        prev = w.start
    return True


_PUNCT = ".,!?;:\"'()[]{}-–—…/\\|@#$%^&*~`+=<> \t\n"


def normalize_token(s):
    return str(s).lower().strip(_PUNCT)


def _lcs_len(a, b):
    dp = [0] * (len(b) + 1)
    for x in a:
        ndp = [0] * (len(b) + 1)
        for j, y in enumerate(b):
            if x == y:
                ndp[j + 1] = dp[j] + 1
            else:
                ndp[j + 1] = dp[j + 1] if dp[j + 1] >= ndp[j] else ndp[j]
        dp = ndp
    return dp[len(b)]


def coverage(expected_text, words):
    """Skor liputan: token harapan yang cocok berurutan (LCS) / total.

    Kembalikan {'cocok': int, 'total': int, 'rasio': float}.
    """
    exp = [normalize_token(t) for t in str(expected_text).split()]
    exp = [t for t in exp if t]
    got = [normalize_token(w.text) for w in words]
    got = [t for t in got if t]
    if not exp:
        return {"cocok": 0, "total": 0, "rasio": 1.0 if not got else 0.0}
    k = _lcs_len(exp, got)
    return {"cocok": k, "total": len(exp), "rasio": k / len(exp)}


def _srt_stamp(t):
    t = max(0.0, float(t))
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def utterances_to_srt(utterances):
    """Ubah daftar Utterance menjadi teks SRT (nomor mulai 1)."""
    lines = []
    for n, u in enumerate(utterances, 1):
        lines.append(str(n))
        lines.append(f"{_srt_stamp(u.start)} --> {_srt_stamp(u.end)}")
        lines.append(u.text if u.text else " ")
        lines.append("")
    return "\n".join(lines)
