"""Entry point: set a random, not-yet-used Pinterest pin as wallpaper.

Fast — never touches the network for scraping, only downloads the one
chosen image. Safe to run silently (see main_silent.pyw).
"""
from logger_setup import get_logger
import wallpaper

log = get_logger("main")


def main() -> None:
    try:
        wallpaper.set_random_wallpaper()
    except Exception:
        log.exception("Unhandled error in main")


if __name__ == "__main__":
    main()
