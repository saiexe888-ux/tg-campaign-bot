import logging
from logging.handlers import RotatingFileHandler

from . import config


def setup() -> None:
    """
    Configure logging: console + logs/bot.log
    """
    root = logging.getLogger()
    root.handlers.clear()

    level = getattr(logging, config.LOG_LEVEL, logging.INFO)

    handlers = [
        logging.StreamHandler()
    ]

    try:
        log_dir = config.BASE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_dir / "bot.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handlers.append(file_handler)
    except Exception:
        pass

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=level,
        handlers=handlers,
    )

    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
