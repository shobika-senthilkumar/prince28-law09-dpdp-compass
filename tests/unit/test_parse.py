from pathlib import Path

from dpdpcompass.ingest.parse import (
    ParseError,
    parse_file,
    parse_pdf_pymupdf,
    parse_pdf_pypdf,
)


def test_parse_markdown(tmp_path: Path) -> None:
    path = tmp_path / "sample.md"
    path.write_text("# Title\n\nSome content.", encoding="utf-8")

    result = parse_file(path)

    assert result.doc_type == "md"
    assert result.metadata["parser"] == "text"
    assert result.pages[0].page_no == 1
    assert result.pages[0].text == "# Title\n\nSome content."


def test_parse_text(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("Hello DPDP Compass.", encoding="utf-8")

    result = parse_file(path)

    assert result.doc_type == "txt"
    assert result.text == "Hello DPDP Compass."
    assert result.metadata["pages"] == 1


def test_parse_json(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    path.write_text('{"title": "DPDP"}', encoding="utf-8")

    result = parse_file(path)

    assert result.doc_type == "json"
    assert result.text == '{"title": "DPDP"}'


def test_parse_html(tmp_path: Path) -> None:
    path = tmp_path / "sample.html"
    path.write_text(
        "<html><body><h1>DPDP Compass</h1><p>Hello world.</p></body></html>",
        encoding="utf-8",
    )

    result = parse_file(path)

    assert result.doc_type == "html"
    assert result.metadata["parser"] == "trafilatura"
    assert "Hello world." in result.text


def test_unsupported_type(tmp_path: Path) -> None:
    path = tmp_path / "sample.docx"
    path.write_bytes(b"not supported")

    try:
        parse_file(path)
    except ParseError as exc:
        assert str(exc) == "unsupported_type"
    else:
        raise AssertionError("Expected ParseError")


def test_pdf_parsers_have_same_basic_contract(tmp_path: Path) -> None:
    import pymupdf

    path = tmp_path / "sample.pdf"

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "DPDP Compass test document.")
    document.save(path)
    document.close()

    pymupdf_result = parse_pdf_pymupdf(path)
    pypdf_result = parse_pdf_pypdf(path)

    assert pymupdf_result.doc_type == "pdf"
    assert pypdf_result.doc_type == "pdf"
    assert pymupdf_result.metadata["pages"] == 1
    assert pypdf_result.metadata["pages"] == 1
    assert "DPDP Compass" in pymupdf_result.text
    assert "DPDP Compass" in pypdf_result.text
