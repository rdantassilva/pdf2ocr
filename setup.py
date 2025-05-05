from setuptools import setup, find_packages

setup(
    name="pdf2ocr",
    version="1.0.0",
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
            'pdf2ocr=pdf2ocr:main',
        ],
    },
    python_requires='>=3.6',
)
