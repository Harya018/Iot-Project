"""
utils/logger.py — Centralised logging configuration.

Call configure_logging() once at application startup.
"""

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a consistent format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
