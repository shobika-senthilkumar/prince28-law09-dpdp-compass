from __future__ import annotations

from pathlib import Path

from dpdpcompass.ingest.parse import parse_pdf_pymupdf, parse_pdf_pypdf


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    notes_path = root / "NOTES.md"
    pdfs = sorted((root / "data" / "raw").rglob("*.pdf"))[:10]

    if not pdfs:
        print("No PDF files found.")
        return 1

    rows: list[str] = []
    results: list[tuple[str, int, int, int, int, str]] = []

    print("Parser comparison")
    print("=" * 80)

    for index, path in enumerate(pdfs, start=1):
        relative_path = path.relative_to(root)

        try:
            pymupdf_doc = parse_pdf_pymupdf(path)
            pypdf_doc = parse_pdf_pypdf(path)

            pymupdf_pages = len(pymupdf_doc.pages)
            pypdf_pages = len(pypdf_doc.pages)
            pymupdf_text = sum(len(page.text) for page in pymupdf_doc.pages)
            pypdf_text = sum(len(page.text) for page in pypdf_doc.pages)

            if pymupdf_pages != pypdf_pages:
                verdict = "Page counts differ; investigate before choosing"
            elif pymupdf_text > pypdf_text:
                verdict = "PyMuPDF preferred; more extracted text"
            elif pypdf_text > pymupdf_text:
                verdict = "PyMuPDF preferred for consistency; pypdf extracted more text"
            else:
                verdict = "Equivalent extraction; PyMuPDF retained for consistency"

            results.append(
                (
                    relative_path.name,
                    pymupdf_pages,
                    pypdf_pages,
                    pymupdf_text,
                    pypdf_text,
                    verdict,
                )
            )

            print(f"\n[{index}/10] {relative_path}")
            print(f"  PyMuPDF: pages={pymupdf_pages}, text_chars={pymupdf_text}")
            print(f"  pypdf:   pages={pypdf_pages}, text_chars={pypdf_text}")
            print(f"  Verdict: {verdict}")

        except Exception as exc:
            verdict = f"Comparison failed: {type(exc).__name__}: {exc}"
            results.append((relative_path.name, 0, 0, 0, 0, verdict))

            print(f"\n[{index}/10] {relative_path}")
            print(f"  Verdict: {verdict}")

    rows.append(
        "Compared PyMuPDF and pypdf on 10 corpus PDFs. "
        "The table below records page counts, extracted text lengths, and the parser verdict."
    )
    rows.append("")
    rows.append(
        "| # | File | PyMuPDF pages | pypdf pages | PyMuPDF chars | pypdf chars | Verdict |"
    )
    rows.append("|---|---|---:|---:|---:|---:|---|")

    for index, (name, pymupdf_pages, pypdf_pages, pymupdf_text, pypdf_text, verdict) in enumerate(
        results, start=1
    ):
        rows.append(
            f"| {index} | {name} | {pymupdf_pages} | {pypdf_pages} | "
            f"{pymupdf_text} | {pypdf_text} | {verdict} |"
        )

    comparison_section = "\n".join(rows)

    notes = notes_path.read_text(encoding="utf-8", errors="replace")

    marker = "### Parser comparison"
    start = notes.find(marker)

    if start == -1:
        notes = notes.rstrip() + "\n\n" + marker + "\n" + comparison_section + "\n"
    else:
        next_section = notes.find("\n### ", start + len(marker))

        end = len(notes) if next_section == -1 else next_section

        notes = notes[:start] + marker + "\n" + comparison_section + "\n" + notes[end:]

    notes_path.write_text(notes, encoding="utf-8")

    print("\nComparison table written to NOTES.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
