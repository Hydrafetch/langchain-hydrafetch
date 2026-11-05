"""LangChain integration for the Hydrafetch web data API."""

from .document_loaders import HydrafetchLoader
from .retrievers import HydrafetchSearchRetriever
from .tools import (
    HydrafetchBrandTool,
    HydrafetchExtractTool,
    HydrafetchJobSearchTool,
    HydrafetchNewsSearchTool,
    HydrafetchScrapeTool,
    HydrafetchSearchTool,
)

__all__ = [
    "HydrafetchBrandTool",
    "HydrafetchExtractTool",
    "HydrafetchJobSearchTool",
    "HydrafetchLoader",
    "HydrafetchNewsSearchTool",
    "HydrafetchScrapeTool",
    "HydrafetchSearchRetriever",
    "HydrafetchSearchTool",
]
__version__ = "0.4.0"
