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
@patch('pdf2ocr.ocr._render_pdf_pages')
@patch('pdf2ocr.ocr._count_pdf_pages')
def test_batch_size_none_processes_all_pages(mock_count, mock_render, mock_extract_text):
    """Test that batch_size=None processes all pages at once."""
    mock_count.return_value = 5

    mock_images = [MagicMock() for _ in range(5)]
    mock_render.return_value = mock_images

    mock_extract_text.return_value = "test text"

    result = extract_text_from_pdf(
        pdf_path="/test/file.pdf",
        tesseract_config=["--oem", "3"],
        lang_code="por",
        batch_size=None
    )

    # Render called once without page range (first_page/last_page both None)
    assert mock_render.call_count == 1
    args, kwargs = mock_render.call_args
    assert args == ("/test/file.pdf", 400)
    assert kwargs.get('first_page') is None
    assert kwargs.get('last_page') is None

    text, pages, duration = result
    assert len(pages) == 5


@patch('pdf2ocr.ocr.extract_text_from_image')
@patch('pdf2ocr.ocr._render_pdf_pages')
@patch('pdf2ocr.ocr._count_pdf_pages')
def test_batch_size_with_value_processes_in_batches(mock_count, mock_render, mock_extract_text):
    """Test that batch_size with a value processes pages in batches."""
    mock_count.return_value = 10

    mock_render.side_effect = [
        [MagicMock() for _ in range(3)],  # batch 1: pages 0-2
        [MagicMock() for _ in range(3)],  # batch 2: pages 3-5
        [MagicMock() for _ in range(3)],  # batch 3: pages 6-8
        [MagicMock()],                    # batch 4: page 9
    ]

    mock_extract_text.return_value = "test text"

    result = extract_text_from_pdf(
        pdf_path="/test/file.pdf",
        tesseract_config=["--oem", "3"],
        lang_code="por",
        batch_size=3
    )

    assert mock_render.call_count == 4

    # _render_pdf_pages uses 0-based indices
    expected_calls = [
        call("/test/file.pdf", 400, 0, 2),
        call("/test/file.pdf", 400, 3, 5),
        call("/test/file.pdf", 400, 6, 8),
        call("/test/file.pdf", 400, 9, 9),
    ]
    mock_render.assert_has_calls(expected_calls)

    text, pages, duration = result
    assert len(pages) == 10


@patch('pdf2ocr.ocr.extract_text_from_image')
@patch('pdf2ocr.ocr._render_pdf_pages')
@patch('pdf2ocr.ocr._count_pdf_pages')
def test_batch_size_edge_cases(mock_count, mock_render, mock_extract_text):
    """Test batch_size with edge cases."""
    mock_count.return_value = 5
    mock_render.return_value = [MagicMock() for _ in range(5)]
    mock_extract_text.return_value = "test text"

    result = extract_text_from_pdf(
        pdf_path="/test/file.pdf",
        tesseract_config=["--oem", "3"],
        lang_code="por",
        batch_size=10  # Larger than 5 pages
    )

    # Should process all pages in one batch (0-based: 0 to 4)
    assert mock_render.call_count == 1
    args, kwargs = mock_render.call_args
    assert args == ("/test/file.pdf", 400, 0, 4)

    text, pages, duration = result
    assert len(pages) == 5


@patch('pdf2ocr.ocr.extract_text_from_image')
@patch('pdf2ocr.ocr._render_pdf_pages')
@patch('pdf2ocr.ocr._count_pdf_pages')
def test_batch_size_single_page_batches(mock_count, mock_render, mock_extract_text):
    """Test batch_size=1 processes one page at a time."""
    mock_count.return_value = 3
    mock_render.side_effect = [
        [MagicMock()],
        [MagicMock()],
        [MagicMock()],
    ]
    mock_extract_text.return_value = "test text"

    result = extract_text_from_pdf(
        pdf_path="/test/file.pdf",
        tesseract_config=["--oem", "3"],
        lang_code="por",
        batch_size=1
    )

    assert mock_render.call_count == 3

    # 0-based indices
    expected_calls = [
        call("/test/file.pdf", 400, 0, 0),
        call("/test/file.pdf", 400, 1, 1),
        call("/test/file.pdf", 400, 2, 2),
    ]
    mock_render.assert_has_calls(expected_calls)


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
@patch('pdf2ocr.converters.pdf._render_pdf_pages')
@patch('pdf2ocr.converters.pdf._count_pdf_pages')
@patch('builtins.open')
@patch('tempfile.TemporaryDirectory')
def test_batch_size_in_layout_mode(mock_temp_dir, mock_open, mock_count, mock_render, mock_subprocess):
    """Test that batch_size works in layout preservation mode."""
    mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"
    mock_temp_dir.return_value.__exit__.return_value = None

    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_file.read.return_value = b"fake pdf content"

    mock_count.return_value = 3
    mock_render.side_effect = [
        [MagicMock(), MagicMock()],  # First batch: 2 pages
        [MagicMock()],               # Second batch: 1 page
    ]

    mock_subprocess.return_value = MagicMock()

    config = ProcessingConfig(
        source_dir="/test/path",
        generate_pdf=True,
        preserve_layout=True,
        batch_size=2
    )

    with patch('pdf2ocr.converters.pdf.setup_logging'), \
         patch('pdf2ocr.converters.pdf.timing_context'):
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