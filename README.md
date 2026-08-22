# langchain-hydrafetch

[![PyPI](https://img.shields.io/pypi/v/langchain-hydrafetch)](https://pypi.org/project/langchain-hydrafetch/)
[![CI](https://github.com/Hydrafetch/langchain-hydrafetch/actions/workflows/ci.yml/badge.svg)](https://github.com/Hydrafetch/langchain-hydrafetch/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/langchain-hydrafetch)](https://pypi.org/project/langchain-hydrafetch/)

LangChain integration for the [Hydrafetch](https://hydrafetch.com) web data API.

Load pages as documents, search the web as a retriever, and give agents tools that read, extract and enrich from the live web.

## Installation

```bash
pip install langchain-hydrafetch
```

Create a key at [app.hydrafetch.com](https://app.hydrafetch.com) and set it:

```bash
export HYDRAFETCH_API_KEY="..."
```

Everything below reads that variable when no `api_key=` is passed.

## Document loader

```python
from langchain_hydrafetch import HydrafetchLoader

docs = HydrafetchLoader("https://example.com/article").load()
print(docs[0].page_content)
```

Three modes. `scrape` loads one page, `crawl` walks a site and loads every page it finds, and `map` returns one document per discovered URL without fetching the bodies.

```python
HydrafetchLoader("https://example.com", mode="crawl", params={"limit": 50}).load()
HydrafetchLoader("https://example.com", mode="map").load()
```

`params` is passed straight through to the API, so anything the endpoint accepts works here. `content_format` chooses what lands in `page_content` — `markdown` by default, or `html`, `rawHtml`, `summary`.

Documents carry `source`, `status`, and whatever page metadata was found: `title`, `description`, `language`, `site_name`, `author`, `published_time`, `word_count`, `page_type`.

Use `lazy_load()` to stream a large crawl instead of building the whole list in memory.

## Retriever

```python
from langchain_hydrafetch import HydrafetchSearchRetriever

retriever = HydrafetchSearchRetriever(k=5)
docs = retriever.invoke("best open source vector databases")
```

By default each document holds the result snippet. Pass `scrape_content=True` to fetch and return the full page body for every result instead:

```python
HydrafetchSearchRetriever(k=3, scrape_content=True).invoke("...")
```

## Agent tools

```python
from langchain_hydrafetch import (
    HydrafetchBrandTool,
    HydrafetchExtractTool,
    HydrafetchScrapeTool,
    HydrafetchSearchTool,
)

tools = [
    HydrafetchSearchTool(),
    HydrafetchScrapeTool(),
    HydrafetchExtractTool(),
    HydrafetchBrandTool(),
]
```

| tool | what it does |
|---|---|
| `hydrafetch_search` | search the web, return title, url and snippet |
| `hydrafetch_scrape` | read one known URL as clean markdown |
| `hydrafetch_extract` | pull structured JSON from pages, by JSON Schema or plain description |
| `hydrafetch_brand` | resolve a company domain to its brand and firmographic record |

Structured extraction takes either a schema or a description:

```python
HydrafetchExtractTool().invoke({
    "urls": ["https://example.com/pricing"],
    "json_schema": {
        "type": "object",
        "properties": {"plans": {"type": "array", "items": {"type": "string"}}},
    },
})
```

## Async

The retriever and every tool support `ainvoke`:

```python
docs = await HydrafetchSearchRetriever().ainvoke("...")
text = await HydrafetchScrapeTool().ainvoke({"url": "https://example.com"})
```

## Configuration

Every class accepts the same connection options, all optional:

| option | default | meaning |
|---|---|---|
| `api_key` | `HYDRAFETCH_API_KEY` | your API key |
| `base_url` | `https://api.hydrafetch.com` | API base URL |
| `timeout` | `120.0` | per-request timeout in seconds |
| `max_retries` | `2` | retries on 429 and 5xx |

## Development

```bash
uv sync
uv run ruff check src tests
uv run pytest -q
```

Unit tests run offline. Integration tests are skipped unless `HYDRAFETCH_API_KEY` is set, and they spend real credits.

## License

MIT
