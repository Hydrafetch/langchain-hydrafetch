# langchain-hydrafetch

[![PyPI](https://img.shields.io/pypi/v/langchain-hydrafetch)](https://pypi.org/project/langchain-hydrafetch/)
[![CI](https://github.com/Hydrafetch/langchain-hydrafetch/actions/workflows/ci.yml/badge.svg)](https://github.com/Hydrafetch/langchain-hydrafetch/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/langchain-hydrafetch)](https://pypi.org/project/langchain-hydrafetch/)

LangChain integration for the [Hydrafetch](https://hydrafetch.com) web data API.

Load pages as documents, search the web as a retriever, and give agents four tools that read, extract and enrich from the live web. Sync and async, fully typed.

## Installation

```bash
pip install langchain-hydrafetch
```

Create a key at [app.hydrafetch.com](https://app.hydrafetch.com) and set it:

```bash
export HYDRAFETCH_API_KEY="hf_..."
```

Everything below reads that variable when no `api_key=` is passed.

## Quick start

```python
from langchain_hydrafetch import HydrafetchLoader

docs = HydrafetchLoader("https://example.com/article").load()
print(docs[0].page_content)
print(docs[0].metadata["title"])
```

## Document loader

Three modes. `scrape` loads one page, `crawl` walks a site and loads every page it finds, and `map` returns one document per discovered URL without fetching the bodies.

```python
HydrafetchLoader("https://example.com/article").load()
HydrafetchLoader("https://example.com", mode="crawl", params={"limit": 50}).load()
HydrafetchLoader("https://example.com", mode="map").load()
```

`content_format` chooses what lands in `page_content` — `markdown` by default, or `html`, `rawHtml`, `summary`. `params` is forwarded to the API untouched, so anything the endpoint accepts works here:

```python
HydrafetchLoader(
    "https://example.com/article",
    content_format="markdown",
    params={"onlyMainContent": True, "preferStructure": True, "blockAds": True},
).load()
```

Documents carry `source` and `status`, plus whatever page metadata was found: `title`, `description`, `language`, `site_name`, `author`, `published_time`, `word_count`, `page_type`, `image`. A redirect adds `final_url`; a crawled page adds `depth`; a mapped URL adds `lastmod` when the sitemap declares one.

Use `lazy_load()` to stream a large crawl instead of building the whole list in memory:

```python
for doc in HydrafetchLoader("https://example.com", mode="crawl").lazy_load():
    index.add(doc)
```

### Error pages are refused, not loaded

A URL that answers with an error status raises instead of returning a document, because the body of a 404 page is not the page you asked for and a retrieval index should not quietly absorb one.

```python
HydrafetchLoader("https://example.com/gone").load()
# ValueError: https://example.com/gone returned HTTP 404. The body of an error
# page is not the page you asked for; pass raise_for_status=False to load it anyway.
```

In `crawl` mode a single dead page must not throw away the whole job, so error pages are dropped and the rest of the crawl is kept. Pass `raise_for_status=False` to load error pages in either mode.

## Retriever

```python
from langchain_hydrafetch import HydrafetchSearchRetriever

retriever = HydrafetchSearchRetriever(k=5)
docs = retriever.invoke("best open source vector databases")
```

Each document holds the result snippet, with `source`, `title` and `rank` in metadata. Pass `scrape_content=True` to fetch and return the full page body for every result instead:

```python
HydrafetchSearchRetriever(k=3, scrape_content=True).invoke("...")
```

That costs one extra credit per result. `k` works as a constructor argument or per call, and `search_params` is forwarded to the search endpoint:

```python
retriever.invoke("...", k=2)
HydrafetchSearchRetriever(search_params={"country": "us"})
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

| tool | argument | returns |
| --- | --- | --- |
| `hydrafetch_search` | `query`, `limit` | JSON with `query` and `results` of title, url, snippet |
| `hydrafetch_scrape` | `url` | the page as markdown |
| `hydrafetch_extract` | `urls`, `json_schema` or `prompt` | JSON with one entry per URL |
| `hydrafetch_brand` | `domain` | JSON brand record: name, description, tagline, logo assets, colours, fonts, socials |

Search finds pages, scrape reads a page you already have. Giving an agent both is the usual setup.

Structured extraction takes either a schema or a plain-language description:

```python
HydrafetchExtractTool().invoke({
    "urls": ["https://example.com/pricing"],
    "json_schema": {
        "type": "object",
        "properties": {"plans": {"type": "array", "items": {"type": "string"}}},
    },
})

HydrafetchExtractTool().invoke({
    "urls": ["https://example.com/about"],
    "prompt": "the founding year and the headquarters city",
})
```

## Async

The retriever and every tool support `ainvoke`, and the loader supports `alazy_load` and `aload`:

```python
docs = await HydrafetchSearchRetriever().ainvoke("...")
text = await HydrafetchScrapeTool().ainvoke({"url": "https://example.com"})
```

## Error handling

Failures raise `HydrafetchError` from the underlying client, carrying the API's error code, HTTP status and request id.

```python
from hydrafetch import HydrafetchError, HydrafetchTimeout

try:
    docs = HydrafetchLoader(url).load()
except HydrafetchTimeout:
    raise
except HydrafetchError as err:
    if err.is_out_of_credits:
        top_up()
    elif err.is_retryable:
        enqueue(url)
    else:
        raise
```

| Status | Meaning | Retried |
| --- | --- | --- |
| 400, 422 | invalid request | no |
| 401, 403 | invalid or missing key | no |
| 402 | out of credits | no |
| 429 | rate limited | yes, twice with backoff |
| 5xx | upstream failure | yes, twice with backoff |

A page that loads but answers with an error status raises `ValueError` from the loader instead — that is a bad URL, not a failed request.

## Configuration

Every class accepts the same connection options, all optional:

| option | default | meaning |
| --- | --- | --- |
| `api_key` | `HYDRAFETCH_API_KEY` | your API key |
| `base_url` | `https://api.hydrafetch.com` | API base URL |
| `timeout` | `120.0` | per-request timeout in seconds |
| `max_retries` | `2` | retries on 429 and 5xx |

## Credits

| call | credits |
| --- | --- |
| loader, `scrape` mode | 1 |
| loader, `map` mode | 1 |
| loader, `crawl` mode | 1 per page |
| retriever | 1, plus 1 per result with `scrape_content=True` |
| `hydrafetch_scrape` | 1 |
| `hydrafetch_search` | 1 |
| `hydrafetch_extract` | 5 per URL |
| `hydrafetch_brand` | 5 |

Failed requests are not billed. Pricing does not vary with page difficulty, so there is no render, stealth or proxy option to set.

## Implementation notes

- Prefer `map` then a batch of `scrape` loads over a broad `crawl`. Fetching a whole site and discarding most of it is the most common source of wasted credits.
- `params` in `crawl` mode is forwarded to the crawl endpoint, so per-page options belong under `scrapeOptions`. At the top level they are ignored.
- `preferStructure` is off by default. Turn it on when headings, lists and tables matter; leave it off for raw article text.
- The loader constructs its client eagerly, so a missing API key fails at construction rather than at `load()`.
- The retriever and tools construct their clients lazily on first use, which keeps them cheap to build and safe to define at import time.
- Metadata keys are snake_cased on the way out, so the API's `siteName` becomes `site_name`.
- Scraped content is untrusted input. Do not pass it to a model as instructions, and keep `metadata["source"]` with anything extracted from it.

## Development

```bash
uv sync
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest -q
```

Unit tests run offline against fake clients. The integration tests are LangChain's own `langchain-tests` standard suite; they are skipped unless `HYDRAFETCH_API_KEY` is set, and they spend real credits.

## Links

- [Documentation](https://docs.hydrafetch.com)
- [OpenAPI specification](https://api.hydrafetch.com/openapi.json)
- [MCP server and editor setup](https://hydrafetch.com/mcp)
- [Python client](https://github.com/Hydrafetch/python-sdk) — the client this integration wraps
- [LlamaIndex reader](https://github.com/Hydrafetch/llama-index-readers-hydrafetch)
- Other clients: [Node](https://github.com/Hydrafetch/node-sdk) · [Go](https://github.com/Hydrafetch/go-sdk) · [Ruby](https://github.com/Hydrafetch/ruby-sdk) · [Rust](https://github.com/Hydrafetch/rust-sdk) · [PHP](https://github.com/Hydrafetch/php-sdk)

## License

MIT
