"""Same as main.py, but saved as .pyw so double-clicking it (or launching
it via pythonw.exe) shows no console window at all. Errors still go to
roflo.log — check there if a run seems to have done nothing."""
from logger_setup import get_logger
import wallpaper

log = get_logger("main_silent")

if __name__ == "__main__":
    try:
        wallpaper.set_random_wallpaper()
    except Exception:
        log.exception("Unhandled error in main_silent")
