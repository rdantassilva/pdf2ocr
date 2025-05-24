"""EPUB conversion and processing functionality."""

import os
import shutil
import subprocess
import time
from typing import Optional

from pdf2ocr.logging_config import log_message

# Map Tesseract language codes to Calibre language codes
TESS_TO_CALIBRE_LANG = {
    "por": "pt",  # Portuguese
    "eng": "en",  # English
    "spa": "es",  # Spanish
    "fra": "fr",  # French
    "deu": "de",  # German
    "ita": "it",  # Italian
    "nld": "nl",  # Dutch
    "rus": "ru",  # Russian
    "tur": "tr",  # Turkish
    "jpn": "ja",  # Japanese
    "chi_sim": "zh",  # Chinese
    "chi_tra": "zh",  # Chinese
    "chi_sim_vert": "zh",  # Chinese
    "chi_tra_vert": "zh",  # Chinese
    "heb": "he",  # Hebrew
}


def is_calibre_available() -> bool:
    """Check if Calibre's ebook-convert is available in the system.

    Returns:
        bool: True if ebook-convert is available, False otherwise
    """
    return shutil.which("ebook-convert") is not None


def check_calibre_requirement(logger=None, quiet=False) -> None:
    """Check if Calibre is installed and provide installation instructions if not.

    Args:
        logger: Optional logger instance
        quiet: Whether to suppress console output

    Raises:
        RuntimeError: If Calibre is not installed
    """
    if not is_calibre_available():
        error_msg = (
            "Calibre is required for EPUB conversion but was not found. "
            "Please install it using one of these methods:\n\n"
            "macOS (using Homebrew):\n"
            "  brew install --cask calibre\n\n"
            "Linux (Debian/Ubuntu):\n"
            "  sudo apt-get install calibre\n\n"
            "Linux (Fedora):\n"
            "  sudo dnf install calibre\n\n"
            "Windows:\n"
            "  Download from https://calibre-ebook.com/download\n\n"
            "After installing, make sure 'ebook-convert' is available in your system PATH.\n"
            "On macOS, you may need to add Calibre to your PATH:\n"
            '  export PATH="$PATH:/Applications/calibre.app/Contents/MacOS"'
        )
        log_message(logger, "ERROR", error_msg, quiet=quiet)
        raise RuntimeError("Calibre not found")


def convert_docx_to_epub(docx_path, epub_path, logger=None, quiet=False, lang="por"):
    """Converts DOCX to EPUB using Calibre.

    Args:
        docx_path: Path to input DOCX file
        epub_path: Path to output EPUB file
        logger: Optional logger instance
        quiet: Whether to suppress output
        lang: Language code for the document

    Returns:
        tuple: (success: bool, processing_time: float, output: str)
    """
    start = time.perf_counter()
    try:
        title = os.path.splitext(os.path.basename(str(epub_path)))[0].replace("_", " ")

        calibre_lang = TESS_TO_CALIBRE_LANG.get(lang)

        cmd = [
            "ebook-convert",
            docx_path,
            epub_path,
            "--title",
            title,
            "--authors",
            "pdf2ocr",
            "--comments",
            "Converted by pdf2ocr",
            "--level1-toc",
            "//h:h1",
        ]

        if calibre_lang:
            cmd += ["--language", calibre_lang]

        # Log the command being executed
        if logger:
            log_message(
                logger,
                "INFO",
                f"Running ebook-convert for {os.path.basename(docx_path)}:\n{' '.join(cmd)}",
                quiet=True,  # Never show in console
            )

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        # Log stdout and stderr if any
        if logger:
            if result.stdout:
                log_message(
                    logger,
                    "INFO",
                    f"ebook-convert output for {os.path.basename(docx_path)}:\n{result.stdout}",
                    quiet=True,  # Never show in console
                )
            if result.stderr:
                log_message(
                    logger,
                    "INFO",
                    f"ebook-convert messages for {os.path.basename(docx_path)}:\n{result.stderr}",
                    quiet=True,  # Never show in console
                )

        return True, time.perf_counter() - start, result.stdout

    except subprocess.CalledProcessError as e:
        error_msg = f"Error converting {os.path.basename(docx_path)} to EPUB"
        if e.stderr:
            error_msg += f": {e.stderr.strip()}"
            # Log the full error output to file
            if logger:
                log_message(
                    logger,
                    "ERROR",
                    f"Full ebook-convert error output:\n{e.stderr}",
                    quiet=True,  # Log to file only
                )
        log_message(logger, "ERROR", error_msg, quiet=False)  # Show error in console
        return False, time.perf_counter() - start, e.stderr
    except Exception as e:
        error_msg = f"Error converting {os.path.basename(docx_path)} to EPUB: {str(e)}"
        log_message(logger, "ERROR", error_msg, quiet=False)  # Show error in console
        return False, time.perf_counter() - start, ""
