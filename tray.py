"""System tray icon: click for a new wallpaper, right-click for the full
menu (rescan, live pool stats, exit) — no terminal ever needs to open.
Run with pythonw.exe for a fully silent tray app.

Requires: pip install pystray
"""
import threading
from typing import Tuple

import pystray
from PIL import Image, ImageDraw, ImageFilter

import cache as cache_mod
import login
import scraper
import wallpaper
from logger_setup import get_logger

log = get_logger("tray")

# Original color scheme (Pinterest-inspired, not a copy of their logo —
# drawing the actual trademarked logo would be an IP problem).
COLOR_IDLE_TOP = (238, 60, 82)      # bright red
COLOR_IDLE_BOTTOM = (173, 20, 39)   # deep red
COLOR_BUSY_TOP = (255, 175, 64)     # amber — "working" state
COLOR_BUSY_BOTTOM = (194, 108, 12)
COLOR_ERROR = (120, 120, 128)       # muted grey — last action failed

SUPERSAMPLE = 4          # draw at 4x then downscale = free anti-aliasing
FINAL_SIZE = 64

_lock = threading.Lock()
_icon: "pystray.Icon | None" = None


def _lerp(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _make_icon_image(state: str = "idle", final_size: int = FINAL_SIZE) -> Image.Image:
    """Renders a crisp, professional-looking tray icon at 4x and downsamples
    it (cheap anti-aliasing — no jagged pixel edges on the circle/glyph)."""
    size = final_size * SUPERSAMPLE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    top, bottom = {
        "idle": (COLOR_IDLE_TOP, COLOR_IDLE_BOTTOM),
        "busy": (COLOR_BUSY_TOP, COLOR_BUSY_BOTTOM),
        "error": (COLOR_ERROR, COLOR_ERROR),
    }[state]

    # vertical gradient background, clipped to a circle
    grad = Image.new("RGBA", (size, size))
    for y in range(size):
        d2 = ImageDraw.Draw(grad)
        d2.line([(0, y), (size, y)], fill=_lerp(top, bottom, y / size) + (255,))

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    img.paste(grad, (0, 0), mask)

    # soft inner rim for a bit of depth
    d.ellipse((size * 0.04, size * 0.04, size * 0.96, size * 0.96),
              outline=(255, 255, 255, 60), width=int(size * 0.02))

    # simple original glyph: mountains + sun (universal "picture/wallpaper" symbol)
    glyph = (255, 255, 255, 235)
    cx, cy = size / 2, size / 2

    # sun
    d.ellipse((cx - size * 0.16, cy - size * 0.30, cx - size * 0.02, cy - size * 0.16),
              fill=glyph)

    # two overlapping mountain peaks
    d.polygon(
        [
            (size * 0.14, size * 0.72),
            (size * 0.40, size * 0.34),
            (size * 0.60, size * 0.58),
            (size * 0.86, size * 0.72),
        ],
        fill=glyph,
    )
    d.polygon(
        [
            (size * 0.34, size * 0.72),
            (size * 0.58, size * 0.42),
            (size * 0.86, size * 0.72),
        ],
        fill=(255, 255, 255, 160),
    )

    img = img.filter(ImageFilter.SMOOTH_MORE)
    return img.resize((final_size, final_size), Image.LANCZOS)


_ICON_CACHE = {state: _make_icon_image(state) for state in ("idle", "busy", "error")}


def _notify(icon: pystray.Icon, message: str) -> None:
    """Best-effort balloon/toast notification — silently skipped on
    backends that don't support it (pystray's Windows backend often
    doesn't), so this never crashes the tray app."""
    try:
        icon.notify(message, title="Roflo Pinterest")
    except Exception:
        pass


def _set_state(icon: pystray.Icon, state: str) -> None:
    icon.icon = _ICON_CACHE[state]


def _pool_stats_text() -> str:
    store = cache_mod.load()
    return f"В пуле: {len(store['pool'])} · показано: {len(store['seen'])}"


def _run_locked(icon: pystray.Icon, label: str, fn) -> None:
    """Runs fn() in a background thread, guarded so two actions never
    overlap, and reflects progress/result on the icon itself."""
    if _lock.locked():
        _notify(icon, "Уже что-то выполняется, подожди")
        return

    def _worker():
        with _lock:
            _set_state(icon, "busy")
            icon.title = f"Roflo Pinterest — {label}..."
            try:
                ok = fn()
                if ok is False:
                    _set_state(icon, "error")
                    _notify(icon, f"{label}: не удалось")
                else:
                    _set_state(icon, "idle")
                    _notify(icon, f"{label}: готово")
            except Exception as e:
                log.exception("Tray action '%s' failed", label)
                _set_state(icon, "error")
                # Include the error text itself in the notification, not
                # just "check the log" — logging can go unnoticed in a
                # windowed exe with no console attached.
                _notify(icon, f"{label}: ошибка — {e}")
            finally:
                icon.title = "Roflo Pinterest"
                icon.update_menu()

    threading.Thread(target=_worker, daemon=True).start()


def _on_new_wallpaper(icon, item):
    _run_locked(icon, "Новые обои", wallpaper.set_random_wallpaper)


def _on_rescan(icon, item):
    _run_locked(icon, "Скан Pinterest", scraper.main)


def _on_login(icon, item):
    _run_locked(icon, "Вход в Pinterest", login.login_via_browser)


def _on_exit(icon, item):
    icon.stop()


def run() -> None:
    global _icon

    menu = pystray.Menu(
        pystray.MenuItem("Новые обои", _on_new_wallpaper, default=True),
        pystray.MenuItem("Обновить пул (scraper)", _on_rescan),
        pystray.MenuItem("Войти в Pinterest", _on_login),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(lambda item: _pool_stats_text(), None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Выход", _on_exit),
    )

    _icon = pystray.Icon(
        "roflo_pinterest",
        _ICON_CACHE["idle"],
        "Roflo Pinterest",
        menu,
    )
    log.info("Tray icon started")
    _icon.run()


if __name__ == "__main__":
    run()
