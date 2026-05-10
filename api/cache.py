import hashlib
import json
import time
from typing import Optional

from .models import BrandCard

CACHE_PATH = "/tmp/brandradar_cache.json"
TTL = 86400  # 24 hours

# In-process layer: avoids file I/O on every repeated lookup within a process lifetime.
_mem: dict[str, tuple[float, list[BrandCard]]] = {}


def _key(channel_url: str) -> str:
    return hashlib.sha256(channel_url.strip().lower().encode()).hexdigest()


def _load() -> dict:
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def get_cached(channel_url: str) -> Optional[list[BrandCard]]:
    key = _key(channel_url)
    now = time.time()

    ts, brands = _mem.get(key, (0.0, []))
    if brands and now - ts < TTL:
        return brands

    entry = _load().get(key)
    if not entry or now - entry.get("ts", 0) > TTL:
        return None
    try:
        cards = [BrandCard(**b) for b in entry["brands"]]
        _mem[key] = (entry["ts"], cards)
        return cards
    except Exception:
        return None


def set_cache(channel_url: str, brands: list[BrandCard]) -> None:
    key = _key(channel_url)
    now = time.time()
    _mem[key] = (now, brands)

    data = _load()
    data[key] = {"ts": now, "brands": [b.model_dump() for b in brands]}
    _save(data)
