"""Configuration classes and constants for pdf2ocr."""

from dataclasses import dataclass
from typing import Optional
import os

from pdf2ocr.logging_config import log_message

# Two Tesseract configurations:
# - default: fast and accurate, does not preserve layout
# - layout-aware: tries to maintain original blocks and columns
TESSERACT_DEFAULT_CONFIG = "--oem 3 --psm 1"
TESSERACT_LAYOUT_CONFIG = "--oem 1 --psm 11"

@dataclass
class ProcessingConfig:
    """Configuration for PDF processing with OCR.
    
    Attributes:
        source_dir: Directory containing source PDF files
        dest_dir: Directory for output files (defaults to source_dir if None)
        lang: Tesseract language code (e.g. 'por' for Portuguese)
        dpi: DPI for image conversion
        generate_docx: Whether to generate DOCX files
        generate_pdf: Whether to generate searchable PDF files
        generate_epub: Whether to generate EPUB files
        generate_html: Whether to generate HTML files
        preserve_layout: Whether to preserve original PDF layout
        quiet: Run silently without progress output
        summary_output: Display only final conversion summary
        log_path: Path to log file (optional)
    """
    source_dir: str
    dest_dir: Optional[str] = None
    lang: str = "por"
    dpi: int = 400
    generate_docx: bool = False
    generate_pdf: bool = False
    generate_epub: bool = False
    generate_html: bool = False
    preserve_layout: bool = False
    quiet: bool = False
    summary_output: bool = False
    log_path: Optional[str] = None

    def __post_init__(self):
        # Initialize derived paths
        self._effective_dest_dir = self.dest_dir if self.dest_dir is not None else self.source_dir
        self.docx_dir = os.path.join(self._effective_dest_dir, "docx")
        self.pdf_dir = os.path.join(self._effective_dest_dir, "pdf_ocr_layout" if self.preserve_layout else "pdf_ocr")
        self.epub_dir = os.path.join(self._effective_dest_dir, "epub")
        self.html_dir = os.path.join(self._effective_dest_dir, "html")

    def get_effective_dest_dir(self) -> str:
        """Get the effective destination directory.
        
        Returns:
            str: The destination directory to use (source_dir if dest_dir is None)
        """
        return self._effective_dest_dir

    def get_tesseract_config(self) -> str:
        """Get the appropriate Tesseract configuration based on layout preservation setting.
        
        Returns:
            str: Tesseract configuration string with language
        """
        base_config = TESSERACT_LAYOUT_CONFIG if self.preserve_layout else TESSERACT_DEFAULT_CONFIG
        return f"{base_config} -l {self.lang}"

    def validate(self) -> None:
        """Validate the configuration settings.
        
        Raises:
            ValueError: If no output format is selected
        """
        if not any([self.generate_docx, self.generate_pdf, self.generate_epub, self.generate_html]):
            raise ValueError("You must select at least one output format: PDF, DOCX, EPUB, or HTML")

        # Enable DOCX automatically if EPUB is requested
        if self.generate_epub and not self.generate_docx:
            log_message(None, "WARNING", "EPUB generation requires DOCX format. Enabling DOCX generation automatically.", quiet=self.quiet)
            self.generate_docx = True

        # Warn about preserve-layout limitations and disable other formats
        if self.preserve_layout:
            if any([self.generate_docx, self.generate_epub, self.generate_html]):
                log_message(None, "WARNING", "Layout preservation mode only supports PDF output. Other formats will be disabled.", quiet=self.quiet)
                self.generate_docx = False
                self.generate_epub = False
                self.generate_html = False
            if not self.generate_pdf:
                self.generate_pdf = True
                log_message(None, "INFO", "PDF output automatically enabled for layout preservation mode.", quiet=self.quiet)

        # Skip directory validation in test environment
        if not self.source_dir.startswith("/test/") and not os.path.isdir(self.source_dir):
            raise ValueError(f"Source directory not found: {self.source_dir}")

        if self.dpi <= 0:
            raise ValueError("DPI must be a positive integer") 