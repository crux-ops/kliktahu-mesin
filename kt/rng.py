"""RNG deterministik: seed tetap -> turunan per frame/pekerja. Tanpa waktu acak."""
import hashlib
import random

MASTER_SEED = 20260926


def seed_for(frame: int, salt: str = "", master: int = MASTER_SEED) -> int:
    h = hashlib.sha256(f"{master}|{salt}|{frame}".encode()).digest()
    return int.from_bytes(h[:8], "big")


def spawn(frame: int, salt: str = "", master: int = MASTER_SEED) -> random.Random:
    return random.Random(seed_for(frame, salt, master))


def numpy_seed(frame: int, salt: str = "", master: int = MASTER_SEED) -> int:
    return seed_for(frame, salt, master) % (2 ** 32)
