"""Tests for DOCX generation."""

import subprocess
from pathlib import Path
from docx import Document
from pdf2ocr.converters import save_as_docx


def test_docx_generated(tmp_path):
    input_folder = "tests/data/"
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = subprocess.run([
        "python3", "-m", "pdf2ocr", input_folder,
        "--docx", "--dest-dir", str(output_dir)
    ], capture_output=True, text=True)

    docx_output = output_dir / "docx"
    assert docx_output.exists(), "DOCX output folder not created"
    assert any(f.suffix == ".docx" for f in docx_output.iterdir()), "DOCX not generated"


def test_docx_paragraph_formatting(tmp_path):
    """Test that paragraphs are preserved correctly in DOCX output."""
    output_file = tmp_path / "test.docx"
    
    # Test text with multiple paragraphs and line breaks
    test_text = (
        "First line of first paragraph\n"
        "Second line of first paragraph\n"
        "Third line of first paragraph\n"
        "\n"
        "First line of second paragraph\n"
        "Second line of second paragraph\n"
        "\n"
        "Single line paragraph"
    )
    
    # Save the document
    save_as_docx(test_text, str(output_file))
    
    # Read back and verify content
    doc = Document(output_file)
    paragraphs = [p for p in doc.paragraphs if p.text.strip()]  # Skip empty paragraphs
    
    # Should have 3 paragraphs
    assert len(paragraphs) == 3, "Wrong number of paragraphs"
    
    # First paragraph should have all lines joined with spaces
    expected_first_para = "First line of first paragraph Second line of first paragraph Third line of first paragraph"
    assert paragraphs[0].text.strip() == expected_first_para
    
    # Second paragraph should have lines joined with spaces
    expected_second_para = "First line of second paragraph Second line of second paragraph"
    assert paragraphs[1].text.strip() == expected_second_para
    
    # Third paragraph should be a single line
    assert paragraphs[2].text.strip() == "Single line paragraph"
    
    # Each paragraph should have a single run since we're joining lines with spaces
    assert len(paragraphs[0].runs) == 1, "First paragraph should have one run"
    assert len(paragraphs[1].runs) == 1, "Second paragraph should have one run"
    assert len(paragraphs[2].runs) == 1, "Third paragraph should have one run"