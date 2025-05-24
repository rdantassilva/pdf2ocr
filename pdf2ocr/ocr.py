"""OCR-related functions for pdf2ocr."""

import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from io import BytesIO
from typing import List, Optional, Tuple

from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageOps
from pypdf import PdfReader
from pytesseract import image_to_string
from reportlab.pdfgen import canvas
from tqdm import tqdm

from pdf2ocr.logging_config import log_message


class OCRError(Exception):
    """Exception raised for errors during OCR processing."""

    pass


# Map most common languages (Tesseract code → Human-readable name)
LANG_NAMES = {
    "por": "Portuguese",
    "eng": "English",
    "spa": "Spanish",
    "fra": "French",
    "deu": "German",
    "ita": "Italian",
    "nld": "Dutch",
    "rus": "Russian",
    "tur": "Turkish",
    "jpn": "Japanese",
    "chi_sim": "Chinese (Simplified)",
    "chi_tra": "Chinese (Traditional)",
    "chi_sim_vert": "Chinese (Simplified, vertical)",
    "chi_tra_vert": "Chinese (Traditional, vertical)",
    "heb": "Hebrew",
}


def preprocess_image(img):
    """Pre-processes image to improve OCR quality.

    Args:
        img: PIL Image object

    Returns:
        PIL Image: Processed image ready for OCR
    """
    img = img.convert("L")  # Convert to grayscale
    img = ImageOps.autocontrast(img)  # Auto contrast enhancement
    img = img.filter(ImageFilter.MedianFilter())  # Noise reduction filter
    return img


def clean_text_portuguese(text):
    """Cleans text by removing unwanted (non-ASCII) non-Portuguese special characters, preserving Portuguese common characters.

    Args:
        text (str): Text to clean

    Returns:
        str: Cleaned text with only Portuguese characters and basic punctuation
    """
    allowed = (
        "a-zA-Z0-9"
        "áéíóúàãõâêôç"
        "ÁÉÍÓÚÀÃÕÂÊÔÇ"
        "\\s"
        "\\.,;:?!()\\[\\]{}\\-\"'"  # basic punctuation
    )
    return re.sub(f"[^{allowed}]", "", text)


def convert_image_to_pdf(image: Image.Image) -> PdfReader:
    """Convert a PIL Image to a PDF.

    Args:
        image: PIL Image to convert

    Returns:
        PdfReader: PDF reader object containing the image
    """
    temp_file = None
    try:
        # Create temporary file for image
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        # Save image to temporary file
        image.save(temp_file.name, format="PNG")

        # Create PDF from image
        pdf_buffer = BytesIO()
        c = canvas.Canvas(pdf_buffer)
        c.setPageSize((image.width, image.height))
        c.drawImage(temp_file.name, 0, 0, width=image.width, height=image.height)
        c.showPage()
        c.save()

        # Return PDF reader
        pdf_buffer.seek(0)
        return PdfReader(pdf_buffer)

    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def extract_text_from_image(image: Image.Image, lang: str, config: str = "") -> str:
    """Extract text from an image using OCR.

    Args:
        image: PIL Image to process
        lang: Language code for OCR
        config: Tesseract configuration string

    Returns:
        str: Extracted text
    """
    # Preprocess image for better OCR results
    image = preprocess_image(image)

    # Extract text using tesseract with configuration
    text = image_to_string(image, lang=lang, config=config)

    # Clean text if Portuguese
    if lang.lower() == "por":
        text = clean_text_portuguese(text)

    return text


def process_pdf_with_ocr(
    pdf_path: str,
    lang: str,
    logger: logging.Logger,
    quiet: bool = False,
    summary: bool = False,
    config: str = "",
) -> list:
    """Process PDF file with OCR.

    Args:
        pdf_path: Path to PDF file
        lang: OCR language code
        logger: Logger instance
        quiet: Whether to suppress progress output
        summary: Whether to show only summary output
        config: Tesseract configuration string

    Returns:
        list: List of tuples (page_number, text)
    """
    pages = []

    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=400, use_pdftocairo=True)

        # Configure tqdm to write to /dev/null in quiet mode
        tqdm_file = open(os.devnull, "w") if (quiet or summary) else sys.stderr

        try:
            # Process each page with OCR
            for i, image in enumerate(
                tqdm(
                    images,
                    desc="Processing pages",
                    unit="page",
                    file=tqdm_file,
                    disable=quiet or summary,
                    leave=False,
                )
            ):  # Disable progress bar in both quiet and summary modes
                text = extract_text_from_image(image, lang, config)
                pages.append((i + 1, text))

        finally:
            # Close tqdm file if it was opened
            if tqdm_file != sys.stderr:
                tqdm_file.close()

    except Exception as e:
        log_message(
            logger, "ERROR", f"Error processing PDF: {str(e)}", quiet=False
        )  # Always show errors
        raise

    return pages


def extract_text_from_pdf(
    pdf_path: str,
    tesseract_config: List[str],
    lang_code: str = "por",
    quiet: bool = False,
    summary: bool = False,
    batch_size: Optional[int] = None,
) -> Tuple[str, List[str], float]:
    """Extract text from PDF using OCR.

    Args:
        pdf_path: Path to PDF file
        tesseract_config: Tesseract configuration options
        lang_code: Language code for OCR (default: por)
        quiet: Whether to suppress progress output
        summary: Whether to show only summary output
        batch_size: Number of pages to process in each batch (disabled by default)

    Returns:
        tuple: (combined text, list of page texts, processing time)
    """
    start_time = time.time()
    final_text = []

    # Convert list config to string
    config_string = " ".join(tesseract_config) if tesseract_config else ""

    try:
        # Get total number of pages
        with open(pdf_path, "rb") as f:
            pdf = PdfReader(f)
            total_pages = len(pdf.pages)

        # Pre-allocate text_pages list with empty strings
        text_pages = [""] * total_pages

        # Configure tqdm to write to /dev/null in quiet mode
        tqdm_file = open(os.devnull, "w") if (quiet or summary) else sys.stderr

        try:
            if batch_size is None:
                # Process all pages at once
                pages_batch = convert_from_path(
                    pdf_path,
                    dpi=400,
                    use_pdftocairo=True,
                )

                # Process each page
                for page_num, page_img in enumerate(
                    tqdm(
                        pages_batch,
                        desc="Processing pages",
                        unit="page",
                        file=tqdm_file,
                        disable=quiet or summary,
                        leave=False,
                    )
                ):
                    # Extract text from image with configuration
                    text = extract_text_from_image(page_img, lang_code, config_string)

                    # Store text directly in pre-allocated list
                    text_pages[page_num] = text
                    final_text.append(text)

                # Explicitly free memory
                del pages_batch
            else:
                # Process pages in batches
                for batch_start in tqdm(
                    range(1, total_pages + 1, batch_size),
                    desc="Processing batches",
                    unit="batch",
                    file=tqdm_file,
                    disable=quiet or summary,
                    leave=False,
                ):
                    batch_end = min(batch_start + batch_size - 1, total_pages)

                    # Convert batch of pages to images
                    pages_batch = convert_from_path(
                        pdf_path,
                        dpi=400,
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
                            disable=quiet or summary,
                            leave=False,
                            position=1,
                        ),
                        start=batch_start - 1,
                    ):
                        # Extract text from image with configuration
                        text = extract_text_from_image(
                            page_img, lang_code, config_string
                        )

                        # Store text directly in pre-allocated list
                        text_pages[page_num] = text
                        final_text.append(text)

                    # Explicitly free memory
                    del pages_batch

        finally:
            # Close tqdm file if it was opened
            if tqdm_file != sys.stderr:
                tqdm_file.close()

    except Exception as e:
        raise OCRError(f"Error during OCR processing: {str(e)}")

    return "\n\n".join(final_text), text_pages, time.time() - start_time


def validate_tesseract_language(
    lang_code: str, logger: Optional[logging.Logger] = None, quiet: bool = False
) -> None:
    """Validate if the specified Tesseract language model is installed.

    Args:
        lang_code: Language code to validate
        logger: Optional logger instance
        quiet: Whether to suppress console output

    Raises:
        RuntimeError: If the language model is not installed
    """
    try:
        # Get list of installed languages
        result = subprocess.run(
            ["tesseract", "--list-langs"], capture_output=True, text=True, check=True
        )

        # Parse installed languages
        installed_langs = result.stdout.strip().split("\n")[
            1:
        ]  # Skip first line (header)

        # Check if language is installed
        if lang_code not in installed_langs:
            error_msg = (
                f"Language model '{lang_code}' not found. Please install it with:\n"
            )
            error_msg += f"sudo apt-get install tesseract-ocr-{lang_code}"
            raise RuntimeError(error_msg)

        log_message(
            logger,
            "INFO",
            f"Using Tesseract language model: {lang_code} ({LANG_NAMES.get(lang_code, 'Unknown')})",
            quiet=quiet,  # Show in summary mode
        )

    except subprocess.CalledProcessError as e:
        error_msg = "Error checking Tesseract language model. Is Tesseract installed?"
        if e.stderr:
            error_msg += f"\nError: {e.stderr.strip()}"
        raise RuntimeError(error_msg) from e
