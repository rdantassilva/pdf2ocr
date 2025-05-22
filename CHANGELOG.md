# 📑 Changelog

All notable changes to this project will be documented in this file.

---

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
