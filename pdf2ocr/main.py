# coding:utf-8

"""Main entry point module for pdf2ocr CLI application.

This module provides the command-line interface and main execution flow for pdf2ocr.
It handles argument parsing, configuration setup, signal handling, and orchestrates
the PDF processing workflow.

Key Functions:
- parse_arguments(): Configure and parse command-line arguments
- signal_handler(): Handle graceful shutdown on interruption signals
- main(): Main entry point that coordinates the entire processing workflow

Command Line Arguments:
- source_dir: Directory containing PDF files to process
- --dest-dir: Optional destination directory for output files
- --pdf, --docx, --html, --epub: Output format selection
- --preserve-layout: Enable layout-preserving PDF mode
- --lang: OCR language code (default: Portuguese)
- --workers: Number of parallel processing workers
- --batch-size: Pages per batch for memory management
- --dpi: Image resolution for OCR processing (72-1200)
- --quiet, --summary: Output verbosity control
- --logfile: Optional log file path

Processing Flow:
1. Parse and validate command-line arguments
2. Create ProcessingConfig with user settings
3. Set up logging and validate Tesseract language
4. Route to appropriate processing function based on mode
5. Handle graceful shutdown and cleanup

Error Handling:
- Validates argument ranges and dependencies
- Provides clear error messages for invalid configurations
- Supports graceful interruption with Ctrl+C
- Ensures proper cleanup of resources
"""

import argparse
import signal
import sys
import time

from pdf2ocr import __version__
from pdf2ocr.config import ProcessingConfig
from pdf2ocr.converters import process_layout_pdf_only, process_pdfs_with_ocr
from pdf2ocr.logging_config import close_logging, log_message, setup_logging
from pdf2ocr.ocr import LANG_NAMES, validate_tesseract_language
from pdf2ocr.state import force_exit, is_shutdown_requested, request_shutdown


def signal_handler(signum, frame):
    """Handle interrupt signals for graceful shutdown"""
    if is_shutdown_requested():  # If CTRL+C is pressed twice
        log_message(None, "WARNING", "\nForce quitting...", quiet=False, summary=False)
        force_exit()
        sys.exit(1)

    request_shutdown()
    log_message(
        None,
        "WARNING",
        "\nShutdown requested. Waiting for current tasks to complete...",
        quiet=False,
        summary=False,
    )


def parse_arguments():
    """Configure and parse command line arguments"""
    parser = argparse.ArgumentParser(
        description=f"pdf2ocr v{__version__} - A CLI tool to apply OCR on PDF files and export to multiple formats."
    )
    parser.add_argument("source_dir", help="Source folder with PDF files")
    parser.add_argument(
        "--dest-dir",
        help="Destination folder (optional, defaults to input folder)",
        default=None,
    )
    parser.add_argument("--docx", action="store_true", help="Generate DOCX files")
    parser.add_argument(
        "--pdf", action="store_true", help="Generate OCR-processed PDF files"
    )
    parser.add_argument("--html", action="store_true", help="Generate html files")
    parser.add_argument(
        "--epub",
        action="store_true",
        help="Generate EPUB files (auto-enables --docx if needed)",
    )
    parser.add_argument(
        "--preserve-layout",
        action="store_true",
        help="Preserve original document layout in PDF output. Best for forms, scientific papers, "
        "and documents where visual formatting is important. Creates output in 'pdf_ocr_layout' directory.",
    )
    parser.add_argument(
        "--lang",
        default="por",
        help="OCR language code (default: por). Use `tesseract --list-langs` to view options.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run silently without progress output",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display only final conversion summary",
    )
    parser.add_argument(
        "--logfile",
        help="Path to log file (optional)",
        default=None,
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Number of parallel workers for processing (default: 2)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of pages to process in each batch (disabled by default)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=400,
        help="DPI for PDF to image conversion (default: 400). Higher values improve OCR quality but increase processing time.",
    )
    parser.add_argument("--version", action="version", version=f"pdf2ocr {__version__}")
    return parser.parse_args()


def main():
    """Main entry point for the PDF OCR converter."""
    # Record start time for total execution measurement
    start_time = time.time()
    logger = None  # Initialize logger to None
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        args = parse_arguments()

        # Validate arguments
        if args.workers < 1:
            print("Error: --workers must be at least 1")
            sys.exit(1)

        if args.batch_size is not None and args.batch_size < 1:
            print("Error: --batch-size must be at least 1")
            sys.exit(1)

        if args.dpi < 72 or args.dpi > 1200:
            print("Error: --dpi must be between 72 and 1200")
            sys.exit(1)

        # Create processing configuration
        config = ProcessingConfig(
            source_dir=args.source_dir,
            dest_dir=args.dest_dir,
            generate_pdf=args.pdf,
            generate_docx=args.docx,
            generate_html=args.html,
            generate_epub=args.epub,
            preserve_layout=args.preserve_layout,
            lang=args.lang,
            quiet=args.quiet,
            summary=args.summary,
            log_path=args.logfile,
            workers=args.workers,
            batch_size=args.batch_size,
            dpi=args.dpi,
        )

        # Set up logging
        logger = setup_logging(config.log_path, config.quiet)

        # Validate Tesseract language
        try:
            validate_tesseract_language(config.lang, logger, config.quiet)
        except RuntimeError as e:
            print(f"Error: {e}")
            sys.exit(1)

        # Show version information and language model info
        log_message(
            logger,
            "INFO",
            f"PDF2OCR v{__version__}",
            quiet=config.quiet,
            summary=config.summary,
        )
        log_message(
            logger,
            "INFO",
            f"Using Tesseract language model: {config.lang} ({LANG_NAMES.get(config.lang, 'Unknown')})",
            quiet=config.quiet,
            summary=config.summary,
        )

        # Process PDFs based on layout preservation setting
        if config.preserve_layout:
            process_layout_pdf_only(config, logger, start_time)
        else:
            process_pdfs_with_ocr(config, logger, start_time)

    except KeyboardInterrupt:
        if not is_shutdown_requested():
            print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing PDFs: {str(e)}")
        sys.exit(1)
    finally:
        if logger:
            close_logging(logger)


if __name__ == "__main__":
    main()
