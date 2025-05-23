"""Common functionality shared between converters."""

from typing import List, Union


def process_paragraphs(text: Union[str, List[str]]) -> List[str]:
    """Process and clean paragraphs from text input.

    This function processes text input and returns a list of clean paragraphs.
    It handles both single strings and lists of strings, and properly formats
    paragraphs by:
    - Joining consecutive lines within paragraphs with spaces
    - Preserving paragraph breaks (double newlines)
    - Removing extra whitespace and empty lines
    - Maintaining proper text flow

    Args:
        text: Input text, can be a single string or list of strings

    Returns:
        List[str]: List of cleaned paragraphs, with each paragraph having proper
                  line joining and spacing.

    Example:
        >>> text = '''First line
        ...          Second line
        ...
        ...          New paragraph'''
        >>> process_paragraphs(text)
        ['First line Second line', 'New paragraph']
    """
    # If input is a list, join with double newlines
    if isinstance(text, list):
        text = "\n\n".join(text)

    # Normalize line endings and remove carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split text into paragraphs (split on double newlines)
    raw_paragraphs = text.split("\n\n")

    # Process each paragraph
    paragraphs = []
    for para in raw_paragraphs:
        if not para.strip():
            continue

        # Split paragraph into lines and clean each line
        lines = [line.strip() for line in para.split("\n")]

        # Join non-empty lines with spaces
        clean_text = " ".join(line for line in lines if line)

        # Only add non-empty paragraphs
        if clean_text:
            paragraphs.append(clean_text)

    return paragraphs
