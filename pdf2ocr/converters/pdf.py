"""PDF conversion and processing functionality."""

import io
import os
import subprocess
import sys
import tempfile
import time
from concurrent import futures
from typing import List, Optional, Tuple

from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from tqdm import tqdm

from pdf2ocr.config import ProcessingConfig
from pdf2ocr.converters.common import process_paragraphs
from pdf2ocr.converters.docx import save_as_docx
from pdf2ocr.converters.epub import convert_docx_to_epub
from pdf2ocr.converters.html import save_as_html
from pdf2ocr.logging_config import (log_conversion_summary, log_message,
                                    log_process_start, setup_logging)
from pdf2ocr.ocr import extract_text_from_pdf
from pdf2ocr.state import is_shutdown_requested
from pdf2ocr.utils import timing_context


def save_as_pdf(text_pages: List[str], output_path: str) -> float:
    """Creates a new PDF with OCR-extracted text in a clean, standardized format.

    This function generates a new PDF document that focuses on text readability
    and consistent formatting. It's ideal for cases where you want to extract
    and reformat content from PDFs (e.g., books, articles, documents).

    Key features:
    - Creates a new PDF with clean, consistent formatting
    - Adds simple page numbers for navigation
    - Uses standard fonts and margins for optimal readability
    - Creates output in 'pdf_ocr' directory
    - Includes PDF metadata (title, author, creation info)

    Technical approach:
    1. Uses reportlab to generate a new PDF from scratch
    2. Applies consistent formatting (margins, fonts, spacing)
    3. Preserves paragraph structure from OCR text
    4. Handles text flow and automatic pagination
    5. Adds document metadata

    Args:
        text_pages: List of text content for each page
        output_path: Path where to save the PDF file

    Returns:
        float: Time taken to save the file in seconds

    Note:
        This differs from process_layout_pdf_only() which preserves original layout.
        Choose this method when you want a clean, reformatted version of the document.
    """
    start = time.perf_counter()

    # Get title from filename
    title = os.path.splitext(os.path.basename(output_path))[0].replace("_", " ")

    # Create PDF with metadata
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(title)
    c.setAuthor("pdf2ocr")
    c.setCreator("pdf2ocr")
    c.setSubject("OCR processed document")
    c.setKeywords("OCR, PDF, text recognition")

    width, height = A4

    # Skip empty pages at the start
    page_offset = 0
    for idx, page_text in enumerate(text_pages):
        if page_text.strip():
            break
        page_offset += 1

    for idx, page_text in enumerate(text_pages[page_offset:], start=1):
        x = 2 * cm  # Left margin
        y = height - 3 * cm  # Top margin

        # Page header
        c.setFont("Helvetica", 10)  # Changed to regular weight for consistency
        header = f"pdf2ocr - Page {idx}"  # New header format
        c.drawString(x, height - 1 * cm, header)  # Aligned left like HTML

        # Main text
        c.setFont("Helvetica", 10)
        line_height = 12

        # Process paragraphs
        for para in process_paragraphs(page_text):
            # Split long paragraphs into lines that fit the page width
            words = para.split()
            current_line = []

            for word in words:
                current_line.append(word)
                line = " ".join(current_line)

                # Check if line width exceeds page width
                if c.stringWidth(line, "Helvetica", 10) > (width - 4 * cm):
                    # Remove last word and draw current line
                    current_line.pop()
                    line = " ".join(current_line)

                    # Draw line and check page break
                    if y < 2 * cm:  # Check page end
                        c.showPage()
                        y = height - 3 * cm
                        # Repeat header on new page
                        c.setFont("Helvetica", 10)
                        c.drawString(x, height - 1 * cm, header)
                        c.setFont("Helvetica", 10)

                    c.drawString(x, y, line)
                    y -= line_height

                    # Start new line with the word that didn't fit
                    current_line = [word]

            # Draw remaining words in the last line
            if current_line:
                line = " ".join(current_line)
                if y < 2 * cm:  # Check page end
                    c.showPage()
                    y = height - 3 * cm
                    # Repeat header on new page
                    c.setFont("Helvetica", 10)
                    c.drawString(x, height - 1 * cm, header)
                    c.setFont("Helvetica", 10)

                c.drawString(x, y, line)
                y -= line_height

            # Extra space between paragraphs
            y -= line_height

        c.showPage()

    c.save()
    return time.perf_counter() - start


def process_single_layout_pdf(
    filename: str, config: ProcessingConfig
) -> Tuple[bool, float, str, List[Tuple[str, str]]]:
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
        temp_pdf_path = os.path.join(config.pdf_dir, f"{base_name}_temp.pdf")

        total_time = 0.0

        # Get total number of pages
        with open(pdf_path, "rb") as f:
            pdf = PdfReader(f)
            total_pages = len(pdf.pages)

        # Process each page with OCR
        pdf_pages = []

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            with timing_context("OCR processing", None) as get_ocr_time:
                # Configure tqdm to write to /dev/null in quiet mode
                tqdm_file = (
                    open(os.devnull, "w")
                    if (config.quiet or config.summary)
                    else sys.stderr
                )

                try:
                    if config.batch_size is None:
                        # Process all pages at once
                        pages_batch = convert_from_path(
                            pdf_path,
                            dpi=200,
                            use_pdftocairo=True,
                        )

                        # Process each page
                        for page_num, page_img in enumerate(
                            tqdm(
                                pages_batch,
                                desc="Processing pages",
                                unit="page",
                                file=tqdm_file,
                                disable=config.quiet or config.summary,
                                leave=False,
                            )
                        ):
                            # Save image to temporary file with high quality for OCR
                            img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                            page_img.save(img_path, "PNG")

                            # Generate PDF with OCR using tesseract with configuration
                            pdf_path_base = os.path.join(temp_dir, f"page_{page_num}")
                            tesseract_config = config.get_tesseract_config()
                            cmd = [
                                "tesseract",
                                img_path,
                                pdf_path_base,
                                "-l",
                                config.lang,
                                "--dpi",
                                "200",
                                "pdf",
                            ] + tesseract_config
                            subprocess.run(cmd, check=True, capture_output=True)

                            # Read generated PDF
                            with open(f"{pdf_path_base}.pdf", "rb") as f:
                                # Ensure we have enough slots in pdf_pages
                                while len(pdf_pages) <= page_num:
                                    pdf_pages.append(None)
                                pdf_pages[page_num] = f.read()

                        # Explicitly free memory
                        del pages_batch
                    else:
                        # Process pages in batches
                        for batch_start in tqdm(
                            range(1, total_pages + 1, config.batch_size),
                            desc="Processing batches",
                            unit="batch",
                            file=tqdm_file,
                            disable=config.quiet or config.summary,
                            leave=False,
                        ):
                            batch_end = min(
                                batch_start + config.batch_size - 1, total_pages
                            )

                            # Convert batch of pages to images
                            pages_batch = convert_from_path(
                                pdf_path,
                                dpi=200,
                                first_page=batch_start,
                                last_page=batch_end,
                                use_pdftocairo=True,
                            )

                            # Process each page in the batch
                            for page_num, page_img in enumerate(
                                tqdm(
                                    pages_batch,
                                    desc=f"Pages {batch_start}-{batch_end}",
                                    unit="page",
                                    file=tqdm_file,
                                    disable=config.quiet or config.summary,
                                    leave=False,
                                    position=1,
                                ),
                                start=batch_start - 1,
                            ):
                                # Save image to temporary file with high quality for OCR
                                img_path = os.path.join(
                                    temp_dir, f"page_{page_num}.png"
                                )
                                page_img.save(img_path, "PNG")

                                # Generate PDF with OCR using tesseract with configuration
                                pdf_path_base = os.path.join(
                                    temp_dir, f"page_{page_num}"
                                )
                                tesseract_config = config.get_tesseract_config()
                                cmd = [
                                    "tesseract",
                                    img_path,
                                    pdf_path_base,
                                    "-l",
                                    config.lang,
                                    "--dpi",
                                    "200",
                                    "pdf",
                                ] + tesseract_config
                                subprocess.run(cmd, check=True, capture_output=True)

                                # Read generated PDF
                                with open(f"{pdf_path_base}.pdf", "rb") as f:
                                    # Ensure we have enough slots in pdf_pages
                                    while len(pdf_pages) <= page_num:
                                        pdf_pages.append(None)
                                    pdf_pages[page_num] = f.read()

                            # Explicitly free memory
                            del pages_batch

                finally:
                    # Close tqdm file if it was opened
                    if tqdm_file != sys.stderr:
                        tqdm_file.close()

            total_time += get_ocr_time.duration
            log_messages = [
                (
                    "INFO",
                    f"  OCR processing took {get_ocr_time.duration:.2f} seconds",
                )
            ]

            # Merge PDF pages into temporary file
            with timing_context("PDF merging", None) as get_merge_time:
                writer = PdfWriter()
                writer.compress = True

                for page_pdf in pdf_pages:
                    if page_pdf is not None:  # Skip any missing pages
                        reader = PdfReader(io.BytesIO(page_pdf))
                        writer.add_page(reader.pages[0])

                with open(temp_pdf_path, "wb") as fout:
                    writer.write(fout)

            total_time += get_merge_time.duration

            # Compress the final PDF using Ghostscript
            with timing_context("PDF compression", None) as get_compress_time:
                cmd = [
                    "gs",
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    "-dPDFSETTINGS=/ebook",  # Balance between quality and size
                    "-dNOPAUSE",
                    "-dQUIET",
                    "-dBATCH",
                    f"-sOutputFile={out_path}",
                    temp_pdf_path,
                ]
                subprocess.run(cmd, check=True, capture_output=True)

                # Remove temporary PDF
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

            total_time += get_compress_time.duration
            log_messages.append(
                (
                    "INFO",
                    f"  Layout-preserving PDF created and compressed in {get_merge_time.duration + get_compress_time.duration:.2f} seconds",
                )
            )

            return True, total_time, None, log_messages

    except Exception as e:
        error_msg = f"Error in {filename} during {e.__class__.__name__}: {str(e)}"
        log_messages.append(("ERROR", error_msg))
        # Clean up temporary file if it exists
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        return False, 0, error_msg, log_messages


def process_layout_pdf_only(config: ProcessingConfig, logger) -> None:
    """Generate searchable PDFs while preserving the original document layout.

    This function processes each PDF file in the source directory and generates
    a searchable PDF that maintains the exact visual appearance of the original.

    Key features:
    - Maintains original document layout and formatting
    - Adds invisible OCR text layer for searchability
    - Uses lower DPI (200) to optimize file size
    - Output in 'pdf_ocr_layout' directory

    Args:
        config: Processing configuration
        logger: Logger instance
    """
    try:
        # Validate configuration
        config.validate(logger)

        # Create output directory
        os.makedirs(config.pdf_dir, exist_ok=True)
        log_message(
            logger,
            "DEBUG",
            f"PDF folder created - {config.pdf_dir}",
            quiet=config.quiet
            or config.summary,  # Hide in both quiet and summary modes
            summary=config.summary,
        )

        # Get list of PDF files
        pdf_files = sorted(
            f for f in os.listdir(config.source_dir) if f.lower().endswith(".pdf")
        )
        if not pdf_files:
            log_message(
                logger,
                "WARNING",
                "No PDF files found!",
                quiet=config.quiet,
                summary=config.summary,
            )  # Show in summary mode
            return

        # Process files in parallel
        with timing_context("Total execution", logger) as get_total_time:
            # Use configured number of workers
            max_workers = config.workers
            log_message(
                logger,
                "INFO",
                "",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
                summary=config.summary,
            )
            log_message(
                logger,
                "INFO",
                f"Processing {len(pdf_files)} files using {max_workers} workers",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
                summary=config.summary,
            )
            if config.batch_size is not None:
                log_message(
                    logger,
                    "INFO",
                    f"Batch-size: {config.batch_size} pages",
                    quiet=config.quiet
                    or config.summary,  # Hide in both quiet and summary modes
                    summary=config.summary,
                )
            log_message(
                logger,
                "INFO",
                "",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
                summary=config.summary,
            )

            # Track processing statistics
            completed = 0
            successful = 0
            failed = 0
            errors = []

            with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all files for processing
                future_to_file = {
                    executor.submit(
                        process_single_layout_pdf, filename, config
                    ): filename
                    for filename in pdf_files
                }

                # Create progress bar if not in quiet or summary mode
                pbar = None
                tqdm_file = None
                if not (config.quiet or config.summary):
                    pbar = tqdm(
                        total=len(pdf_files),
                        desc="Processing files",
                        unit="file",
                        leave=False,
                        position=0,
                    )
                else:
                    # Open /dev/null for tqdm output in quiet mode
                    tqdm_file = open(os.devnull, "w")
                    pbar = tqdm(
                        total=len(pdf_files),
                        desc="Processing files",
                        unit="file",
                        leave=False,
                        position=0,
                        file=tqdm_file,
                        disable=True,
                    )

                try:
                    # Process results as they complete
                    for future in futures.as_completed(future_to_file):
                        if is_shutdown_requested():
                            log_message(
                                logger,
                                "WARNING",
                                "Shutdown requested. Waiting for current tasks to complete...",
                                quiet=config.quiet,  # Show in summary mode
                                summary=config.summary,
                            )
                            break

                        filename = future_to_file[future]
                        completed += 1

                        try:
                            success, processing_time, error, log_messages = (
                                future.result()
                            )

                            # Clear progress bar line if it exists
                            if pbar:
                                pbar.clear()

                            # Log file start
                            log_message(
                                logger,
                                "INFO",
                                f"[{completed}/{len(pdf_files)}] Processing: {filename}",
                                quiet=config.quiet
                                or config.summary,  # Hide in both quiet and summary modes
                                summary=config.summary,
                            )

                            # Write all log messages from the child process
                            for level, message in log_messages:
                                log_message(
                                    logger,
                                    level,
                                    message,
                                    quiet=config.quiet
                                    or config.summary,  # Hide in both quiet and summary modes
                                    summary=config.summary,
                                )

                            if success:
                                successful += 1
                                log_message(
                                    logger,
                                    "INFO",
                                    f"  ✓ Completed successfully in {processing_time:.2f} seconds\n",
                                    quiet=config.quiet
                                    or config.summary,  # Hide in both quiet and summary modes
                                    summary=config.summary,
                                )
                            else:
                                failed += 1
                                if error:
                                    errors.append((filename, error))
                                    log_message(
                                        logger,
                                        "ERROR",
                                        f"  ✗ Failed: {error}\n",
                                        quiet=config.quiet,  # Show in summary mode
                                        summary=config.summary,
                                    )

                            # Update progress bar if it exists
                            if pbar:
                                pbar.update(1)

                        except Exception as e:
                            failed += 1
                            error_msg = f"Error processing {filename}: {str(e)}"
                            log_message(
                                logger,
                                "ERROR",
                                error_msg,
                                quiet=config.quiet,
                                summary=config.summary,
                            )  # Show in summary mode
                            errors.append((filename, error_msg))
                            if pbar:
                                pbar.update(1)

                finally:
                    # Close progress bar and file
                    if pbar:
                        pbar.close()
                    if tqdm_file:
                        tqdm_file.close()

            # Log final summary
            total_time = get_total_time()
            summary = [
                "\nProcessing Summary:",
                "----------------",
                f"Files processed: {completed}",
                f"Total time: {total_time:.2f} seconds",
            ]

            if completed > 0:
                avg_time = total_time / completed
                summary.append(f"Average time per file: {avg_time:.2f} seconds")

            summary.extend([f"Successful: {successful}", f"Failed: {failed}"])

            if errors:
                summary.extend(["\nErrors:", "-------"])
                for filename, error in errors:
                    summary.extend([f"• {filename}:", f"  {error}"])

            # Remove empty lines at the beginning if they exist
            while summary and not summary[0]:
                summary.pop(0)

            log_message(
                logger,
                "INFO",
                "\n".join(summary),
                quiet=config.quiet,
                summary=config.summary,
            )  # Show in summary mode

    except Exception as e:
        log_message(
            logger,
            "ERROR",
            f"Error processing PDFs: {str(e)}",
            quiet=config.quiet,  # Show in summary mode
            summary=config.summary,
        )
        raise


def process_single_pdf(
    filename: str, config: ProcessingConfig
) -> Tuple[bool, float, Optional[str], List[Tuple[str, str]]]:
    """Process a single PDF file and generate requested output formats.

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
        temp_pdf_path = os.path.join(config.pdf_dir, f"{base_name}_temp.pdf")

        total_time = 0.0

        # Extract text from PDF
        with timing_context("Text extraction", None) as get_text_time:
            final_text, text_pages, ocr_time = extract_text_from_pdf(
                pdf_path,
                config.get_tesseract_config(),
                quiet=config.quiet,
                summary=config.summary,
                batch_size=config.batch_size,
            )
        total_time += get_text_time.duration
        log_messages.append(
            (
                "INFO",
                f"    Text extracted in {get_text_time.duration:.2f} seconds",
            )
        )

        # Generate requested output formats
        with timing_context("File generation", None) as get_file_time:
            if config.generate_pdf:
                with timing_context("PDF generation", None) as get_pdf_time:
                    save_as_pdf(text_pages, out_path)
                total_time += get_pdf_time.duration
                log_messages.append(
                    (
                        "INFO",
                        f"    PDF created in {get_pdf_time.duration:.2f} seconds",
                    )
                )

            if config.generate_docx:
                with timing_context("DOCX generation", None) as get_docx_time:
                    docx_output = os.path.join(config.docx_dir, f"{base_name}.docx")
                    save_as_docx(text_pages, docx_output)
                total_time += get_docx_time.duration
                log_messages.append(
                    (
                        "INFO",
                        f"    DOCX created in {get_docx_time.duration:.2f} seconds",
                    )
                )

            if config.generate_html:
                with timing_context("HTML generation", None) as get_html_time:
                    html_output = os.path.join(config.html_dir, f"{base_name}.html")
                    save_as_html(text_pages, html_output)
                total_time += get_html_time.duration
                log_messages.append(
                    (
                        "INFO",
                        f"    HTML created in {get_html_time.duration:.2f} seconds",
                    )
                )

            if config.generate_epub:
                with timing_context("EPUB generation", None) as get_epub_time:
                    epub_output = os.path.join(config.epub_dir, f"{base_name}.epub")
                    docx_output = os.path.join(config.docx_dir, f"{base_name}.docx")
                    success, duration, output = convert_docx_to_epub(
                        docx_output,
                        epub_output,
                        logger=logger,
                        quiet=config.quiet,
                        lang=config.lang,
                    )
                    if not success:
                        raise RuntimeError(
                            f"Failed to convert {base_name} to EPUB: {output}"
                        )
                total_time += get_epub_time.duration
                log_messages.append(
                    (
                        "INFO",
                        f"    EPUB created in {get_epub_time.duration:.2f} seconds",
                    )
                )

            return True, total_time, None, log_messages

    except Exception as e:
        error_msg = f"Error in {filename} during {e.__class__.__name__}: {str(e)}"
        log_messages.append(("ERROR", error_msg))
        return False, 0, error_msg, log_messages


def process_pdfs_with_ocr(config: ProcessingConfig, logger) -> None:
    """Process PDF files with OCR and convert to selected formats.

    This function processes each PDF file in the source directory with OCR
    and generates the requested output formats (PDF, DOCX, HTML, EPUB).

    Key features:
    - Parallel processing with configurable number of workers
    - Progress tracking and logging
    - Multiple output formats
    - Error handling and reporting
    - Graceful shutdown support

    Args:
        config: Processing configuration
        logger: Logger instance
    """
    try:
        # Validate configuration
        config.validate(logger)

        # Show EPUB/DOCX dependency warning
        if config.generate_epub and not config.generate_docx:
            log_message(
                logger,
                "WARNING",
                "EPUB generation requires DOCX format. Enabling DOCX generation automatically.",
                quiet=config.quiet,  # Show in summary mode
            )
            config.generate_docx = True

        # Create output directories
        if config.generate_pdf:
            os.makedirs(config.pdf_dir, exist_ok=True)
            log_message(
                logger,
                "DEBUG",
                f"PDF folder created - {config.pdf_dir}",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        if config.generate_docx:
            os.makedirs(config.docx_dir, exist_ok=True)
            log_message(
                logger,
                "DEBUG",
                f"DOCX folder created - {config.docx_dir}",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        if config.generate_html:
            os.makedirs(config.html_dir, exist_ok=True)
            log_message(
                logger,
                "DEBUG",
                f"HTML folder created - {config.html_dir}",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        if config.generate_epub:
            os.makedirs(config.epub_dir, exist_ok=True)
            log_message(
                logger,
                "DEBUG",
                f"EPUB folder created - {config.epub_dir}",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        log_message(
            logger, "DEBUG", "", quiet=config.quiet or config.summary
        )  # Empty line after directories

        # Get list of PDF files
        pdf_files = sorted(
            f for f in os.listdir(config.source_dir) if f.lower().endswith(".pdf")
        )
        if not pdf_files:
            log_message(
                logger, "WARNING", "No PDF files found!", quiet=config.quiet
            )  # Show in summary mode
            return

        # Process files in parallel
        with timing_context("Total execution", logger) as get_total_time:
            # Use configured number of workers
            max_workers = config.workers
            log_message(
                logger,
                "INFO",
                "",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )
            log_message(
                logger,
                "INFO",
                f"Processing {len(pdf_files)} files using {max_workers} workers",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )
            if config.batch_size is not None:
                log_message(
                    logger,
                    "INFO",
                    f"Batch-size: {config.batch_size} pages",
                    quiet=config.quiet
                    or config.summary,  # Hide in both quiet and summary modes
                )
            log_message(
                logger,
                "INFO",
                "",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

            # Track processing statistics
            completed = 0
            successful = 0
            failed = 0
            errors = []

            with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all files for processing
                future_to_file = {
                    executor.submit(process_single_pdf, filename, config): filename
                    for filename in pdf_files
                }

                # Create progress bar if not in quiet or summary mode
                pbar = None
                tqdm_file = None
                if not (config.quiet or config.summary):
                    pbar = tqdm(
                        total=len(pdf_files),
                        desc="Processing files",
                        unit="file",
                        leave=False,
                        position=0,
                    )
                else:
                    # Open /dev/null for tqdm output in quiet mode
                    tqdm_file = open(os.devnull, "w")
                    pbar = tqdm(
                        total=len(pdf_files),
                        desc="Processing files",
                        unit="file",
                        leave=False,
                        position=0,
                        file=tqdm_file,
                        disable=True,
                    )

                try:
                    # Process results as they complete
                    for future in futures.as_completed(future_to_file):
                        if is_shutdown_requested():
                            log_message(
                                logger,
                                "WARNING",
                                "Shutdown requested. Waiting for current tasks to complete...",
                                quiet=config.quiet,  # Show in summary mode
                                summary=config.summary,
                            )
                            break

                        filename = future_to_file[future]
                        completed += 1

                        try:
                            success, processing_time, error, log_messages = (
                                future.result()
                            )

                            # Clear progress bar line if it exists
                            if pbar:
                                pbar.clear()

                            # Log file start
                            log_message(
                                logger,
                                "INFO",
                                f"[{completed}/{len(pdf_files)}] Processing: {filename}",
                                quiet=config.quiet
                                or config.summary,  # Hide in both quiet and summary modes
                                summary=config.summary,
                            )

                            # Write all log messages from the child process
                            for level, message in log_messages:
                                log_message(
                                    logger,
                                    level,
                                    message,
                                    quiet=config.quiet
                                    or config.summary,  # Hide in both quiet and summary modes
                                    summary=config.summary,
                                )

                            if success:
                                successful += 1
                                log_message(
                                    logger,
                                    "INFO",
                                    f"  ✓ Completed successfully in {processing_time:.2f} seconds\n",
                                    quiet=config.quiet
                                    or config.summary,  # Hide in both quiet and summary modes
                                    summary=config.summary,
                                )
                            else:
                                failed += 1
                                if error:
                                    errors.append((filename, error))
                                    log_message(
                                        logger,
                                        "ERROR",
                                        f"  ✗ Failed: {error}\n",
                                        quiet=config.quiet,  # Show in summary mode
                                        summary=config.summary,
                                    )

                            # Update progress bar if it exists
                            if pbar:
                                pbar.update(1)

                        except Exception as e:
                            failed += 1
                            error_msg = f"Error processing {filename}: {str(e)}"
                            log_message(
                                logger,
                                "ERROR",
                                error_msg,
                                quiet=config.quiet,
                                summary=config.summary,
                            )  # Show in summary mode
                            errors.append((filename, error_msg))
                            if pbar:
                                pbar.update(1)

                finally:
                    # Close progress bar and file
                    if pbar:
                        pbar.close()
                    if tqdm_file:
                        tqdm_file.close()

            # Log final summary
            total_time = get_total_time()
            summary = [
                "\nProcessing Summary:",
                "----------------",
                f"Files processed: {completed}",
                f"Total time: {total_time:.2f} seconds",
            ]

            if completed > 0:
                avg_time = total_time / completed
                summary.append(f"Average time per file: {avg_time:.2f} seconds")

            summary.extend([f"Successful: {successful}", f"Failed: {failed}"])

            if errors:
                summary.extend(["\nErrors:", "-------"])
                for filename, error in errors:
                    summary.extend([f"• {filename}:", f"  {error}"])

            # Remove empty lines at the beginning if they exist
            while summary and not summary[0]:
                summary.pop(0)

            log_message(
                logger, "INFO", "\n".join(summary), quiet=config.quiet
            )  # Show in summary mode

    except Exception as e:
        log_message(
            logger,
            "ERROR",
            f"Error processing PDFs: {str(e)}",
            quiet=config.quiet,  # Show in summary mode
        )
        raise
