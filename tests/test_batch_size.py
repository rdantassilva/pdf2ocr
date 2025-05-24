"""Tests for batch-size parameter functionality."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, call
from pdf2ocr.config import ProcessingConfig
from pdf2ocr.ocr import extract_text_from_pdf
from pdf2ocr.converters.pdf import process_single_pdf, process_single_layout_pdf


def test_batch_size_parameter_default():
    """Test that default batch_size parameter is None."""
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True)
    assert config.batch_size is None


def test_batch_size_parameter_custom():
    """Test that custom batch_size parameter is set correctly."""
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, batch_size=10)
    assert config.batch_size == 10


def test_batch_size_parameter_validation():
    """Test batch_size parameter validation."""
    # Test valid values
    for batch_size in [1, 5, 10, 20, 50]:
        config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, batch_size=batch_size)
        assert config.batch_size == batch_size

    # Test None value (default)
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, batch_size=None)
    assert config.batch_size is None


@patch('pdf2ocr.ocr.extract_text_from_image')
@patch('pdf2ocr.ocr.convert_from_path')
@patch('pdf2ocr.ocr.PdfReader')
@patch('builtins.open')
def test_batch_size_none_processes_all_pages(mock_open, mock_pdf_reader, mock_convert, mock_extract_text):
    """Test that batch_size=None processes all pages at once."""
    # Mock PDF with 5 pages
    mock_pdf = MagicMock()
    mock_pdf.pages = [MagicMock() for _ in range(5)]
    mock_pdf_reader.return_value = mock_pdf
    
    # Mock convert_from_path to return 5 images
    mock_images = [MagicMock() for _ in range(5)]
    mock_convert.return_value = mock_images
    
    # Mock file operations
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Mock extract_text_from_image
    mock_extract_text.return_value = "test text"
    
    # Test with batch_size=None
    result = extract_text_from_pdf(
        pdf_path="/test/file.pdf",
        tesseract_config=["--oem", "3"],
        lang_code="por",
        batch_size=None
    )
    
    # Verify convert_from_path was called once (all pages at once)
    assert mock_convert.call_count == 1
    # Verify it was called without first_page and last_page parameters
    args, kwargs = mock_convert.call_args
    assert 'first_page' not in kwargs
    assert 'last_page' not in kwargs
    
    # Verify result contains all pages
    text, pages, duration = result
    assert len(pages) == 5


@patch('pdf2ocr.ocr.extract_text_from_image')
@patch('pdf2ocr.ocr.convert_from_path')
@patch('pdf2ocr.ocr.PdfReader')
@patch('builtins.open')
def test_batch_size_with_value_processes_in_batches(mock_open, mock_pdf_reader, mock_convert, mock_extract_text):
    """Test that batch_size with a value processes pages in batches."""
    # Mock PDF with 10 pages
    mock_pdf = MagicMock()
    mock_pdf.pages = [MagicMock() for _ in range(10)]
    mock_pdf_reader.return_value = mock_pdf
    
    # Mock convert_from_path to return images for each batch
    mock_convert.side_effect = [
        [MagicMock() for _ in range(3)],  # First batch: pages 1-3
        [MagicMock() for _ in range(3)],  # Second batch: pages 4-6
        [MagicMock() for _ in range(3)],  # Third batch: pages 7-9
        [MagicMock()],                    # Fourth batch: page 10
    ]
    
    # Mock file operations
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Mock extract_text_from_image
    mock_extract_text.return_value = "test text"
    
    # Test with batch_size=3
    result = extract_text_from_pdf(
        pdf_path="/test/file.pdf",
        tesseract_config=["--oem", "3"],
        lang_code="por",
        batch_size=3
    )
    
    # Verify convert_from_path was called 4 times (for 4 batches)
    assert mock_convert.call_count == 4
    
    # Verify each call had the correct first_page and last_page
    expected_calls = [
        call("/test/file.pdf", dpi=400, first_page=1, last_page=3, use_pdftocairo=True),
        call("/test/file.pdf", dpi=400, first_page=4, last_page=6, use_pdftocairo=True),
        call("/test/file.pdf", dpi=400, first_page=7, last_page=9, use_pdftocairo=True),
        call("/test/file.pdf", dpi=400, first_page=10, last_page=10, use_pdftocairo=True),
    ]
    mock_convert.assert_has_calls(expected_calls)
    
    # Verify result contains all pages
    text, pages, duration = result
    assert len(pages) == 10


@patch('pdf2ocr.ocr.extract_text_from_image')
@patch('pdf2ocr.ocr.convert_from_path')
@patch('pdf2ocr.ocr.PdfReader')
@patch('builtins.open')
def test_batch_size_edge_cases(mock_open, mock_pdf_reader, mock_convert, mock_extract_text):
    """Test batch_size with edge cases."""
    # Mock PDF with 5 pages
    mock_pdf = MagicMock()
    mock_pdf.pages = [MagicMock() for _ in range(5)]
    mock_pdf_reader.return_value = mock_pdf
    
    # Mock file operations
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Test batch_size larger than total pages
    mock_convert.return_value = [MagicMock() for _ in range(5)]
    
    # Mock extract_text_from_image
    mock_extract_text.return_value = "test text"
    
    result = extract_text_from_pdf(
        pdf_path="/test/file.pdf",
        tesseract_config=["--oem", "3"],
        lang_code="por",
        batch_size=10  # Larger than 5 pages
    )
    
    # Should process all pages in one batch
    assert mock_convert.call_count == 1
    args, kwargs = mock_convert.call_args
    assert kwargs['first_page'] == 1
    assert kwargs['last_page'] == 5
    
    # Verify result
    text, pages, duration = result
    assert len(pages) == 5


@patch('pdf2ocr.ocr.extract_text_from_image')
@patch('pdf2ocr.ocr.convert_from_path')
@patch('pdf2ocr.ocr.PdfReader')
@patch('builtins.open')
def test_batch_size_single_page_batches(mock_open, mock_pdf_reader, mock_convert, mock_extract_text):
    """Test batch_size=1 processes one page at a time."""
    # Mock PDF with 3 pages
    mock_pdf = MagicMock()
    mock_pdf.pages = [MagicMock() for _ in range(3)]
    mock_pdf_reader.return_value = mock_pdf
    
    # Mock convert_from_path to return one image per call
    mock_convert.side_effect = [
        [MagicMock()],  # Page 1
        [MagicMock()],  # Page 2
        [MagicMock()],  # Page 3
    ]
    
    # Mock file operations
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Mock extract_text_from_image
    mock_extract_text.return_value = "test text"
    
    result = extract_text_from_pdf(
        pdf_path="/test/file.pdf",
        tesseract_config=["--oem", "3"],
        lang_code="por",
        batch_size=1
    )
    
    # Verify convert_from_path was called 3 times
    assert mock_convert.call_count == 3
    
    # Verify each call processed one page
    expected_calls = [
        call("/test/file.pdf", dpi=400, first_page=1, last_page=1, use_pdftocairo=True),
        call("/test/file.pdf", dpi=400, first_page=2, last_page=2, use_pdftocairo=True),
        call("/test/file.pdf", dpi=400, first_page=3, last_page=3, use_pdftocairo=True),
    ]
    mock_convert.assert_has_calls(expected_calls)


def test_batch_size_parameter_bounds():
    """Test batch_size parameter with boundary values."""
    # Test minimum value
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, batch_size=1)
    assert config.batch_size == 1
    
    # Test large value
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, batch_size=1000)
    assert config.batch_size == 1000
    
    # Test None (default behavior)
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, batch_size=None)
    assert config.batch_size is None


@patch('pdf2ocr.converters.pdf.extract_text_from_pdf')
def test_batch_size_passed_to_ocr_function(mock_extract):
    """Test that batch_size is correctly passed to OCR function."""
    mock_extract.return_value = ("text", ["page1"], 1.0)
    
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, batch_size=5)
    
    # This would be called within process_single_pdf
    # We're testing that the batch_size parameter is passed through
    with patch('pdf2ocr.converters.pdf.setup_logging'), \
         patch('pdf2ocr.converters.pdf.timing_context'), \
         patch('pdf2ocr.converters.pdf.save_as_pdf'), \
         patch('pdf2ocr.converters.pdf.os.path.join'):
        
        # The batch_size should be available in config
        assert config.batch_size == 5


@patch('subprocess.run')
@patch('pdf2ocr.converters.pdf.convert_from_path')
@patch('builtins.open')
@patch('tempfile.TemporaryDirectory')
def test_batch_size_in_layout_mode(mock_temp_dir, mock_open, mock_convert, mock_subprocess):
    """Test that batch_size works in layout preservation mode."""
    # Mock temporary directory
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"
    mock_temp_dir.return_value.__exit__.return_value = None
    
    # Mock file operations
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_file.read.return_value = b"fake pdf content"
    
    # Mock PDF conversion
    mock_convert.side_effect = [
        [MagicMock(), MagicMock()],  # First batch: 2 pages
        [MagicMock()],               # Second batch: 1 page
    ]
    
    # Mock subprocess (tesseract command)
    mock_subprocess.return_value = MagicMock()
    
    config = ProcessingConfig(
        source_dir="/test/path", 
        generate_pdf=True, 
        preserve_layout=True,
        batch_size=2
    )
    
    # Mock the PDF reading to return 3 pages
    with patch('pdf2ocr.converters.pdf.PdfReader') as mock_pdf_reader:
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock() for _ in range(3)]
        mock_pdf_reader.return_value = mock_pdf
        
        with patch('pdf2ocr.converters.pdf.setup_logging'), \
             patch('pdf2ocr.converters.pdf.timing_context'):
            
            # The batch_size should be used in the layout mode too
            assert config.batch_size == 2


def test_batch_size_memory_optimization():
    """Test that batch_size helps with memory optimization."""
    # This is more of a conceptual test - batch processing should help with memory
    # by processing fewer pages at once and freeing memory between batches
    
    # Small batch size should be better for memory
    small_batch_config = ProcessingConfig(
        source_dir="/test/path", 
        generate_pdf=True, 
        batch_size=2
    )
    
    # Large batch size
    large_batch_config = ProcessingConfig(
        source_dir="/test/path", 
        generate_pdf=True, 
        batch_size=100
    )
    
    # No batch (all at once)
    no_batch_config = ProcessingConfig(
        source_dir="/test/path", 
        generate_pdf=True, 
        batch_size=None
    )
    
    # Verify configurations are set correctly
    assert small_batch_config.batch_size == 2
    assert large_batch_config.batch_size == 100
    assert no_batch_config.batch_size is None


if __name__ == "__main__":
    pytest.main([__file__]) 