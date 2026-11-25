import json
from collections import defaultdict
from pathlib import Path

MANIFEST = Path("data/manifest.jsonl")


def main() -> None:
    groups: dict[str, list[dict]] = defaultdict(list)

    with MANIFEST.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)

            if record.get("status") != "downloaded":
                continue

            sha256 = record.get("sha256")
            if sha256:
                groups[sha256].append(record)

    duplicates = {sha256: records for sha256, records in groups.items() if len(records) > 1}

    print(f"Downloaded documents: {sum(len(records) for records in groups.values())}")
    print(f"Unique SHA-256 hashes: {len(groups)}")
    print(f"Duplicate content groups: {len(duplicates)}")

    for sha256, records in duplicates.items():
        print(f"\nSHA-256: {sha256}")
        print(f"Copies: {len(records)}")

        for record in records:
            print(f"  URL: {record.get('url')}")
            print(f"  Path: {record.get('path')}")


if __name__ == "__main__":
    main()
