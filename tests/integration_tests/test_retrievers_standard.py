from __future__ import annotations

import os
from typing import Any

import pytest
from langchain_tests.integration_tests import RetrieversIntegrationTests

from langchain_hydrafetch import HydrafetchSearchRetriever

pytestmark = pytest.mark.skipif(
    not os.environ.get("HYDRAFETCH_API_KEY"),
    reason="set HYDRAFETCH_API_KEY to run integration tests",
)


class TestSearchRetrieverIntegration(RetrieversIntegrationTests):
    """
    LangChain's own contract for a retriever, run against the live API.

    The tools already ran this suite and the retriever did not, which left the surface most likely
    to drift untested: `k` reaches us as a constructor field AND as a per-call kwarg, and the two
    paths are separate code. The unit tests cover both against a fake client; this proves the same
    contract holds through a real search, which is the claim the LangChain docs listing makes.
    """

    @property
    def retriever_constructor(self) -> type[HydrafetchSearchRetriever]:
        return HydrafetchSearchRetriever

    @property
    def retriever_constructor_params(self) -> dict[str, Any]:
        # Snippets only. Scraping each hit would turn one standard run into a dozen page fetches
        # and bill the credits for them, and it tests the scrape surface rather than the retriever.
        return {"scrape_content": False}

    @property
    def retriever_query_example(self) -> str:
        return "what is retrieval augmented generation"

    @property
    def num_results_arg_name(self) -> str:
        return "k"
