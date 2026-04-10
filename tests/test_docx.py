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

    test_text = (
        "First line of the first paragraph that continues across\n"
        "multiple visual lines in the original document.\n"
        "\n"
        "Second paragraph starts here after the blank line and also\n"
        "spans two visual lines in the source.\n"
        "\n"
        "Third paragraph is a single line."
    )

    save_as_docx(test_text, str(output_file))

    doc = Document(output_file)
    paragraphs = [p for p in doc.paragraphs if p.text.strip()]

    assert len(paragraphs) == 3, f"Expected 3 paragraphs, got {len(paragraphs)}"

    assert "first paragraph" in paragraphs[0].text
    assert "Second paragraph" in paragraphs[1].text
    assert "Third paragraph" in paragraphs[2].text

    for i, p in enumerate(paragraphs):
        assert len(p.runs) == 1, f"Paragraph {i} should have one run"