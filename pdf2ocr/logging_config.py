"""Logging configuration for pdf2ocr."""

import os
import sys
from datetime import datetime
from typing import Optional, TextIO

# Global variable to track the last message
_last_message = ""

def setup_logging(log_path: Optional[str] = None, quiet: bool = False, is_worker: bool = False) -> TextIO:
    """Set up logging to file with line buffering.
    
    Args:
        log_path: Optional path to log file
        quiet: Whether to suppress console output
        is_worker: Whether this is a worker process
        
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
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        
        # Only write the process start header for the main process
        if not is_worker:
            log_file.write("=== Process Started ===\n\n")
    
    return log_file


def log_message(logger, level: str, message: str, quiet: bool = False) -> None:
    """Log a message to both console and file if logger is provided.
    
    Args:
        logger: TextIOWrapper instance or None
        level: Log level (INFO, ERROR, etc)
        message: Message to log
        quiet: Whether to suppress console output
    """
    global _last_message
    
    # Skip empty messages if the previous message was also empty
    if message == "" and _last_message == "":
        return
    
    # Always log to file if logger is provided
    if logger:
        # Add timestamp and level for file logging
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"{timestamp} - {level} - {message}\n"
        
        # Add extra newlines for warnings and special messages
        if level == "WARNING":
            # Only add newline before if previous message wasn't empty
            if _last_message != "":
                log_line = "\n" + log_line
            log_line = log_line + "\n"
        elif "Using Tesseract language model:" in message:
            log_line = "\n" + log_line + "\n"
        elif "Processing file" in message:
            log_line = "\n" + log_line
        elif "Total time for file:" in message:
            log_line += "\n"
        
        logger.write(log_line)
        logger.flush()  # Ensure message is written immediately
    
    # Only print to console if not quiet
    if not quiet:
        if level == "ERROR":
            print(f"\033[91m{message}\033[0m", file=sys.stderr)  # Red text
        elif level == "WARNING":
            # Only print newline before if previous message wasn't empty
            if _last_message != "":
                print()
            print(f"\033[93m{message}\033[0m", file=sys.stderr)  # Yellow text
            print()  # Always print newline after
        elif level == "DEBUG":
            print(f"\033[90m{message}\033[0m")  # Gray text
        elif level == "HEADER":
            print(f"\033[1m{message}\033[0m")  # Bold text
        else:
            print(message)
    
    # Store the last message to help control spacing
    _last_message = message


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