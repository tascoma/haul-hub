import logging
import logging.handlers
from pathlib import Path

from app.core.config import settings

_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


def configure_logging() -> None:
    _LOG_DIR.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # Rotate at 10 MB, keep 5 backups
    file_handler = logging.handlers.RotatingFileHandler(
        _LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.addHandler(console)
    root.addHandler(file_handler)
