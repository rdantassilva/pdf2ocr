import subprocess

def test_lang_argument(tmp_path):
    input_folder = "tests/data/"
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = subprocess.run([
        "python3", "-m", "pdf2ocr", input_folder,
        "--pdf", "--lang", "por", "--dest-dir", str(output_dir)
    ], capture_output=True, text=True)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    assert result.returncode == 0
    assert "OCR PDF created" in result.stdout
