import subprocess

def test_epub_generated(tmp_path):
    input_folder = "tests/data/"
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = subprocess.run([
        "python3", "-m", "pdf2ocr", input_folder,
        "--docx", "--epub", "--dest-dir", str(output_dir)
    ], capture_output=True, text=True)

    epub_output = output_dir / "epub"
    assert epub_output.exists(), "EPUB output folder not created"
    assert any(f.suffix == ".epub" for f in epub_output.iterdir()), "EPUB not generated"