[![PyPI](https://img.shields.io/pypi/v/pdf2ocr)](https://pypi.org/project/pdf2ocr/)
[![Coverage Status](https://img.shields.io/badge/coverage-90%25-brightgreen)](https://github.com/rdantassilva/pdf2ocr)

# pdf2ocr

A CLI tool to apply OCR on PDF files and export to multiple formats.

---

## 📄 Features

- 🔍 Extracts text from scanned PDFs using Tesseract OCR
- 📘 Outputs DOCX, HTML, EPUB and searchable PDF files with preserved paragraph structure
- 📚 Converts DOCX to EPUB via Calibre, including metadata
- 📈 Displays progress bars and detailed summary logs
- 📂 Supports layout-preserving mode for high-fidelity PDF OCR

---

## 🚀 Quick Install & Usage

### Install globally

Install `pdf2ocr` and use it as a command-line tool:

```bash
pip install pdf2ocr 
```
---
### 📌 Usage Examples

Generate multiple output formats with logging:

```bash
pdf2ocr ./pdfs --docx --pdf --epub --html --dest-dir ./output --logfile pdf2ocr.log
```

Generate layout-preserving OCR PDFs only:

```bash
pdf2ocr ./pdfs --pdf --preserve-layout --dest-dir ./output --logfile pdf2ocr.log
```

Process multiple files in parallel with 8 workers:

```bash
pdf2ocr ./pdfs --pdf --html --epub --workers 8 --logfile pdf2ocr.log
```

Enable batch processing for large PDFs to reduce memory usage:

```bash
pdf2ocr ./pdfs --pdf --batch-size 5 --logfile pdf2ocr.log  # Process 5 pages at a time
```

> ⚠️ When using `--preserve-layout`, only PDF output is supported. Other formats will be automatically disabled.

---


## 🌍 Language Support

`pdf2ocr` is currently optimized for **Portuguese** 🇧🇷🇵🇹 and uses it as the default OCR language.

You can override the language using the `--lang` option. Examples:

```bash
pdf2ocr ./pdfs --pdf --lang eng  # For English 🇬🇧🇺🇲
```

```bash
pdf2ocr ./pdfs --pdf --lang spa  # For Spanish (Español) 🇪🇸🇲🇽🇦🇷🇨🇱🇨🇴
```

```bash
pdf2ocr ./pdfs --pdf --lang fra  # For French (Français) 🇫🇷
```

**To check the code for all languages supported by Tesseract, run the command below:**
```bash
tesseract --list-langs
```

---

## 🧱 System Requirements and Tesseract language models

### Ubuntu / Debian (APT)

Install Tesseract OCR and the most common language models:

```bash
sudo apt update && sudo apt install tesseract-ocr \
    tesseract-ocr-por tesseract-ocr-eng tesseract-ocr-spa \
    tesseract-ocr-fra tesseract-ocr-ita
```

> Or, to install **all available language models**:

```bash
sudo apt install tesseract-ocr-all
```

---

### Fedora / Red Hat / CentOS / AlmaLinux / Rocky Linux (DNF or YUM)

#### OCR requirements:

```bash
# For modern systems (DNF)
sudo dnf install tesseract poppler-utils calibre

# For older systems (YUM)
sudo yum install tesseract poppler-utils calibre
```

#### To install additional OCR language models:

```bash
sudo dnf install tesseract-langpack-por tesseract-langpack-eng \
    tesseract-langpack-spa tesseract-langpack-fra tesseract-langpack-ita
```

> There is no equivalent to `tesseract-ocr-all` on Red Hat-based systems — install only the languages you need.

### macOS (Homebrew)

```bash
brew install tesseract poppler
brew install --cask calibre
```

#### 💡 Tip for macOS/Homebrew users:

> 📌 **Important:** If `ebook-convert` is not available after installing Calibre, add it to your PATH:
>
> ```bash
> export PATH="$PATH:/Applications/calibre.app/Contents/MacOS"
> ```
>
> To make it permanent:
>
> ```bash
> echo 'export PATH="$PATH:/Applications/calibre.app/Contents/MacOS"' >> ~/.zshrc
> source ~/.zshrc
> ```

> Check Calibre installation:
> 
> ```bash
> ebook-convert --version
> ```

---

## 🐍 Python Setup (for development)

To use in a virtual environment:

```bash
python3 -m venv venv_pdf2ocr
source venv_pdf2ocr/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Command Line Options

```bash
pdf2ocr -h
```

- `source_folder`: Folder containing the input PDF files.
- `--dest-dir`: Destination folder for output files (default: same as input).
- `--docx`: Generate DOCX files with preserved paragraph structure.
- `--pdf`: Generate OCR-processed PDF files.
- `--epub`: Generate EPUB files (requires `--docx`; uses Calibre).
- `--html`: Generate HTML files.
- `--preserve-layout`: Preserve the visual layout of original documents (PDF only).
- `--lang`: Set the OCR language code (default: por). Use tesseract --list-langs to check installed options.
- `--quiet`: Run silently without progress output.
- `--summary`: Display only final conversion summary.
- `--logfile`: Path to save detailed log output (UTF-8 encoded).
- `--workers`: Number of parallel workers for processing (default: 2).
- `--batch-size`: Number of pages to process in each batch (disabled by default). Use this to optimize memory usage for large PDFs.
- `--version`: show program's version number and exit

---

## 🛠️ Makefile Commands

| Command         | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `make venv`     | Create and set up a virtual environment (`venv_pdf2ocr`)                    |
| `make install`  | Install `pdf2ocr` globally (or into active virtualenv)                      |
| `make run`      | Run `pdf2ocr` with example parameters (PDF, DOCX, EPUB, HTML)               |
| `make test`     | Run automated tests with `pytest`                                           |
| `make lint`     | Run `flake8` to check code quality                                          |
| `make format`   | Auto-format code using `black` and `isort`                                  |
| `make clean`    | Remove Python cache, logs, build files and other generated artifacts        |

---

## 📄 License

MIT
