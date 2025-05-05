# Makefile for pdf2ocr

venv:
	python3 -m venv venv_pdf2ocr
	source venv_pdf2ocr/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

install:
	pip install .

run:
	python3 pdf2ocr/main.py ~/Downloads --pdf --docx --epub

clean:
	rm -rf __pycache__ output *.log pdf2ocr.egg-info/ build/
