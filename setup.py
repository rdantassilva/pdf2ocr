from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pdf2ocr",
    version="1.0.4",
    packages=find_packages(),
    install_requires=[
        'pytesseract>=0.3.10',
        'pdf2image>=1.16.0',
        'python-docx>=0.8.11',
        'reportlab>=4.0.0',
        'tqdm>=4.45.0',
        'Pillow>=9.0.0'
    ],
    entry_points={
        'console_scripts': [
            'pdf2ocr=pdf2ocr.main:main',
        ],
    },
    python_requires='>=3.6',
    author="Rafael Dantas",
    description="OCR PDF to Docx, searchable PDFs and EPUB.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT"
)

