import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

# constants
LOG_FORMAT_CONSOLE="%(levelname)s:    %(message)s"
LOG_FORMAT_FILE="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Configures and returns a structured logger instance.

    This logger sends:
    1. INFO messages and above to the Console (stdout).
    2. DEBUG messages and above to a rotating log file in the /logs directory.

    Args:
        name (str): The name of the logger (usually __name__).
        log_level (str): The default logging level (default: "INFO").

    Returns:
        logging.Logger: A configured logger instance.
    """
    # 1. Determine the Project Root and Logs Directory
    # We go up 3 levels from /src/utils/logger.py to get to /backend
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    log_dir = os.path.join(backend_root, "logs")

    os.makedirs(log_dir, exist_ok=True)
    
    # 2. Initialize Logger
    logger = logging.getLogger(name)
    
    # If logger already has handlers, return it to avoid duplicate logs
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG) # Capture everything at the root level

    # 3. Console Handler (Standard Output) - For human readability
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_format = logging.Formatter(LOG_FORMAT_CONSOLE)
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # 4. File Handler (Rotating) - For deep debugging history
    # Keeps 3 backup files of 5MB each
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "sentinell.log"),
        maxBytes=5 * 1024 * 1024, # 5 MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(LOG_FORMAT_FILE)
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger

