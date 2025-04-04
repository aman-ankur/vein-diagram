import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Set up centralized logging configuration for the application.
    This configures both file and console handlers with appropriate log levels.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Remove all existing handlers to prevent duplicate logging
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    # Common format for all logs
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler - only show INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for application logs - rotating file handler to manage size
    app_log_path = os.path.join(log_dir, 'app.log')
    file_handler = RotatingFileHandler(
        app_log_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Configure specific loggers with custom levels
    loggers_config = {
        'uvicorn': logging.WARNING,  # Reduce uvicorn logs
        'uvicorn.access': logging.WARNING,  # Reduce access logs
        'uvicorn.error': logging.ERROR,  # Keep error logs
        'fastapi': logging.WARNING,  # Reduce FastAPI framework logs
        'app.api': logging.WARNING,  # Reduce API logs except errors
        'app.core.auth': logging.WARNING,  # Reduce auth logs
        'app.db': logging.WARNING,  # Reduce DB logs except errors
        'app.services': logging.WARNING,  # Reduce service logs except errors
        'app.models': logging.WARNING,  # Reduce model logs except errors
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        # Prevent logger from propagating to root logger to avoid duplicate logs
        logger.propagate = False
        # Add handlers directly to this logger
        logger.handlers = [console_handler, file_handler]

    # Disable certain DEBUG logs that are too verbose
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    # Create a separate error log file for ERROR and above
    error_log_path = os.path.join(log_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler) 