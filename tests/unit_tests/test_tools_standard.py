from __future__ import annotations

from typing import Any

from langchain_tests.unit_tests import ToolsUnitTests

from langchain_hydrafetch import (
    HydrafetchBrandTool,
    HydrafetchExtractTool,
    HydrafetchScrapeTool,
    HydrafetchSearchTool,
)


class TestScrapeToolUnit(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type[HydrafetchScrapeTool]:
        return HydrafetchScrapeTool

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        return {"api_key": "test-key"}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        return {"url": "https://example.com"}


class TestSearchToolUnit(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type[HydrafetchSearchTool]:
        return HydrafetchSearchTool

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        return {"api_key": "test-key"}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        return {"query": "hydrafetch", "limit": 3}


class TestExtractToolUnit(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type[HydrafetchExtractTool]:
        return HydrafetchExtractTool

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        return {"api_key": "test-key"}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        return {"urls": ["https://example.com"], "prompt": "the page title"}


class TestBrandToolUnit(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type[HydrafetchBrandTool]:
        return HydrafetchBrandTool

    @property
    def tool_constructor_params(self) -> dict[str, Any]:
        return {"api_key": "test-key"}

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        return {"domain": "stripe.com"}
