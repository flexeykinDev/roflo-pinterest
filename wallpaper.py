"""Download and set desktop wallpaper on Windows, with validation + retries."""
import ctypes
import os
import tempfile
from typing import Optional

import requests
from PIL import Image

import cache as cache_mod
import config
from logger_setup import get_logger

log = get_logger("wallpaper")


def _download(url: str) -> Optional[str]:
    try:
        r = requests.get(
            url,
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        log.warning("Download failed for %s: %s", url, e)
        return None

    if len(r.content) < config.MIN_IMAGE_BYTES:
        log.warning("Image too small (%d bytes), skipping: %s", len(r.content), url)
        return None

    ext = os.path.splitext(url)[1].split("?")[0] or ".jpg"
    tmp_path = os.path.join(tempfile.gettempdir(), f"pin_wallpaper{ext}")
    with open(tmp_path, "wb") as f:
        f.write(r.content)

    try:
        with Image.open(tmp_path) as img:
            img.verify()
    except Exception as e:
        log.warning("Not a valid image, skipping %s: %s", url, e)
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return None

    return tmp_path


def _apply(path: str) -> None:
    spi_setdeskwallpaper = 20
    spif_updateinifile = 0x01
    spif_sendchange = 0x02
    ctypes.windll.user32.SystemParametersInfoW(
        spi_setdeskwallpaper, 0, path, spif_updateinifile | spif_sendchange
    )


def set_random_wallpaper() -> bool:
    """Pick a pin never shown before, download + validate it (retrying on
    failure), set it as wallpaper, and record it in the seen history."""
    store = cache_mod.load()

    if not store["pool"]:
        log.info("Pool exhausted, resetting cycle")
        cache_mod.reset_cycle(store)

    if not store["pool"]:
        log.error("Cache is empty — run scraper.py first")
        cache_mod.save(store)
        return False

    tried = 0
    while tried < config.DOWNLOAD_RETRIES:
        url = cache_mod.pick_and_consume(store)
        if url is None:
            break
        tried += 1

        path = _download(url)
        if path:
            _apply(path)
            cache_mod.save(store)
            log.info("Wallpaper set from %s", url)
            return True
        # broken/dead url — it's already moved into `seen` by
        # pick_and_consume, so it won't be retried again either

    cache_mod.save(store)
    log.error("All %d candidates failed to download", tried)
    return False
