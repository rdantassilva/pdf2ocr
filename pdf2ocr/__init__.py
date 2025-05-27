"""pdf2ocr - A CLI tool to apply OCR on PDF files and export to multiple formats.

This package provides comprehensive functionality to convert PDF files to searchable formats
using OCR (Optical Character Recognition) technology with advanced image preprocessing
and parallel processing capabilities.

Core Dependencies:
- 📜 PIL/Pillow: Advanced image processing and enhancement for optimal OCR
- 🔍 pytesseract: Python interface for Tesseract OCR engine
- 📊 tqdm: Progress tracking for batch operations
- 📄 pdf2image: High-quality PDF to image conversion
- 📝 python-docx: Word document generation with formatting
- 🖨️ reportlab: Professional PDF creation and manipulation
- 🏷️ tesseract-ocr: Industry-standard OCR engine
- 🖼️ poppler-utils: PDF processing utilities (pdftoppm)
- 📚 calibre: E-book conversion suite (ebook-convert)
- 🐍 pypdf: PDF merging and manipulation
- 🧮 numpy: Numerical operations for image processing (optional)
- 🔬 scipy: Advanced image filtering and enhancement (optional)
- 🖼️ scikit-image: Professional image processing algorithms (optional)

Advanced Image Preprocessing Pipeline:
1. 🎨 Automatic grayscale conversion with optimized parameters
2. 🔧 Auto-contrast enhancement for better text visibility
3. 🔇 Intelligent noise reduction using median filtering
4. 💡 Adaptive Histogram Equalization (CLAHE) for varying lighting
5. ✨ Text-specific sharpening to improve character definition
6. 🎯 Conservative contrast boosting for enhanced readability
7. 🔍 Unsharp masking for fine-tuned text edge enhancement

PDF Generation Modes:
1. Layout-Preserving Mode (--preserve-layout):
   - Maintains exact visual appearance of original document
   - Adds invisible OCR text layer for searchability
   - Best for forms, scientific papers, magazines, technical documents
   - Advanced compression with Ghostscript optimization
   - Output in 'pdf_ocr_layout' directory

2. Standard Mode (default):
   - Creates new documents with clean, consistent formatting
   - Focuses on text readability and accessibility
   - Best for books, articles, general documents
   - Multiple output formats: PDF, DOCX, HTML, EPUB
   - Output in format-specific directories

Performance Features:
- 🚀 Parallel processing with configurable worker threads
- 🔄 Batch processing for memory-efficient handling of large PDFs
- ⚙️ Configurable DPI settings (72-1200) for quality vs. speed trade-offs
- 📊 Real-time progress tracking and comprehensive logging
- 🛡️ Robust error handling with automatic fallbacks
- 🔧 Graceful shutdown support for long-running operations

Conversion Flow:
1. 📄 PDF pages converted to high-quality images using pdf2image
2. 🖼️ Advanced image preprocessing applied for optimal OCR quality
3. 🔍 Tesseract OCR extracts text with language-specific models
4. 📝 Multiple output formats generated simultaneously
5. 📚 Optional EPUB conversion via Calibre integration
6. 📊 Comprehensive processing statistics and timing reports

Quality Control:
- DPI optimization: 72-150 (fast), 200-400 (balanced), 500-1200 (maximum quality)
- Automatic image enhancement with fallback mechanisms
- Language-specific OCR optimization (Portuguese default)
- Memory-efficient batch processing for large documents
- Comprehensive error logging and recovery

Usage Examples:
    Basic usage:
        >>> from pdf2ocr.config import ProcessingConfig
        >>> from pdf2ocr.converters import process_pdfs_with_ocr
        >>> config = ProcessingConfig(source_dir="./pdfs", generate_pdf=True)
        >>> process_pdfs_with_ocr(config, logger=None)

    Command line:
        $ pdf2ocr ./pdfs --pdf --docx --epub --workers 4 --dpi 600

Important Notes:
- EPUB generation requires Calibre installation
- Advanced image processing uses optional dependencies (scipy, scikit-image)
- Processing time scales with DPI setting and document complexity
- All image enhancements are applied automatically
- Supports graceful interruption and resume capabilities
"""

__version__ = "1.0.19"
