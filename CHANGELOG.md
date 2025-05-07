# 📑 Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

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
