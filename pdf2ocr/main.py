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
import io
import os
import time
import sys
import signal
from concurrent import futures
from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter, PdfMerger
from pytesseract import image_to_pdf_or_hocr
from tqdm import tqdm
import logging
from pypdf.generic import NameObject, DictionaryObject, ArrayObject, IndirectObject
import subprocess
import tempfile

from pdf2ocr import __version__
from pdf2ocr.config import ProcessingConfig
from pdf2ocr.converters import (convert_docx_to_epub, save_as_docx, save_as_html,
                               save_as_pdf)
from pdf2ocr.logging_config import (log_conversion_summary, log_process_complete,
                                  log_process_start, setup_logging, close_logging,
                                  log_message)
from pdf2ocr.ocr import (extract_text_from_pdf, validate_tesseract_language,
                        process_pdf_with_ocr, convert_image_to_pdf,
                        make_invisible_text_layer)
from pdf2ocr.utils import check_dependencies, timing_context

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle interrupt signals for graceful shutdown"""
    global shutdown_requested
    if shutdown_requested:  # If CTRL+C is pressed twice, force exit
        log_message(None, "WARNING", "\nForce quitting...", quiet=False)
        sys.exit(1)
    shutdown_requested = True
    log_message(None, "WARNING", "\nShutdown requested. Waiting for current tasks to complete...", quiet=False)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def process_single_pdf(filename: str, config: ProcessingConfig) -> tuple:
    """Process a single PDF file.
    
    Args:
        filename: Name of the PDF file to process
        config: Processing configuration
        
    Returns:
        tuple: (success: bool, processing_time: float, error_message: str, log_messages: list)
    """
    # Setup logging for this process
    logger = setup_logging(config.log_path, config.quiet, is_worker=True)
    log_messages = []
    
    try:
        pdf_path = os.path.join(config.source_dir, filename)
        base_name = os.path.splitext(filename)[0]
        
        with timing_context(f"Processing {filename}", logger) as get_file_time:
            try:
                # Process PDF pages with OCR
                pages = process_pdf_with_ocr(pdf_path, config.lang, logger, config.quiet, config.summary_output)
                page_texts = [text for _, text in pages]
                
                # Generate output files based on configuration
                output_files = []
                
                if config.generate_pdf:
                    pdf_path = os.path.join(config.pdf_dir, base_name + "_ocr.pdf")
                    with timing_context("PDF generation", logger) as get_pdf_time:
                        save_as_pdf(page_texts, pdf_path, base_name)
                        output_files.append(("PDF", get_pdf_time()))
                
                if config.generate_html:
                    html_path = os.path.join(config.html_dir, base_name + ".html")
                    with timing_context("HTML generation", logger) as get_html_time:
                        save_as_html(page_texts, html_path)
                        output_files.append(("HTML", get_html_time()))
                
                if config.generate_docx:
                    docx_path = os.path.join(config.docx_dir, base_name + ".docx")
                    with timing_context("DOCX generation", logger) as get_docx_time:
                        save_as_docx(page_texts, docx_path)
                        output_files.append(("DOCX", get_docx_time()))
                    
                    if config.generate_epub:
                        epub_path = os.path.join(config.epub_dir, base_name + ".epub")
                        with timing_context("EPUB generation", logger) as get_epub_time:
                            success, _, output = convert_docx_to_epub(docx_path, epub_path, config.lang)
                            # Log ebook-convert output only to file (force quiet=True)
                            if output and logger:
                                log_message(logger, "INFO", f"ebook-convert output for {filename}:", quiet=True)
                                log_message(logger, "INFO", output, quiet=True)
                            if success:
                                output_files.append(("EPUB", get_epub_time()))
                            else:
                                raise Exception(f"EPUB conversion failed: {output}")
                
                # Generate log messages for all successful outputs
                log_messages.extend([
                    ("INFO", f"{format} created in {time:.2f} seconds")
                    for format, time in output_files
                ])
                
                return True, get_file_time(), None, log_messages
                
            except Exception as e:
                # Add context to the error message
                error_msg = f"Error in {filename} during {e.__class__.__name__}: {str(e)}"
                log_messages.append(("ERROR", error_msg))
                return False, get_file_time(), error_msg, log_messages

    except Exception as e:
        # Handle setup/initialization errors
        error_msg = f"Failed to initialize processing for {filename}: {str(e)}"
        log_messages.append(("ERROR", error_msg))
        return False, 0, error_msg, log_messages
        
    finally:
        # Ensure logger is properly closed
        if logger and hasattr(logger, 'close'):
            logger.close()


def process_pdfs_with_ocr(config: ProcessingConfig, logger: logging.Logger):
    """Main function that orchestrates the entire conversion process"""
    
    global shutdown_requested
    
    # Helper function to determine if we should show a message in console
    def should_show_message():
        if config.quiet:  # In quiet mode, show nothing
            return False
        if config.summary_output:  # In summary mode, show nothing except summary
            return False
        return True  # In normal mode, show everything
    
    # Validate configuration
    config.validate()
    
    try:
        # Create output directories
        os.makedirs(config.get_effective_dest_dir(), exist_ok=True)
        if config.generate_docx:
            os.makedirs(config.docx_dir, exist_ok=True)
            log_message(logger, "DEBUG", f"DOCX folder created - {config.docx_dir}", quiet=not should_show_message())
        if config.generate_pdf:
            os.makedirs(config.pdf_dir, exist_ok=True)
            log_message(logger, "DEBUG", f"PDF folder created - {config.pdf_dir}", quiet=not should_show_message())
        if config.generate_epub:
            os.makedirs(config.epub_dir, exist_ok=True)
            log_message(logger, "DEBUG", f"EPUB folder created - {config.epub_dir}", quiet=not should_show_message())
        if config.generate_html:
            os.makedirs(config.html_dir, exist_ok=True)
            log_message(logger, "DEBUG", f"HTML folder created - {config.html_dir}", quiet=not should_show_message())
            
        # Add empty line after folder creation
        log_message(logger, "DEBUG", "", quiet=not should_show_message())
        
        # Get list of PDF files
        pdf_files = sorted(f for f in os.listdir(config.source_dir) if f.lower().endswith(".pdf"))
        if not pdf_files:
            log_message(logger, "WARNING", "No PDF files found!", quiet=False)  # Always show warnings
            return
        
        # Process files in parallel
        with timing_context("Total execution", logger) as get_total_time:
            # Use configured number of workers
            max_workers = config.workers
            log_message(logger, "INFO", f"Processing {len(pdf_files)} files using {max_workers} worker{'s' if max_workers > 1 else ''}", quiet=not should_show_message())
            log_message(logger, "INFO", "", quiet=not should_show_message())  # Empty line for readability
            
            # Track processing statistics
            completed = 0
            successful = 0
            failed = 0
            errors = []
            active_files = set()
            
            with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all files for processing
                future_to_file = {
                    executor.submit(process_single_pdf, filename, config): filename
                    for filename in pdf_files
                }
                
                # Process results as they complete
                try:
                    for future in futures.as_completed(future_to_file):
                        if shutdown_requested:
                            executor.shutdown(wait=False)
                            break
                            
                        filename = future_to_file[future]
                        completed += 1
                        
                        try:
                            success, processing_time, error, log_messages = future.result()
                            
                            # Log file start and messages
                            log_message(logger, "INFO", f"\n[{completed}/{len(pdf_files)}] Processing: {filename}", quiet=not should_show_message())
                            
                            # Write all log messages from the child process
                            for level, message in log_messages:
                                log_message(logger, level, "  " + message, quiet=not should_show_message())
                            
                            if success:
                                successful += 1
                                log_process_complete(logger, processing_time, quiet=not should_show_message())
                                log_message(logger, "INFO", f"  ✓ Completed successfully in {processing_time:.2f} seconds", quiet=not should_show_message())
                            else:
                                failed += 1
                                if error:
                                    errors.append((filename, error))
                                    log_message(logger, "ERROR", f"  ✗ Failed: {error}", quiet=False)  # Always show errors
                            
                            # Add empty line for readability
                            log_message(logger, "INFO", "", quiet=not should_show_message())
                            
                        except Exception as e:
                            failed += 1
                            error_msg = f"Error processing {filename}: {str(e)}"
                            log_message(logger, "ERROR", error_msg, quiet=False)  # Always show errors
                            errors.append((filename, error_msg))
                            
                except KeyboardInterrupt:
                    executor.shutdown(wait=False)
                    log_message(logger, "WARNING", "\nProcessing interrupted by user.", quiet=False)  # Always show interruption
                    return
            
            if shutdown_requested:
                log_message(logger, "WARNING", "\nProcessing interrupted by user.", quiet=False)  # Always show interruption
                return
                
            # Log final summary
            total_time = get_total_time()
            summary = [
                f"\nProcessing Summary:",
                f"----------------",
                f"Files processed: {completed}",
                f"Total time: {total_time:.2f} seconds"
            ]
            
            if completed > 0:
                avg_time = total_time / completed
                summary.append(f"Average time per file: {avg_time:.2f} seconds")
            
            summary.extend([
                f"Successful: {successful}",
                f"Failed: {failed}"
            ])
            
            if errors:
                summary.extend([
                    "\nErrors:",
                    "-------"
                ])
                for filename, error in errors:
                    summary.append(f"• {filename}:")
                    summary.append(f"  {error}")
            
            # Show summary based on mode:
            # - In quiet mode: don't show
            # - In summary mode: show
            # - In normal mode: show
            show_summary = not config.quiet
            log_message(logger, "INFO", "\n".join(summary), quiet=not show_summary)
        
    except Exception as e:
        log_message(logger, "ERROR", f"Error processing PDFs: {str(e)}", quiet=False)  # Always show errors
        raise


def process_single_layout_pdf(filename: str, config: ProcessingConfig) -> tuple:
    """Process a single PDF file in layout-preserving mode.
    
    Args:
        filename: Name of the PDF file to process
        config: Processing configuration
        
    Returns:
        tuple: (success: bool, processing_time: float, error_message: str, log_messages: list)
    """
    # Setup logging for this process
    logger = setup_logging(config.log_path, config.quiet, is_worker=True)
    log_messages = []
    
    try:
        pdf_path = os.path.join(config.source_dir, filename)
        base_name = os.path.splitext(filename)[0]
        out_path = os.path.join(config.pdf_dir, f"{base_name}_ocr.pdf")
        
        with timing_context(f"Processing {filename}", logger) as get_file_time:
            # Convert PDF to images with lower DPI for layout preservation
            pages = convert_from_path(pdf_path, dpi=200)
            
            # Process each page with OCR
            pdf_pages = []
            
            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                with timing_context("OCR processing", logger) as get_ocr_time:
                    for page_num, page_img in enumerate(tqdm(pages, desc="Processing pages", unit="page")):
                        # Save image to temporary file
                        img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                        page_img.save(img_path, "PNG")
                        
                        # Generate PDF with OCR using tesseract
                        pdf_path = os.path.join(temp_dir, f"page_{page_num}")
                        cmd = [
                            "tesseract",
                            img_path,
                            pdf_path,
                            "-l", config.lang,
                            "--dpi", "200",
                            "pdf"
                        ]
                        subprocess.run(cmd, check=True, capture_output=True)
                        
                        # Read generated PDF
                        with open(f"{pdf_path}.pdf", "rb") as f:
                            pdf_pages.append(f.read())
                
                log_messages.append(("INFO", f"OCR completed in {get_ocr_time():.2f} seconds"))
                
                # Merge PDF pages
                with timing_context("PDF merging", logger) as get_merge_time:
                    writer = PdfWriter()
                    
                    for page_pdf in pdf_pages:
                        reader = PdfReader(io.BytesIO(page_pdf))
                        writer.add_page(reader.pages[0])
                    
                    with open(out_path, "wb") as fout:
                        writer.write(fout)
                
                log_messages.append(("INFO", f"Layout-preserving PDF created in {get_merge_time():.2f} seconds"))
            
            return True, get_file_time(), None, log_messages
            
    except Exception as e:
        error_msg = f"Error in {filename} during {e.__class__.__name__}: {str(e)}"
        log_messages.append(("ERROR", error_msg))
        return False, 0, error_msg, log_messages


def process_layout_pdf_only(config: ProcessingConfig, logger: logging.Logger):
    """Generate searchable PDFs while preserving the original document layout.

    This function creates a searchable PDF that maintains the exact visual appearance
    of the original document. It's ideal for documents where layout and formatting
    are crucial (e.g., forms, scientific papers, magazines).

    Key features:
    - Preserves original document layout, fonts, and formatting
    - Adds invisible OCR text layer for searchability
    - Uses lower DPI (200) to optimize file size
    - Creates output in 'pdf_ocr_layout' directory
    """
    try:
        # Show warning about layout preservation mode
        log_message(logger, "WARNING", "Layout preservation mode only supports PDF output. Other formats will be disabled.", quiet=config.quiet)
        
        # Create output directory
        os.makedirs(config.pdf_dir, exist_ok=True)
        log_message(logger, "DEBUG", f"Preserve-layout PDF folder created - {config.pdf_dir}", quiet=config.quiet)
        log_message(logger, "DEBUG", "", quiet=config.quiet)  # Add empty line after directory creation
        
        # Get list of PDF files
        pdf_files = sorted(f for f in os.listdir(config.source_dir) if f.lower().endswith(".pdf"))
        if not pdf_files:
            log_message(logger, "WARNING", "No PDF files found!", quiet=config.quiet)
            return

        # Process files in parallel
        with timing_context("Total execution", logger) as get_total_time:
            # Use configured number of workers
            max_workers = config.workers
            log_message(logger, "INFO", f"Processing {len(pdf_files)} files using {max_workers} worker{'s' if max_workers > 1 else ''}", quiet=config.quiet)
            log_message(logger, "INFO", "", quiet=config.quiet)  # Empty line for readability
            
            # Track processing statistics
            completed = 0
            successful = 0
            failed = 0
            errors = []
            
            with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all files for processing
                future_to_file = {
                    executor.submit(process_single_layout_pdf, filename, config): filename
                    for filename in pdf_files
                }
                
                # Process results as they complete
                for future in futures.as_completed(future_to_file):
                    filename = future_to_file[future]
                    completed += 1
                    
                    try:
                        success, processing_time, error, log_messages = future.result()
                        
                        # Log file start
                        log_message(logger, "INFO", f"\n[{completed}/{len(pdf_files)}] Processing: {filename}", quiet=config.quiet)
                        
                        # Write all log messages from the child process
                        for level, message in log_messages:
                            log_message(logger, level, "  " + message, quiet=config.quiet)
                        
                        if success:
                            successful += 1
                            log_process_complete(logger, processing_time, quiet=config.quiet)
                            log_message(logger, "INFO", f"  ✓ Completed successfully in {processing_time:.2f} seconds", quiet=config.quiet)
                        else:
                            failed += 1
                            if error:
                                errors.append((filename, error))
                                log_message(logger, "ERROR", f"  ✗ Failed: {error}", quiet=config.quiet)
                        
                        # Add empty line for readability
                        log_message(logger, "INFO", "", quiet=config.quiet)
                        
                    except Exception as e:
                        failed += 1
                        error_msg = f"Error processing {filename}: {str(e)}"
                        log_message(logger, "ERROR", error_msg, quiet=config.quiet)
                        errors.append((filename, error_msg))
            
            # Log final summary
            total_time = get_total_time()
            summary = [
                f"\nProcessing Summary:",
                f"----------------",
                f"Files processed: {len(pdf_files)}",
                f"Total time: {total_time:.2f} seconds"
            ]
            
            if len(pdf_files) > 0:
                avg_time = total_time / len(pdf_files)
                summary.append(f"Average time per file: {avg_time:.2f} seconds")
            
            summary.extend([
                f"Successful: {successful}",
                f"Failed: {failed}"
            ])
            
            if errors:
                summary.extend([
                    "\nErrors:",
                    "-------"
                ])
                for filename, error in errors:
                    summary.append(f"• {filename}:")
                    summary.append(f"  {error}")
            
            log_message(logger, "INFO", "\n".join(summary), quiet=config.quiet)
        
    except Exception as e:
        log_message(logger, "ERROR", f"Error processing layout PDF: {str(e)}", quiet=config.quiet)
        raise


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
             "and documents where visual formatting is important. Creates output in 'pdf_ocr_layout' directory."
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
            workers=args.workers
        )
        
        # Setup logging
        logger = setup_logging(config.log_path, config.quiet)
        
        try:
            # Show version info and validate language only in normal mode (not quiet, not summary)
            show_header = not (config.quiet or config.summary_output)
            
            # Show version info first
            log_message(logger, "HEADER", f"PDF2OCR v{__version__}", quiet=not show_header)
            log_message(logger, "INFO", "", quiet=not show_header)  # Add empty line after version
            
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
