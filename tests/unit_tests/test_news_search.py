from __future__ import annotations

import json
from typing import Any

from langchain_hydrafetch import HydrafetchNewsSearchTool

ARTICLE = {
    "title": "Acme raises $10M",
    "url": "https://example.com/acme",
    "source": "Example News",
    "publishedAt": "2026-11-04T10:00:00.000Z",
    "snippet": "Acme raised $10 million.",
    "imageUrl": "https://example.com/acme.jpg",
    "data": None,
}


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def news(self, query: str, **kwargs: Any) -> Any:
        self.calls.append({"query": query, **kwargs})
        return {"query": query, "status": "ok", "results": [ARTICLE]}


def test_news_search_maps_its_arguments_and_keeps_the_useful_fields() -> None:
    tool = HydrafetchNewsSearchTool(api_key="test-key")
    fake = FakeClient()
    tool._client = fake
    out = json.loads(tool.invoke({"query": "acme raises", "time_range": "day", "limit": 5}))
    assert out == {
        "articles": [
            {
                "title": "Acme raises $10M",
                "url": "https://example.com/acme",
                "source": "Example News",
                "publishedAt": "2026-11-04T10:00:00.000Z",
                "snippet": "Acme raised $10 million.",
            }
        ]
    }
    assert fake.calls == [{"query": "acme raises", "timeRange": "day", "limit": 5}]
