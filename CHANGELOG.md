# 📑 Changelog

All notable changes to this project will be documented in this file.

---

## [v1.0.19 - 2025-05-26]

### ✨ Added
- **Advanced Image Preprocessing Pipeline** for significantly improved OCR accuracy on distorted documents:
  - Automatic grayscale conversion with optimized parameters
  - Auto-contrast enhancement for better text visibility
  - Intelligent noise reduction using median filtering
  - Adaptive Histogram Equalization (CLAHE) for varying lighting conditions
  - Text-specific sharpening to improve character definition
  - Conservative contrast boosting for enhanced readability
  - Unsharp masking for fine-tuned text edge enhancement
- **`--dpi` Configuration Option** to control PDF to image conversion quality (default: 400, range: 72-1200)
- **Robust Error Handling** with automatic fallbacks to ensure processing never fails
- **Optional Advanced Dependencies** (scipy, scikit-image) with graceful degradation when unavailable
- **Unified Processing** - all output formats now benefit from advanced image enhancements

### 🛠 Changed
- **Enhanced OCR Quality** across all modes (standard and layout-preserving)
- **Improved Text Recognition** especially for poor quality scans, faded text, and noisy documents
- **Configurable Image Resolution** with `--dpi` parameter for quality vs. performance trade-offs
- **Optimized Processing Pipeline** with intelligent edge preservation during noise reduction
- **Better Memory Management** with validation checks to prevent image corruption
- **Updated Dependencies** to include numpy, scipy, and scikit-image for advanced image processing
- **Unified DPI Configuration** across all processing modes and Tesseract operations

### 🐛 Fixed
- **Image Processing Stability** with comprehensive error handling and fallback mechanisms
- **Memory Efficiency** improvements in image preprocessing pipeline

---

## [v1.0.18 - 2025-05-23]

### ✨ Added
- `--batch-size` option to control number of pages processed in each batch (disabled by default).
- Improved memory management by processing PDF pages in configurable batches.

### 🛠 Changed
- Fixed total processing time calculation to accurately reflect all operations.
- Improved log message formatting for better readability.
- Enhanced progress reporting with batch size information.
- Changed batch processing to be disabled by default for better compatibility with most PDFs.

## [v1.0.17 - 2025-05-22]

### ✨ Added
- `--workers` option for parallel PDF processing with configurable number of worker processes.
- Centralized logging system with consistent output formatting across all operations.
- Enhanced PDF compression in layout-preserving mode using Ghostscript post-OCR compression.

### 🛠 Changed
- Refactored paragraph processing in `converters.py` to use a shared helper function `_process_paragraphs`.
- Improved PDF text rendering with better line wrapping and word boundaries.
- Enhanced Calibre output handling to log only to file, never to console.
- Fixed HTML template to properly interpolate title using f-strings.
- Unified logging approach with better control over quiet and summary modes.
- Improved progress reporting for parallel processing.
- Renamed `logger` parameter to `log_file` in logging functions for better clarity.
- Optimized layout-preserving mode to maintain OCR quality while reducing final file size.

### 🐛 Fixed
- Removed redundant subprocess arguments in EPUB conversion.
- Fixed subprocess.run() call in convert_docx_to_epub by removing conflicting stderr argument.
- Improved error handling in EPUB conversion with clearer error messages.
- Fixed race conditions in parallel processing logging.
- Fixed PDF compression in layout-preserving mode to use only supported methods.

## [v1.0.12] - 2025-05-08

### ✨ Added
- `--lang` option to set the Tesseract OCR language (default: `por`).
- Validation for selected OCR language (via `tesseract --list-langs`).
- Logging and CLI feedback for the selected OCR language.
- Automatic language check with clear errors if model is missing.
- Unit test to validate the `--lang` argument.
- Section in README explaining supported languages and installation of Tesseract language models.
- Enhanced test coverage and language-specific cleanup for Portuguese.

### 🛠 Changed
- Portuguese text cleaning (`clean_text_portuguese`) is now applied only when `--lang por` is used.
- Output directory for layout-preserving PDFs renamed to `pdf_ocr_layout`.
- Clarified README structure and included flag examples (🇧🇷, 🇺🇲, 🇪🇸...).

### 🐛 Fixed
- Syntax error when mixing positional and keyword arguments in `process_pdfs_with_ocr`.
- PDF not being found in expected folder during automated test execution.

---

## [v1.0.8] - 2025-05-06

### ✨ Added
- `--html` option to export OCR results as HTML.
- `--preserve-layout` mode to generate searchable PDFs while retaining original visual layout.
- EPUB generation now includes title, author, language, and description metadata.
- DOCX, PDF, and EPUB outputs now preserve original paragraph structure from scanned documents.

### 🛠 Changed
- EPUB generation now uses the input file name as the EPUB title, with `pdf2ocr` as author.
- PDF header text is now Unicode-safe and optionally sanitized for unsupported fonts.

### 🐛 Fixed
- Incorrect EPUB metadata defaults (e.g., "Unknown" title and "python-docx" author).
- Line spacing inconsistencies in multi-paragraph OCR results.

---

## [v1.0.0] - Initial release

- Basic OCR processing for scanned PDFs.
- Output to DOCX and searchable PDF formats.
- EPUB generation (via Calibre) with minimal formatting.
