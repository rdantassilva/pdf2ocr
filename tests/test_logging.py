"""Tests for logging functionality."""

import os
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
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


def test_quiet_mode(tmp_path):
    """Test quiet mode output behavior."""
    # Setup test paths
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    log_file = tmp_path / "test_quiet.log"
    output_dir.mkdir()

    # Create configuration with quiet mode
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_pdf=True,
        quiet=True,
        log_path=str(log_file)
    )

    # Capture stdout and stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with redirect_stdout(stdout), redirect_stderr(stderr):
        # Log some test messages
        logger = setup_logging(str(log_file), quiet=True)
        
        # Version and language info (should not appear in quiet mode)
        log_message(logger, "INFO", f"PDF2OCR v{__version__}", quiet=config.quiet)
        log_message(logger, "INFO", "Using Tesseract language model: por (Portuguese)", quiet=config.quiet)
        
        # Regular info (should not appear in quiet mode)
        log_message(logger, "INFO", "Processing files...", quiet=config.quiet)
        
        # Warning (should not appear in quiet mode)
        log_message(logger, "WARNING", "Test warning message", quiet=config.quiet)
        
        # Error (should appear even in quiet mode)
        log_message(logger, "ERROR", "Test error message", quiet=config.quiet)

        # Process files to test tqdm output
        process_pdfs_with_ocr(config, logger)

    # Get captured output
    stdout_content = stdout.getvalue()
    stderr_content = stderr.getvalue()

    # Verify quiet mode behavior
    assert "PDF2OCR v" not in stdout_content, "Version info should not appear in quiet mode"
    assert "Using Tesseract language model" not in stdout_content, "Language info should not appear in quiet mode"
    assert "Processing files" not in stdout_content, "Regular info should not appear in quiet mode"
    assert "WARNING" not in stderr_content, "Warnings should not appear in quiet mode"
    assert "Test error message" in stderr_content, "Errors should appear even in quiet mode"
    
    # Check specifically for tqdm progress messages
    assert "Processing pages:" not in stdout_content, "tqdm progress should not appear in stdout in quiet mode"
    assert "Processing pages:" not in stderr_content, "tqdm progress should not appear in stderr in quiet mode"
    assert "%" not in stdout_content and "%" not in stderr_content, "Progress percentage should not appear in quiet mode"

    # Verify log file contains everything
    with open(log_file, 'r') as f:
        log_content = f.read()
        assert "PDF2OCR v" in log_content, "Version info should be in log file"
        assert "Using Tesseract language model" in log_content, "Language info should be in log file"
        assert "Processing files" in log_content, "Regular info should be in log file"
        assert "WARNING" in log_content, "Warnings should be in log file"
        assert "Test error message" in log_content, "Errors should be in log file"


def test_quiet_mode_with_layout(tmp_path):
    """Test quiet mode output behavior with layout preservation."""
    # Setup test paths
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    log_file = tmp_path / "test_quiet_layout.log"
    output_dir.mkdir()

    # Create configuration with quiet mode and layout preservation
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_pdf=True,
        generate_docx=True,  # Enable DOCX to trigger the warning
        generate_epub=True,  # Enable EPUB to trigger the warning
        preserve_layout=True,
        quiet=True,
        log_path=str(log_file)
    )

    # Capture stdout and stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with redirect_stdout(stdout), redirect_stderr(stderr):
        # Process files in layout mode
        process_layout_pdf_only(config, setup_logging(str(log_file), quiet=True))

    # Get captured output
    stdout_content = stdout.getvalue()
    stderr_content = stderr.getvalue()

    # In quiet mode, stdout must be completely empty
    assert stdout_content == "", f"stdout should be empty in quiet mode, but got:\n{stdout_content}"

    # In quiet mode, stderr should only contain errors (if any)
    # Check specifically for tqdm progress bar patterns
    tqdm_patterns = [
        "Processing pages:",  # Progress bar description
        "%|",                # Progress percentage with bar
        "it/s]",            # Speed indicator
        "page]",            # Unit indicator
        "[K",               # ANSI escape code used by tqdm
        "it [",             # Another tqdm pattern
    ]
    for pattern in tqdm_patterns:
        assert pattern not in stderr_content, f"tqdm pattern '{pattern}' should not appear in quiet mode, but got:\n{stderr_content}"

    # If there are any other messages in stderr, they must be errors
    if stderr_content and not any(error_indicator in stderr_content for error_indicator in ["ERROR:", "Error in", "Error during"]):
        assert False, f"stderr should only contain errors in quiet mode, but got:\n{stderr_content}"

    # Verify log file contains everything
    with open(log_file, 'r') as f:
        log_content = f.read()
        assert "Layout preservation mode only supports PDF output" in log_content, "Layout warning should be in log file"
        assert "Processing 1 files using" in log_content, "Processing info should be in log file"
        assert "PDF folder created" in log_content, "Debug info should be in log file"
        assert "OCR processing took" in log_content, "Processing info should be in log file"
        assert "Layout-preserving PDF created" in log_content, "Processing info should be in log file"
        assert "Processing Summary" in log_content, "Summary should be in log file"


def test_summary_mode(tmp_path):
    """Test summary mode output behavior."""
    # Setup test paths
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    log_file = tmp_path / "test_summary.log"
    output_dir.mkdir()

    # Create configuration with summary mode
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_pdf=True,
        summary=True,
        log_path=str(log_file)
    )

    # Capture stdout and stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with redirect_stdout(stdout), redirect_stderr(stderr):
        # Log some test messages
        logger = setup_logging(str(log_file), quiet=False)
        
        # Version and language info (should appear in summary mode)
        log_message(logger, "INFO", f"PDF2OCR v{__version__}", quiet=False)
        log_message(logger, "INFO", "Using Tesseract language model: por (Portuguese)", quiet=False)
        
        # Regular info (should not appear in summary mode)
        log_message(logger, "INFO", "Processing files...", quiet=config.summary)
        log_message(logger, "DEBUG", "Creating output directory", quiet=config.summary)
        
        # Warning (should appear in summary mode)
        log_message(logger, "WARNING", "Test warning message", quiet=False)
        
        # Error (should appear in summary mode)
        log_message(logger, "ERROR", "Test error message", quiet=False)
        
        # Summary (should appear in summary mode)
        log_message(logger, "INFO", "\nProcessing Summary:\n----------------\nFiles processed: 1", quiet=False)

        # Process files to test tqdm output
        process_pdfs_with_ocr(config, logger)

    # Get captured output
    stdout_content = stdout.getvalue()
    stderr_content = stderr.getvalue()

    # Verify summary mode behavior
    assert "PDF2OCR v" in stdout_content, "Version info should appear in summary mode"
    assert "Using Tesseract language model" in stdout_content, "Language info should appear in summary mode"
    assert "Processing files" not in stdout_content, "Regular info should not appear in summary mode"
    assert "Creating output directory" not in stdout_content, "Debug info should not appear in summary mode"
    assert "WARNING" in stderr_content, "Warnings should appear in summary mode"
    assert "Test error message" in stderr_content, "Errors should appear in summary mode"
    assert "Processing Summary:" in stdout_content, "Summary should appear in summary mode"

    # Check specifically for tqdm progress messages
    assert "Processing pages:" not in stdout_content, "tqdm progress should not appear in stdout in summary mode"
    assert "Processing pages:" not in stderr_content, "tqdm progress should not appear in stderr in summary mode"
    assert "%" not in stdout_content and "%" not in stderr_content, "Progress percentage should not appear in summary mode"

    # Verify log file contains everything
    with open(log_file, 'r') as f:
        log_content = f.read()
        assert "PDF2OCR v" in log_content, "Version info should be in log file"
        assert "Using Tesseract language model" in log_content, "Language info should be in log file"
        assert "Processing files" in log_content, "Regular info should be in log file"
        assert "Creating output directory" in log_content, "Debug info should be in log file"
        assert "WARNING" in log_content, "Warnings should be in log file"
        assert "Test error message" in log_content, "Errors should be in log file"
        assert "Processing Summary:" in log_content, "Summary should be in log file"


def test_summary_mode_with_layout(tmp_path):
    """Test summary mode output behavior with layout preservation."""
    # Setup test paths
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    log_file = tmp_path / "test_summary_layout.log"
    output_dir.mkdir()

    # Create configuration with summary mode and layout preservation
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_pdf=True,
        generate_docx=True,  # Enable DOCX to trigger the warning
        generate_epub=True,  # Enable EPUB to trigger the warning
        preserve_layout=True,
        summary=True,
        log_path=str(log_file)
    )

    # Capture stdout and stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with redirect_stdout(stdout), redirect_stderr(stderr):
        # Log some test messages
        logger = setup_logging(str(log_file), quiet=False)
        
        # Version and language info (should appear in summary mode)
        log_message(logger, "INFO", f"PDF2OCR v{__version__}", quiet=False)
        log_message(logger, "INFO", "Using Tesseract language model: por (Portuguese)", quiet=False)
        
        # Layout warning (should appear in summary mode)
        log_message(
            logger,
            "WARNING",
            "Layout preservation mode only supports PDF output. Other formats will be disabled.",
            quiet=False
        )
        
        # Regular info (should not appear in summary mode)
        log_message(logger, "INFO", "Processing files...", quiet=config.summary)
        log_message(logger, "DEBUG", "Creating output directory", quiet=config.summary)
        
        # Progress info (should not appear in summary mode)
        log_message(logger, "INFO", "Processing page 1 of 10", quiet=config.summary)
        
        # Summary (should appear in summary mode)
        log_message(logger, "INFO", "\nProcessing Summary:\n----------------\nFiles processed: 1", quiet=False)

    # Get captured output
    stdout_content = stdout.getvalue()
    stderr_content = stderr.getvalue()

    # Verify summary mode behavior with layout preservation
    assert "PDF2OCR v" in stdout_content, "Version info should appear in summary mode"
    assert "Using Tesseract language model" in stdout_content, "Language info should appear in summary mode"
    assert "Layout preservation mode" in stderr_content, "Layout warning should appear in summary mode"
    assert "Processing files" not in stdout_content, "Regular info should not appear in summary mode"
    assert "Creating output directory" not in stdout_content, "Debug info should not appear in summary mode"
    assert "Processing page" not in stdout_content, "Progress info should not appear in summary mode"
    assert "Processing pages" not in stdout_content, "Progress bar should not appear in summary mode"
    assert "Processing Summary:" in stdout_content, "Summary should appear in summary mode"

    # Verify log file contains everything
    with open(log_file, 'r') as f:
        log_content = f.read()
        assert "PDF2OCR v" in log_content, "Version info should be in log file"
        assert "Using Tesseract language model" in log_content, "Language info should be in log file"
        assert "Layout preservation mode" in log_content, "Layout warning should be in log file"
        assert "Processing files" in log_content, "Regular info should be in log file"
        assert "Creating output directory" in log_content, "Debug info should be in log file"
        assert "Processing page" in log_content, "Progress info should be in log file"
        assert "Processing Summary:" in log_content, "Summary should be in log file"


def test_ebook_convert_logging_behavior(tmp_path):
    """Test that ebook-convert output is logged to file but not shown in console."""
    # Setup test paths
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    log_file = tmp_path / "test_ebook_convert.log"
    output_dir.mkdir()

    # Create configuration with EPUB generation
    config = ProcessingConfig(
        source_dir=input_pdf,
        dest_dir=str(output_dir),
        generate_docx=True,  # Required for EPUB
        generate_epub=True,
        log_path=str(log_file)
    )

    # Mock subprocess.run to simulate ebook-convert execution
    from unittest.mock import patch, MagicMock
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Converting input to output...\nConversion completed successfully\nOutput written to test.epub"
    mock_result.stderr = "ebook-convert (calibre 5.44.0)\nCreated by: Kovid Goyal <kovid@kovidgoyal.net>"
    
    # Capture stdout and stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with patch('subprocess.run') as mock_subprocess:
        mock_subprocess.return_value = mock_result
        
        # Also mock calibre availability check
        with patch('pdf2ocr.converters.epub.is_calibre_available', return_value=True):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                # Set up logging
                logger = setup_logging(str(log_file), quiet=False)
                
                # Test the EPUB conversion directly
                from pdf2ocr.converters.epub import convert_docx_to_epub
                
                # Create a mock DOCX file
                mock_docx_path = tmp_path / "test.docx"
                mock_docx_path.write_text("mock docx content")
                mock_epub_path = tmp_path / "test.epub"
                
                # Run the conversion
                success, duration, output = convert_docx_to_epub(
                    str(mock_docx_path), 
                    str(mock_epub_path), 
                    logger=logger, 
                    quiet=False, 
                    lang="por"
                )

    # Get captured output
    stdout_content = stdout.getvalue()
    stderr_content = stderr.getvalue()

    # Verify that ebook-convert output does NOT appear in console
    assert "Converting input to output" not in stdout_content, "ebook-convert stdout should not appear in console"
    assert "Converting input to output" not in stderr_content, "ebook-convert stdout should not appear in console"
    assert "ebook-convert (calibre" not in stdout_content, "ebook-convert stderr should not appear in console"
    assert "ebook-convert (calibre" not in stderr_content, "ebook-convert stderr should not appear in console"
    assert "Conversion completed successfully" not in stdout_content, "ebook-convert details should not appear in console"
    assert "Conversion completed successfully" not in stderr_content, "ebook-convert details should not appear in console"

    # Verify that ebook-convert output DOES appear in log file
    with open(log_file, 'r') as f:
        log_content = f.read()
        
        # Check that the command is logged
        assert "Running ebook-convert for test.docx" in log_content, "ebook-convert command should be logged"
        assert "ebook-convert" in log_content, "ebook-convert command should be in log"
        
        # Check that stdout is logged
        assert "ebook-convert output for test.docx" in log_content, "ebook-convert output header should be logged"
        assert "Converting input to output" in log_content, "ebook-convert stdout should be logged"
        assert "Conversion completed successfully" in log_content, "ebook-convert completion message should be logged"
        
        # Check that stderr is logged
        assert "ebook-convert messages for test.docx" in log_content, "ebook-convert messages header should be logged"
        assert "ebook-convert (calibre" in log_content, "ebook-convert version info should be logged"
        assert "Created by: Kovid Goyal" in log_content, "ebook-convert author info should be logged"

    # Verify conversion was successful
    assert success, "EPUB conversion should succeed"
    assert duration > 0, "Conversion should take some time"
    assert output == mock_result.stdout, "Output should match mocked stdout"


def test_ebook_convert_error_logging_behavior(tmp_path):
    """Test that ebook-convert errors are logged to file and shown in console."""
    # Setup test paths
    log_file = tmp_path / "test_ebook_convert_error.log"

    # Mock subprocess.run to simulate ebook-convert failure
    from unittest.mock import patch, MagicMock
    import subprocess
    
    mock_error = subprocess.CalledProcessError(
        returncode=1, 
        cmd=['ebook-convert', 'test.docx', 'test.epub'],
        stderr="Error: Input file 'test.docx' is corrupted\nConversion failed with exit code 1"
    )
    
    # Capture stdout and stderr
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with patch('subprocess.run') as mock_subprocess:
        mock_subprocess.side_effect = mock_error
        
        # Also mock calibre availability check
        with patch('pdf2ocr.converters.epub.is_calibre_available', return_value=True):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                # Set up logging
                logger = setup_logging(str(log_file), quiet=False)
                
                # Test the EPUB conversion directly
                from pdf2ocr.converters.epub import convert_docx_to_epub
                
                # Create a mock DOCX file
                mock_docx_path = tmp_path / "test.docx"
                mock_docx_path.write_text("mock docx content")
                mock_epub_path = tmp_path / "test.epub"
                
                # Run the conversion (should fail)
                success, duration, output = convert_docx_to_epub(
                    str(mock_docx_path), 
                    str(mock_epub_path), 
                    logger=logger, 
                    quiet=False, 
                    lang="por"
                )

    # Get captured output
    stdout_content = stdout.getvalue()
    stderr_content = stderr.getvalue()

    # Verify that error summary DOES appear in console (errors should be shown)
    assert "Error converting test.docx to EPUB" in stderr_content, "Error summary should appear in console"
    assert "Input file 'test.docx' is corrupted" in stderr_content, "Error details should appear in console"

    # Verify that detailed error output is logged to file
    with open(log_file, 'r') as f:
        log_content = f.read()
        
        # Check that the full error is logged
        assert "Full ebook-convert error output" in log_content, "Full error header should be logged"
        assert "Input file 'test.docx' is corrupted" in log_content, "Error details should be logged"
        assert "Conversion failed with exit code 1" in log_content, "Full error should be logged"
        
        # Check that the error summary is also logged
        assert "Error converting test.docx to EPUB" in log_content, "Error summary should be logged"

    # Verify conversion failed
    assert not success, "EPUB conversion should fail"
    assert duration > 0, "Failed conversion should still take some time"
    assert "Input file 'test.docx' is corrupted" in output, "Output should contain error details" 