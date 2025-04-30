# pdf2ocr

Python script to apply OCR to PDF files and generate output in DOCX, searchable PDF, and EPUB formats.

## System Requirements

### Ubuntu/Debian (APT)

```bash
sudo apt update && sudo apt install tesseract-ocr poppler-utils calibre
```

### Fedora / Red Hat / CentOS / AlmaLinux / Rocky Linux (DNF or YUM)

```bash
# For modern systems (DNF)
sudo dnf install tesseract poppler-utils calibre

# For older systems (YUM)
sudo yum install tesseract poppler-utils calibre
```

### macOS (Homebrew)

> 💡 **Tip for macOS/Homebrew users:**  
> It's strongly recommended to use a virtual environment to avoid system restrictions:
>
> ```bash
> python3 -m venv venv
> source venv/bin/activate
> pip3 install --upgrade pip
> pip3 install -r requirements.txt
> ```
>
> This avoids issues with Homebrew-protected Python environments (PEP 668).

```bash
brew install tesseract poppler
brew install --cask calibre
```

> 📌 **Important (macOS only):**  
> If `ebook-convert` is not available after installing Calibre, you need to manually add it to your PATH:
>
> ```bash
> export PATH="/Applications/calibre.app/Contents/MacOS:$PATH"
> ```
>
> To make it permanent, add it to your shell config file (`~/.zshrc` or `~/.bash_profile`):
>
> ```bash
> echo 'export PATH="/Applications/calibre.app/Contents/MacOS:$PATH"' >> ~/.zshrc
> source ~/.zshrc
> ```

Then check it:

```bash
ebook-convert --version
```

## Python

It's recommended to use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Installing dependencies

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 pdf2ocr.py source_folder --docx --pdf --epub --dest-dir output_folder --short-output
```

### Options

- `source_folder`: Folder with input PDF files
- `--dest-dir`: Output folder (default is the input folder)
- `--docx`: Generate DOCX files
- `--pdf`: Generate OCR-processed PDF files
- `--epub`: Generate EPUB files (requires `--docx`)
- `--short-output`: Show only final summary output
- `--logfile`: Path to save detailed log output (UTF-8)

## Example

```bash
python3 pdf2ocr.py ./pdfs --docx --pdf --epub --dest-dir ./output --logfile log.txt
```

## License

MIT License - see the LICENSE file for details.
