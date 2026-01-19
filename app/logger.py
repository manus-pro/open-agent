import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

def setup_logger(name, level=logging.INFO, log_file=None, rotation='midnight', format_str=None):
    """
    Set up a logger with configurable settings.
    
    Args:
        name (str): Logger name
        level (int): Logging level
        log_file (str, optional): Path to log file
        rotation (str, optional): Log rotation interval
        format_str (str, optional): Log format string
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Use default format if none provided
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_str)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log file is specified)
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            
        file_handler = TimedRotatingFileHandler(
            log_file, 
            when=rotation,
            backupCount=7
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name="open-agent", config=None):
    """
    Get a logger with configuration from the config file.
    
    Args:
        name (str, optional): Logger name
        config (dict, optional): Configuration dictionary
        
    Returns:
        logging.Logger: Configured logger
    """
    if config is None:
        return setup_logger(name)
    
    log_config = config.get("logging", {})
    
    # Parse log level
    level_str = log_config.get("level", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    
    # Get log file path
    log_file = log_config.get("file")
    
    # Get rotation
    rotation = log_config.get("rotation", "midnight")
    
    # Get format
    format_str = log_config.get("format")
    
    return setup_logger(name, level, log_file, rotation, format_str)
