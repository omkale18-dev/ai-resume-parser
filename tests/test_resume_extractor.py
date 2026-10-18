from __future__ import annotations

import io
import pytest
import pymupdf as fitz
import docx

from src.resume_extractor import (
    extract_text,
    extract_text_from_docx,
    extract_text_from_pdf,
    validate_file,
)

def _create_sample_pdf(content: str = "Test resume content") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), content)
    pdf_bytes: bytes = doc.write()
    doc.close()
    return pdf_bytes

def _create_sample_docx(content: str = "Test resume content") -> bytes:
    doc = docx.Document()
    doc.add_paragraph(content)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def test_validate_file_valid_pdf() -> None:
    content = b"%PDF-1.4 sample content"
    is_valid, msg = validate_file(content, "my_resume.pdf")

    assert is_valid is True
    assert msg == ""

def test_validate_file_valid_docx() -> None:
    content = b"PK\x03\x04 sample docx archive data"
    is_valid, msg = validate_file(content, "my_resume.docx")

    assert is_valid is True
    assert msg == ""

def test_validate_file_empty() -> None:
    is_valid, msg = validate_file(b"", "resume.pdf")

    assert is_valid is False
    assert "empty" in msg.lower()

def test_validate_file_unsupported_extension() -> None:
    content = b"Plain text resume content"
    is_valid_txt, msg_txt = validate_file(content, "resume.txt")
    is_valid_png, msg_png = validate_file(content, "resume.png")

    assert is_valid_txt is False
    assert "unsupported" in msg_txt.lower()
    assert ".txt" in msg_txt

    assert is_valid_png is False
    assert "unsupported" in msg_png.lower()
    assert ".png" in msg_png

def test_validate_file_too_large() -> None:
    large_content = b"x" * (2 * 1024 * 1024)
    is_valid, msg = validate_file(large_content, "resume.pdf", max_size_mb=1)

    assert is_valid is False
    assert "exceeds" in msg.lower()
    assert "1 MB" in msg

def test_validate_file_no_extension() -> None:
    content = b"Test file content"

    is_valid_no_ext, msg_no_ext = validate_file(content, "resumefile")
    assert is_valid_no_ext is False
    assert "extension" in msg_no_ext.lower()

    is_valid_empty_name, msg_empty_name = validate_file(content, "")
    assert is_valid_empty_name is False
    assert "extension" in msg_empty_name.lower()

def test_extract_text_unsupported_format() -> None:
    content = b"Some resume content"

    with pytest.raises(ValueError) as exc_info_unsupported:
        extract_text(content, "resume.txt")
    assert "unsupported" in str(exc_info_unsupported.value).lower()

    with pytest.raises(ValueError) as exc_info_no_ext:
        extract_text(content, "resumefile")
    assert "extension" in str(exc_info_no_ext.value).lower()

def test_extract_text_from_pdf_empty() -> None:
    with pytest.raises(ValueError) as exc_info:
        extract_text_from_pdf(b"")

    assert "empty" in str(exc_info.value).lower()

def test_extract_text_from_docx_empty() -> None:
    with pytest.raises(ValueError) as exc_info:
        extract_text_from_docx(b"")

    assert "empty" in str(exc_info.value).lower()

def test_extract_text_dispatches_pdf() -> None:
    sample_text = "Senior Python Engineer Resume Content"
    pdf_bytes = _create_sample_pdf(sample_text)

    result = extract_text(pdf_bytes, "arjun_resume.pdf")

    assert isinstance(result, dict)
    assert result.get("source_format") == "pdf"
    assert sample_text in result.get("text", "")
    assert result.get("num_pages") == 1
    assert "is_scanned" in result
    assert isinstance(result.get("metadata"), dict)

def test_extract_text_dispatches_docx() -> None:
    sample_text = "Full Stack Developer Resume with React and Node.js"
    docx_bytes = _create_sample_docx(sample_text)

    result = extract_text(docx_bytes, "arjun_resume.docx")

    assert isinstance(result, dict)
    assert result.get("source_format") == "docx"
    assert sample_text in result.get("text", "")
    assert result.get("num_paragraphs", 0) >= 1
    assert isinstance(result.get("metadata"), dict)

def test_extract_text_from_pdf_corrupt() -> None:
    corrupt_bytes = b"Not a real PDF header or document content"

    with pytest.raises(ValueError) as exc_info:
        extract_text_from_pdf(corrupt_bytes)

    assert "failed to open pdf document" in str(exc_info.value).lower()

def test_extract_text_from_docx_corrupt() -> None:
    corrupt_bytes = b"Not a real ZIP/DOCX archive"

    with pytest.raises(ValueError) as exc_info:
        extract_text_from_docx(corrupt_bytes)

    assert "failed to open docx document" in str(exc_info.value).lower()
