from __future__ import annotations

from typing import Any

from langchain_core.callbacks import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field, PrivateAttr

from ._common import build_async_client, build_client, unwrap


class HydrafetchSearchRetriever(BaseRetriever):
    """Retrieve web results for a query using Hydrafetch's first-party search."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    k: int = 5
    scrape_content: bool = False
    content_format: str = "markdown"
    search_params: dict[str, Any] = Field(default_factory=dict)

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

    def _params(self, k: int | None) -> dict[str, Any]:
        params = dict(self.search_params)
        params.setdefault("limit", k or self.k)
        return params

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        k: int | None = None,
        **kwargs: Any,
    ) -> list[Document]:
        data = unwrap(self._sync().search(query, **self._params(k)))
        documents = [_result_to_document(item) for item in _results(data)]
        if not self.scrape_content:
            return documents[: k or self.k]
        return [self._with_content(doc) for doc in documents[: k or self.k]]

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
        k: int | None = None,
        **kwargs: Any,
    ) -> list[Document]:
        data = unwrap(await self._async().search(query, **self._params(k)))
        documents = [_result_to_document(item) for item in _results(data)]
        if not self.scrape_content:
            return documents[: k or self.k]
        return [await self._awith_content(doc) for doc in documents[: k or self.k]]

    def _with_content(self, document: Document) -> Document:
        source = document.metadata.get("source")
        if not source:
            return document
        page = unwrap(self._sync().scrape(source, formats=[self.content_format]))
        content = page.get(self.content_format)
        if content:
            document.page_content = str(content)
        return document

    async def _awith_content(self, document: Document) -> Document:
        source = document.metadata.get("source")
        if not source:
            return document
        page = unwrap(await self._async().scrape(source, formats=[self.content_format]))
        content = page.get(self.content_format)
        if content:
            document.page_content = str(content)
        return document


def _results(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in (data.get("results") or []) if isinstance(item, dict)]


def _result_to_document(item: dict[str, Any]) -> Document:
    metadata: dict[str, Any] = {"source": item.get("url") or ""}
    if item.get("title"):
        metadata["title"] = item["title"]
    if item.get("rank") is not None:
        metadata["rank"] = item["rank"]
    return Document(page_content=str(item.get("snippet") or ""), metadata=metadata)
