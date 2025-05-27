from setuptools import setup, find_packages
import re

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()


def get_version():
    with open("pdf2ocr/__init__.py", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string. \nCheck the variable __version__ in your __init__.py file")

setup(
    name="pdf2ocr",
    version=get_version(),
    packages=find_packages(),
    install_requires=[
    'pytesseract>=0.3.10',
    'pdf2image>=1.16.0',
    'python-docx>=0.8.11',
    'reportlab>=4.0.0',
    'tqdm>=4.45.0',
    'Pillow>=9.0.0',
    'pypdf>=3.15.0'
    ],
    entry_points={
        'console_scripts': [
            'pdf2ocr=pdf2ocr.main:main',
        ],
    },
    python_requires='>=3.6',
    author="Rafael Dantas",
    description="A CLI tool to apply OCR on PDF files and export to multiple formats.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT"
)

