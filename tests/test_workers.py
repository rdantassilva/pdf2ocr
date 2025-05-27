"""Tests for workers parameter functionality."""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from pdf2ocr.config import ProcessingConfig
from pdf2ocr.converters.pdf import process_pdfs_with_ocr, process_layout_pdf_only
from pdf2ocr.logging_config import setup_logging


def test_workers_parameter_default():
    """Test that default workers parameter is set correctly."""
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True)
    assert config.workers == 2


def test_workers_parameter_custom():
    """Test that custom workers parameter is set correctly."""
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=8)
    assert config.workers == 8


def test_workers_parameter_validation():
    """Test workers parameter validation."""
    # Test valid values
    for workers in [1, 2, 4, 8, 16]:
        config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=workers)
        assert config.workers == workers

    # Test that negative values are still accepted (config doesn't validate this)
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=-1)
    assert config.workers == -1


@patch('pdf2ocr.converters.pdf.os.makedirs')
@patch('pdf2ocr.converters.pdf.futures.ProcessPoolExecutor')
@patch('pdf2ocr.converters.pdf.os.listdir')
@patch('pdf2ocr.converters.pdf.timing_context')
def test_workers_used_in_process_pool(mock_timing, mock_listdir, mock_executor, mock_makedirs):
    """Test that the workers parameter is passed to ProcessPoolExecutor."""
    # Mock setup - include PDF files so ProcessPoolExecutor gets used
    mock_listdir.return_value = ['test1.pdf', 'test2.pdf']  # PDF files present
    mock_makedirs.return_value = None
    mock_timing.return_value.__enter__ = MagicMock()
    mock_timing.return_value.__exit__ = MagicMock()
    mock_timing.return_value.__call__ = MagicMock(return_value=10.0)
    
    # Mock the executor context manager and its behavior
    mock_executor_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_executor_instance
    mock_executor.return_value.__exit__.return_value = None
    
    # Mock futures for the submit calls
    mock_future1, mock_future2 = MagicMock(), MagicMock()
    mock_executor_instance.submit.side_effect = [mock_future1, mock_future2]
    
    # Mock as_completed and future results
    with patch('pdf2ocr.converters.pdf.futures.as_completed') as mock_as_completed:
        mock_as_completed.return_value = [mock_future1, mock_future2]
        mock_future1.result.return_value = (True, 10.0, None, [])
        mock_future2.result.return_value = (True, 10.0, None, [])
        
        # Create config with custom workers
        config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=6)
        logger = setup_logging()
        
        # Run the function
        process_pdfs_with_ocr(config, logger)
        
        # Verify ProcessPoolExecutor was called with correct max_workers
        mock_executor.assert_called_once_with(max_workers=6)


@patch('pdf2ocr.converters.pdf.os.makedirs')
@patch('pdf2ocr.converters.pdf.futures.ProcessPoolExecutor')
@patch('pdf2ocr.converters.pdf.os.listdir')
@patch('pdf2ocr.converters.pdf.timing_context')
def test_workers_used_in_layout_mode(mock_timing, mock_listdir, mock_executor, mock_makedirs):
    """Test that the workers parameter is used in layout preservation mode."""
    # Mock setup - include PDF files so ProcessPoolExecutor gets used
    mock_listdir.return_value = ['test1.pdf', 'test2.pdf']  # PDF files present
    mock_makedirs.return_value = None
    mock_timing.return_value.__enter__ = MagicMock()
    mock_timing.return_value.__exit__ = MagicMock()
    mock_timing.return_value.__call__ = MagicMock(return_value=10.0)
    
    # Mock the executor context manager and its behavior
    mock_executor_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_executor_instance
    mock_executor.return_value.__exit__.return_value = None
    
    # Mock futures for the submit calls
    mock_future1, mock_future2 = MagicMock(), MagicMock()
    mock_executor_instance.submit.side_effect = [mock_future1, mock_future2]
    
    # Mock as_completed and future results
    with patch('pdf2ocr.converters.pdf.futures.as_completed') as mock_as_completed:
        mock_as_completed.return_value = [mock_future1, mock_future2]
        mock_future1.result.return_value = (True, 10.0, None, [])
        mock_future2.result.return_value = (True, 10.0, None, [])
        
        # Create config with custom workers and layout preservation
        config = ProcessingConfig(
            source_dir="/test/path", 
            generate_pdf=True, 
            preserve_layout=True, 
            workers=4
        )
        logger = setup_logging()
        
        # Run the function
        process_layout_pdf_only(config, logger)
        
        # Verify ProcessPoolExecutor was called with correct max_workers
        mock_executor.assert_called_once_with(max_workers=4)


@patch('pdf2ocr.converters.pdf.os.makedirs')
@patch('pdf2ocr.converters.pdf.process_single_pdf')
@patch('pdf2ocr.converters.pdf.futures.ProcessPoolExecutor')
@patch('pdf2ocr.converters.pdf.os.listdir')
@patch('pdf2ocr.converters.pdf.timing_context')
def test_workers_parallel_execution(mock_timing, mock_listdir, mock_executor, mock_process_single, mock_makedirs):
    """Test that multiple workers are used for parallel processing."""
    # Mock setup
    mock_listdir.return_value = ['file1.pdf', 'file2.pdf', 'file3.pdf']
    mock_makedirs.return_value = None
    mock_timing.return_value.__enter__ = MagicMock()
    mock_timing.return_value.__exit__ = MagicMock()
    mock_timing.return_value.__call__ = MagicMock(return_value=10.0)
    
    # Mock executor and futures
    mock_executor_instance = MagicMock()
    mock_executor.return_value.__enter__.return_value = mock_executor_instance
    mock_executor.return_value.__exit__.return_value = None
    
    # Mock futures
    mock_future1, mock_future2, mock_future3 = MagicMock(), MagicMock(), MagicMock()
    mock_executor_instance.submit.side_effect = [mock_future1, mock_future2, mock_future3]
    
    # Mock as_completed to return futures in order
    with patch('pdf2ocr.converters.pdf.futures.as_completed') as mock_as_completed:
        mock_as_completed.return_value = [mock_future1, mock_future2, mock_future3]
        
        # Mock future results
        for future in [mock_future1, mock_future2, mock_future3]:
            future.result.return_value = (True, 10.0, None, [])
    
        # Create config with multiple workers
        config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=3)
        logger = setup_logging()
        
        # Run the function
        process_pdfs_with_ocr(config, logger)
        
        # Verify that submit was called for each PDF file
        assert mock_executor_instance.submit.call_count == 3
        
        # Verify that the correct function was submitted
        for call in mock_executor_instance.submit.call_args_list:
            assert call[0][0] == mock_process_single


def test_workers_parameter_bounds():
    """Test workers parameter with boundary values."""
    # Test minimum reasonable value
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=1)
    assert config.workers == 1
    
    # Test large value
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=100)
    assert config.workers == 100
    
    # Test zero (edge case - may not be practical but should be handled)
    config = ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=0)
    assert config.workers == 0


@patch('pdf2ocr.converters.pdf.os.makedirs')
@patch('pdf2ocr.converters.pdf.os.listdir')
def test_workers_parameter_with_different_formats(mock_listdir, mock_makedirs):
    """Test workers parameter works with different output formats."""
    mock_listdir.return_value = []
    mock_makedirs.return_value = None
    
    configs = [
        ProcessingConfig(source_dir="/test/path", generate_pdf=True, workers=4),
        ProcessingConfig(source_dir="/test/path", generate_docx=True, workers=6),
        ProcessingConfig(source_dir="/test/path", generate_html=True, workers=2),
        ProcessingConfig(source_dir="/test/path", generate_epub=True, workers=8),
    ]
    
    for config in configs:
        # Just verify the configuration is valid and workers parameter is preserved
        assert hasattr(config, 'workers')
        assert config.workers in [2, 4, 6, 8]


if __name__ == "__main__":
    pytest.main([__file__]) 