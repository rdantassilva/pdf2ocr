"""Logging configuration for pdf2ocr."""

import os
import sys
from datetime import datetime
from typing import Optional, TextIO

# Global variable to track the last message
_last_message = ""


def setup_logging(
    log_path: Optional[str] = None, quiet: bool = False, is_worker: bool = False
) -> TextIO:
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


def log_message(
    log_file, level: str, message: str, quiet: bool = False, summary: bool = False
) -> None:
    """Log a message to both console and file if log_file is provided.

    Args:
        log_file: TextIOWrapper or Logger instance or None
        level: Message level (INFO, WARNING, ERROR, DEBUG)
        message: Message to log
        quiet: Whether to suppress console output
        summary: Whether to show only summary information
    """
    global _last_message

    # Always log to file if provided
    if log_file:
        # Check if it's a logger object (has info method) or a file object
        if hasattr(log_file, "info"):
            # It's a logger object
            if level == "ERROR":
                log_file.error(message)
            elif level == "WARNING":
                log_file.warning(message)
            elif level == "DEBUG":
                log_file.debug(message)
            else:
                log_file.info(message)
        else:
            # It's a file object, write with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"{timestamp} - {level} - {message}\n"
            log_file.write(log_line)
            log_file.flush()  # Ensure message is written immediately

    # Determine message type
    is_error = level == "ERROR"
    is_warning = level == "WARNING"
    is_version = "PDF2OCR v" in message
    is_lang_info = "Using Tesseract language model:" in message
    is_summary = "Processing Summary:" in message

    # Determine if message should be shown in console
    if quiet:
        # In quiet mode, show ONLY errors
        should_print = is_error
    else:
        # In non-quiet mode:
        if summary:
            # Summary mode: show version, warnings, errors, language info, and final summary
            should_print = (
                is_error or is_warning or is_version or is_lang_info or is_summary
            )
        else:
            # Normal mode: show everything except ebook-convert output
            should_print = "ebook-convert" not in message

    if should_print:
        # Add WARNING prefix only for console output
        console_message = f"WARNING: {message}" if is_warning else message

        # Add a blank line before if this is a new section
        if _last_message and (is_warning or is_lang_info or is_version or is_summary):
            print()

        # Print the message with appropriate formatting
        if is_error:
            print(f"\033[91m{console_message}\033[0m", file=sys.stderr)  # Red text
        elif is_warning:
            print(f"\033[93m{console_message}\033[0m", file=sys.stderr)  # Yellow text
        elif level == "DEBUG":
            print(f"\033[90m{console_message}\033[0m")  # Gray text
        elif level == "HEADER":
            print(f"\033[1m{console_message}\033[0m")  # Bold text
        else:
            print(console_message)

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


def log_process_start(
    log_file: TextIO,
    filename: str,
    current: int,
    total: int,
    quiet: bool = False,
    summary: bool = False,
) -> None:
    """Log the start of processing a file."""
    msg = f"Processing file {current:02d} of {total:02d}: {filename}"
    log_message(log_file, "INFO", msg, quiet=quiet, summary=summary)


def log_conversion_summary(
    log_file: TextIO,
    total_files: int,
    total_time: float,
    quiet: bool = False,
    summary: bool = False,
) -> None:
    """Log conversion summary."""
    log_message(
        log_file, "HEADER", "=== Conversion Summary ===", quiet=quiet, summary=summary
    )
    log_message(
        log_file,
        "INFO",
        f"Total files processed: {total_files}",
        quiet=quiet,
        summary=summary,
    )
    log_message(
        log_file,
        "INFO",
        f"Total execution time: {total_time:.2f} seconds",
        quiet=quiet,
        summary=summary,
    )
    if total_files > 0:
        avg_time = total_time / total_files
        log_message(
            log_file,
            "INFO",
            f"Average time per file: {avg_time:.2f} seconds",
            quiet=quiet,
            summary=summary,
        )
