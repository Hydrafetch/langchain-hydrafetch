from __future__ import annotations

import json
from typing import Any

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from ._common import build_async_client, build_client, unwrap


class _HydrafetchTool(BaseTool):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    api_key: str | None = None
    base_url: str | None = None
    timeout: float | None = None
    max_retries: int | None = None

    _client: Any = PrivateAttr(default=None)
    _aclient: Any = PrivateAttr(default=None)

    def _sync(self) -> Any:
        if self._client is None:
            self._client = build_client(self.api_key, self.base_url, self.timeout, self.max_retries)
        return self._client

    def _async(self) -> Any:
        if self._aclient is None:
            self._aclient = build_async_client(
                self.api_key, self.base_url, self.timeout, self.max_retries
            )
        return self._aclient


class ScrapeInput(BaseModel):
    url: str = Field(description="The absolute URL of the page to read.")


class HydrafetchScrapeTool(_HydrafetchTool):
    """Read one web page and return it as clean markdown."""

    name: str = "hydrafetch_scrape"
    description: str = (
        "Read a single web page and return its main content as clean markdown. "
        "Use this when you already have the URL of the page you need."
    )
    args_schema: type[BaseModel] = ScrapeInput

    def _run(self, url: str, run_manager: CallbackManagerForToolRun | None = None) -> str:
        data = unwrap(self._sync().scrape(url, formats=["markdown"]))
        return str(data.get("markdown") or "")

    async def _arun(
        self, url: str, run_manager: AsyncCallbackManagerForToolRun | None = None
    ) -> str:
        data = unwrap(await self._async().scrape(url, formats=["markdown"]))
        return str(data.get("markdown") or "")


class SearchInput(BaseModel):
    query: str = Field(description="What to search the web for.")
    limit: int = Field(default=5, description="How many results to return.")


class HydrafetchSearchTool(_HydrafetchTool):
    """Search the web and return titles, URLs and snippets."""

    name: str = "hydrafetch_search"
    description: str = (
        "Search the web and return a list of results with title, url and snippet. "
        "Use this when you need to find pages rather than read a known URL."
    )
    args_schema: type[BaseModel] = SearchInput

    def _run(
        self, query: str, limit: int = 5, run_manager: CallbackManagerForToolRun | None = None
    ) -> str:
        data = unwrap(self._sync().search(query, limit=limit))
        return _dump(_trim_results(data, limit))

    async def _arun(
        self,
        query: str,
        limit: int = 5,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        data = unwrap(await self._async().search(query, limit=limit))
        return _dump(_trim_results(data, limit))


class ExtractInput(BaseModel):
    urls: list[str] = Field(description="Absolute URLs to extract from.")
    json_schema: dict[str, Any] | None = Field(
        default=None, description="JSON Schema describing the shape to extract."
    )
    prompt: str | None = Field(
        default=None, description="Plain-language description of what to extract."
    )


class HydrafetchExtractTool(_HydrafetchTool):
    """Extract structured JSON from one or more pages."""

    name: str = "hydrafetch_extract"
    description: str = (
        "Extract structured JSON from one or more web pages, either against a JSON Schema "
        "or from a plain-language description of the fields you want."
    )
    args_schema: type[BaseModel] = ExtractInput

    def _run(
        self,
        urls: list[str],
        json_schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        return _dump(unwrap(self._sync().extract(urls, **_extract_options(json_schema, prompt))))

    async def _arun(
        self,
        urls: list[str],
        json_schema: dict[str, Any] | None = None,
        prompt: str | None = None,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        payload = await self._async().extract(urls, **_extract_options(json_schema, prompt))
        return _dump(unwrap(payload))


class BrandInput(BaseModel):
    domain: str = Field(description="A company domain, for example 'stripe.com'.")


class HydrafetchBrandTool(_HydrafetchTool):
    """Resolve a company domain to its brand and firmographic record."""

    name: str = "hydrafetch_brand"
    description: str = (
        "Given a company domain, return its brand record: name, description, logo, "
        "colours, and social profiles. Use this to enrich a company from its website."
    )
    args_schema: type[BaseModel] = BrandInput

    def _run(self, domain: str, run_manager: CallbackManagerForToolRun | None = None) -> str:
        return _dump(unwrap(self._sync().brand(domain)))

    async def _arun(
        self, domain: str, run_manager: AsyncCallbackManagerForToolRun | None = None
    ) -> str:
        return _dump(unwrap(await self._async().brand(domain)))


def _extract_options(json_schema: dict[str, Any] | None, prompt: str | None) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if json_schema is not None:
        options["schema"] = json_schema
    if prompt is not None:
        options["prompt"] = prompt
    return options


def _trim_results(data: dict[str, Any], limit: int) -> dict[str, Any]:
    results = [item for item in (data.get("results") or []) if isinstance(item, dict)]
    return {
        "query": data.get("query"),
        "results": [
            {k: item.get(k) for k in ("title", "url", "snippet") if item.get(k) is not None}
            for item in results[:limit]
        ],
    }


def _dump(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)
