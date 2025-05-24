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
    parser.add_argument("--version", action="version", version=f"pdf2ocr {__version__}")
    return parser.parse_args()


def main():
    """Main entry point for the PDF OCR converter."""
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
            process_layout_pdf_only(config, logger)
        else:
            process_pdfs_with_ocr(config, logger)

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
