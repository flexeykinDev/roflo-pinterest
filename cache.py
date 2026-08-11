"""Read/write and manage the pins pool + the seen-history registry.

Keys are the PIN'S OWN HASH ID (the filename Pinterest uses), not the
full URL — the same pin is served under several different URLs
(originals/736x/564x folders), so deduping on the raw URL let the same
picture back in under a different resolution. Deduping on the id fixes
that: same picture, one entry, no matter which size variant is seen.

Format on disk:
{
  "pool": {pin_id: {"url": <best quality url>, "added": <unix ts>}},
  "seen": {pin_id: {"url": <best quality url>, "added": <unix ts>}}
}
"""
import json
import os
import random
import time
from typing import Dict, Optional

import config


def canonical_id(url: str) -> str:
    """The stable part of a pin's URL — same across originals/736x/564x."""
    name = url.rsplit("/", 1)[-1]
    name = name.split("?", 1)[0]
    return os.path.splitext(name)[0]


def _empty_store() -> dict:
    return {"pool": {}, "seen": {}}


def _is_new_format(d: dict) -> bool:
    for bucket in ("pool", "seen"):
        for v in d.get(bucket, {}).values():
            return isinstance(v, dict) and "url" in v
    return True  # empty buckets — nothing to migrate, treat as current


def load() -> dict:
    if not os.path.exists(config.CACHE_FILE):
        return _empty_store()
    with open(config.CACHE_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return _empty_store()

    migrated = _empty_store()

    if "pool" in data or "seen" in data:
        if _is_new_format(data):
            data.setdefault("pool", {})
            data.setdefault("seen", {})
            return data
        # previous format: pool/seen were {url: timestamp}
        for url, ts in data.get("pool", {}).items():
            pid = canonical_id(url)
            migrated["pool"][pid] = {"url": url, "added": ts}
        for url, ts in data.get("seen", {}).items():
            pid = canonical_id(url)
            migrated["seen"][pid] = {"url": url, "added": ts}
        return migrated

    # oldest format: flat {url: {"added":..., "used":...}}
    for url, meta in data.items():
        pid = canonical_id(url)
        ts = meta.get("added", time.time())
        bucket = "seen" if meta.get("used") else "pool"
        migrated[bucket][pid] = {"url": url, "added": ts}
    return migrated


def save(store: dict) -> None:
    tmp_path = config.CACHE_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, config.CACHE_FILE)


def add_new(store: dict, pins: Dict[str, str]) -> int:
    """pins: {pin_id: best_quality_url}. Skips ids already known in
    either pool or seen — this is what stops a pin from reappearing
    just because Pinterest served it under a different-size URL."""
    now = time.time()
    added = 0
    for pid, url in pins.items():
        if pid in store["pool"] or pid in store["seen"]:
            continue
        store["pool"][pid] = {"url": url, "added": now}
        added += 1
    return added


def prune_old_pool(store: dict) -> int:
    cutoff = time.time() - config.MAX_AGE_DAYS * 86400
    stale = [pid for pid, e in store["pool"].items() if e["added"] < cutoff]
    for pid in stale:
        del store["pool"][pid]
    return len(stale)


def trim_pool(store: dict) -> int:
    pool = store["pool"]
    if len(pool) <= config.MAX_CACHE_SIZE:
        return 0
    by_age = sorted(pool.items(), key=lambda kv: kv[1]["added"])
    removed = 0
    for pid, _ in by_age:
        if len(pool) <= config.MAX_CACHE_SIZE:
            break
        del pool[pid]
        removed += 1
    return removed


def trim_seen(store: dict) -> int:
    seen = store["seen"]
    if len(seen) <= config.MAX_SEEN_SIZE:
        return 0
    by_age = sorted(seen.items(), key=lambda kv: kv[1]["added"])
    removed = 0
    for pid, _ in by_age:
        if len(seen) <= config.MAX_SEEN_SIZE:
            break
        del seen[pid]
        removed += 1
    return removed


def pick_and_consume(store: dict) -> Optional[str]:
    """Pop one random pin out of the pool, move it into seen, return
    its download URL."""
    pool = store["pool"]
    if not pool:
        return None
    pid = random.choice(list(pool.keys()))
    entry = pool.pop(pid)
    store["seen"][pid] = entry
    return entry["url"]


def reset_cycle(store: dict) -> None:
    store["pool"].update(store["seen"])
    store["seen"] = {}
