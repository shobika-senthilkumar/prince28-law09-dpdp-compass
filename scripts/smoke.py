"""Smoke test the live DPDP Compass deployment."""

import sys

import httpx


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/smoke.py <base-url>")
        return 1

    base_url = sys.argv[1].rstrip("/")

    checks = [
        ("/health", "health"),
        ("/ready", "ready"),
        ("/v1/documents?limit=1", "documents"),
    ]

    with httpx.Client(timeout=30.0) as client:
        for path, name in checks:
            response = client.get(f"{base_url}{path}")
            response.raise_for_status()

            if name == "health":
                data = response.json()
                print(f"ok /health -> {response.status_code}, version {data.get('version')}")
            elif name == "ready":
                print(f"ok /ready -> {response.status_code} {response.json()}")
            else:
                print(f"ok /v1/documents?limit=1 -> {response.status_code}")

    print("Smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
