"""Tests for PDF generation."""

import subprocess
from pathlib import Path
from pdf2ocr.config import ProcessingConfig
from pdf2ocr.main import process_pdfs_with_ocr
from pdf2ocr.utils import setup_logging

def test_pdf_generated(tmp_path):
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Create configuration
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_pdf=True
    )

    # Setup logger for testing
    logger = setup_logging(log_path=None, quiet=True)

    # Run the process
    process_pdfs_with_ocr(config, logger)

    # Check if PDF was generated
    pdf_dir = output_dir / "pdf_ocr"
    assert pdf_dir.exists()
    assert any(pdf_dir.glob("*_ocr.pdf"))