from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from hydrafetch import AsyncHydrafetch, Hydrafetch
from langchain_core.documents import Document

CONTENT_FORMATS = ("markdown", "html", "rawHtml", "summary")

_METADATA_KEYS = (
    "title",
    "description",
    "language",
    "siteName",
    "author",
    "publishedTime",
    "wordCount",
    "pageType",
    "image",
)


def build_client(
    api_key: str | None,
    base_url: str | None,
    timeout: float | None,
    max_retries: int | None,
) -> Hydrafetch:
    return Hydrafetch(api_key, **_client_kwargs(base_url, timeout, max_retries))


def build_async_client(
    api_key: str | None,
    base_url: str | None,
    timeout: float | None,
    max_retries: int | None,
) -> AsyncHydrafetch:
    return AsyncHydrafetch(api_key, **_client_kwargs(base_url, timeout, max_retries))


def _client_kwargs(
    base_url: str | None, timeout: float | None, max_retries: int | None
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if base_url is not None:
        kwargs["base_url"] = base_url
    if timeout is not None:
        kwargs["timeout"] = timeout
    if max_retries is not None:
        kwargs["max_retries"] = max_retries
    return kwargs


def unwrap(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload if isinstance(payload, dict) else {}


def page_to_document(data: Mapping[str, Any], content_format: str) -> Document:
    content = data.get(content_format)
    if content is None and content_format != "markdown":
        content = data.get("markdown")
    if content is None:
        structured = data.get("structured") or data.get("json")
        content = str(structured) if structured is not None else ""

    metadata: dict[str, Any] = {"source": data.get("url") or data.get("finalUrl") or ""}
    if data.get("finalUrl") and data.get("finalUrl") != metadata["source"]:
        metadata["final_url"] = data["finalUrl"]
    if data.get("status") is not None:
        metadata["status"] = data["status"]

    raw_metadata = data.get("metadata")
    if isinstance(raw_metadata, Mapping):
        for key in _METADATA_KEYS:
            value = raw_metadata.get(key)
            if value is not None:
                metadata[_snake(key)] = value

    return Document(page_content=str(content), metadata=metadata)


def _snake(key: str) -> str:
    out: list[str] = []
    for char in key:
        if char.isupper():
            out.append("_")
            out.append(char.lower())
        else:
            out.append(char)
    return "".join(out)
