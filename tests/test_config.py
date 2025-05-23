import pytest
from pdf2ocr.config import ProcessingConfig, TESSERACT_DEFAULT_CONFIG, TESSERACT_LAYOUT_CONFIG

def test_config_defaults():
    """Test default configuration values"""
    config = ProcessingConfig(source_dir="/test/path")
    
    assert config.source_dir == "/test/path"
    assert config.dest_dir is None
    assert config.lang == "por"
    assert not config.generate_docx
    assert not config.generate_pdf
    assert not config.generate_epub
    assert not config.generate_html
    assert not config.preserve_layout
    assert not config.quiet
    assert not config.summary
    assert config.log_path is None

def test_config_validation_no_output():
    """Test validation when no output format is selected"""
    config = ProcessingConfig(source_dir="/test/path")
    
    with pytest.raises(ValueError) as exc_info:
        config.validate()
    assert "must select at least one output format" in str(exc_info.value)

def test_config_validation_layout_formats():
    """Test validation when preserve_layout is used with other formats"""
    config = ProcessingConfig(
        source_dir="/test/path",
        preserve_layout=True,
        generate_docx=True
    )
    
    # Should disable other formats and enable PDF
    config.validate()
    assert config.preserve_layout
    assert config.generate_pdf  # PDF should be enabled
    assert not config.generate_docx  # Other formats should be disabled
    assert not config.generate_epub
    assert not config.generate_html

def test_config_epub_enables_docx():
    """Test that enabling EPUB automatically enables DOCX"""
    config = ProcessingConfig(
        source_dir="/test/path",
        generate_epub=True
    )
    
    config.validate()
    assert config.generate_docx
    assert config.generate_epub

def test_tesseract_config_default():
    """Test Tesseract configuration string generation without layout preservation"""
    config = ProcessingConfig(
        source_dir="/test/path",
        generate_pdf=True,
        lang="eng"
    )
    
    expected = f"{TESSERACT_DEFAULT_CONFIG} -l eng"
    assert config.get_tesseract_config() == expected

def test_tesseract_config_layout():
    """Test Tesseract configuration string generation with layout preservation"""
    config = ProcessingConfig(
        source_dir="/test/path",
        generate_pdf=True,
        preserve_layout=True,
        lang="eng"
    )
    
    expected = f"{TESSERACT_LAYOUT_CONFIG} -l eng"
    assert config.get_tesseract_config() == expected 