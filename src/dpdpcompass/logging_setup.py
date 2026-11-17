import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=level,
        format='{"level":"%(levelname)s","msg":"%(message)s"}',
        stream=sys.stdout,
    )
