"""
Utility module for logging setup and standardized logging across all project modules.

This module provides consistent logging configuration for both file and console output,
working identically on both Windows and Linux environments.

Functions:
    setup_logger(name): Creates and configures a logger for a module
    log_exception(logger, message, exc_info): Logs exception with traceback
    get_log_path(): Returns the path to the log directory
"""

import os
import sys
import logging
import datetime
import traceback
import platform


def get_log_path():
    """
    Returns the path to the logs directory, creating it if it doesn't exist.
    
    Returns:
        str: Absolute path to the logs directory
    """
    # Determine base directory (works in both package and direct execution)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Check if we're in the expected Mach3 directory structure
    if os.path.basename(os.path.dirname(base_dir)).lower() == 'scripts':
        # We're being imported from somewhere unexpected
        # Fall back to a location relative to the current file
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    log_dir = os.path.join(base_dir, 'Logs')
    
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    return log_dir


def setup_logger(name, level=logging.INFO, console_level=logging.WARNING):
    """
    Creates and configures a logger for a module.
    
    Args:
        name: Name of the logger (typically __name__ of the calling module)
        level: Logging level for file output (default: INFO)
        console_level: Logging level for console output (default: WARNING)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get the logger for this name
    logger = logging.getLogger(name)
    
    # Only configure if it hasn't been set up already
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create log file with today's date
        log_dir = get_log_path()
        today = datetime.datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f"system_{today}.log")
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        # Set formatters
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Log initialization
        logger.info(f"Logger initialized - {platform.system()} {platform.release()}")
    
    return logger


def log_exception(logger, message, exc_info=None):
    """
    Logs an exception with traceback.
    
    Args:
        logger: Logger instance to use
        message: Message describing what happened
        exc_info: Exception info (default: current exception from sys.exc_info())
    """
    if exc_info is None:
        exc_info = sys.exc_info()
    
    if exc_info[0] is not None:  # If there's an actual exception
        error_type = exc_info[0].__name__
        error_msg = str(exc_info[1])
        error_trace = ''.join(traceback.format_exception(*exc_info))
        
        logger.error(f"{message}: {error_type} - {error_msg}")
        logger.debug(f"Traceback:\n{error_trace}")
    else:
        logger.error(message)


# Example usage if run directly
if __name__ == "__main__":
    # Create a sample logger
    logger = setup_logger("logging_utils_test")
    
    # Log some messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test exception logging
    try:
        result = 1 / 0
    except Exception:
        log_exception(logger, "Error during division operation")
        
    print(f"Log file created at: {get_log_path()}")
