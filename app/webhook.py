import logging

from flask import Flask, abort, request

from . import config
from . import logging_setup
from .application import create_application
from .webhook_processor import WebhookProcessor


logging_setup.setup()

logger = logging.getLogger(__name__)

app = Flask(__name__)

processor = None
startup_error = ""

try:
    processor = WebhookProcessor(create_application())
except Exception as exc:
    startup_error = str(exc)
    logger.exception("Failed to start webhook processor")


@app.route("/")
def index():
    """
    Simple health-check page.
    """
    if processor is None:
        return f"Bot startup error: {startup_error}", 500

    return "Telegram campaign bot webhook is running."


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Telegram webhook endpoint.
    """
    if processor is None:
        abort(500)

    if config.WEBHOOK_SECRET:
        sent_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")

        if sent_secret != config.WEBHOOK_SECRET:
            logger.warning("Rejected webhook request with invalid secret")
            abort(403)

    data = request.get_json(silent=True)

    if not data:
        abort(400)

    try:
        processor.enqueue(data)
    except Exception:
        logger.exception("Could not enqueue Telegram update")
        abort(500)

    return "OK", 200
