"""HTML conversion and processing functionality."""

import os
import time
from typing import List, Optional

from pdf2ocr.converters.common import process_paragraphs


def save_as_html(text_pages: List[str], output_path: str, max_sentences: Optional[int] = None) -> float:
    """Creates a new HTML document with OCR-extracted text in a clean format.

    This function generates a new HTML document that focuses on text readability
    and consistent formatting. It's ideal for cases where you want to extract
    and reformat content from PDFs into a web-friendly format.

    Key features:
    - Creates a new HTML with clean, consistent formatting
    - Uses semantic HTML5 elements
    - Includes responsive CSS styling
    - Creates output in 'html_ocr' directory
    - Includes document metadata

    Technical approach:
    1. Generates a new HTML5 document from scratch
    2. Applies consistent CSS styling
    3. Preserves paragraph structure from OCR text
    4. Uses semantic HTML elements for better accessibility
    5. Adds document metadata

    Args:
        text_pages: List of text content for each page
        output_path: Path where to save the HTML file

    Returns:
        float: Time taken to save the file in seconds
    """
    start = time.perf_counter()

    # Get title from filename
    title = os.path.splitext(os.path.basename(output_path))[0].replace("_", " ")

    # HTML template with CSS styling
    html_start = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .page {{
            margin-bottom: 40px;
            padding: 20px;
            border: 1px solid #eee;
            border-radius: 5px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .page-header {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        p {{
            margin: 0 0 1em;
            text-align: justify;
        }}
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #1a1a1a;
                color: #e0e0e0;
            }}
            .page {{
                background-color: #2d2d2d;
                border-color: #404040;
            }}
            .page-header {{
                color: #b0b0b0;
                border-bottom-color: #404040;
            }}
        }}
        @media print {{
            .page {{
                border: none;
                box-shadow: none;
                margin-bottom: 20px;
                page-break-after: always;
            }}
            body {{
                max-width: none;
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
"""

    html_end = """</body>
</html>"""

    html_content = []
    page_num = 0
    for page_text in text_pages:
        paragraphs = process_paragraphs(page_text, max_sentences=max_sentences)
        if not paragraphs:
            continue

        page_num += 1
        html_content.append('<div class="page">')
        html_content.append(f'<div class="page-header">pdf2ocr - Page {page_num}</div>')

        for para in paragraphs:
            html_content.append(f"<p>{para}</p>")

        html_content.append("</div>")

    # Combine all parts
    html_output = html_start + "\n".join(html_content) + html_end

    # Save the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    return time.perf_counter() - start
