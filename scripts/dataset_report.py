import argparse
import math
from pathlib import Path

from pypdf import PdfReader


def estimate_tokens(text_chars: int) -> int:
    # Rough estimate: ~4 characters per token for English text.
    return max(0, math.ceil(text_chars / 4))


def estimate_embedding_storage(tokens: int, dimensions: int = 1536) -> int:
    # float32 = 4 bytes per dimension.
    return tokens * dimensions * 4


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-pages", type=int, default=1000)
    args = parser.parse_args()

    raw_dir = Path("data/raw")
    pdfs = sorted(raw_dir.rglob("*.pdf"))

    total_pages = 0
    total_chars = 0

    print(f"PDF files: {len(pdfs)}")
    print()

    for pdf in pdfs:
        try:
            reader = PdfReader(str(pdf))
            pages = len(reader.pages)
            chars = 0

            for page in reader.pages:
                text = page.extract_text() or ""
                chars += len(text)

            total_pages += pages
            total_chars += chars

            print(f"{pdf.name}: {pages} pages, {chars:,} characters")

        except Exception as exc:
            print(f"{pdf.name}: ERROR - {exc}")

    tokens = estimate_tokens(total_chars)
    embedding_bytes = estimate_embedding_storage(tokens)

    full_pages = args.full_pages
    avg_chars_per_page = total_chars / total_pages if total_pages else 0
    estimated_full_chars = avg_chars_per_page * full_pages
    estimated_full_tokens = estimate_tokens(round(estimated_full_chars))
    estimated_full_embedding_bytes = estimate_embedding_storage(estimated_full_tokens)

    print()
    print("=== Dataset Summary ===")
    print(f"Total pages: {total_pages:,}")
    print(f"Extracted characters: {total_chars:,}")
    print(f"Estimated tokens: {tokens:,}")
    print(f"Estimated embedding storage: {embedding_bytes / (1024**2):.2f} MiB")

    print()
    print(f"=== {full_pages:,}-Page Capacity Estimate ===")
    print(f"Estimated characters: {estimated_full_chars:,.0f}")
    print(f"Estimated tokens: {estimated_full_tokens:,}")
    print(f"Estimated embedding storage: {estimated_full_embedding_bytes / (1024**3):.2f} GiB")


if __name__ == "__main__":
    main()
