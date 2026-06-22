"""Parser extensions for PDF and code files."""

from __future__ import annotations

import pytest

from api.ingestion.parser import detect_document_type, parse_document_text


def test_detect_code_file_types() -> None:
    assert detect_document_type("module.py") == "py"
    assert detect_document_type("app.ts") == "ts"


def test_parse_python_code_as_text() -> None:
    text = parse_document_text("def hello():\n    return 42", "py")
    assert "hello" in text


def test_pdf_requires_pymupdf() -> None:
    import importlib.util

    from api.ingestion.pdf_extractor import extract_pdf_text

    if importlib.util.find_spec("fitz") is None:
        with pytest.raises(ImportError):
            extract_pdf_text(b"%PDF-1.4 fake")
    else:
        with pytest.raises(Exception):
            extract_pdf_text(b"%PDF-1.4 fake")
