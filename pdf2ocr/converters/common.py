"""Common functionality shared between converters."""

import re
from collections import Counter
from typing import List, Union

_SENTENCE_END = re.compile(r"[.!?:;]\s*$")
_PAGE_NUM = re.compile(r"^\s*\d{1,4}\s*$")
_OCR_HEADER = re.compile(r"^pdf2ocr\s*-\s*Page\s*\d+$", re.IGNORECASE)
_HEADING_LIKE = re.compile(
    r"^(\d{1,2}[\s.)\-–—]+[A-ZÀ-Ú]|Cap[ií]tulo|CAPÍTULO|Introdu|Conclus|Refer[êe]ncias)",
    re.IGNORECASE,
)


def _fix_ocr_ligatures(text: str) -> str:
    """Fix broken typographic ligatures from OCR/PDF extraction.

    OCR and PDF extractors sometimes split ligature glyphs ("fi", "fl", "ff")
    with a space: "fi nanceiro" → "financeiro", "refl exão" → "reflexão".
    Also replaces Unicode ligature codepoints (U+FB00–FB04).
    """
    text = text.replace("\ufb00", "ff")
    text = text.replace("\ufb01", "fi")
    text = text.replace("\ufb02", "fl")
    text = text.replace("\ufb03", "ffi")
    text = text.replace("\ufb04", "ffl")

    _lower = r"[a-záàâãéèêíïóôõúüç]"
    text = re.sub(rf"fi\s+(?={_lower})", "fi", text)
    text = re.sub(rf"fl\s+(?={_lower})", "fl", text)
    text = re.sub(rf"ff\s+(?={_lower})", "ff", text)
    return text


def merge_lines_into_paragraphs(text: str) -> str:
    """Reconstruct proper paragraphs from OCR / PDF-extracted text.

    OCR and PDF extraction produce one line per visual line, breaking paragraphs
    arbitrarily.  This function merges consecutive lines that belong to the same
    paragraph.

    Key rules (adapted from doc2audio's ``_rebuild_pdf_paragraphs``):
    - Blank lines only flush a paragraph when the accumulated text ends with
      sentence-terminal punctuation (``.!?:;``).  Otherwise the blank line is
      treated as OCR noise and the paragraph continues.
    - Lines that look like page numbers are discarded.
    - Lines that look like headings (ALL CAPS or "Capítulo …" patterns) always
      start a new paragraph.
    - Bullet / numbered-list items always start a new paragraph.
    - A new paragraph starts when the previous line ends with sentence-terminal
      punctuation **and** the next line begins with an uppercase letter.

    Returns paragraphs separated by double newlines so that downstream code
    can split on ``\\n\\n`` as usual.
    """
    lines = text.splitlines()
    if not lines:
        return text

    paragraphs: List[str] = []
    current: List[str] = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if current and _SENTENCE_END.search(current[-1]):
                paragraphs.append(" ".join(current))
                current = []
            continue

        if _PAGE_NUM.match(stripped) or _OCR_HEADER.match(stripped):
            continue

        is_heading = (
            stripped.isupper() and len(stripped) > 3
        ) or _HEADING_LIKE.match(stripped)

        is_list_item = (
            stripped.startswith(("•", "-", "–", "—", "▪"))
        ) or (
            len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)"
        )

        if is_heading or is_list_item:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            if is_heading:
                paragraphs.append(stripped)
            else:
                current.append(stripped)
            continue

        if not current:
            current.append(stripped)
            continue

        prev = current[-1]
        starts_upper = stripped[0].isupper() if stripped else False

        if _SENTENCE_END.search(prev) and starts_upper:
            paragraphs.append(" ".join(current))
            current = [stripped]
        else:
            current.append(stripped)

    if current:
        paragraphs.append(" ".join(current))

    result = "\n\n".join(paragraphs)
    return _fix_ocr_ligatures(result)


def strip_repeated_headers_footers(text_pages: List[str]) -> List[str]:
    """Remove lines that repeat as headers/footers across most pages.

    Detects lines appearing in the first or last two lines of ≥60 % of pages,
    then filters them out from every page.
    """
    if len(text_pages) < 3:
        return text_pages

    line_counts: Counter = Counter()
    for page_text in text_pages:
        lines = page_text.split("\n")
        candidates = set()
        for line in lines[:2] + lines[-2:]:
            stripped = line.strip()
            if stripped:
                candidates.add(stripped)
        for line in candidates:
            line_counts[line] += 1

    threshold = len(text_pages) * 0.6
    repeated = {line for line, count in line_counts.items() if count >= threshold}

    if not repeated:
        return text_pages

    cleaned: List[str] = []
    for page_text in text_pages:
        filtered = "\n".join(
            line for line in page_text.split("\n")
            if line.strip() not in repeated
        )
        cleaned.append(filtered)

    return cleaned


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+")


def _split_long_paragraph(text: str, max_sentences: int) -> List[str]:
    """Split a paragraph that exceeds *max_sentences* into smaller chunks.

    Splits on sentence boundaries (after ``.!?…`` followed by whitespace).
    Each resulting chunk has at most *max_sentences* sentences.
    """
    sentences = _SENTENCE_SPLIT.split(text)
    if len(sentences) <= max_sentences:
        return [text]

    chunks: List[str] = []
    for i in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[i : i + max_sentences])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def process_paragraphs(
    text: Union[str, List[str]],
    max_sentences: Optional[int] = None,
) -> List[str]:
    """Process and clean paragraphs from text input.

    This function processes text input and returns a list of clean paragraphs.
    It handles both single strings and lists of strings, and properly formats
    paragraphs by:
    - Reconstructing logical paragraphs from line-level OCR output
    - Preserving paragraph breaks (double newlines)
    - Removing extra whitespace and empty lines
    - Maintaining proper text flow
    - Optionally splitting overly long paragraphs at sentence boundaries

    Args:
        text: Input text, can be a single string or list of strings
        max_sentences: If set, paragraphs exceeding this number of sentences
            are split at sentence boundaries as a safety net.

    Returns:
        List[str]: List of cleaned paragraphs.
    """
    if isinstance(text, list):
        text = "\n\n".join(text)

    text = text.replace("\r\n", "\n").replace("\r", "\n")

    text = merge_lines_into_paragraphs(text)

    raw_paragraphs = text.split("\n\n")

    paragraphs = []
    for para in raw_paragraphs:
        if not para.strip():
            continue

        lines = [line.strip() for line in para.split("\n")]
        clean_text = " ".join(line for line in lines if line)

        if clean_text:
            if max_sentences and max_sentences > 0:
                paragraphs.extend(_split_long_paragraph(clean_text, max_sentences))
            else:
                paragraphs.append(clean_text)

    return paragraphs
