"""Ensures Playwright's Chromium browser binary is present.

Pip (and the PyInstaller exe built from this repo) only ship the
Playwright driver — the ~150 MB Chromium binary itself is fetched
separately on first use, exactly what `playwright install chromium`
does for a normal install. Idempotent: skips the download if the
browser is already there, so this is cheap to call on every run.
"""
import subprocess

from logger_setup import get_logger

log = get_logger("browser_setup")

_checked = False


def ensure_chromium() -> None:
    global _checked
    if _checked:
        return
    try:
        from playwright._impl._driver import compute_driver_executable, get_driver_env

        driver_executable, driver_cli = compute_driver_executable()
        subprocess.run(
            [str(driver_executable), str(driver_cli), "install", "chromium"],
            env=get_driver_env(),
            check=True,
            capture_output=True,
            text=True,
        )
        _checked = True
    except Exception as e:
        log.warning("Chromium auto-install check failed: %s", e)
