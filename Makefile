# Makefile for pdf2ocr

venv:
	python3 -m venv venv
	source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

install:
	pip install .

run:
	python3 pdf2ocr/main.py ./example_pdfs --pdf --docx --epub --dest-dir ./output

clean:
	rm -rf __pycache__ *.deb output *.log
