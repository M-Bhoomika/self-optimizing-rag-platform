"""PDF text extraction using PyMuPDF when available."""

from __future__ import annotations


def extract_pdf_text(content: bytes) -> str:
    """Extract plain text from PDF bytes using PyMuPDF (``fitz``).

    Raises:
        ImportError: when PyMuPDF is not installed.
        ValueError: when the PDF cannot be parsed or contains no text.
    """
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "PyMuPDF is required for PDF ingestion. Install with: pip install pymupdf"
        ) from exc

    if not content:
        raise ValueError("PDF content is empty.")

    with fitz.open(stream=content, filetype="pdf") as document:
        pages = [page.get_text("text") for page in document]
    text = "\n".join(page.strip() for page in pages if page and page.strip())
    if not text:
        raise ValueError("PDF contains no extractable text.")
    return text
