import html
import logging
import re
import threading
import time
from collections import deque
from functools import wraps
from urllib.parse import urlparse

from . import config


# ------------------------------------------------------------------
# Simple in-memory anti-spam / rate limiter
# ------------------------------------------------------------------

RATE_STORE = {}
RATE_LOCK = threading.Lock()

IG_USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")


def allow(user_id: int, action: str, max_calls: int, seconds: int) -> bool:
    """
    Returns True if action allowed, False if user is too fast.
    """
    now = time.monotonic()
    key = (int(user_id), action)

    with RATE_LOCK:
        if len(RATE_STORE) > 20000:
            RATE_STORE.clear()

        dq = RATE_STORE.setdefault(key, deque())

        while dq and now - dq[0] > seconds:
            dq.popleft()

        if len(dq) >= max_calls:
            return False

        dq.append(now)
        return True


# ------------------------------------------------------------------
# HTML helpers
# ------------------------------------------------------------------

def esc(value) -> str:
    """Escape text for Telegram HTML."""
    return html.escape(str(value), quote=False)


def mention(user) -> str:
    """HTML mention of a Telegram user."""
    name = user.first_name or user.username or str(user.id)
    return f'<a href="tg://user?id={user.id}">{esc(name)}</a>'


# ------------------------------------------------------------------
# Instagram helpers
# ------------------------------------------------------------------

def clean_instagram_username(raw: str):
    """Validate Instagram username. Accepts @username or username."""
    if not raw:
        return None

    username = raw.strip().lstrip("@")

    if IG_USERNAME_RE.match(username):
        return username.lower()

    return None


def normalize_link(raw: str) -> str:
    """Normalize a submitted link (add https, remove query, etc)."""
    raw = (raw or "").strip()
    if not raw:
        return ""

    raw = raw.split()[0].strip("<>")

    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)

    if not parsed.netloc:
        return ""

    path = parsed.path.rstrip("/")

    return f"{parsed.scheme}://{parsed.netloc.lower()}{path}"


def is_instagram_link(raw: str) -> bool:
    """Check if link looks like an Instagram reel/post/tv link."""
    link = normalize_link(raw)
    parsed = urlparse(link)

    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    if host not in {"instagram.com", "instagr.am"}:
        return False

    path = parsed.path.lower()

    return path.startswith(
        (
            "/reel/",
            "/reels/",
            "/p/",
            "/tv/",
        )
    )


# ------------------------------------------------------------------
# Formatting helpers
# ------------------------------------------------------------------

def format_money(value) -> str:
    try:
        return f"{float(value or 0):.2f}"
    except Exception:
        return "0.00"


def status_emoji(status: str) -> str:
    return {
        "pending": "⏳",
        "approved": "✅",
        "rejected": "❌",
    }.get(status, "❔")


# ------------------------------------------------------------------
# Admin authorization decorator
# ------------------------------------------------------------------

def require_admin(handler):
    """
    Only users listed in ADMIN_IDS can use the wrapped handler.
    """
    @wraps(handler)
    async def wrapper(update, context):
        user = update.effective_user

        if not user or user.id not in config.ADMIN_IDS:
            logging.getLogger(__name__).warning(
                "Unauthorized admin attempt by %s",
                user.id if user else "unknown",
            )

            try:
                if update.callback_query:
                    await update.callback_query.answer(
                        "⛔ Not authorized.",
                        show_alert=True,
                    )
                elif update.effective_message:
                    await update.effective_message.reply_text(
                        "⛔ Not authorized."
                    )
            except Exception:
                pass

            return

        return await handler(update, context)

    return wrapper
