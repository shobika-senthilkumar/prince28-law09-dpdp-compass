import argparse
import csv
import hashlib
import json
import mimetypes
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = (ROOT / "data" / "raw").resolve()


def register(folder, url):
    folder = folder.resolve()

    if not folder.is_relative_to(RAW_ROOT):
        raise ValueError("Folder must be inside data/raw/")

    if not folder.is_dir():
        raise ValueError(f"Folder does not exist: {folder}")

    with (ROOT / "data" / "sources.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(x for x in f if x.strip() and not x.lstrip().startswith("#")))

    source = next((r for r in rows if r["url"].strip() == url), None)
    if not source:
        raise ValueError("URL not found in data/sources.csv")

    for key in ("source", "licence", "title"):
        if not source.get(key, "").strip():
            raise ValueError(f"Missing {key} in sources.csv")

    files = [p for p in folder.rglob("*") if p.is_file() and not p.name.endswith(".part")]

    if len(files) != 1:
        raise ValueError(f"Expected exactly one completed file in {folder}; found {len(files)}")

    path = files[0]
    if path.stat().st_size == 0:
        raise ValueError("File is empty")

    if path.suffix.lower() == ".pdf" and b"%PDF-" not in path.read_bytes()[:1024]:
        raise ValueError("File is not a valid PDF")

    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    manifest = ROOT / "data" / "manifest.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)

    latest = {}
    if manifest.exists():
        with manifest.open(encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    latest[record.get("url")] = record
                except (json.JSONDecodeError, AttributeError):
                    continue

    old = latest.get(url, {})
    if old.get("status") == "downloaded":
        old_path = (ROOT / old.get("path", "")).resolve()
        if old_path.is_file() and old_path.is_relative_to(ROOT):
            print(f"Already registered: {url}")
            return

    record = {
        "url": url,
        "source": source["source"],
        "licence": source["licence"],
        "title": source["title"],
        "status": "downloaded",
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
        "content_type": (
            "application/pdf"
            if path.suffix.lower() == ".pdf"
            else mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        ),
        "http_status": None,
        "etag": None,
        "attempts": 0,
        "method": "manual",
        "downloaded_at": datetime.now(UTC).isoformat(),
    }

    if manifest.exists() and manifest.stat().st_size:
        with manifest.open("rb+") as f:
            f.seek(-1, 2)
            if f.read(1) != b"\n":
                f.write(b"\n")

    with manifest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(
        f"Registered: {path.relative_to(ROOT)} "
        f"({record['bytes']:,} bytes, SHA-256 {record['sha256'][:12]}...)"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--from-url", required=True)
    args = parser.parse_args()

    try:
        register(args.folder, args.from_url)
    except (ValueError, OSError, KeyError) as exc:
        print(f"Registration error: {exc}", file=sys.stderr)
        sys.exit(1)
