import os
import pytest
from pdf2ocr.converters import remove_accents, save_as_docx, save_as_html
from docx import Document

def test_remove_accents():
    """Test accent removal from text"""
    test_cases = [
        ("áéíóú", "aeiou"),
        ("àãõâêô", "aaoaeo"),
        ("ÁÉÍÓÚ", "AEIOU"),
        ("çÇ", "cC"),
        ("texto sem acento", "texto sem acento"),
        ("múltiplas    palavras", "multiplas    palavras"),
        ("símbolos!@#$%", "simbolos!@#$%"),
    ]
    
    for input_text, expected in test_cases:
        assert remove_accents(input_text) == expected

def test_save_as_docx(tmp_path):
    """Test DOCX file generation and content"""
    output_file = tmp_path / "test.docx"
    test_text = """First paragraph
    with multiple lines.

    Second paragraph
    also with multiple lines.
    """
    
    # Save the document
    save_as_docx(test_text, str(output_file))
    
    # Verify file was created
    assert output_file.exists()
    
    # Read back and verify content
    doc = Document(output_file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    assert len(paragraphs) == 2
    assert "First paragraph with multiple lines" in paragraphs[0]
    assert "Second paragraph also with multiple lines" in paragraphs[1]
    
    # Verify document properties
    core_props = doc.core_properties
    assert core_props.author == "pdf2ocr"
    assert core_props.title == "test"

def test_save_as_html(tmp_path):
    """Test HTML file generation and content"""
    output_file = tmp_path / "test.html"
    test_text = "Line 1\nLine 2\n\nParagraph 2"
    
    # Save the HTML
    save_as_html(test_text, str(output_file))
    
    # Verify file was created
    assert output_file.exists()
    
    # Read back and verify content
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check HTML structure
    assert "<!DOCTYPE html>" in content
    assert "<html lang=\"en\">" in content
    assert "<meta charset=\"UTF-8\">" in content
    assert "<p>" in content  # Check for paragraph tags
    assert "Line 1" in content
    assert "Line 2" in content
    assert "Paragraph 2" in content 