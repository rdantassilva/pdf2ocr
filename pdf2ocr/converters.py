"""Converters module for pdf2ocr.

This module provides the main conversion functionality for pdf2ocr.
It imports and re-exports the conversion functions from the specialized submodules.
"""

from pdf2ocr.converters.docx import save_as_docx
from pdf2ocr.converters.epub import convert_docx_to_epub
from pdf2ocr.converters.html import save_as_html
from pdf2ocr.converters.pdf import (process_layout_pdf_only,
                                    process_pdfs_with_ocr, save_as_pdf)

__all__ = [
    "process_pdfs_with_ocr",
    "process_layout_pdf_only",
    "save_as_pdf",
    "save_as_docx",
    "save_as_html",
    "convert_docx_to_epub",
]
