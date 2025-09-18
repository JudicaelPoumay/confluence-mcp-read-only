"""
Pydantic models for Confluence API responses.

This package provides type-safe models for working with Atlassian API data,
including conversion methods from API responses to structured models and
simplified dictionaries for API responses.
"""

# Re-export models for easier imports
from .base import ApiModel, TimestampMixin
from .confluence import (
    ConfluenceAttachment,
    ConfluenceComment,
    ConfluenceLabel,
    ConfluencePage,
    ConfluenceSearchResult,
    ConfluenceSpace,
    ConfluenceUser,
    ConfluenceVersion,
)
from .constants import (
    CONFLUENCE_DEFAULT_ID,
    CONFLUENCE_DEFAULT_SPACE,
    CONFLUENCE_DEFAULT_VERSION,
    DEFAULT_TIMESTAMP,
    EMPTY_STRING,
    NONE_VALUE,
    UNKNOWN,
)

# Additional models will be added as they are implemented

__all__ = [
    # Base models
    "ApiModel",
    "TimestampMixin",
    # Constants
    "CONFLUENCE_DEFAULT_ID",
    "CONFLUENCE_DEFAULT_SPACE",
    "CONFLUENCE_DEFAULT_VERSION",
    "DEFAULT_TIMESTAMP",
    "EMPTY_STRING",
    "NONE_VALUE",
    "UNKNOWN",
    # Confluence models
    "ConfluenceUser",
    "ConfluenceSpace",
    "ConfluencePage",
    "ConfluenceComment",
    "ConfluenceLabel",
    "ConfluenceVersion",
    "ConfluenceSearchResult",
    "ConfluenceAttachment",
]
