"""Configure structured, privacy-conscious standard-library logging."""

import json
import logging
import threading
from datetime import UTC, datetime

_CONFIG_LOCK = threading.Lock()
_CONFIGURED_LEVEL: int | None = None


class PrivacySafeJsonFormatter(logging.Formatter):
    """Serialize only approved operational fields; omit exception messages."""

    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, str] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            event["exception_type"] = record.exc_info[0].__name__
        return json.dumps(event, ensure_ascii=True)


def configure_logging(level: str = "INFO") -> None:
    """Configure the process logger once, without repeatedly adding handlers."""
    global _CONFIGURED_LEVEL

    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise TypeError(f"Unsupported LOG_LEVEL: {level}")
    with _CONFIG_LOCK:
        root_logger = logging.getLogger()
        if _CONFIGURED_LEVEL is None:
            if root_logger.handlers:
                for handler in root_logger.handlers:
                    handler.setFormatter(PrivacySafeJsonFormatter())
            else:
                handler = logging.StreamHandler()
                handler.setFormatter(PrivacySafeJsonFormatter())
                root_logger.addHandler(handler)
        root_logger.setLevel(numeric_level)
        _CONFIGURED_LEVEL = numeric_level
