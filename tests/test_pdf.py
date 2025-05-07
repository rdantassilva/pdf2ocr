import subprocess

def test_pdf_generated(tmp_path):
    input_pdf = "tests/data/"
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = subprocess.run([
        "python3", "-m", "pdf2ocr", input_pdf,
        "--pdf", "--dest-dir", str(output_dir)
    ], capture_output=True, text=True)


    pdf_output = output_dir / "pdf_ocr"
    assert pdf_output.exists(), "PDF output folder not created"
    assert any(f.name.endswith("_ocr.pdf") for f in pdf_output.iterdir()), "Layout PDF not generated"