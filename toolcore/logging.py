import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logger(
    name: str,
    log_dir: Path,
    log_file_name: str,
    *,
    console_enabled: bool = False,
    console_level: int or None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 10,
) -> logging.Logger:
    """Configures a rotating file logger and optional console logging output."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
        
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / log_file_name
    
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    console_handler = logging.StreamHandler()
    c_level = console_level if console_level is not None else (logging.INFO if console_enabled else logging.WARNING)
    console_handler.setLevel(c_level)
    console_handler.setFormatter(formatter)
    
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
