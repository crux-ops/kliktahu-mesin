#!/usr/bin/env python3
"""Bangun timeline.json: durasi scene (dari VO bila ada), caption, dan titik pratinjau otomatis.

Mesin v2: menambah `preview` (titik waktu pemeriksaan mata) + peringatan durasi bila
melewati MAXDUR (env MAXDUR, default 59s) beserta saran nilai SPEED yang diperlukan.
"""
import json, os, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mesin_util

MAXDUR = float(os.environ.get("MAXDUR", "59"))

BASE = os.path.dirname(os.path.abspath(__file__))


def audio_dur(path):
    with wave.open(path) as w:
        return w.getnframes() / float(w.getframerate())


def vo_duration(sc, audio_dir):
    """Durasi VO: pakai file audio kalau ada, kalau belum pakai estimasi kata."""
    p = os.path.join(audio_dir, sc["id"] + ".wav") if audio_dir else None
    if p and os.path.exists(p):
        try:
            return audio_dur(p)
        except Exception:
            pass
    words = len(sc["vo"].split())
    if sc["type"] == "intro":
        return max(2.6, words / 2.45)
    if sc["type"] == "outro":
        return max(2.4, words / 2.45)
    return max(2.8, words / 2.55)


def chunk_text(text, max_words=4, max_chars=34):
    """Pecah teks jadi potongan caption pendek (gaya subtitle shorts)."""
    words = text.replace("  ", " ").split()
    chunks, cur = [], []
    for w in words:
        trial = cur + [w]
        if cur and (len(trial) > max_words or len(" ".join(trial)) > max_chars):
            chunks.append(" ".join(cur))
            cur = [w]
        else:
            cur = trial
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def build(content, audio_dir=None):
    scenes = []
    t = 0.0
    lead = content.get("lead_in", 0.5)
    # ekor (jeda setelah VO) bisa diatur per episode; default sama seperti sebelumnya
    tail = {"fact": float(content.get("tail_fact", 1.35)),
            "intro": float(content.get("tail_intro", 1.30)),
            "outro": float(content.get("tail_outro", 1.70))}
    for sc in content["scenes"]:
        sc = dict(sc)
        vd = vo_duration(sc, audio_dir)
        if sc["type"] == "fact":
            dur = round(vd + tail["fact"], 3)
        elif sc["type"] == "intro":
            dur = round(vd + tail["intro"], 3)
        else:
            dur = round(vd + tail["outro"], 3)
        sc["vo_dur"] = round(vd, 3)
        sc["dur"] = dur
        sc["start"] = round(t, 3)
        sc["vo_at"] = round(t + lead, 3)
        caps = chunk_text(sc["vo"])
        total_chars = sum(len(c) for c in caps) or 1
        span = max(0.6, dur - lead - 0.45)
        # distribusi waktu caption proporsional panjang karakter (tanpa kode mati)
        tcur = lead
        cap_list = []
        for i, c in enumerate(caps):
            share = span * (len(c) / total_chars)
            cap_list.append({"t": round(tcur, 3), "d": round(share, 3), "text": c})
            tcur += share
        sc["captions"] = cap_list
        scenes.append(sc)
        t += dur
    out = {"total": round(t, 3), "lead_in": lead, "scenes": scenes,
            "title": content.get("title", ""),
            "meta": {"header_badge": content.get("header_badge", ""),
                     "brand": content.get("channel", "KlikTahu"),
                     "bg_element": content.get("bg_element", "none")}}
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    content = json.load(open(os.path.join(here, "content.json")))
    adir = os.path.join(here, "audio_proc")
    if not os.path.isdir(adir):
        adir = os.path.join(here, "audio")
    tl = build(content, adir)
    tl["preview"] = mesin_util.preview_times(tl)
    out = os.path.join(here, "timeline.json")
    json.dump(tl, open(out, "w"), ensure_ascii=False, indent=1)
    print("total:", tl["total"], "s")
    for s in tl["scenes"]:
        print(f"  {s['id']:6s} start={s['start']:6.2f} dur={s['dur']:5.2f} vo={s['vo_dur']:5.2f} caps={len(s['captions'])}")
    print("pratinjau otomatis:", ", ".join(f"{e['scene']}@{e['t']:.1f}s" for e in tl["preview"]))
    # --- jaga durasi: beri tahu lebih awal, bukan setelah render 18 menit ---
    vo_sum = sum(s["vo_dur"] for s in tl["scenes"])
    extra = tl["total"] - vo_sum
    if tl["total"] > MAXDUR:
        speed = float(os.environ.get("SPEED", "1.20"))
        butuh = vo_sum * speed / max(0.5, (MAXDUR - extra - 0.5))
        print(f"PERINGATAN: total {tl['total']:.1f}s > MAXDUR {MAXDUR:.0f}s. "
              f"Sarankan SPEED={butuh:.2f} lalu proses-ulang audio.")
        sys.exit(2)
    print(f"durasi aman: {tl['total']:.1f}s (MAXDUR {MAXDUR:.0f}s, sisa {MAXDUR - tl['total']:.1f}s)")
