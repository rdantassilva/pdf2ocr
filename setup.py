from setuptools import setup, find_packages

setup(
    name="pdf2ocr",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pillow",
        "pytesseract",
        "tqdm",
        "pdf2image",
        "python-docx",
        "reportlab"
    ],
    entry_points={
        "console_scripts": [
            "pdf2ocr=pdf2ocr.main:main"
        ]
    },
    author="Your Name",
    description="OCR PDF to DOCX, searchable PDF and EPUB.",
    license="MIT"
)
