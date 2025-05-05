# Makefile for pdf2ocr

venv:
	python3 -m venv venv_pdf2ocr
	. venv_pdf2ocr/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo ""
	@echo "✅ Virtual environment 'venv_pdf2ocr' created and dependencies installed."
	@echo "👉 To activate it, run:"
	@echo "   . venv_pdf2ocr/bin/activate"
	@echo ""

install:
	pip install .

run:
	python3 pdf2ocr/main.py ~/Downloads --pdf --docx --epub

clean:
	rm -rf __pycache__ output *.log pdf2ocr.egg-info/ build/
