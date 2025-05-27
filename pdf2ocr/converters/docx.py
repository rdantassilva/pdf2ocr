"""DOCX conversion and processing functionality."""

import os
import time
from typing import List, Union

from docx import Document
from docx.shared import Pt, RGBColor

from pdf2ocr.converters.common import process_paragraphs


def save_as_docx(text_pages: Union[str, List[str]], output_path: str) -> float:
    """Creates a new DOCX document with OCR-extracted text in a clean format.

    This function generates a new Word document that focuses on text readability
    and consistent formatting. It's ideal for cases where you want to extract
    and reformat content from PDFs into an editable Word format.

    Key features:
    - Creates a new DOCX with clean, consistent formatting
    - Preserves paragraph structure and text flow
    - Uses standard fonts and margins for optimal readability
    - Creates output in 'docx_ocr' directory
    - Includes document properties (title, author)

    Args:
        text_pages: Text content as a string or list of pages
        output_path: Path where to save the DOCX file

    Returns:
        float: Time taken to save the file in seconds
    """
    start = time.perf_counter()

    # Create new document
    doc = Document()

    # Set document properties
    doc.core_properties.author = "pdf2ocr"
    doc.core_properties.title = os.path.splitext(os.path.basename(output_path))[0]

    # Set default font
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)
    font.color.rgb = RGBColor(0, 0, 0)

    # Process text content
    paragraphs = process_paragraphs(text_pages)

    # Add paragraphs to document
    for para in paragraphs:
        if para.strip():  # Skip empty paragraphs
            p = doc.add_paragraph(para.strip())
            p.style = doc.styles["Normal"]

    # Save the document
    doc.save(output_path)
    return time.perf_counter() - start
