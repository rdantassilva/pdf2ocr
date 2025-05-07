# pdf2ocr

Python script to apply OCR on PDF files and generate output in DOCX, searchable PDF, HTML and EPUB formats.

---

## 📄 Features

- 📄 Extracts text from scanned PDFs using Tesseract OCR
- 📘 Outputs DOCX, HTML and searchable PDFs
- 📚 Converts to EPUB (via Calibre)
- 🧼 Cleans unwanted characters while preserving Portuguese accents
- 📈 Shows progress bars and summary logs

---

## 🚀 Quick Install & Usage

### Install globally

You can install pdf2ocr and use it as a command-line tool by simply:

```bash
pip install pdf2ocr 
```

### Run

Use the command:

```bash
pdf2ocr ./pdfs --docx --pdf --epub --dest-dir ./output --logfile log.txt
```

---


## 🧱 System Requirements

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

> 📌 **Important (macOS only):**  
> If `ebook-convert` is not available after installing Calibre, you need to manually add it to your PATH:
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

Check Calibre installation:

```bash
ebook-convert --version
```

---

## 🐍 Python Setup (for development)

To use in a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ Command Line Options

```bash
pdf2ocr source_folder --docx --pdf --epub --dest-dir output_folder --logfile log.txt
```

- `source_folder`: Folder containing the input PDF files.
- `--dest-dir`: Destination folder for output files (default: same as input).
- `--docx`: Generate DOCX files with preserved paragraph structure.
- `--pdf`: Generate OCR-processed PDF files (now with improved paragraph handling).
- `--epub`: Generate EPUB files (requires `--docx`; uses Calibre's `ebook-convert`).
- `--html`: Generate html files
- `--preserve-layout`: Preserve original document layout (PDF only)
- `--short-output`: Show only the final summary (quiet mode).
- `--logfile`: Path to write detailed log output (UTF-8 encoded).

---

## 📌 Example

```bash
pdf2ocr ./pdfs --docx --pdf --epub --dest-dir ./output --logfile log.txt
```

---

## 🛠️ Makefile Commands

| Command         | Description                                                        |
|-----------------|--------------------------------------------------------------------|
| `make venv`     | Create and activate a Python virtual environment                   |
| `make install`  | Install pdf2ocr globally                                           |
| `make run`      | Run the script with example parameters                             |
| `make clean`    | Remove cache, logs, and generated output                           |

---

## 📄 License

MIT
