import subprocess

def test_preserve_layout_pdf(tmp_path):
    input_folder = "tests/data/"
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = subprocess.run([
        "python3", "-m", "pdf2ocr", input_folder,
        "--pdf", "--preserve-layout", "--dest-dir", str(output_dir)
    ], capture_output=True, text=True)

    print("STDOUT:\n", result.stdout)
    print("STDERR:\n", result.stderr)
    print("Arquivos gerados:", list(output_dir.rglob("*")))

    pdf_output = output_dir / "pdf_ocr_layout"
    print("Subpastas em output_dir:", [p.name for p in output_dir.iterdir()])
    assert pdf_output.exists(), "Preserve-layout PDF folder not created"
    assert any(f.name.endswith("_ocr.pdf") for f in pdf_output.iterdir()), "Layout PDF not generated"
