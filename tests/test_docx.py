import subprocess

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