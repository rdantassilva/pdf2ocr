"""Tests for tesseract_config parameter usage."""

import os
from unittest.mock import patch, MagicMock, mock_open
from PIL import Image
import pytest

from pdf2ocr.ocr import extract_text_from_image, extract_text_from_pdf
from pdf2ocr.config import ProcessingConfig


def test_extract_text_from_image_uses_config():
    """Test that extract_text_from_image correctly passes config to pytesseract."""
    # Create a test image
    test_image = Image.new('RGB', (100, 100), color='white')
    
    # Mock pytesseract.image_to_string
    with patch('pdf2ocr.ocr.image_to_string') as mock_image_to_string:
        mock_image_to_string.return_value = "test text"
        
        # Test with custom config
        result = extract_text_from_image(test_image, "por", "--psm 6 --oem 3")
        
        # Verify that image_to_string was called with the correct config
        mock_image_to_string.assert_called_once()
        args, kwargs = mock_image_to_string.call_args
        
        assert kwargs['lang'] == "por"
        assert kwargs['config'] == "--psm 6 --oem 3"
        assert result == "test text"


def test_extract_text_from_image_with_empty_config():
    """Test that extract_text_from_image works with empty config."""
    # Create a test image
    test_image = Image.new('RGB', (100, 100), color='white')
    
    # Mock pytesseract.image_to_string
    with patch('pdf2ocr.ocr.image_to_string') as mock_image_to_string:
        mock_image_to_string.return_value = "test text"
        
        # Test with empty config
        result = extract_text_from_image(test_image, "por", "")
        
        # Verify that image_to_string was called with empty config
        mock_image_to_string.assert_called_once()
        args, kwargs = mock_image_to_string.call_args
        
        assert kwargs['lang'] == "por"
        assert kwargs['config'] == ""
        assert result == "test text"


def test_extract_text_from_image_default_config():
    """Test that extract_text_from_image uses default empty config when not specified."""
    # Create a test image
    test_image = Image.new('RGB', (100, 100), color='white')
    
    # Mock pytesseract.image_to_string
    with patch('pdf2ocr.ocr.image_to_string') as mock_image_to_string:
        mock_image_to_string.return_value = "test text"
        
        # Test without specifying config (should use default empty string)
        result = extract_text_from_image(test_image, "por")
        
        # Verify that image_to_string was called with default empty config
        mock_image_to_string.assert_called_once()
        args, kwargs = mock_image_to_string.call_args
        
        assert kwargs['lang'] == "por"
        assert kwargs['config'] == ""
        assert result == "test text"


def test_extract_text_from_pdf_passes_config_to_image_function():
    """Test that extract_text_from_pdf correctly converts list config to string and passes it."""
    test_pdf_path = "test.pdf"
    tesseract_config = ["--psm", "6", "--oem", "3"]

    mock_image1 = MagicMock()
    mock_image2 = MagicMock()

    with patch('pdf2ocr.ocr._count_pdf_pages', return_value=2), \
         patch('pdf2ocr.ocr._render_pdf_pages', return_value=[mock_image1, mock_image2]), \
         patch('pdf2ocr.ocr.extract_text_from_image') as mock_extract_text:

        mock_extract_text.side_effect = ["text from page 1", "text from page 2"]

        result_text, result_pages, duration = extract_text_from_pdf(
            test_pdf_path, tesseract_config, "por"
        )

        assert mock_extract_text.call_count == 2

        args1, _ = mock_extract_text.call_args_list[0]
        assert args1[0] == mock_image1
        assert args1[1] == "por"
        assert args1[2] == "--psm 6 --oem 3"

        args2, _ = mock_extract_text.call_args_list[1]
        assert args2[0] == mock_image2
        assert args2[1] == "por"
        assert args2[2] == "--psm 6 --oem 3"

        assert result_text == "text from page 1\n\ntext from page 2"
        assert result_pages == ["text from page 1", "text from page 2"]
        assert duration > 0


def test_extract_text_from_pdf_with_empty_config():
    """Test that extract_text_from_pdf works with empty tesseract_config."""
    test_pdf_path = "test.pdf"
    tesseract_config = []

    mock_image = MagicMock()

    with patch('pdf2ocr.ocr._count_pdf_pages', return_value=1), \
         patch('pdf2ocr.ocr._render_pdf_pages', return_value=[mock_image]), \
         patch('pdf2ocr.ocr.extract_text_from_image') as mock_extract_text:

        mock_extract_text.return_value = "test text"

        result_text, result_pages, duration = extract_text_from_pdf(
            test_pdf_path, tesseract_config, "por"
        )

        mock_extract_text.assert_called_once()
        args, _ = mock_extract_text.call_args

        assert args[0] == mock_image
        assert args[1] == "por"
        assert args[2] == ""


def test_extract_text_from_pdf_with_none_config():
    """Test that extract_text_from_pdf works with None tesseract_config."""
    test_pdf_path = "test.pdf"
    tesseract_config = None

    mock_image = MagicMock()

    with patch('pdf2ocr.ocr._count_pdf_pages', return_value=1), \
         patch('pdf2ocr.ocr._render_pdf_pages', return_value=[mock_image]), \
         patch('pdf2ocr.ocr.extract_text_from_image') as mock_extract_text:

        mock_extract_text.return_value = "test text"

        result_text, result_pages, duration = extract_text_from_pdf(
            test_pdf_path, tesseract_config, "por"
        )

        mock_extract_text.assert_called_once()
        args, _ = mock_extract_text.call_args

        assert args[0] == mock_image
        assert args[1] == "por"
        assert args[2] == ""


def test_config_get_tesseract_config_default():
    """Test that ProcessingConfig.get_tesseract_config returns correct default config."""
    config = ProcessingConfig(
        source_dir="test",
        generate_pdf=True,
        preserve_layout=False
    )
    
    result = config.get_tesseract_config()
    expected = ["--oem", "3", "--psm", "1"]  # TESSERACT_DEFAULT_CONFIG split
    
    assert result == expected


def test_config_get_tesseract_config_layout():
    """Test that ProcessingConfig.get_tesseract_config returns correct layout config."""
    config = ProcessingConfig(
        source_dir="test",
        generate_pdf=True,
        preserve_layout=True
    )
    
    result = config.get_tesseract_config()
    expected = ["--oem", "1", "--psm", "11"]  # TESSERACT_LAYOUT_CONFIG split
    
    assert result == expected


def test_integration_config_to_image_function():
    """Integration test: config from ProcessingConfig flows to extract_text_from_image."""
    config = ProcessingConfig(
        source_dir="test",
        generate_pdf=True,
        preserve_layout=True
    )

    test_pdf_path = "test.pdf"
    mock_image = MagicMock()

    with patch('pdf2ocr.ocr._count_pdf_pages', return_value=1), \
         patch('pdf2ocr.ocr._render_pdf_pages', return_value=[mock_image]), \
         patch('pdf2ocr.ocr.extract_text_from_image') as mock_extract_text:

        mock_extract_text.return_value = "test text"

        result_text, result_pages, duration = extract_text_from_pdf(
            test_pdf_path,
            config.get_tesseract_config(),  # ["--oem", "1", "--psm", "11"]
            "por"
        )

        mock_extract_text.assert_called_once()
        args, _ = mock_extract_text.call_args

        assert args[0] == mock_image
        assert args[1] == "por"
        assert args[2] == "--oem 1 --psm 11" 