# coding:utf-8

"""
Script for OCR on PDFs generating DOCX, OCR-processed PDF and EPUB.

Description of Libraries:
- 📜 PIL/Pillow: Image processing (open, convert and enhance images for OCR)
- 🔍 pytesseract: Python interface for Tesseract OCR (text recognition in images)
- 📊 tqdm: Displays progress bars for long operations
- 📄 pdf2image: Converts PDF pages to images for processing
- 📝 python-docx: Creates and manipulates Word documents (.docx)
- 🖨️ reportlab: Programmatic PDF generation
- 🏷️ tesseract-ocr: OCR engine (optical character recognition)
- 🖼️ poppler-utils: PDF manipulation tools (includes pdftoppm)
- 📚 calibre: E-book management suite (provides ebook-convert)

Conversion Flow:
1. 📄 pdf2image uses `pdftoppm` to convert PDFs to images
2. 🖼️ pytesseract uses `tesseract-ocr` to extract text from images
3. 📝 python-docx generates Word documents with extracted text
4. 🖨️ reportlab creates PDFs with OCR-processed text
5. 📚 calibre (optional) converts DOCX to EPUB using `ebook-convert`

Important Notes:
- To generate EPUB, Calibre must be installed on the system
- The `ebook-convert` command must be available in PATH
- Very large files may require more time and memory
- OCR quality depends on the original PDF clarity
- The script creates separate folders for each output type (docx, pdf, epub)
"""

import os           # File system operations
import re           # Regular expressions for text cleaning
import time         # Performance timing
import subprocess   # Execute external commands
import shutil       # High-level file and binary operations
import argparse     # Command-line argument parsing
import platform     # Detect operating system
from PIL import Image, ImageFilter, ImageOps      # Image preprocessing
from pdf2image import convert_from_path           # PDF to image conversion
from pytesseract import image_to_string           # OCR text extraction
from tqdm import tqdm                             # Progress bars
from docx import Document                         # Word document creation
from reportlab.pdfgen import canvas               # PDF generation
from reportlab.lib.pagesizes import A4            # Standard page size
from reportlab.lib.units import cm                # Measurement units

# Two Tesseract configurations:
# - default: fast and accurate, does not preserve layout
# - layout-aware: tries to maintain original blocks and columns
tesseract_default_config = r'--oem 3 --psm 1 -l por'
tesseract_layout_config  = r'--oem 1 --psm 11 -l por'

def detect_package_manager():
    """Detect the system's package manager."""
    system = platform.system()
    if system == "Darwin":
        return "brew"
    elif system == "Linux":
        if shutil.which("apt"):
            return "apt"
        if shutil.which("dnf"):
            return "dnf"
        if shutil.which("yum"):
            return "yum"
    return None

def check_dependencies(generate_epub=False):
    """Check for required system commands and suggest install commands."""
    missing = []
    if shutil.which('tesseract') is None:
        missing.append('tesseract (OCR)')
    if shutil.which('pdftoppm') is None:
        missing.append('poppler-utils (pdftoppm for PDF to image conversion)')
    if generate_epub and shutil.which('ebook-convert') is None:
        missing.append('calibre (ebook-convert for EPUB)')

    if missing:
        print("\n❌ Missing dependencies detected:")
        for item in missing:
            print(f"   - {item}")
        pm = detect_package_manager()
        print("\nℹ️ Install required packages using:")
        if pm == "apt":
            print("   sudo apt install tesseract-ocr poppler-utils calibre")
        elif pm == "dnf":
            print("   sudo dnf install tesseract poppler-utils calibre")
        elif pm == "yum":
            print("   sudo yum install tesseract poppler-utils calibre")
        elif pm == "brew":
            print("   brew install tesseract poppler")
            print("   brew install --cask calibre")
            print("\n📌 If 'ebook-convert' is not found, add Calibre to your PATH:")
            print("   echo 'export PATH=\"$PATH:/Applications/calibre.app/Contents/MacOS\"' >> ~/.zshrc")
            print("   source ~/.zshrc")
        else:
            print("   Please install the missing dependencies manually.")
        exit(1)

def preprocess_image(img):
    """Convert image to grayscale, enhance contrast, and reduce noise."""
    img = img.convert('L')
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter())
    return img

def clean_text_portuguese(text):
    """Remove unwanted symbols while preserving Portuguese accents."""
    allowed = (
        'a-zA-Z0-9'
        'áéíóúàãõâêôç'
        'ÁÉÍÓÚÀÃÕÂÊÔÇ'
        '\\s'
        '\\.,;:?!()\\[\\]{}\\-"\''  # basic punctuation
    )
    return re.sub(f'[^{allowed}]', '', text)

def extract_text_from_pdf(pdf_path, quiet=False, tesseract_config=None):
    """Run OCR on each page image and return concatenated text and page texts."""
    pages = convert_from_path(pdf_path, dpi=400)
    full_text = ""
    page_texts = []
    start = time.perf_counter()

    for img in tqdm(pages, desc="Extracting text (OCR)...", disable=quiet, ncols=75):
        img = preprocess_image(img)
        text = image_to_string(img, config=tesseract_config)
        text = clean_text_portuguese(text)
        page_texts.append(text)
        full_text += text + "\n\n"

    return full_text, page_texts, time.perf_counter() - start

def save_as_docx(text, path):
    """Save OCR text to a DOCX file."""
    t0 = time.perf_counter()
    doc = Document()
    for line in text.split('\n'):
        if line.strip():
            doc.add_paragraph(line.strip())
    doc.save(path)
    return time.perf_counter() - t0

def save_as_pdf(page_texts, path, name):
    """Create a searchable PDF from OCR page texts."""
    t0 = time.perf_counter()
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    for i, pt in enumerate(page_texts, start=1):
        x, y = 2*cm, h - 3*cm
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(w/2, h - 1*cm, f"OCR - {name} - Page {i}")
        c.setFont("Helvetica", 10)
        for line in pt.split('\n'):
            if line.strip():
                c.drawString(x, y, line.strip())
                y -= 12
                if y < 2*cm:
                    c.showPage()
                    y = h - 3*cm
        c.showPage()
    c.save()
    return time.perf_counter() - t0

def convert_docx_to_epub(docx_path, epub_path):
    """Convert a DOCX file to EPUB using Calibre's ebook-convert."""
    t0 = time.perf_counter()
    try:
        res = subprocess.run(
            ["ebook-convert", docx_path, epub_path],
            capture_output=True, text=True, check=True
        )
        return True, time.perf_counter() - t0, res.stdout
    except subprocess.CalledProcessError as e:
        return False, time.perf_counter() - t0, e.stderr

def process_pdfs_with_ocr(input_dir, output_dir,
                          to_docx, to_pdf, to_epub,
                          tesseract_config,
                          quiet=False, summary=False, logfile=None):
    """Coordinate OCR, file generation, and logging for all PDFs in a folder."""
    if to_epub and not to_docx:
        if not quiet and not summary:
            print("ℹ️ EPUB requires DOCX; enabling DOCX generation.")
        to_docx = True

    log = None
    if logfile:
        log = open(logfile, "w", encoding="utf-8", buffering=1)
        log.write("=== Process Started ===\n\n")

    os.makedirs(output_dir, exist_ok=True)
    if to_docx: os.makedirs(os.path.join(output_dir, 'docx'), exist_ok=True)
    if to_pdf:  os.makedirs(os.path.join(output_dir, 'pdf'), exist_ok=True)
    if to_epub: os.makedirs(os.path.join(output_dir, 'epub'), exist_ok=True)

    files = sorted(f for f in os.listdir(input_dir) if f.lower().endswith('.pdf'))
    if not files:
        if not quiet: print("⚠️ No PDF files found!")
        return

    start_all = time.perf_counter()
    for idx, fname in enumerate(files, start=1):
        if not quiet and not summary:
            print(f"\n📄 Processing file {idx:02d}/{len(files)}: {fname}")
        if log: log.write(f"\n--- Processing {idx:02d}/{len(files)}: {fname} ---\n")

        try:
            path = os.path.join(input_dir, fname)
            base = os.path.splitext(fname)[0]
            text, pages, ocr_t = extract_text_from_pdf(path, quiet, tesseract_config)
            if not quiet and not summary:
                print(f"🔹 OCR done in {ocr_t:.2f}s")
            if log: log.write(f"✅ OCR: {ocr_t:.2f}s\n")

            if to_docx:
                out = os.path.join(output_dir, 'docx', base + '.docx')
                dt = save_as_docx(text, out)
                if not quiet and not summary: print(f"    - DOCX in {dt:.2f}s")
                if log: log.write(f"✅ DOCX: {dt:.2f}s\n")

            if to_pdf:
                out = os.path.join(output_dir, 'pdf', base + '_ocr.pdf')
                dt = save_as_pdf(pages, out, base)
                if not quiet and not summary: print(f"    - PDF in {dt:.2f}s")
                if log: log.write(f"✅ PDF: {dt:.2f}s\n")

            if to_epub:
                epub_out = os.path.join(output_dir, 'epub', base + '.epub')
                ok, dt, msg = convert_docx_to_epub(
                    os.path.join(output_dir, 'docx', base + '.docx'),
                    epub_out
                )
                status = "✅" if ok else "❌"
                if not quiet and not summary:
                    print(f"    - {status} EPUB in {dt:.2f}s")
                if log: log.write(f"{status} EPUB: {dt:.2f}s\n")

        except Exception as e:
            if not quiet and not summary: print(f"❌ Error: {e}")
            if log: log.write(f"❌ Error: {e}\n")

    total_t = time.perf_counter() - start_all
    if not quiet: print(f"\n🎯 Completed in {total_t:.2f}s")
    if log:
        log.write(f"\n=== Completed in {total_t:.2f}s ===\n")
        log.close()

def main():
    parser = argparse.ArgumentParser(
        description="Script for OCR on PDFs generating DOCX, PDF and EPUB."
    )
    parser.add_argument("source_dir", help="Input folder with PDF files")
    parser.add_argument("--dest-dir", "--output-dir",
                        dest="dest_dir", help="Output folder (defaults to input folder)",
                        default=None)
    parser.add_argument("--docx", action="store_true", help="Generate DOCX files")
    parser.add_argument("--pdf", action="store_true", help="Generate OCR-processed PDF files")
    parser.add_argument("--epub", action="store_true",
                        help="Generate EPUB files (requires --docx)")
    parser.add_argument("--quiet", action="store_true", help="Silence output")
    parser.add_argument("--short-output", "--summary-output", dest="summary",
                        action="store_true", help="Show only summary output")
    parser.add_argument("--logfile", help="Path to log file (optional)")
    parser.add_argument("--preserve-layout", action="store_true",
                        help="Preserve original document layout during OCR")

    args = parser.parse_args()
    check_dependencies(generate_epub=args.epub)

    source = os.path.expanduser(args.source_dir)
    dest   = os.path.expanduser(args.dest_dir) if args.dest_dir else source

    # Choose appropriate Tesseract config
    tct_cfg = (
        tesseract_layout_config if args.preserve_layout
        else tesseract_default_config
    )

    if not (args.docx or args.pdf or args.epub):
        print("⚠️ You must select at least one option: --docx, --pdf, --epub")
        exit(1)

    process_pdfs_with_ocr(
        source, dest,
        args.docx, args.pdf, args.epub,
        tct_cfg,
        quiet=args.quiet,
        summary=args.summary,
        logfile=args.logfile
    )

if __name__ == "__main__":
    main()

