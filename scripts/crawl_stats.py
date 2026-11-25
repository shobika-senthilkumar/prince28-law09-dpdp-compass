import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    manifest_path = Path("data/manifest.jsonl")
    groups = defaultdict(list)

    with manifest_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") == "downloaded":
                groups[record.get("source", "unknown")].append(record)

    print("Crawl statistics")
    print("=================")

    total_files = 0
    total_bytes = 0
    multi_attempt = 0

    for source, records in sorted(groups.items()):
        files = len(records)
        size = sum(int(record.get("bytes", 0) or 0) for record in records)
        total_files += files
        total_bytes += size
        multi_attempt += sum(1 for record in records if int(record.get("attempts", 0) or 0) > 1)

        print(f"{source}: files={files}, MB={size / (1024 * 1024):.2f}")

    print(f"Total files: {total_files}")
    print(f"Total MB: {total_bytes / (1024 * 1024):.2f}")
    print(f"Documents needing more than one attempt: {multi_attempt}")

    print("Slowest site: unavailable (manifest has no duration data)")


if __name__ == "__main__":
    main()
