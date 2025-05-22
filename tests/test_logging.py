"""Tests for logging functionality."""

import os
from pathlib import Path
from pdf2ocr.config import ProcessingConfig
from pdf2ocr.main import process_pdfs_with_ocr, process_layout_pdf_only
from pdf2ocr.logging_config import setup_logging, log_message
from pdf2ocr import __version__


def test_logging_output(tmp_path):
    """Test if log file is created and contains content."""
    # Setup test paths
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    log_file = tmp_path / "test.log"
    output_dir.mkdir()

    # Create configuration with logging
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_pdf=True,
        log_path=str(log_file)
    )

    # Run the process
    process_pdfs_with_ocr(config, setup_logging(str(log_file), quiet=True))

    # Check if log file exists and has content
    assert log_file.exists(), "Log file was not created"
    assert log_file.stat().st_size > 0, "Log file is empty"


def test_layout_mode_logging(tmp_path):
    """Test if log file is created and contains content in layout mode."""
    # Setup test paths
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    log_file = tmp_path / "test_layout.log"
    output_dir.mkdir()

    # Create configuration with logging and layout preservation
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_pdf=True,
        preserve_layout=True,
        log_path=str(log_file)
    )

    # Run the process
    process_layout_pdf_only(config, setup_logging(str(log_file), quiet=True))

    # Check if log file exists and has content
    assert log_file.exists(), "Log file was not created"
    assert log_file.stat().st_size > 0, "Log file is empty"


def test_quiet_mode_logging(tmp_path):
    """Test if log file is created and contains content in quiet mode."""
    # Setup test paths
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    log_file = tmp_path / "test_quiet.log"
    output_dir.mkdir()

    # Create configuration with logging and quiet mode
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_pdf=True,
        quiet=True,
        log_path=str(log_file)
    )

    # Run the process
    process_pdfs_with_ocr(config, setup_logging(str(log_file), quiet=True))

    # Check if log file exists and has content
    assert log_file.exists(), "Log file was not created"
    assert log_file.stat().st_size > 0, "Log file is empty" 