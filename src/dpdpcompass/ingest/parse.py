from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf
import pytesseract
import trafilatura
from pypdf import PdfReader

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class ParseError(Exception):
    """Raised when a source file cannot be parsed."""


@dataclass
class ParsedPage:
    page_no: int
    text: str
    headings: list[str]


@dataclass
class ParsedDoc:
    path: str
    doc_type: str
    text: str
    pages: list[ParsedPage]
    metadata: dict[str, Any]


def _heading_path(lines: list[str], index: int) -> list[str]:
    """Return the simple heading path active at a given line."""
    headings: list[str] = []

    for line in lines[: index + 1]:
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                level = len(stripped) - len(stripped.lstrip("#"))
                headings = headings[: max(0, level - 1)]
                headings.append(heading)

    return headings


def _parse_text(content: str) -> ParsedDoc:
    """Parse Markdown, plain text, or data files."""
    lines = content.splitlines()
    headings: list[str] = []
    pages: list[ParsedPage] = []

    for _index, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                level = len(stripped) - len(stripped.lstrip("#"))
                headings = headings[: max(0, level - 1)]
                headings.append(heading)

    pages.append(
        ParsedPage(
            page_no=1,
            text=content,
            headings=headings,
        )
    )

    return ParsedDoc(
        path="",
        doc_type="text",
        text=content,
        pages=pages,
        metadata={"parser": "text", "pages": 1},
    )


def _ocr_page(page: pymupdf.Page, language: str = "eng") -> str:
    """Render a PDF page and extract text using Tesseract OCR."""
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
    image = pixmap.tobytes("png")

    from io import BytesIO

    from PIL import Image

    return pytesseract.image_to_string(
        Image.open(BytesIO(image)),
        lang=language,
    ).strip()


def parse_pdf_pymupdf(path: Path) -> ParsedDoc:
    """Parse a PDF using PyMuPDF."""
    try:
        document = pymupdf.open(path)
    except Exception as exc:
        raise ParseError(f"Could not open PDF: {exc}") from exc

    pages: list[ParsedPage] = []
    text_parts: list[str] = []
    ocr_pages: list[int] = []

    try:
        for index, page in enumerate(document):
            text = page.get_text("text").strip()

            if len(text) < 20:
                text = _ocr_page(page)
                if text:
                    ocr_pages.append(index + 1)
            text_parts.append(text)

            pages.append(
                ParsedPage(
                    page_no=index + 1,
                    text=text,
                    headings=[],
                )
            )
    finally:
        document.close()

    full_text = "\n\n".join(part for part in text_parts if part)

    if not full_text.strip():
        raise ParseError("no_text_layer")

    return ParsedDoc(
        path=str(path),
        doc_type="pdf",
        text=full_text,
        pages=pages,
        metadata={
            "parser": "pymupdf",
            "pages": len(pages),
            "ocr_pages": ocr_pages,
        },
    )


def parse_pdf_pypdf(path: Path) -> ParsedDoc:
    """Parse a PDF using pypdf."""
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise ParseError(f"Could not open PDF: {exc}") from exc

    pages: list[ParsedPage] = []
    text_parts: list[str] = []

    for index, page in enumerate(reader.pages):
        try:
            text = (page.extract_text() or "").strip()
        except Exception as exc:
            raise ParseError(f"Failed to extract page {index + 1}: {exc}") from exc

        text_parts.append(text)

        pages.append(
            ParsedPage(
                page_no=index + 1,
                text=text,
                headings=[],
            )
        )

    full_text = "\n\n".join(part for part in text_parts if part)

    if not full_text.strip():
        raise ParseError("no_text_layer")

    return ParsedDoc(
        path=str(path),
        doc_type="pdf",
        text=full_text,
        pages=pages,
        metadata={
            "parser": "pypdf",
            "pages": len(pages),
        },
    )


def parse_html(path: Path) -> ParsedDoc:
    """Parse HTML using trafilatura."""
    content = path.read_text(encoding="utf-8", errors="replace")

    extracted = trafilatura.extract(
        content,
        include_links=True,
        include_tables=True,
    )

    if not extracted:
        raise ParseError("empty")

    return ParsedDoc(
        path=str(path),
        doc_type="html",
        text=extracted,
        pages=[
            ParsedPage(
                page_no=1,
                text=extracted,
                headings=[],
            )
        ],
        metadata={
            "parser": "trafilatura",
            "pages": 1,
        },
    )


def parse_file(path: Path) -> ParsedDoc:
    """Parse one supported source file."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return parse_pdf_pymupdf(path)

    if suffix in {".html", ".htm"}:
        return parse_html(path)

    if suffix in {
        ".md",
        ".txt",
        ".csv",
        ".json",
        ".jsonl",
        ".xml",
    }:
        content = path.read_text(encoding="utf-8", errors="replace")
        parsed = _parse_text(content)
        parsed.path = str(path)
        parsed.doc_type = suffix.lstrip(".")
        parsed.metadata["parser"] = "text"
        return parsed

    raise ParseError("unsupported_type")
