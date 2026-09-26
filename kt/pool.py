"""Multiproses frame: urutan deterministik, tiap pekerja mandiri (tanpa objek Skia lintas proses)."""
import concurrent.futures as cf
import multiprocessing as mp


def _ctx():
    try:
        return mp.get_context("fork")
    except (AttributeError, ValueError):
        return mp.get_context("spawn")


def render_range(fn, start: int, end: int, jobs: int = 4, chunksize: int = 4):
    """Jalankan fn(i) untuk i in [start, end). Kembalikan hasil URUT indeks."""
    idx = list(range(start, end))
    if not idx:
        return []
    if jobs <= 1:
        return [fn(i) for i in idx]
    with cf.ProcessPoolExecutor(max_workers=jobs, mp_context=_ctx()) as ex:
        return list(ex.map(fn, idx, chunksize=chunksize))
