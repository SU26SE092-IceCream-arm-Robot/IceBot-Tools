import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from raglib.config import RAG_LOG_BACKUP_COUNT, RAG_LOG_CONSOLE, RAG_LOG_DIR, RAG_LOG_MAX_BYTES


def configure_logger(name: str, log_file_name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    RAG_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = Path(RAG_LOG_DIR) / log_file_name

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if RAG_LOG_CONSOLE else logging.WARNING)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=RAG_LOG_MAX_BYTES,
        backupCount=RAG_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
