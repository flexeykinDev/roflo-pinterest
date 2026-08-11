"""Generates assets/roflo.ico from the same glyph tray.py draws for the
tray icon, so the .exe's file/taskbar icon matches. Run once (or whenever
tray.py's glyph changes) — the .ico is checked in, this isn't needed at
build time.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tray import _make_icon_image  # noqa: E402

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "roflo.ico")
SIZES = [16, 32, 48, 64, 128, 256]


def main() -> None:
    base = _make_icon_image("idle", final_size=256)
    base.save(OUT_PATH, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"Wrote {os.path.abspath(OUT_PATH)}")


if __name__ == "__main__":
    main()
