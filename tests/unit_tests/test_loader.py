from __future__ import annotations

from typing import Any

import pytest

from langchain_hydrafetch import HydrafetchLoader

SCRAPE_PAYLOAD = {
    "data": {
        "url": "https://example.com",
        "finalUrl": "https://example.com/",
        "status": 200,
        "markdown": "# Example\n\nBody text.",
        "metadata": {
            "title": "Example",
            "description": "An example page.",
            "language": "en",
            "siteName": "Example",
            "wordCount": 3,
            "pageType": "article",
            "publishedTime": "2026-08-01T00:00:00Z",
        },
    }
}

MAP_PAYLOAD = {
    "data": {
        "url": "https://example.com",
        "links": [
            {"url": "https://example.com/a", "lastmod": "2026-08-01"},
            {"url": "https://example.com/b"},
            {"nope": True},
        ],
        "count": 2,
    }
}

CRAWL_PAYLOAD = {
    "data": {
        "status": "completed",
        "pages": [
            {
                "url": "https://example.com/a",
                "depth": 1,
                "data": {"url": "https://example.com/a", "markdown": "A", "metadata": {}},
            },
            {"url": "https://example.com/failed", "status": "failed", "data": None},
        ],
    }
}


class FakeClient:
    def __init__(self, **payloads: Any) -> None:
        self.payloads = payloads
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _record(self, name: str, *args: Any, **kwargs: Any) -> Any:
        self.calls.append((name, args, kwargs))
        return self.payloads[name]

    def scrape(self, *args: Any, **kwargs: Any) -> Any:
        return self._record("scrape", *args, **kwargs)

    def map(self, *args: Any, **kwargs: Any) -> Any:
        return self._record("map", *args, **kwargs)

    def crawl(self, *args: Any, **kwargs: Any) -> Any:
        return self._record("crawl", *args, **kwargs)


@pytest.fixture
def patch_client(monkeypatch: pytest.MonkeyPatch):
    def _apply(**payloads: Any) -> FakeClient:
        fake = FakeClient(**payloads)
        monkeypatch.setattr(
            "langchain_hydrafetch.document_loaders.build_client", lambda *a, **k: fake
        )
        return fake

    return _apply


def test_scrape_mode_maps_content_and_metadata(patch_client) -> None:
    patch_client(scrape=SCRAPE_PAYLOAD)
    docs = HydrafetchLoader("https://example.com", api_key="k").load()

    assert len(docs) == 1
    assert docs[0].page_content == "# Example\n\nBody text."
    assert docs[0].metadata["source"] == "https://example.com"
    assert docs[0].metadata["title"] == "Example"
    assert docs[0].metadata["site_name"] == "Example"
    assert docs[0].metadata["published_time"] == "2026-08-01T00:00:00Z"
    assert docs[0].metadata["status"] == 200


def test_scrape_mode_requests_the_chosen_format(patch_client) -> None:
    fake = patch_client(scrape=SCRAPE_PAYLOAD)
    HydrafetchLoader("https://example.com", api_key="k", content_format="html").load()

    assert fake.calls[0][2]["formats"] == ["html"]


def test_map_mode_yields_one_document_per_link(patch_client) -> None:
    patch_client(map=MAP_PAYLOAD)
    docs = HydrafetchLoader("https://example.com", mode="map", api_key="k").load()

    assert [d.page_content for d in docs] == ["https://example.com/a", "https://example.com/b"]
    assert docs[0].metadata["lastmod"] == "2026-08-01"


def test_crawl_mode_skips_pages_without_data(patch_client) -> None:
    patch_client(crawl=CRAWL_PAYLOAD)
    docs = HydrafetchLoader("https://example.com", mode="crawl", api_key="k").load()

    assert len(docs) == 1
    assert docs[0].metadata["depth"] == 1


def test_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="mode must be"):
        HydrafetchLoader("https://example.com", mode="nope", api_key="k")


def test_lazy_load_does_not_materialise_everything(patch_client) -> None:
    patch_client(map=MAP_PAYLOAD)
    stream = HydrafetchLoader("https://example.com", mode="map", api_key="k").lazy_load()

    assert next(stream).page_content == "https://example.com/a"


NOT_FOUND_PAYLOAD = {
    "data": {
        "url": "https://example.com/gone",
        "status": 404,
        "markdown": "# Page Not Found",
        "metadata": {"title": "Page Not Found"},
    }
}

CRAWL_WITH_404 = {
    "data": {
        "status": "completed",
        "pages": [
            {"url": "https://ex.com/a", "data": {"url": "a", "status": 200, "markdown": "A"}},
            {"url": "https://ex.com/b", "data": {"url": "b", "status": 404, "markdown": "B"}},
        ],
    }
}


def test_scrape_refuses_an_error_page_by_default(patch_client) -> None:
    patch_client(scrape=NOT_FOUND_PAYLOAD)
    with pytest.raises(ValueError, match="HTTP 404"):
        HydrafetchLoader("https://example.com/gone", api_key="k").load()


def test_scrape_loads_an_error_page_when_asked(patch_client) -> None:
    patch_client(scrape=NOT_FOUND_PAYLOAD)
    docs = HydrafetchLoader("https://example.com/gone", api_key="k", raise_for_status=False).load()

    assert docs[0].metadata["status"] == 404


def test_crawl_drops_error_pages_rather_than_failing_the_job(patch_client) -> None:
    patch_client(crawl=CRAWL_WITH_404)
    docs = HydrafetchLoader("https://example.com", mode="crawl", api_key="k").load()

    assert [d.page_content for d in docs] == ["A"]


def test_crawl_keeps_error_pages_when_asked(patch_client) -> None:
    patch_client(crawl=CRAWL_WITH_404)
    docs = HydrafetchLoader(
        "https://example.com", mode="crawl", api_key="k", raise_for_status=False
    ).load()

    assert [d.page_content for d in docs] == ["A", "B"]
