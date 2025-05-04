# pdf2ocr

Python script to apply OCR to PDF files and generate output in DOCX, searchable PDF, and EPUB formats.

## Features

- 📄 Extracts text from scanned PDFs using Tesseract OCR
- 📘 Outputs DOCX and searchable PDFs
- 📚 Converts to EPUB (via Calibre)
- 🧼 Cleans unwanted characters while preserving Portuguese accents
- 📈 Shows progress bars and summary logs

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

```bash
brew install tesseract poppler
brew install --cask calibre
```

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

> 📌 **Important (macOS only):**  
> If `ebook-convert` is not available after installing Calibre, you need to manually add it to your PATH:
>
> ```bash
> export PATH="$PATH:/Applications/calibre.app/Contents/MacOS"
> ```
>
> To make it permanent, add it to your shell config file (`~/.zshrc` or `~/.bash_profile`):
>
> ```bash
> echo 'export PATH="$PATH:/Applications/calibre.app/Contents/MacOS"' >> ~/.zshrc
> source ~/.zshrc
> ```

Then check:

```bash
ebook-convert --version
```

## Python Setup

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 pdf2ocr.py source_folder --docx --pdf --epub --dest-dir output_folder --logfile log.txt
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

MIT


## Makefile Commands

| Command       | Description                                                        |
|---------------|--------------------------------------------------------------------|
| `make venv`   | Create and activate a Python virtual environment                   |
| `make install`| Install dependencies from `requirements.txt`                       |
| `make run`    | Run the script with example parameters                             |
| `make deb`    | Generate a .deb package using the `build_deb.sh` script            |
| `make clean`  | Remove cache, logs, and generated output                           |
