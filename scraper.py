"""Scrape Pinterest feed/boards for pin image URLs and merge into the cache.

Run this on a schedule (Task Scheduler, daily is plenty) — main.py never
touches the network for scraping, it only reads the cache this produces.
"""
import re
from typing import Dict

from playwright.sync_api import sync_playwright

import cache as cache_mod
import config
from logger_setup import get_logger

log = get_logger("scraper")

# Captures the size folder (originals/736x/564x) and the pin's own
# filename separately, so we can dedupe by the filename (stable across
# resolutions) while still knowing which variant is highest quality.
PIN_URL_RE = re.compile(
    r'https://i\.pinimg\.com/(originals|736x|564x)/[0-9a-fA-F]{2}/[0-9a-fA-F]{2}/'
    r'[0-9a-fA-F]{2}/([^\s"\\]+?\.(?:jpg|jpeg|png))'
)

# Higher number = better quality. Used to pick the best variant when the
# same pin shows up more than once in the same page (or across pages).
SIZE_PRIORITY = {"originals": 3, "736x": 2, "564x": 1}


def _extract_best_pins(html: str) -> Dict[str, str]:
    """Returns {pin_id: best_quality_url} for every pin found in html.
    pin_id is the filename without extension — the same across all size
    variants, so this is what dedup should key on, not the full URL."""
    best: Dict[str, tuple] = {}  # pin_id -> (priority, url)
    for m in PIN_URL_RE.finditer(html):
        size, filename = m.group(1), m.group(2)
        pin_id = filename.rsplit(".", 1)[0]
        url = m.group(0)
        prio = SIZE_PRIORITY.get(size, 0)
        current = best.get(pin_id)
        if current is None or prio > current[0]:
            best[pin_id] = (prio, url)
    return {pid: url for pid, (prio, url) in best.items()}


def _scrape_page(page, url: str) -> Dict[str, str]:
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    for _ in range(5):
        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(600)
    html = page.content()
    return _extract_best_pins(html)


def scrape_all() -> Dict[str, str]:
    """Merges pins across every target page, keeping the best-quality
    URL if the same pin_id turns up on more than one page."""
    targets = [config.FEED_URL, *config.BOARD_URLS]
    merged: Dict[str, str] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=config.AUTH_FILE)
        page = context.new_page()
        for target in targets:
            try:
                found = _scrape_page(page, target)
                log.info("Found %d unique pins at %s", len(found), target)
                for pid, url in found.items():
                    cur = merged.get(pid)
                    if cur is None:
                        merged[pid] = url
                    else:
                        cur_prio = SIZE_PRIORITY.get(cur.split("/")[3], 0)
                        new_prio = SIZE_PRIORITY.get(url.split("/")[3], 0)
                        if new_prio > cur_prio:
                            merged[pid] = url
            except Exception as e:
                log.error("Failed to scrape %s: %s", target, e)
        browser.close()

    return merged


def main() -> None:
    store = cache_mod.load()
    before_pool = len(store["pool"])
    before_seen = len(store["seen"])

    pins = scrape_all()
    added = cache_mod.add_new(store, pins)
    removed_old = cache_mod.prune_old_pool(store)
    removed_pool = cache_mod.trim_pool(store)
    removed_seen = cache_mod.trim_seen(store)

    cache_mod.save(store)

    msg = (
        f"Пул было: {before_pool}, показано всего было: {before_seen}, "
        f"найдено уникальных пинов: {len(pins)}, добавлено новых: {added}, "
        f"удалено устаревших из пула: {removed_old}, обрезано (лимит пула): {removed_pool}, "
        f"обрезано (лимит истории): {removed_seen}, "
        f"сейчас в пуле: {len(store['pool'])}, показано всего: {len(store['seen'])}"
    )
    log.info(msg)
    print(msg)


if __name__ == "__main__":
    main()
