"""Logging configuration for pdf2ocr."""

import os
import sys
from datetime import datetime
from typing import Optional, TextIO


def setup_logging(log_path: Optional[str] = None, quiet: bool = False) -> TextIO:
    """Set up logging to file with line buffering.
    
    Args:
        log_path: Optional path to log file
        quiet: Whether to suppress console output
        
    Returns:
        TextIO: Log file handle if log_path is provided, None otherwise
    """
    log_file = None
    
    if log_path:
        # Create directory if needed
        dir_name = os.path.dirname(log_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # Open log file with line buffering
        log_file = open(log_path, "w", encoding="utf-8", buffering=1)
        log_file.write("=== Process Started ===\n\n")
    
    return log_file


def log_message(logger, level, message, quiet=False):
    """Log a message to both file and console.
    
    Args:
        logger: Logger object or None for console-only output
        level: Message level (DEBUG, INFO, WARNING, ERROR)
        message: Message text
        quiet: Whether to suppress console output
    """
    if logger:
        # Add timestamp and level for file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"{timestamp} - {level} - {message}\n"
        
        # Add extra newlines for warnings and special messages
        if level == "WARNING":
            log_message = "\n" + log_message + "\n"
        elif "Using Tesseract language model:" in message:
            log_message = "\n" + log_message + "\n"
        elif "Processing file" in message:
            log_message = "\n" + log_message
        elif "Total time for file:" in message:
            log_message += "\n"
        
        logger.write(log_message)
        
    if not quiet:
        # Format message based on level and terminal support
        if sys.stdout.isatty():  # Terminal supports colors
            if level == "DEBUG":
                message = f"\033[36m{message}\033[0m"  # Cyan
            elif level == "INFO":
                pass  # No color for INFO
            elif level == "WARNING":
                # Add WARNING: prefix and color
                message = f"\033[33m\nWARNING: {message}\n\033[0m"  # Yellow
            elif level == "ERROR":
                message = f"\033[31m{message}\033[0m"  # Red
            elif level == "HEADER":
                message = f"\033[1;34m{message}\033[0m"  # Bold Blue
        else:
            # Add WARNING: prefix for non-color terminals
            if level == "WARNING":
                message = f"\nWARNING: {message}\n"
        
        # Add extra newlines for special messages
        if "Using Tesseract language model:" in message:
            message = "\n" + message
        elif "Processing file" in message:
            message = "\n" + message
        elif "Total time for file:" in message:
            message += "\n"
        elif "Conversion Summary" in message:
            message = "\n" + message
        
        print(message)


def close_logging(log_file: Optional[TextIO]) -> None:
    """Close the log file if open.
    
    Args:
        log_file: Optional file handle to close
    """
    if log_file:
        log_file.write("\n=== Process Completed ===\n")
        log_file.close()


def log_process_start(logger: TextIO, filename: str, current: int, total: int, quiet: bool = False) -> None:
    """Log the start of processing a file."""
    msg = f"Processing file {current:02d} of {total:02d}: {filename}"
    log_message(logger, "INFO", msg, quiet=quiet)


def log_process_complete(logger: TextIO, elapsed: float, quiet: bool = False) -> None:
    """Log completion of file processing."""
    msg = f"Total time for file: {elapsed:.2f} seconds"
    log_message(logger, "INFO", msg, quiet=quiet)


def log_conversion_summary(logger: TextIO, total_files: int, total_time: float, quiet: bool = False) -> None:
    """Log conversion summary."""
    log_message(logger, "HEADER", "=== Conversion Summary ===", quiet=quiet)
    log_message(logger, "INFO", f"Total files processed: {total_files}", quiet=quiet)
    log_message(logger, "INFO", f"Total execution time: {total_time:.2f} seconds", quiet=quiet)
    if total_files > 0:
        avg_time = total_time / total_files
        log_message(logger, "INFO", f"Average time per file: {avg_time:.2f} seconds", quiet=quiet) 