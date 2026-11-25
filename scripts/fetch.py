"""Command-line entry point for corpus fetching."""

import argparse
import asyncio
import sys
import time
from pathlib import Path

from dpdpcompass.ingest.fetch import fetch_all, read_sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the DPDP Compass document corpus.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    urls = subparsers.add_parser("urls", help="download URLs in data/sources.csv")
    urls.add_argument(
        "--sources",
        type=Path,
        default=Path("data/sources.csv"),
    )
    urls.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="minimum delay between requests to the same host",
    )
    urls.add_argument(
        "--max-concurrency",
        type=int,
        default=4,
    )
    urls.add_argument(
        "--max-attempts",
        type=int,
        default=4,
    )

    args = parser.parse_args()

    try:
        sources = read_sources(args.sources)
        started = time.perf_counter()
        number = 0

        def report(record: dict) -> None:
            nonlocal number
            number += 1
            status = record["status"]

            if status == "downloaded":
                size = record["bytes"] / 1024
                print(f"[{number:2}] {status:10} {size:8.1f} kB {record['path']}")
            else:
                print(f"[{number:2}] {status:10} {record.get('error', '')} {record['url']}")

        counts = asyncio.run(
            fetch_all(
                sources,
                root=Path("."),
                max_concurrency=args.max_concurrency,
                per_host_delay=args.delay,
                max_attempts=args.max_attempts,
                on_result=report,
            )
        )
        elapsed = time.perf_counter() - started

        print(
            f"sources={len(sources)} "
            f"downloaded={counts['downloaded']} "
            f"skipped={counts['skipped']} "
            f"blocked={counts['blocked']} "
            f"failed={counts['failed']} "
            f"seconds={elapsed:.1f}"
        )
        return 1 if counts["failed"] else 0

    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
