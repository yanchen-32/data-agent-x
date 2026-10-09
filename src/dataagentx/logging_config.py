import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """给整个进程配置一次根 logger。"""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)