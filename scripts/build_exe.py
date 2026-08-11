"""Builds RofloPinterest.exe — a onefile, no-console Windows executable
bundling the tray app (and everything it needs: scraper, wallpaper,
cache, login) so end users don't need Python or `pip install -r
requirements.txt` at all.

Usage (from the venv):
    python scripts/build_exe.py

Output: dist/RofloPinterest.exe
"""
import os
import sys

import PyInstaller.__main__

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PyInstaller.__main__.run([
    os.path.join(BASE_DIR, "tray.py"),
    "--name", "RofloPinterest",
    "--onefile",
    "--windowed",
    "--icon", os.path.join(BASE_DIR, "assets", "roflo.ico"),
    # Playwright's browser driver (node.exe + its JS) lives inside the
    # playwright package as data files — collect_all pulls it in. The
    # ~150 MB Chromium browser binary itself is NOT part of this: it's
    # fetched on first use by browser_setup.ensure_chromium().
    "--collect-all", "playwright",
    "--hidden-import", "six.moves.queue",
    "--distpath", os.path.join(BASE_DIR, "dist"),
    "--workpath", os.path.join(BASE_DIR, "build"),
    "--specpath", BASE_DIR,
    "--noconfirm",
])
