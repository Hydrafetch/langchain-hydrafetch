from __future__ import annotations

from typing import Any

import pytest

from langchain_hydrafetch import HydrafetchSearchRetriever

SEARCH_PAYLOAD = {
    "data": {
        "query": "clean web data",
        "status": "ok",
        "results": [
            {"title": "One", "url": "https://a.example", "snippet": "first", "rank": 1},
            {"title": "Two", "url": "https://b.example", "snippet": "second", "rank": 2},
            {"title": "Three", "url": "https://c.example", "snippet": "third", "rank": 3},
        ],
    }
}

SCRAPE_PAYLOAD = {"data": {"url": "https://a.example", "markdown": "full page body"}}


class FakeClient:
    def __init__(self) -> None:
        self.search_calls: list[dict[str, Any]] = []
        self.scraped: list[str] = []

    def search(self, query: str, **kwargs: Any) -> Any:
        self.search_calls.append({"query": query, **kwargs})
        return SEARCH_PAYLOAD

    def scrape(self, url: str, **kwargs: Any) -> Any:
        self.scraped.append(url)
        return SCRAPE_PAYLOAD


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr("langchain_hydrafetch.retrievers.build_client", lambda *a, **k: client)
    return client


def test_returns_snippets_as_documents(fake: FakeClient) -> None:
    docs = HydrafetchSearchRetriever(api_key="k").invoke("clean web data")

    assert [d.page_content for d in docs] == ["first", "second", "third"]
    assert docs[0].metadata == {"source": "https://a.example", "title": "One", "rank": 1}


def test_k_constructor_param_limits_results(fake: FakeClient) -> None:
    docs = HydrafetchSearchRetriever(api_key="k", k=2).invoke("clean web data")

    assert len(docs) == 2
    assert fake.search_calls[0]["limit"] == 2


def test_k_kwarg_overrides_the_constructor(fake: FakeClient) -> None:
    docs = HydrafetchSearchRetriever(api_key="k", k=3).invoke("clean web data", k=1)

    assert len(docs) == 1
    assert fake.search_calls[0]["limit"] == 1


def test_scrape_content_replaces_the_snippet(fake: FakeClient) -> None:
    docs = HydrafetchSearchRetriever(api_key="k", k=1, scrape_content=True).invoke("q")

    assert docs[0].page_content == "full page body"
    assert fake.scraped == ["https://a.example"]


def test_search_params_pass_through(fake: FakeClient) -> None:
    HydrafetchSearchRetriever(api_key="k", search_params={"country": "us"}).invoke("q")

    assert fake.search_calls[0]["country"] == "us"
