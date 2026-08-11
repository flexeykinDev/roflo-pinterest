"""One-time helper: registers Windows Scheduled Tasks for this project so
you don't have to click through the Task Scheduler GUI.

Usage (from the project folder, venv activated or not — paths are absolute):
    python setup_task.py                 # daily scraper only
    python setup_task.py --with-logon    # + wallpaper change at every logon

Re-running is safe — tasks are recreated (/F = force overwrite).
"""
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")
VENV_PYTHONW = os.path.join(BASE_DIR, "venv", "Scripts", "pythonw.exe")


def _check_venv() -> None:
    if not os.path.exists(VENV_PYTHON):
        print(f"Не найден venv по пути {VENV_PYTHON}")
        print("Сначала создай venv: python -m venv venv")
        sys.exit(1)


def create_daily_scraper_task() -> None:
    script = os.path.join(BASE_DIR, "scraper.py")
    cmd = [
        "schtasks", "/Create", "/F",
        "/SC", "DAILY", "/ST", "09:00",
        "/TN", "RofloPinterestScraper",
        "/TR", f'"{VENV_PYTHON}" "{script}"',
    ]
    subprocess.run(cmd, check=True)
    print("Задача RofloPinterestScraper создана (ежедневно в 09:00)")


def create_logon_wallpaper_task() -> None:
    script = os.path.join(BASE_DIR, "main.py")
    cmd = [
        "schtasks", "/Create", "/F",
        "/SC", "ONLOGON",
        "/TN", "RofloPinterestWallpaper",
        "/TR", f'"{VENV_PYTHONW}" "{script}"',
    ]
    subprocess.run(cmd, check=True)
    print("Задача RofloPinterestWallpaper создана (при входе в систему)")


if __name__ == "__main__":
    _check_venv()
    create_daily_scraper_task()
    if "--with-logon" in sys.argv:
        create_logon_wallpaper_task()
