from __future__ import annotations

import json
from typing import Any

from langchain_hydrafetch import HydrafetchJobSearchTool

JOB = {
    "title": "Data Engineer",
    "company": "Acme",
    "domain": "acme.com",
    "url": "https://acme.com/jobs/1",
}


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def search_jobs(self, query: str, **kwargs: Any) -> Any:
        self.calls.append({"query": query, **kwargs})
        return [JOB]


def test_job_search_maps_its_arguments_to_the_api_fields() -> None:
    tool = HydrafetchJobSearchTool(api_key="test-key")
    fake = FakeClient()
    tool._client = fake
    out = json.loads(
        tool.invoke(
            {"query": "data engineer", "location": "Berlin", "remote_only": True, "limit": 5}
        )
    )
    assert out == {"jobs": [JOB]}
    assert fake.calls == [
        {"query": "data engineer", "limit": 5, "location": "Berlin", "remoteOnly": True}
    ]


def test_job_search_leaves_out_filters_that_were_not_given() -> None:
    tool = HydrafetchJobSearchTool(api_key="test-key")
    fake = FakeClient()
    tool._client = fake
    tool.invoke({"query": "nurse"})
    assert fake.calls == [{"query": "nurse", "limit": 10}]
