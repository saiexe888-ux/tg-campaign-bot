import os
from pathlib import Path

from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


def _parse_admin_ids(value: str) -> frozenset:
    """
    Parse ADMIN_IDS from .env.
    Example: 123456789,987654321
    """
    ids = set()

    if not value:
        return frozenset()

    for part in value.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue

        try:
            ids.add(int(part))
        except ValueError:
            pass

    return frozenset(ids)


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# webhook = PythonAnywhere, polling = local/VPS
MODE = os.getenv("MODE", "webhook").strip().lower()

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip().rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()

ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "bot.db"))).expanduser().absolute()

SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@your_support").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()


def require_config() -> None:
    """
    Check required settings before bot starts.
    """
    errors = []

    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is missing")

    if not ADMIN_IDS:
        errors.append("ADMIN_IDS is missing")

    if MODE == "webhook":
        if not WEBHOOK_URL:
            errors.append("WEBHOOK_URL is missing")
        if not WEBHOOK_SECRET:
            errors.append("WEBHOOK_SECRET is missing")

    if errors:
        raise RuntimeError("Configuration errors: " + "; ".join(errors))
