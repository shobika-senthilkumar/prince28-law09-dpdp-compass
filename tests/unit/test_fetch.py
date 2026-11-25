import asyncio
import hashlib

import httpx
import pytest

from dpdpcompass.ingest import fetch as fetch_module
from dpdpcompass.ingest.fetch import (
    DownloadError,
    HostGate,
    Manifest,
    Robots,
    Source,
    backoff_delay,
    fetch_all,
    fetch_one,
    file_stem,
    pick_ext,
    read_sources,
    retry_after_seconds,
    slug,
)


def test_slug_normalizes_text():
    assert slug("India Code / DPDP Act") == "india-code-dpdp-act"


def test_slug_has_fallback_for_empty_text():
    assert slug(" !!! ") == "source"


def test_file_stem_is_stable():
    url = "https://example.org/DPDP%20Act.pdf"
    expected_hash = hashlib.sha256(url.encode()).hexdigest()[:8]

    assert file_stem(url) == f"dpdp-act-{expected_hash}"
    assert file_stem(url) == file_stem(url)


def test_pick_ext_uses_known_url_extension():
    assert (
        pick_ext(
            "https://example.org/document.pdf",
            "application/octet-stream",
        )
        == ".pdf"
    )


def test_pick_ext_uses_content_type():
    assert (
        pick_ext(
            "https://example.org/download",
            "application/pdf; charset=binary",
        )
        == ".pdf"
    )


def test_backoff_delay_stays_within_cap(monkeypatch):
    monkeypatch.setattr(
        fetch_module.random,
        "uniform",
        lambda low, high: high,
    )

    assert backoff_delay(3, base=1, cap=5) == 5


def test_retry_after_parses_seconds():
    assert retry_after_seconds("12") == 12.0


def test_retry_after_rejects_invalid_value():
    assert retry_after_seconds("not-a-date") is None
    assert retry_after_seconds(None) is None


def test_read_sources_ignores_comments_and_duplicates(tmp_path):
    path = tmp_path / "sources.csv"
    path.write_text(
        "# comment\n"
        "url,source,licence,title\n"
        "https://example.org/a.pdf,test,Public notice,A\n"
        "https://example.org/a.pdf,test,Public notice,A duplicate\n",
        encoding="utf-8",
    )

    sources = read_sources(path)

    assert len(sources) == 1
    assert sources[0].source == "test"
    assert sources[0].licence == "Public notice"


def test_read_sources_rejects_non_http_url(tmp_path):
    path = tmp_path / "sources.csv"
    path.write_text(
        "url,source,licence,title\nftp://example.org/a.pdf,test,Public notice,A\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="http"):
        read_sources(path)


def test_read_sources_requires_licence(tmp_path):
    path = tmp_path / "sources.csv"
    path.write_text(
        "url,source,licence,title\nhttps://example.org/a.pdf,test,,A\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="licence"):
        read_sources(path)


def test_manifest_roundtrip_and_done(tmp_path):
    target = tmp_path / "data" / "raw" / "test" / "a.pdf"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"document")

    manifest = Manifest(tmp_path / "data" / "manifest.jsonl")
    manifest.add(
        {
            "url": "https://example.org/a.pdf",
            "status": "downloaded",
            "path": target.relative_to(tmp_path).as_posix(),
        }
    )

    restored = Manifest(tmp_path / "data" / "manifest.jsonl")

    assert restored.done("https://example.org/a.pdf", tmp_path)


def test_manifest_not_done_when_file_is_missing(tmp_path):
    manifest = Manifest(tmp_path / "data" / "manifest.jsonl")
    manifest.add(
        {
            "url": "https://example.org/a.pdf",
            "status": "downloaded",
            "path": "data/raw/test/a.pdf",
        }
    )

    assert not manifest.done(
        "https://example.org/a.pdf",
        tmp_path,
    )


@pytest.mark.asyncio
async def test_robots_respects_disallow_and_crawl_delay():
    def handler(request):
        return httpx.Response(
            200,
            text=("User-agent: *\nDisallow: /private\nCrawl-delay: 2\n"),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        robots = Robots(client)

        allowed, delay = await robots.check("https://example.org/public")
        blocked, _ = await robots.check("https://example.org/private/file.pdf")

    assert allowed is True
    assert blocked is False
    assert delay == 2.0


@pytest.mark.asyncio
async def test_robots_fails_closed_on_connection_error():
    def handler(request):
        raise httpx.ConnectError(
            "robots unavailable",
            request=request,
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        robots = Robots(client)
        allowed, _ = await robots.check("https://example.org/document.pdf")

    assert allowed is False


@pytest.mark.asyncio
async def test_host_gate_waits_between_requests():
    sleeps = []

    async def fake_sleep(delay):
        sleeps.append(delay)

    gate = HostGate(2.0, fake_sleep)

    await gate.wait("example.org")
    await gate.wait("example.org")

    assert len(sleeps) == 1
    assert 0 < sleeps[0] <= 2.0


@pytest.mark.asyncio
async def test_download_writes_file_and_hash(tmp_path):
    body = b"official document bytes"

    def handler(request):
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/pdf",
                "ETag": '"test-etag"',
            },
            content=body,
        )

    src = Source(
        "https://example.org/act.pdf",
        "test",
        "Public notice",
        "Test Act",
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_module._download(
            client,
            src,
            tmp_path,
            tmp_path / "data" / "raw",
        )

    file_path = tmp_path / result["path"]

    assert file_path.read_bytes() == body
    assert result["bytes"] == len(body)
    assert result["sha256"] == hashlib.sha256(body).hexdigest()
    assert result["etag"] == '"test-etag"'
    assert not file_path.with_name(file_path.name + ".part").exists()


@pytest.mark.asyncio
async def test_download_removes_part_file_when_too_large(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(fetch_module, "MAX_BYTES", 2)

    def handler(request):
        return httpx.Response(
            200,
            headers={"Content-Type": "application/pdf"},
            content=b"too large",
        )

    src = Source(
        "https://example.org/large.pdf",
        "test",
        "Public notice",
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(DownloadError, match="larger than"):
            await fetch_module._download(
                client,
                src,
                tmp_path,
                tmp_path / "data" / "raw",
            )

    raw_dir = tmp_path / "data" / "raw"
    assert not list(raw_dir.rglob("*.part"))


@pytest.mark.asyncio
async def test_fetch_one_retries_temporary_server_error(
    tmp_path,
    monkeypatch,
):
    attempts = 0

    def handler(request):
        nonlocal attempts

        if request.url.path == "/robots.txt":
            return httpx.Response(404)

        attempts += 1
        if attempts == 1:
            return httpx.Response(503)

        return httpx.Response(
            200,
            headers={"Content-Type": "application/pdf"},
            content=b"document",
        )

    monkeypatch.setattr(
        fetch_module,
        "backoff_delay",
        lambda attempt: 0.0,
    )

    async def no_sleep(delay):
        return None

    src = Source(
        "https://example.org/act.pdf",
        "test",
        "Public notice",
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        record = await fetch_one(
            client,
            src,
            root=tmp_path,
            raw_dir=tmp_path / "data" / "raw",
            robots=Robots(client),
            gate=HostGate(0, no_sleep),
            slots=asyncio.Semaphore(2),
            max_attempts=3,
            sleep=no_sleep,
        )

    assert record["status"] == "downloaded"
    assert record["attempts"] == 2
    assert attempts == 2


@pytest.mark.asyncio
async def test_fetch_one_never_downloads_robots_blocked_url(
    tmp_path,
):
    document_requests = 0

    def handler(request):
        nonlocal document_requests

        if request.url.path == "/robots.txt":
            return httpx.Response(
                200,
                text="User-agent: *\nDisallow: /private\n",
            )

        document_requests += 1
        return httpx.Response(200, content=b"document")

    async def no_sleep(delay):
        return None

    src = Source(
        "https://example.org/private/act.pdf",
        "test",
        "Public notice",
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        record = await fetch_one(
            client,
            src,
            root=tmp_path,
            raw_dir=tmp_path / "data" / "raw",
            robots=Robots(client),
            gate=HostGate(0, no_sleep),
            slots=asyncio.Semaphore(1),
            max_attempts=2,
            sleep=no_sleep,
        )

    assert record["status"] == "blocked"
    assert document_requests == 0


@pytest.mark.asyncio
async def test_fetch_all_skips_existing_download(tmp_path):
    target = tmp_path / "data" / "raw" / "test" / "a.pdf"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"already downloaded")

    src = Source(
        "https://example.org/a.pdf",
        "test",
        "Public notice",
    )

    manifest = Manifest(tmp_path / "data" / "manifest.jsonl")
    manifest.add(
        {
            "url": src.url,
            "status": "downloaded",
            "path": target.relative_to(tmp_path).as_posix(),
        }
    )

    counts = await fetch_all([src], root=tmp_path)

    assert counts == {
        "downloaded": 0,
        "skipped": 1,
        "blocked": 0,
        "failed": 0,
    }


@pytest.mark.asyncio
async def test_fetch_all_records_successful_download(tmp_path):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404)

        return httpx.Response(
            200,
            headers={"Content-Type": "application/pdf"},
            content=b"test PDF bytes",
        )

    src = Source(
        "https://example.org/a.pdf",
        "test",
        "Public notice",
        "Test document",
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        counts = await fetch_all(
            [src],
            root=tmp_path,
            per_host_delay=0,
            client=client,
        )

    assert counts["downloaded"] == 1
    assert counts["skipped"] == 0

    manifest = Manifest(tmp_path / "data" / "manifest.jsonl")
    assert manifest.done(src.url, tmp_path)
    assert manifest.records[src.url]["licence"] == "Public notice"


@pytest.mark.asyncio
async def test_fetch_all_rejects_zero_concurrency():
    with pytest.raises(ValueError, match="max_concurrency"):
        await fetch_all(
            [],
            max_concurrency=0,
        )


@pytest.mark.asyncio
async def test_fetch_all_rejects_negative_delay():
    with pytest.raises(ValueError, match="delay"):
        await fetch_all(
            [],
            per_host_delay=-1,
        )


def test_manifest_repairs_incomplete_final_line(tmp_path):
    path = tmp_path / "data" / "manifest.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(
        '{"url":"https://example.org/a.pdf","status":"failed"}',
        encoding="utf-8",
    )

    Manifest(path)

    assert path.read_text(encoding="utf-8").endswith("\n")


def test_read_sources_rejects_unverified_licence(tmp_path):
    path = tmp_path / "sources.csv"
    path.write_text(
        "url,source,licence,title\nhttps://example.org/a.pdf,test,TODO verify,A\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="verify the licence"):
        read_sources(path)


@pytest.mark.asyncio
async def test_download_rejects_non_200_response(tmp_path):
    def handler(request):
        return httpx.Response(404)

    src = Source(
        "https://example.org/missing.pdf",
        "test",
        "Public notice",
    )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(DownloadError) as exc:
            await fetch_module._download(
                client,
                src,
                tmp_path,
                tmp_path / "data" / "raw",
            )

    assert exc.value.code == 404
