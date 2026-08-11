"""Ensures Playwright's Chromium browser binary is present.

Pip (and the PyInstaller exe built from this repo) only ship the
Playwright driver — the ~150 MB Chromium binary itself is fetched
separately on first use, exactly what `playwright install chromium`
does for a normal install. Idempotent: skips the download if the
browser is already there, so this is cheap to call on every run.
"""
import os
import subprocess
import sys

import config
from logger_setup import get_logger

log = get_logger("browser_setup")

_checked = False

if getattr(sys, "frozen", False):
    # Playwright's driver forces PLAYWRIGHT_BROWSERS_PATH=0 ("local, next
    # to the driver") the moment it detects a frozen app — see
    # playwright/_impl/_transport.py. If we install Chromium below without
    # also setting this, `install` puts it in the normal shared cache
    # (%LOCALAPPDATA%\ms-playwright) while the actual browser launch later
    # looks in the frozen-only local path instead, finds nothing, and
    # fails. Pin both install and launch to the same real folder.
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH", os.path.join(config.BASE_DIR, "browsers")
    )


def _hide_console_kwargs() -> dict:
    """node.exe is a console-subsystem binary — spawning it from our
    --windowed parent (which has no console of its own) makes Windows
    flash a brand new console window for it unless we explicitly hide it."""
    if sys.platform != "win32":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {"startupinfo": startupinfo, "creationflags": subprocess.CREATE_NO_WINDOW}


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
            **_hide_console_kwargs(),
        )
        _checked = True
    except Exception as e:
        log.warning("Chromium auto-install check failed: %s", e)
