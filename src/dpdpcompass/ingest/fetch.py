"""Polite, resumable downloader for the DPDP Compass corpus.

Rules:
1. Check robots.txt before requesting a document.
2. Limit concurrency and space requests to the same host.
3. Use timeouts and retry only temporary failures.
4. Stream to a .part file, then atomically rename on completion.
5. Record completed downloads in data/manifest.jsonl.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import random
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

import httpx
from protego import Protego

CONTACT = "https://github.com/shobika-senthilkumar/prince28-law09-dpdp-compass"
ROBOTS_TOKEN = "examate-student-bot"
USER_AGENT = f"{ROBOTS_TOKEN}/0.1 (student project; +{CONTACT})"

RETRYABLE = {408, 425, 429, 500, 502, 503, 504}
MAX_WAIT = 120.0
MAX_BYTES = 200 * 1024 * 1024
ATTEMPT_TIMEOUT = 300.0

KNOWN_EXT = {
    ".pdf",
    ".html",
    ".htm",
    ".json",
    ".txt",
    ".md",
    ".mdx",
    ".rst",
    ".adoc",
    ".xml",
    ".yaml",
    ".yml",
    ".zip",
    ".docx",
    ".xlsx",
    ".xls",
    ".csv",
}

EXT_BY_TYPE = {
    "application/pdf": ".pdf",
    "text/html": ".html",
    "application/json": ".json",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/csv": ".csv",
    "application/xml": ".xml",
    "text/xml": ".xml",
    "application/zip": ".zip",
    "application/yaml": ".yaml",
}

Sleep = Callable[[float], Awaitable[None]]


@dataclass(frozen=True)
class Source:
    url: str
    source: str
    licence: str
    title: str = ""


class DownloadError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retry_after = retry_after


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def slug(value: str, limit: int = 60) -> str:
    """Return a filesystem-safe lowercase name."""
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result[:limit] or "source"


def file_stem(url: str) -> str:
    """Return a stable readable filename based on a URL."""
    parts = urlsplit(url)
    last = unquote(parts.path.rstrip("/").rsplit("/", 1)[-1]) or parts.netloc
    name = last.rsplit(".", 1)[0] if "." in last else last
    fingerprint = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"{slug(name)}-{fingerprint}"


def pick_ext(url: str, content_type: str) -> str:
    """Choose a known extension from the URL or MIME type."""
    suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix in KNOWN_EXT:
        return suffix
    media_type = content_type.split(";")[0].strip().lower()
    return EXT_BY_TYPE.get(media_type, ".bin")


def backoff_delay(
    attempt: int,
    *,
    base: float = 1.0,
    cap: float = 60.0,
) -> float:
    """Exponential backoff with full jitter."""
    ceiling = min(cap, base * 2**attempt)
    return random.uniform(0.0, ceiling)


def retry_after_seconds(value: str | None) -> float | None:
    """Parse Retry-After as seconds or an HTTP date."""
    if not value:
        return None

    value = value.strip()
    if value.isdigit():
        return float(value)

    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)

    return max(
        0.0,
        (when - datetime.now(UTC)).total_seconds(),
    )


def read_sources(path: Path) -> list[Source]:
    """Read and validate data/sources.csv."""
    sources: list[Source] = []
    seen: set[str] = set()

    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {path}")

    with path.open(encoding="utf-8-sig", newline="") as handle:
        lines = (line for line in handle if line.strip() and not line.lstrip().startswith("#"))
        reader = csv.DictReader(lines)
        required = {"url", "source", "licence"}

        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("sources.csv must have url, source, licence, and title columns")

        for number, row in enumerate(reader, start=1):
            url = (row.get("url") or "").strip()
            name = (row.get("source") or "").strip()
            licence = (row.get("licence") or "").strip()
            title = (row.get("title") or "").strip()

            parts = urlsplit(url)
            if parts.scheme not in {"http", "https"} or not parts.netloc:
                raise ValueError(f"sources row {number}: not an http(s) URL")
            if not name or not licence:
                raise ValueError(f"sources row {number}: source and licence are required")
            if licence.upper().startswith("TODO"):
                raise ValueError(f"sources row {number}: verify the licence before downloading")

            if url not in seen:
                seen.add(url)
                sources.append(Source(url, name, licence, title))

    return sources


class Manifest:
    """Append-only log; the latest record for each URL wins."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.records: dict[str, dict] = {}

        if not path.exists():
            return

        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = record.get("url")
            if isinstance(url, str):
                self.records[url] = record

        if text and not text.endswith("\n"):
            with path.open("a", encoding="utf-8") as handle:
                handle.write("\n")

    def done(self, url: str, root: Path) -> bool:
        record = self.records.get(url, {})
        if record.get("status") != "downloaded":
            return False

        relative = record.get("path")
        if not isinstance(relative, str):
            return False

        root_resolved = root.resolve()
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            return False

        return candidate.is_file()

    def add(self, record: dict) -> None:
        self.records[record["url"]] = record
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class Robots:
    """Fetch robots.txt once per origin and apply its rules."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._rules: dict[str, Protego | None] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def _load(self, origin: str) -> Protego | None:
        try:
            response = await self._client.get(origin + "/robots.txt")
        except httpx.HTTPError:
            return None

        if response.status_code == 429 or response.status_code >= 500:
            return None

        if response.status_code >= 400:
            return Protego.parse("")

        return Protego.parse(response.text)

    async def check(self, url: str) -> tuple[bool, float]:
        """Return whether URL is allowed and its crawl delay."""
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"

        lock = self._locks.setdefault(origin, asyncio.Lock())
        async with lock:
            if origin not in self._rules:
                self._rules[origin] = await self._load(origin)

        rules = self._rules[origin]
        if rules is None:
            return False, 0.0

        allowed = rules.can_fetch(url, ROBOTS_TOKEN)
        delay = float(rules.crawl_delay(ROBOTS_TOKEN) or 0.0)
        return allowed, delay


class HostGate:
    """Enforce a delay between requests to the same host."""

    def __init__(self, delay: float, sleep: Sleep) -> None:
        self._delay = delay
        self._sleep = sleep
        self._next_ok: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def wait(
        self,
        host: str,
        crawl_delay: float = 0.0,
    ) -> None:
        lock = self._locks.setdefault(host, asyncio.Lock())
        async with lock:
            pause = self._next_ok.get(host, 0.0) - time.monotonic()
            if pause > 0:
                await self._sleep(pause)

            self._next_ok[host] = time.monotonic() + max(self._delay, crawl_delay)


def make_client(max_concurrency: int = 4) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(30.0, connect=10.0),
        limits=httpx.Limits(max_connections=max_concurrency),
        follow_redirects=True,
    )


async def _download(
    client: httpx.AsyncClient,
    src: Source,
    root: Path,
    raw_dir: Path,
    *,
    etag: str | None = None,
) -> dict:
    """Stream one document to a temporary file, then rename it."""
    headers = {"If-None-Match": etag} if etag else None
    async with client.stream("GET", src.url, headers=headers) as response:
        if response.status_code == 304:
            return {
                "status": "not_modified",
                "http_status": 304,
                "etag": response.headers.get("ETag") or etag,
            }

        if response.status_code != 200:
            raise DownloadError(
                f"HTTP {response.status_code}",
                code=response.status_code,
                retry_after=retry_after_seconds(response.headers.get("Retry-After")),
            )

        content_type = response.headers.get("Content-Type", "")
        name = file_stem(src.url) + pick_ext(src.url, content_type)
        target = raw_dir / slug(src.source) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        part = target.with_name(name + ".part")

        digest = hashlib.sha256()
        size = 0

        try:
            with part.open("wb") as handle:
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise DownloadError(f"larger than {MAX_BYTES // (1024 * 1024)} MB")
                    digest.update(chunk)
                    handle.write(chunk)

            part.replace(target)
        finally:
            part.unlink(missing_ok=True)

    return {
        "path": target.relative_to(root).as_posix(),
        "bytes": size,
        "sha256": digest.hexdigest(),
        "content_type": content_type.split(";")[0].strip(),
        "http_status": 200,
        "etag": response.headers.get("ETag"),
    }


async def fetch_one(
    client: httpx.AsyncClient,
    src: Source,
    *,
    root: Path,
    raw_dir: Path,
    robots: Robots,
    gate: HostGate,
    slots: asyncio.Semaphore,
    max_attempts: int,
    sleep: Sleep,
    previous: dict | None = None,
) -> dict:
    """Download one source with robots checks and selective retries."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    record = {
        "url": src.url,
        "source": src.source,
        "licence": src.licence,
        "title": src.title,
        "via": "http",
    }

    allowed, crawl_delay = await robots.check(src.url)
    if not allowed:
        return record | {
            "status": "blocked",
            "error": "robots.txt disallows this URL or could not be read",
            "fetched_at": now_iso(),
        }

    host = urlsplit(src.url).netloc
    error = ""
    code: int | None = None

    for attempt in range(1, max_attempts + 1):
        wait = backoff_delay(attempt - 1)

        try:
            async with slots:
                await gate.wait(host, crawl_delay)
                async with asyncio.timeout(ATTEMPT_TIMEOUT):
                    fields = await _download(
                        client,
                        src,
                        root,
                        raw_dir,
                        etag=(previous or {}).get("etag"),
                    )

            if fields.get("status") == "not_modified":
                return (
                    record
                    | (previous or {})
                    | fields
                    | {
                        "status": "downloaded",
                        "attempts": attempt,
                        "fetched_at": now_iso(),
                    }
                )

            return (
                record
                | fields
                | {
                    "status": "downloaded",
                    "attempts": attempt,
                    "fetched_at": now_iso(),
                }
            )

        except DownloadError as exc:
            error, code = str(exc), exc.code
            if code not in RETRYABLE:
                break

            if exc.retry_after is not None:
                if exc.retry_after > MAX_WAIT:
                    error = (
                        f"{error}: server asked us to wait {exc.retry_after:.0f}s; run again later"
                    )
                    break
                wait = max(wait, exc.retry_after)

        except (httpx.TransportError, TimeoutError) as exc:
            error, code = type(exc).__name__, None

        except httpx.HTTPError as exc:
            error, code = type(exc).__name__, None
            break

        if attempt < max_attempts:
            await sleep(min(wait, MAX_WAIT))

    return record | {
        "status": "failed",
        "http_status": code,
        "error": error,
        "attempts": attempt,
        "fetched_at": now_iso(),
    }


async def fetch_all(
    sources: list[Source],
    *,
    root: Path = Path("."),
    max_concurrency: int = 4,
    per_host_delay: float = 0.5,
    max_attempts: int = 4,
    client: httpx.AsyncClient | None = None,
    sleep: Sleep = asyncio.sleep,
    on_result: Callable[[dict], None] | None = None,
) -> dict[str, int]:
    """Download pending sources and append completed manifest records."""
    if max_concurrency < 1:
        raise ValueError("max_concurrency must be at least 1")
    if per_host_delay < 0:
        raise ValueError("per_host_delay cannot be negative")

    raw_dir = root / "data" / "raw"
    manifest = Manifest(root / "data" / "manifest.jsonl")
    todo = [src for src in sources if not manifest.done(src.url, root)]

    counts = {
        "downloaded": 0,
        "skipped": len(sources) - len(todo),
        "blocked": 0,
        "failed": 0,
    }

    if not todo:
        return counts

    own_client = client is None
    active_client = client or make_client(max_concurrency)
    robots = Robots(active_client)
    gate = HostGate(per_host_delay, sleep)
    slots = asyncio.Semaphore(max_concurrency)

    tasks = [
        asyncio.create_task(
            fetch_one(
                active_client,
                src,
                root=root,
                raw_dir=raw_dir,
                robots=robots,
                gate=gate,
                slots=slots,
                max_attempts=max_attempts,
                sleep=sleep,
            )
        )
        for src in todo
    ]

    try:
        for finished in asyncio.as_completed(tasks):
            record = await finished
            status = record["status"]
            counts[status] += 1

            previous = manifest.records.get(record["url"], {})
            same_problem = (
                previous.get("status"),
                previous.get("error"),
            ) == (
                status,
                record.get("error"),
            )

            if status == "downloaded" or not same_problem:
                manifest.add(record)

            if on_result:
                on_result(record)

    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise

    finally:
        if own_client:
            await active_client.aclose()

    return counts
