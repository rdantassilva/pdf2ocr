"""Tests for common text processing utilities."""

from pdf2ocr.converters.common import (
    merge_lines_into_paragraphs,
    process_paragraphs,
    strip_repeated_headers_footers,
)


class TestMergeLinesIntoParagraphs:

    def test_blank_lines_after_sentence_end_create_paragraph_breaks(self):
        text = (
            "This is the first paragraph that talks about the creation and nature of\n"
            "all things in our world. It ends here with a final sentence.\n"
            "\n"
            "This is the second paragraph which starts after a blank line and should be separate."
        )
        result = merge_lines_into_paragraphs(text)
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
        assert len(paragraphs) == 2

    def test_blank_lines_without_sentence_end_do_not_break(self):
        """OCR may insert blank lines in the middle of a paragraph.
        If the last accumulated line does NOT end with terminal punctuation,
        the blank line is treated as noise and the paragraph continues."""
        text = (
            "a criação aberta e que a sua consumação consiste em vir a ser átria e\n"
            "\n"
            "moradia da glória de Deus. Já aqui na história, pessoas experimentam."
        )
        result = merge_lines_into_paragraphs(text)
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
        assert len(paragraphs) == 1
        assert "e moradia" in paragraphs[0]

    def test_short_line_ending_sentence_starts_new_paragraph(self):
        text = (
            "This is a long line that fills most of the average width of a typical document page extracted.\n"
            "End of section.\n"
            "Beginning of new section with a capital letter and long content that continues."
        )
        result = merge_lines_into_paragraphs(text)
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
        assert len(paragraphs) >= 2

    def test_list_items_start_new_paragraphs(self):
        text = "Introduction text here.\n• First item\n• Second item\n- Third item"
        result = merge_lines_into_paragraphs(text)
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
        assert any("First item" in p for p in paragraphs)
        assert any("Second item" in p for p in paragraphs)

    def test_numbered_items_start_new_paragraphs(self):
        text = "Some context here.\n1. First point\n2. Second point"
        result = merge_lines_into_paragraphs(text)
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
        assert any("1." in p for p in paragraphs)
        assert any("2." in p for p in paragraphs)

    def test_empty_input(self):
        assert merge_lines_into_paragraphs("") == ""

    def test_whitespace_only(self):
        result = merge_lines_into_paragraphs("   \n   \n   ")
        assert result.strip() == ""

    def test_single_line(self):
        text = "Just one line."
        result = merge_lines_into_paragraphs(text)
        assert result.strip() == "Just one line."

    def test_consecutive_long_lines_merge(self):
        """In real OCR output, visual line breaks happen mid-sentence.
        Consecutive lines without sentence-ending punctuation should merge."""
        text = (
            "This is a long line that represents the first part of a paragraph in a PDF\n"
            "document and this is another long line that continues the same paragraph\n"
            "extracted from the PDF source file without any sentence endings."
        )
        result = merge_lines_into_paragraphs(text)
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
        assert len(paragraphs) == 1

    def test_sentence_end_uppercase_start_breaks_paragraph(self):
        """A line ending with terminal punctuation followed by a line starting
        with uppercase is treated as a paragraph boundary."""
        text = (
            "This is the end of the first paragraph about creation.\n"
            "This is the start of a new paragraph about something else entirely."
        )
        result = merge_lines_into_paragraphs(text)
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
        assert len(paragraphs) == 2

    def test_page_numbers_are_filtered(self):
        text = "Some content here that continues for\n42\na while longer."
        result = merge_lines_into_paragraphs(text)
        assert "42" not in result

    def test_headings_start_new_paragraph(self):
        text = (
            "End of previous section content.\n"
            "INTRODUCTION\n"
            "This is the beginning of a new section that starts here."
        )
        result = merge_lines_into_paragraphs(text)
        paragraphs = [p.strip() for p in result.split("\n\n") if p.strip()]
        assert any("INTRODUCTION" in p for p in paragraphs)

    def test_ligatures_are_fixed(self):
        text = "A efi cácia da refl exão fi losófi ca."
        result = merge_lines_into_paragraphs(text)
        assert "eficácia" in result
        assert "reflexão" in result
        assert "filosófica" in result

    def test_pdf2ocr_headers_are_stripped(self):
        """When re-processing a pdf2ocr output, the 'pdf2ocr - Page X'
        headers from the source should be stripped from the text."""
        text = (
            "pdf2ocr - Page 4\n"
            "doutrina cristã da criação é uma concepção de mundo à luz\n"
            "do messias Jesus e sob os aspectos do tempo messiânico."
        )
        result = merge_lines_into_paragraphs(text)
        assert "pdf2ocr" not in result
        assert "doutrina cristã" in result


class TestStripRepeatedHeadersFooters:

    def test_removes_repeated_headers(self):
        pages = [
            "Journal of Science\nActual content page one.\nPage 1",
            "Journal of Science\nActual content page two.\nPage 2",
            "Journal of Science\nActual content page three.\nPage 3",
            "Journal of Science\nActual content page four.\nPage 4",
        ]
        result = strip_repeated_headers_footers(pages)
        for page in result:
            assert "Journal of Science" not in page

    def test_preserves_unique_content(self):
        pages = [
            "Header\nUnique content A.\nFooter",
            "Header\nUnique content B.\nFooter",
            "Header\nUnique content C.\nFooter",
        ]
        result = strip_repeated_headers_footers(pages)
        assert any("Unique content A" in p for p in result)
        assert any("Unique content B" in p for p in result)
        assert any("Unique content C" in p for p in result)

    def test_skips_short_documents(self):
        pages = ["Page one content.", "Page two content."]
        result = strip_repeated_headers_footers(pages)
        assert result == pages

    def test_no_repeated_lines(self):
        pages = [
            "Unique header A\nContent A.",
            "Unique header B\nContent B.",
            "Unique header C\nContent C.",
        ]
        result = strip_repeated_headers_footers(pages)
        assert result == pages

    def test_empty_input(self):
        assert strip_repeated_headers_footers([]) == []


class TestProcessParagraphs:

    def test_basic_paragraph_splitting(self):
        text = (
            "This is the first paragraph that talks about the creation and nature of\n"
            "all things in our world. It ends here.\n"
            "\n"
            "This is the second paragraph which starts after a blank line."
        )
        result = process_paragraphs(text)
        assert len(result) == 2
        assert "first paragraph" in result[0]
        assert "second paragraph" in result[1]

    def test_list_input(self):
        pages = ["Page one text.", "Page two text."]
        result = process_paragraphs(pages)
        assert len(result) >= 2

    def test_empty_input(self):
        assert process_paragraphs("") == []
        assert process_paragraphs([]) == []
