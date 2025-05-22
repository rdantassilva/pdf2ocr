"""Functions for converting between different document formats."""

import os
import subprocess
import time
from typing import Union, List

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def save_as_docx(text, output_path):
    """Saves extracted text to a DOCX file.
    
    Args:
        text (Union[str, List[str]]): The text content to save. Can be a single string or a list of page texts.
        output_path (str): Path where to save the DOCX file
        
    Returns:
        float: Time taken to save the file in seconds
    """
    start = time.perf_counter()
    title = os.path.splitext(os.path.basename(output_path))[0].replace("_", " ")
    document = Document()
    document.core_properties.title = title
    document.core_properties.author = "pdf2ocr"

    # Handle both single text and list of texts
    if isinstance(text, list):
        # Add title as heading for multi-page documents
        document.add_heading(title, level=1)
        
        # Join all pages with double newlines and process as a single text
        full_text = "\n\n".join(text)
        
        # Process paragraphs
        paragraphs = full_text.strip().split("\n\n")
        for para in paragraphs:
            clean_para = para.strip().replace("\n", " ")
            if clean_para:
                document.add_paragraph(clean_para)
    else:
        # Process single text string
        paragraphs = text.strip().split("\n\n")
        for para in paragraphs:
            clean_para = para.strip().replace("\n", " ")
            if clean_para:
                document.add_paragraph(clean_para)

    document.save(output_path)
    return time.perf_counter() - start


def save_as_pdf(text_pages, output_path, filename):
    """Creates a new PDF with OCR-extracted text in a clean, standardized format.

    This function generates a new PDF document that focuses on text readability
    and consistent formatting. It's ideal for cases where you want to extract
    and reformat content from PDFs (e.g., books, articles, documents).

    Key features:
    - Creates a new PDF with clean, consistent formatting
    - Adds simple page numbers for navigation
    - Uses standard fonts and margins for optimal readability
    - Creates output in 'pdf_ocr' directory
    - Includes PDF metadata (title, author, creation info)

    Technical approach:
    1. Uses reportlab to generate a new PDF from scratch
    2. Applies consistent formatting (margins, fonts, spacing)
    3. Preserves paragraph structure from OCR text
    4. Handles text flow and automatic pagination
    5. Adds document metadata

    Args:
        text_pages (list): List of text content for each page
        output_path (str): Path where to save the PDF file
        filename (str): Original filename for header information

    Returns:
        float: Time taken to save the file in seconds

    Note:
        This differs from process_layout_pdf_only() which preserves original layout.
        Choose this method when you want a clean, reformatted version of the document.
    """
    start = time.perf_counter()
    
    # Get title from filename
    title = os.path.splitext(os.path.basename(output_path))[0].replace("_", " ")
    
    # Create PDF with metadata
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(title)
    c.setAuthor("pdf2ocr")
    c.setCreator("pdf2ocr")
    c.setSubject("OCR processed document")
    c.setKeywords("OCR, PDF, text recognition")
    
    width, height = A4

    # Skip empty pages at the start
    page_offset = 0
    for idx, page_text in enumerate(text_pages):
        if page_text.strip():
            break
        page_offset += 1

    for idx, page_text in enumerate(text_pages[page_offset:], start=1):
        x = 2 * cm  # Left margin
        y = height - 3 * cm  # Top margin

        # Page header
        c.setFont("Helvetica", 10)  # Changed to regular weight for consistency
        header = f"pdf2ocr - Page {idx}"  # New header format
        c.drawString(x, height - 1 * cm, header)  # Aligned left like HTML

        # Main text
        c.setFont("Helvetica", 10)
        line_height = 12

        # Preserve paragraphs
        paragraphs = page_text.strip().split("\n\n")
        for para in paragraphs:
            lines = para.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line:
                    c.drawString(x, y, line)
                    y -= line_height
                    if y < 2 * cm:  # Check page end
                        c.showPage()
                        y = height - 3 * cm
                        # Repeat header on new page
                        c.setFont("Helvetica", 10)
                        c.drawString(x, height - 1 * cm, header)
                        c.setFont("Helvetica", 10)
            y -= line_height  # Extra space between paragraphs

        c.showPage()

    c.save()
    return time.perf_counter() - start


def save_as_html(text, output_path):
    """Saves extracted text to an HTML file.
    
    Args:
        text (Union[str, List[str]]): The text content to save. Can be a single string or a list of page texts.
        output_path (str): Path where to save the HTML file
        
    Returns:
        float: Time taken to save the file in seconds
    """
    start = time.perf_counter()
    try:
        title = os.path.splitext(os.path.basename(output_path))[0].replace("_", " ")
        
        # Start HTML content
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
        h1 {{ color: #333; }}
        .page {{ margin-bottom: 30px; }}
        .page-number {{ color: #666; font-style: italic; margin-bottom: 10px; }}
        p {{ margin-bottom: 15px; }}
    </style>
</head>
<body>"""

        # Handle both single text and list of texts
        if isinstance(text, list):
            # Add title for multi-page documents
            html_content += f"\n<h1>{title}</h1>\n"
            
            # Skip empty pages at the start
            page_offset = 0
            for idx, page_text in enumerate(text):
                if page_text.strip():
                    break
                page_offset += 1
            
            # Process each page
            for page_num, page_text in enumerate(text[page_offset:], start=1):
                html_content += f'\n<div class="page">\n'
                html_content += f'<div class="page-number">Page {page_num}</div>\n'
                
                # Process paragraphs in this page
                paragraphs = page_text.split("\n\n")
                for para in paragraphs:
                    if not para.strip():
                        continue
                    
                    # Join lines with spaces for better readability
                    lines = [line.strip() for line in para.split("\n")]
                    clean_text = " ".join(line for line in lines if line)
                    html_content += f"<p>{clean_text}</p>\n"
                
                html_content += "</div>\n"
        else:
            # Process single text string
            paragraphs = text.split("\n\n")
            for para in paragraphs:
                if not para.strip():
                    continue
                
                # Join lines with spaces for better readability
                lines = [line.strip() for line in para.split("\n")]
                clean_text = " ".join(line for line in lines if line)
                html_content += f"<p>{clean_text}</p>\n"

        # Close HTML
        html_content += "</body>\n</html>"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    except Exception as e:
        raise Exception(f"Failed to save HTML: {e}")

    return time.perf_counter() - start


def convert_docx_to_epub(docx_path, epub_path, lang):
    """Converts DOCX to EPUB using Calibre.
    
    Args:
        docx_path (str): Path to source DOCX file
        epub_path (str): Path where to save the EPUB file
        lang (str): Language code for the document
        
    Returns:
        tuple: (success: bool, time_taken: float, output: str)
    """
    start = time.perf_counter()
    try:
        title = os.path.splitext(os.path.basename(str(epub_path)))[0].replace("_", " ")

        # Expanded language mapping
        TESS_TO_CALIBRE_LANG = {
            "por": "pt-BR",  # Brazilian Portuguese
            "eng": "en-US",  # US English
            "spa": "es",     # Spanish
            "fra": "fr",     # French
            "deu": "de-DE",  # German
            "ita": "it",     # Italian
            "nld": "nl",     # Dutch
            "rus": "ru",     # Russian
            "tur": "tr",     # Turkish
            "jpn": "ja",     # Japanese
            "chi_sim": "zh-CN",  # Simplified Chinese
            "chi_tra": "zh-TW",  # Traditional Chinese
            "chi_sim_vert": "zh-CN",  # Simplified Chinese (vertical)
            "chi_tra_vert": "zh-TW",  # Traditional Chinese (vertical)
            "heb": "he",     # Hebrew
        }

        tess_lang = lang.lower()  # Normalize language code
        calibre_lang = TESS_TO_CALIBRE_LANG.get(tess_lang)

        # Build command with improved options
        cmd = [
            "ebook-convert",
            str(docx_path),  # Ensure path is string
            str(epub_path),  # Ensure path is string
            "--title", title,
            "--authors", "pdf2ocr",
            "--comments", "Converted by pdf2ocr",
            "--chapter", "//h:h1",  # Use h1 headings as chapter markers
            "--chapter-mark", "pagebreak",  # Add page breaks at chapters
            "--level1-toc", "//h:h1",  # Use h1 headings in TOC
            "--toc-threshold", "1",  # Include all headings in TOC
            "--max-toc-links", "50",  # Reasonable limit for TOC entries
            "--pretty-print",  # Format HTML for better readability
        ]

        if calibre_lang:
            cmd.extend(["--language", calibre_lang])

        # Check if source file exists
        if not os.path.exists(docx_path):
            return False, time.perf_counter() - start, f"Source file not found: {docx_path}"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(epub_path), exist_ok=True)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return True, time.perf_counter() - start, result.stdout

    except subprocess.CalledProcessError as e:
        error_msg = f"EPUB conversion failed: {e.stderr}"
        if "ebook-convert: command not found" in str(e):
            error_msg = "Calibre (ebook-convert) not found. Please install Calibre and ensure it's in your PATH."
        return False, time.perf_counter() - start, error_msg
    except Exception as e:
        return False, time.perf_counter() - start, f"Unexpected error: {str(e)}"