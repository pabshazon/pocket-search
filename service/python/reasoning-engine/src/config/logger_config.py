import logging
import os

from typing import Optional

class LoggerConfig:
    def __init__(self, show_filepath: bool = False):
        self.show_filepath = show_filepath
        
    def get_format_string(self) -> str:
        """Returns the format string based on configuration"""
        base_format = '[%(asctime)s - %(levelname)s] %(message)s'
        filepath_format = ' - %(pathname)s:%(lineno)d'
        
        return f'{base_format}{filepath_format}' if self.show_filepath else f'{base_format}'
    
    def configure(
        self,
        level: int = logging.INFO,  # @todo fix issue that this overrides main.py config
        log_file: Optional[str] = None
    ) -> None:
        """Configure the root logger with the specified settings"""
        formatter = logging.Formatter(
            fmt=self.get_format_string(),
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Clear any existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
