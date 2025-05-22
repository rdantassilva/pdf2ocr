"""Utility functions for pdf2ocr."""

import platform
import shutil
import sys
import time
from contextlib import contextmanager
from logging import Logger
from typing import Optional

from pdf2ocr.logging_config import log_message, setup_logging


class Timer:
    """A simple timer class that can be pickled."""

    def __init__(self):
        self.start_time = time.perf_counter()
        self.duration = None

    def stop(self):
        """Stop the timer and return the duration."""
        if self.duration is None:  # Only update if not already stopped
            self.duration = time.perf_counter() - self.start_time
        return self.duration

    def __call__(self):
        """Get the current duration without stopping."""
        if self.duration is not None:  # If already stopped, return stored duration
            return self.duration
        return time.perf_counter() - self.start_time


def detect_package_manager() -> Optional[str]:
    """Detect the system's package manager.

    Returns:
        str: Package manager name ('brew', 'apt', 'dnf', 'yum') or None if not found
    """
    system = platform.system()

    if system == "Darwin":
        if shutil.which("brew"):
            return "brew"
    elif system == "Linux":
        package_managers = ["apt", "dnf", "yum"]
        for pm in package_managers:
            if shutil.which(pm):
                return pm
    return None


def check_dependencies(generate_epub=False):
    """Checks if required system dependencies are installed.

    Args:
        generate_epub (bool): Whether to check for Calibre dependency

    Raises:
        SystemExit: If any required dependency is missing
    """
    logger = setup_logging()

    missing = []

    # Check for required dependencies
    if not shutil.which("tesseract"):
        missing.append("tesseract")
    if not shutil.which("pdftoppm"):
        missing.append("pdftoppm")
    if generate_epub and not shutil.which("ebook-convert"):
        missing.append("ebook-convert (Calibre)")

    if missing:
        log_message(logger, "ERROR", f"Missing dependencies: {', '.join(missing)}")
        log_message(
            logger, "INFO", "Please install the required dependencies and try again."
        )
        sys.exit(1)


@contextmanager
def timing_context(
    operation_name: str, logger: Optional[Logger] = None, log_timing: bool = False
) -> Timer:
    """Context manager for timing operations.

    Args:
        operation_name: Name of the operation being timed
        logger: Optional logger to log the timing information
        log_timing: Whether to log the timing message (default: False)

    Yields:
        Timer: A Timer object that can be used to get the duration

    Example:
        with timing_context("PDF Processing", logger) as timer:
            process_pdf(file)
            # timer() will give the current duration
            # timer.stop() will give the final duration
    """
    timer = Timer()
    try:
        yield timer
    finally:
        duration = timer.stop()
        if logger and log_timing:
            log_message(
                logger,
                "INFO",
                f"  {operation_name} took {duration:.2f} seconds",
                quiet=False,
            )
