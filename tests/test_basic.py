import subprocess

def test_help_command_runs():
    result = subprocess.run(["python3", "-m", "pdf2ocr", "-h"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()