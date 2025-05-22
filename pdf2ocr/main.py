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


def process_pdfs_with_ocr(config: ProcessingConfig, logger: logging.Logger):
    """Main function that orchestrates the entire conversion process"""
    
    # Validate configuration
    config.validate()
    
    try:
        # Create output directories
        os.makedirs(config.get_effective_dest_dir(), exist_ok=True)
        if config.generate_docx:
            os.makedirs(config.docx_dir, exist_ok=True)
            log_message(logger, "DEBUG", f"DOCX folder created - {config.docx_dir}", quiet=config.quiet)
        if config.generate_pdf:
            os.makedirs(config.pdf_dir, exist_ok=True)
            log_message(logger, "DEBUG", f"PDF folder created - {config.pdf_dir}", quiet=config.quiet)
        if config.generate_epub:
            os.makedirs(config.epub_dir, exist_ok=True)
            log_message(logger, "DEBUG", f"EPUB folder created - {config.epub_dir}", quiet=config.quiet)
        if config.generate_html:
            os.makedirs(config.html_dir, exist_ok=True)
            log_message(logger, "DEBUG", f"HTML folder created - {config.html_dir}", quiet=config.quiet)
            
        # Add empty line after folder creation
        log_message(logger, "DEBUG", "", quiet=config.quiet)
        
        # Process each PDF file
        pdf_files = sorted(f for f in os.listdir(config.source_dir) if f.lower().endswith(".pdf"))
        if not pdf_files:
            log_message(logger, "WARNING", "No PDF files found!", quiet=config.quiet)
            return
        
        with timing_context("Total execution", logger) as get_total_time:
            for idx, filename in enumerate(pdf_files, start=1):
                log_process_start(logger, filename, idx, len(pdf_files), quiet=config.quiet)
                
                try:
                    pdf_path = os.path.join(config.source_dir, filename)
                    base_name = os.path.splitext(filename)[0]
                    
                    with timing_context(f"Processing {filename}", logger) as get_file_time:
                        # Process PDF pages with OCR
                        pages = process_pdf_with_ocr(pdf_path, config.lang, config.dpi, logger)
                        page_texts = [text for _, text in pages]
                        
                        # Generate output files
                        if config.generate_pdf:
                            pdf_path = os.path.join(config.pdf_dir, base_name + "_ocr.pdf")
                            with timing_context("PDF generation", logger) as get_pdf_time:
                                save_as_pdf(page_texts, pdf_path, base_name)
                            log_message(logger, "INFO", f"OCR PDF created in {get_pdf_time():.2f} seconds", quiet=config.quiet)
                        
                        if config.generate_html:
                            html_path = os.path.join(config.html_dir, base_name + ".html")
                            with timing_context("HTML generation", logger) as get_html_time:
                                save_as_html(page_texts, html_path)
                            log_message(logger, "INFO", f"HTML created in {get_html_time():.2f} seconds", quiet=config.quiet)
                        
                        if config.generate_docx:
                            docx_path = os.path.join(config.docx_dir, base_name + ".docx")
                            with timing_context("DOCX generation", logger) as get_docx_time:
                                save_as_docx(page_texts, docx_path)
                            log_message(logger, "INFO", f"DOCX created in {get_docx_time():.2f} seconds", quiet=config.quiet)
                            
                            if config.generate_epub:
                                epub_path = os.path.join(config.epub_dir, base_name + ".epub")
                                with timing_context("EPUB generation", logger) as get_epub_time:
                                    success, _, output = convert_docx_to_epub(docx_path, epub_path, config.lang)
                                    if success:
                                        log_message(logger, "INFO", f"EPUB created in {get_epub_time():.2f} seconds", quiet=config.quiet)
                                    else:
                                        log_message(logger, "ERROR", f"Failed to create EPUB: {output}", quiet=config.quiet)
                    
                    log_process_complete(logger, get_file_time(), quiet=config.quiet)
                    
                except Exception as e:
                    log_message(logger, "ERROR", f"Error processing {filename}: {str(e)}", quiet=config.quiet)
                    continue
        
        log_conversion_summary(logger, len(pdf_files), get_total_time(), quiet=config.quiet)
        
    except Exception as e:
        log_message(logger, "ERROR", f"Error processing PDFs: {str(e)}", quiet=config.quiet)


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
        
        # Process each PDF file
        pdf_files = sorted(f for f in os.listdir(config.source_dir) if f.lower().endswith(".pdf"))
        if not pdf_files:
            log_message(logger, "WARNING", "No PDF files found!", quiet=config.quiet)
            return
        
        with timing_context("Total execution", logger) as get_total_time:
            for idx, filename in enumerate(pdf_files, start=1):
                log_process_start(logger, filename, idx, len(pdf_files), quiet=config.quiet)
                
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
                            
                            log_message(logger, "INFO", f"OCR completed in {get_ocr_time():.2f} seconds", quiet=config.quiet)
                            
                            # Merge PDF pages
                            with timing_context("PDF merging", logger) as get_merge_time:
                                writer = PdfWriter()
                                
                                for page_pdf in pdf_pages:
                                    reader = PdfReader(io.BytesIO(page_pdf))
                                    writer.add_page(reader.pages[0])
                                
                                with open(out_path, "wb") as fout:
                                    writer.write(fout)
                            
                            log_message(logger, "INFO", f"Layout-preserving PDF created in {get_merge_time():.2f} seconds", quiet=config.quiet)
                    
                    log_process_complete(logger, get_file_time(), quiet=config.quiet)
                    
                except Exception as e:
                    log_message(logger, "ERROR", f"Error processing {filename}: {str(e)}", quiet=config.quiet)
                    continue
        
        log_conversion_summary(logger, len(pdf_files), get_total_time(), quiet=config.quiet)
        
    except Exception as e:
        log_message(logger, "ERROR", f"Error processing layout PDF: {str(e)}", quiet=config.quiet)


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
        "--dpi",
        type=int,
        default=400,
        help="DPI for image conversion (default: 400)",
    )
    parser.add_argument("--quiet", action="store_true", help="Run silently (no output)")
    parser.add_argument(
        "--short-output",
        "--summary-output",
        dest="summary_output",
        action="store_true",
        help="Display only final conversion summary (short output mode)",
    )
    parser.add_argument("--logfile", help="Path to log file (optional)")
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
            dpi=args.dpi,
            generate_pdf=args.pdf,
            generate_html=args.html,
            generate_docx=args.docx,
            generate_epub=args.epub,
            preserve_layout=args.preserve_layout,
            quiet=args.quiet,
            summary_output=args.summary_output,
            log_path=args.logfile
        )
        
        # Setup logging
        logger = setup_logging(config.log_path, config.quiet)
        
        try:
            # Show version info first
            log_message(logger, "HEADER", f"PDF2OCR v{__version__}", quiet=config.quiet)
            
            # Validate Tesseract language
            validate_tesseract_language(args.lang, logger, args.quiet)
            
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
