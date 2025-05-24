from typing import List, Optional, Tuple
import time
import os
import sys
from pdf2image import convert_from_path
from tqdm import tqdm

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
                    # Extract text from image
                    text = extract_text_from_image(page_img, lang_code)

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
                        # Extract text from image
                        text = extract_text_from_image(page_img, lang_code)

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