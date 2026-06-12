import logging
from raglib.config import RAG_LOG_BACKUP_COUNT, RAG_LOG_CONSOLE, RAG_LOG_DIR, RAG_LOG_MAX_BYTES
from toolcore.logging import configure_logger as shared_configure_logger


def configure_logger(name: str, log_file_name: str) -> logging.Logger:
    """Configures logger by delegating to shared toolcore logger configuration."""
    return shared_configure_logger(
        name,
        RAG_LOG_DIR,
        log_file_name,
        console_enabled=RAG_LOG_CONSOLE,
        max_bytes=RAG_LOG_MAX_BYTES,
        backup_count=RAG_LOG_BACKUP_COUNT
    )
