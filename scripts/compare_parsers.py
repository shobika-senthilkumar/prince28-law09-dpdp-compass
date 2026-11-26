from __future__ import annotations

from pathlib import Path

from dpdpcompass.ingest.parse import parse_pdf_pymupdf, parse_pdf_pypdf


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    pdfs = sorted((root / "data" / "raw").rglob("*.pdf"))[:10]

    if not pdfs:
        print("No PDF files found.")
        return 1

    print("Parser comparison")
    print("=" * 80)

    for index, path in enumerate(pdfs, start=1):
        try:
            pymupdf_doc = parse_pdf_pymupdf(path)
            pypdf_doc = parse_pdf_pypdf(path)

            pymupdf_text = sum(len(page.text) for page in pymupdf_doc.pages)
            pypdf_text = sum(len(page.text) for page in pypdf_doc.pages)

            print(f"\n[{index}/10] {path.relative_to(root)}")
            print(f"  PyMuPDF: pages={len(pymupdf_doc.pages)}, text_chars={pymupdf_text}")
            print(f"  pypdf:   pages={len(pypdf_doc.pages)}, text_chars={pypdf_text}")

            if len(pymupdf_doc.pages) == len(pypdf_doc.pages):
                print("  Verdict: page counts match")
            else:
                print("  Verdict: page counts differ")

        except Exception as exc:
            print(f"\n[{index}/10] {path.relative_to(root)}")
            print(f"  Verdict: comparison failed - {type(exc).__name__}: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
