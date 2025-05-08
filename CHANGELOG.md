# 📑 Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

## [v1.0.12] - 2024-05-25

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

## [v1.0.8] - 2024-05-06

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