from __future__ import annotations

import os
from typing import Any

import pytest
from langchain_tests.integration_tests import ToolsIntegrationTests

from langchain_hydrafetch import HydrafetchScrapeTool, HydrafetchSearchTool

pytestmark = pytest.mark.skipif(
    not os.environ.get("HYDRAFETCH_API_KEY"),
    reason="set HYDRAFETCH_API_KEY to run integration tests",
)


class TestScrapeToolIntegration(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> type[HydrafetchScrapeTool]:
        return HydrafetchScrapeTool

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        return {"url": "https://example.com"}


class TestSearchToolIntegration(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> type[HydrafetchSearchTool]:
        return HydrafetchSearchTool

    @property
    def tool_invoke_params_example(self) -> dict[str, Any]:
        return {"query": "hydrafetch", "limit": 2}
