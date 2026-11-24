import logging
import sys


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures structured logging that strictly avoids logging PII, bodies or chat text."""
    logger = logging.getLogger("pothsathi")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    return logger


logger = setup_logging()
