"""One-time interactive login to capture a Pinterest session for Playwright.

Run this once. It opens a real (visible) browser window — log in normally,
then come back to the terminal and press Enter. Re-run whenever the saved
session expires (scraper.py will start returning 0 images).
"""
from playwright.sync_api import sync_playwright

import config


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.pinterest.com/login/")

        input("Залогинься в открывшемся окне, потом нажми Enter здесь...")

        context.storage_state(path=config.AUTH_FILE)
        browser.close()
        print(f"Сессия сохранена в {config.AUTH_FILE}")


if __name__ == "__main__":
    main()
