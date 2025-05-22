# coding:utf-8

"""
A CLI tool to apply OCR on PDF files and export to multiple formats.

Description of Libraries:
- 📜 PIL/Pillow: Image processing (open, convert and enhance images for OCR)
- 🔍 pytesseract: Python interface for Tesseract OCR (text recognition in images)
- 📊 tqdm: Displays progress bars for long operations
- 📄 pdf2image: Converts PDF pages to images for processing
- 📝 python-docx: Creates and manipulates Word documents (.docx)
- 🖨️ reportlab: Programmatic PDF generation
- 🏷️ tesseract-ocr: OCR engine (optical character recognition)
- 🖼️ poppler-utils: PDF manipulation tools (includes pdftoppm)
- 📚 calibre: E-book management suite (provides ebook-convert)
- 🐍 pypdf: Merge per-page searchable PDFs into one (layout-preserving PDF mode)

PDF Generation Modes:
1. Layout-Preserving Mode (--preserve-layout):
   - Maintains exact visual appearance of original document
   - Adds invisible OCR text layer for searchability
   - Best for forms, scientific papers, magazines
   - Uses lower DPI (200) to optimize file size
   - Output in 'pdf_ocr_layout' directory

2. Standard Mode (default):
   - Creates new PDF with clean, consistent formatting
   - Focuses on text readability and accessibility
   - Best for books, articles, general documents
   - Uses standard fonts and margins
   - Output in 'pdf_ocr' directory

Conversion Flow:
1. 📄 pdf2image uses `pdftoppm` to convert PDFs to images
2. 🖼️ pytesseract uses `tesseract-ocr` to extract text from images
3. 📝 python-docx generates Word documents with extracted text
4. 🖨️ reportlab creates PDFs with OCR-processed text
5. 📚 calibre (optional) converts DOCX to EPUB using `ebook-convert`

Important Notes:
- To generate EPUB, Calibre must be installed on the system
- The `ebook-convert` command must be available in PATH
- Very large files may require more time and memory
- OCR quality depends on the original PDF clarity
- The script creates separate folders for each output type (docx, pdf, epub)
"""

import argparse
import signal
import sys

from pdf2ocr import __version__
from pdf2ocr.config import ProcessingConfig
from pdf2ocr.converters import (process_pdfs_with_ocr, process_layout_pdf_only)
from pdf2ocr.logging_config import close_logging, log_message, setup_logging
from pdf2ocr.ocr import validate_tesseract_language
from pdf2ocr.state import shutdown_requested


def signal_handler(signum, frame):
    """Handle interrupt signals for graceful shutdown"""
    global shutdown_requested
    if shutdown_requested:  # If CTRL+C is pressed twice, force exit
        log_message(None, "WARNING", "\nForce quitting...", quiet=False)
        sys.exit(1)
    shutdown_requested = True
    log_message(
        None,
        "WARNING",
        "\nShutdown requested. Waiting for current tasks to complete...",
        quiet=False,
    )


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


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
    parser.add_argument("--version", action="version", version=f"pdf2ocr {__version__}")
    return parser.parse_args()


def main():
    """Main entry point for the PDF OCR converter."""
    args = parse_arguments()

    try:
        # Create configuration from arguments
        config = ProcessingConfig(
            source_dir=args.source_dir,
            dest_dir=args.dest_dir,
            lang=args.lang,
            generate_pdf=args.pdf,
            generate_html=args.html,
            generate_docx=args.docx,
            generate_epub=args.epub,
            preserve_layout=args.preserve_layout,
            quiet=args.quiet,
            summary_output=args.summary,
            log_path=args.logfile,
            workers=args.workers,
        )

        # Setup logging
        logger = setup_logging(config.log_path, config.quiet)

        try:
            # Show version info and validate language only in normal mode (not quiet, not summary)
            show_header = not (config.quiet or config.summary_output)

            # Show version info first
            log_message(
                logger, "HEADER", f"PDF2OCR v{__version__}", quiet=not show_header
            )
            log_message(
                logger, "INFO", "", quiet=not show_header
            )  # Add empty line after version

            # Validate Tesseract language
            validate_tesseract_language(args.lang, logger, not show_header)

            # Process PDFs
            if config.preserve_layout:
                process_layout_pdf_only(config, logger)
            else:
                process_pdfs_with_ocr(config, logger)

        finally:
            close_logging(logger)

    except Exception as e:
        if not args.quiet:
            log_message(None, "ERROR", str(e), quiet=args.quiet)
        sys.exit(1)


if __name__ == "__main__":
    main()
