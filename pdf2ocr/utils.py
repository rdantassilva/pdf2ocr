"""Utility functions for pdf2ocr."""

import platform
import shutil
import sys
from typing import Optional

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