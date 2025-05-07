# Makefile for pdf2ocr

venv:
	python3 -m venv venv_pdf2ocr
	. venv_pdf2ocr/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && pip install -r requirements-dev.txt && pip install -e .
	@echo ""
	@echo "✅ Virtual environment 'venv_pdf2ocr' created and dependencies installed."
	@echo "👉 To activate it, run:"
	@echo "   . venv_pdf2ocr/bin/activate"
	@echo ""

install:
	pip install .

run:
	python3 pdf2ocr/main.py ~/Downloads --pdf --docx --epub --html

test:
	python3 -m pytest tests

lint:
	flake8 pdf2ocr

format:
	black pdf2ocr
	isort pdf2ocr

clean:
	rm -rf __pycache__ output *.log pdf2ocr.egg-info/ build/
