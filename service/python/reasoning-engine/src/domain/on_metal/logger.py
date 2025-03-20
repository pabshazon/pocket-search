import logging
from typing import Optional
from src.config.logger_config import LoggerConfig

_logger_config: Optional[LoggerConfig] = None

def init_logging(
    show_filepath: bool = False,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> None:
    """
    Initialize logging configuration. Should be called once at application startup.
    """
    global _logger_config
    if _logger_config is not None:
        return  # Already initialized
    
    _logger_config = LoggerConfig(show_filepath=show_filepath)
    _logger_config.configure(level=level, log_file=log_file)

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a configured logger instance.
    If logging hasn't been initialized, initializes with default settings.
    """
    if _logger_config is None:
        init_logging()  # Initialize with defaults if not done explicitly
    return logging.getLogger(name)
