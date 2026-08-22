from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Literal

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from ._common import build_client, page_to_document, unwrap

Mode = Literal["scrape", "crawl", "map"]


class HydrafetchLoader(BaseLoader):
    """Load web pages as LangChain documents via the Hydrafetch API."""

    def __init__(
        self,
        url: str,
        *,
        mode: Mode = "scrape",
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        content_format: str = "markdown",
        raise_for_status: bool = True,
        params: dict[str, Any] | None = None,
    ) -> None:
        if mode not in ("scrape", "crawl", "map"):
            raise ValueError(f"mode must be 'scrape', 'crawl' or 'map', got {mode!r}")
        self.url = url
        self.mode = mode
        self.content_format = content_format
        self.raise_for_status = raise_for_status
        self.params = params or {}
        self._client = build_client(api_key, base_url, timeout, max_retries)

    def lazy_load(self) -> Iterator[Document]:
        if self.mode == "scrape":
            yield from self._load_scrape()
        elif self.mode == "map":
            yield from self._load_map()
        else:
            yield from self._load_crawl()

    def _load_scrape(self) -> Iterator[Document]:
        data = unwrap(self._client.scrape(self.url, **self._scrape_params()))
        if self.raise_for_status and not _ok(data):
            raise ValueError(
                f"{self.url} returned HTTP {data.get('status')}. The body of an error page is "
                "not the page you asked for; pass raise_for_status=False to load it anyway."
            )
        yield page_to_document(data, self.content_format)

    def _load_map(self) -> Iterator[Document]:
        data = unwrap(self._client.map(self.url, **self.params))
        for entry in data.get("links") or []:
            if not isinstance(entry, dict):
                continue
            found = entry.get("url")
            if not found:
                continue
            metadata: dict[str, Any] = {"source": found}
            if entry.get("lastmod"):
                metadata["lastmod"] = entry["lastmod"]
            yield Document(page_content=found, metadata=metadata)

    def _load_crawl(self) -> Iterator[Document]:
        job = unwrap(self._client.crawl(self.url, **self._scrape_params()))
        for page in job.get("pages") or []:
            if not isinstance(page, dict):
                continue
            data = page.get("data")
            if not isinstance(data, dict):
                continue
            data.setdefault("url", page.get("url") or page.get("requestedUrl"))
            if self.raise_for_status and not _ok(data):
                continue
            document = page_to_document(data, self.content_format)
            if page.get("depth") is not None:
                document.metadata["depth"] = page["depth"]
            yield document

    def _scrape_params(self) -> dict[str, Any]:
        params = dict(self.params)
        params.setdefault("formats", [self.content_format])
        return params


def _ok(data: dict[str, Any]) -> bool:
    status = data.get("status")
    if status is None:
        return True
    try:
        return 200 <= int(status) < 300
    except (TypeError, ValueError):
        return True
