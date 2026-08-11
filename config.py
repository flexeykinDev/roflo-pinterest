"""Central configuration for the Roflo Pinterest wallpaper tool."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Pinterest source ---
FEED_URL = "https://www.pinterest.com/"
BOARD_URLS: list[str] = [
    # "https://www.pinterest.com/username/board-name/",
]

# --- Files ---
AUTH_FILE = os.path.join(BASE_DIR, "pinterest_auth.json")
CACHE_FILE = os.path.join(BASE_DIR, "pins_cache.json")
LOG_FILE = os.path.join(BASE_DIR, "roflo.log")

# --- Cache behaviour ---
MAX_AGE_DAYS = 14          # remove never-shown pool candidates older than this
MAX_CACHE_SIZE = 500       # cap on the POOL (not-yet-shown candidates)
MAX_SEEN_SIZE = 5000       # cap on SEEN history — kept large: these are cheap
                           # strings, and shrinking this is what causes repeats
DOWNLOAD_RETRIES = 5       # how many candidates to try if one fails/is broken

# --- Image filtering ---
MIN_IMAGE_BYTES = 15_000   # skip tiny/broken images (rules out most icons)

# --- Networking ---
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15
