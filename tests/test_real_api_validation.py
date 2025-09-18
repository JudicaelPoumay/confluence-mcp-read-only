"""
Test file for validating the refactored FastMCP tools with real API data.

This test file connects to a real Confluence instance to validate
that our model refactoring works correctly with actual API data.

These tests will be skipped if the required environment variables are not set
or if the --use-real-data flag is not passed to pytest.

To run these tests:
    pytest tests/test_real_api_validation.py --use-real-data

Required environment variables:
    - CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN
    - CONFLUENCE_TEST_PAGE_ID, CONFLUENCE_TEST_SPACE_KEY
"""

import os

import pytest
from fastmcp import Client
from fastmcp.client import FastMCPTransport
from mcp.types import TextContent

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.confluence.comments import CommentsMixin as ConfluenceCommentsMixin
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.confluence.labels import LabelsMixin as ConfluenceLabelsMixin
from mcp_atlassian.confluence.pages import PagesMixin
from mcp_atlassian.confluence.search import SearchMixin as ConfluenceSearchMixin
from mcp_atlassian.models.confluence import (
    ConfluenceComment,
    ConfluenceLabel,
    ConfluencePage,
)
from mcp_atlassian.servers import main_mcp


@pytest.fixture
def confluence_config() -> ConfluenceConfig:
    """Create a ConfluenceConfig from environment variables."""
    return ConfluenceConfig.from_env()


@pytest.fixture
def confluence_client(confluence_config: ConfluenceConfig) -> ConfluenceFetcher:
    """Create a ConfluenceFetcher instance."""
    return ConfluenceFetcher(config=confluence_config)


@pytest.fixture
def test_page_id() -> str:
    """Get test Confluence page ID from environment."""
    page_id = os.environ.get("CONFLUENCE_TEST_PAGE_ID")
    if not page_id:
        pytest.skip("CONFLUENCE_TEST_PAGE_ID environment variable not set")
    return page_id


@pytest.fixture
def test_space_key() -> str:
    """Get test Confluence space key from environment."""
    space_key = os.environ.get("CONFLUENCE_TEST_SPACE_KEY")
    if not space_key:
        pytest.skip("CONFLUENCE_TEST_SPACE_KEY environment variable not set")
    return space_key


# Only use asyncio backend for anyio tests
pytestmark = pytest.mark.anyio(backends=["asyncio"])


@pytest.fixture(scope="class")
async def api_validation_client():
    """Provides a FastMCP client connected to the main server for tool calls."""
    transport = FastMCPTransport(main_mcp)
    client = Client(transport=transport)
    async with client as connected_client:
        yield connected_client


async def call_tool(
    client: Client, tool_name: str, arguments: dict
) -> list[TextContent]:
    """Helper function to call tools via the client."""
    return await client.call_tool(tool_name, arguments)


class TestRealConfluenceValidation:
    """
    Test class for validating Confluence models with real API data.

    These tests will be skipped if:
    1. The --use-real-data flag is not passed to pytest
    2. The required Confluence environment variables are not set
    """

    def test_get_page_content(self, use_real_confluence_data, test_page_id):
        """Test that get_page_content returns a proper ConfluencePage model."""
        if not use_real_confluence_data:
            pytest.skip("Real Confluence data testing is disabled")

        config = ConfluenceConfig.from_env()
        pages_client = PagesMixin(config=config)

        page = pages_client.get_page_content(test_page_id)

        assert isinstance(page, ConfluencePage)
        assert page.id == test_page_id
        assert page.title is not None
        assert page.content is not None

        assert page.space is not None
        assert page.space.key is not None

        assert page.content_format in ["storage", "view", "markdown"]

    def test_get_page_comments(self, use_real_confluence_data, test_page_id):
        """Test that page comments are properly converted to ConfluenceComment models."""
        if not use_real_confluence_data:
            pytest.skip("Real Confluence data testing is disabled")

        config = ConfluenceConfig.from_env()
        comments_client = ConfluenceCommentsMixin(config=config)

        comments = comments_client.get_page_comments(test_page_id)

        if len(comments) == 0:
            pytest.skip("Test page has no comments")

        for comment in comments:
            assert isinstance(comment, ConfluenceComment)
            assert comment.id is not None
            assert comment.body is not None

    def test_get_page_labels(self, use_real_confluence_data, test_page_id):
        """Test that page labels are properly converted to ConfluenceLabel models."""
        if not use_real_confluence_data:
            pytest.skip("Real Confluence data testing is disabled")

        config = ConfluenceConfig.from_env()
        labels_client = ConfluenceLabelsMixin(config=config)

        labels = labels_client.get_page_labels(test_page_id)

        if len(labels) == 0:
            pytest.skip("Test page has no labels")

        for label in labels:
            assert isinstance(label, ConfluenceLabel)
            assert label.id is not None
            assert label.name is not None

    def test_search_content(self, use_real_confluence_data):
        """Test that search returns ConfluencePage models."""
        if not use_real_confluence_data:
            pytest.skip("Real Confluence data testing is disabled")

        config = ConfluenceConfig.from_env()
        search_client = ConfluenceSearchMixin(config=config)

        cql = 'type = "page" ORDER BY created DESC'
        results = search_client.search(cql, limit=5)

        assert len(results) > 0
        for page in results:
            assert isinstance(page, ConfluencePage)
            assert page.id is not None
            assert page.title is not None


@pytest.mark.anyio
async def test_confluence_get_page_content(
    confluence_client: ConfluenceFetcher, test_page_id: str
) -> None:
    """Test retrieving a page from Confluence."""
    page = confluence_client.get_page_content(test_page_id)

    assert page is not None
    assert page.id == test_page_id
    assert page.title is not None
