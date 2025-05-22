"""Utility functions for pdf2ocr."""

import platform
import shutil
import sys
from typing import Optional
from contextlib import contextmanager
import time
from logging import Logger

from pdf2ocr.logging_config import setup_logging, log_message


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
        package_managers = ['apt', 'dnf', 'yum']
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
        log_message(logger, "INFO", "Please install the required dependencies and try again.")
        sys.exit(1)


@contextmanager
def timing_context(operation_name: str, logger: Optional[Logger] = None) -> float:
    """Context manager for timing operations.
    
    Args:
        operation_name: Name of the operation being timed
        logger: Optional logger to log the timing information
        
    Returns:
        float: Duration of the operation in seconds
        
    Example:
        with timing_context("PDF Processing", logger) as duration:
            process_pdf(file)
            print(f"Operation took {duration:.2f} seconds")
    """
    start_time = time.perf_counter()
    try:
        yield lambda: time.perf_counter() - start_time
    finally:
        duration = time.perf_counter() - start_time
        return duration 