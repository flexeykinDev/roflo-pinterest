"""One-time interactive login to capture a Pinterest session for Playwright.

Run this once. It opens a real (visible) browser window — log in normally,
then confirm you're done. Re-run whenever the saved session expires
(scraper.py will start returning 0 images).
"""
from playwright.sync_api import sync_playwright

import browser_setup
import config


def _do_login(wait_for_confirmation) -> None:
    browser_setup.ensure_chromium()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.pinterest.com/login/")

        wait_for_confirmation()

        context.storage_state(path=config.AUTH_FILE)
        browser.close()


def login_via_browser() -> bool:
    """Same login flow, but driven by a modal message box instead of a
    terminal `input()` — used by tray.py, which has no console attached."""
    import ctypes

    def _confirm():
        MB_OK = 0x0
        MB_ICONINFORMATION = 0x40
        MB_TOPMOST = 0x40000
        ctypes.windll.user32.MessageBoxW(
            0,
            "Залогинься в открывшемся окне Pinterest, потом нажми ОК здесь.",
            "Roflo Pinterest — вход",
            MB_OK | MB_ICONINFORMATION | MB_TOPMOST,
        )

    _do_login(_confirm)
    return True


def main() -> None:
    _do_login(lambda: input("Залогинься в открывшемся окне, потом нажми Enter здесь..."))
    print(f"Сессия сохранена в {config.AUTH_FILE}")


if __name__ == "__main__":
    main()
