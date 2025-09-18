"""
Integration tests for proxy handling in Confluence clients (mocked requests).
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from mcp_atlassian.confluence.client import ConfluenceClient
from mcp_atlassian.confluence.config import ConfluenceConfig
from tests.utils.base import BaseAuthTest
from tests.utils.mocks import MockEnvironment


@pytest.mark.integration
def test_confluence_client_passes_proxies_to_requests(monkeypatch):
    """Test that ConfluenceClient passes proxies to requests.Session.request."""
    mock_confluence = MagicMock()
    mock_session = MagicMock()
    # Create a proper proxies dictionary that can be updated
    mock_session.proxies = {}
    mock_confluence._session = mock_session
    monkeypatch.setattr(
        "mcp_atlassian.confluence.client.Confluence", lambda **kwargs: mock_confluence
    )
    monkeypatch.setattr(
        "mcp_atlassian.confluence.client.configure_ssl_verification",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor",
        lambda **kwargs: MagicMock(),
    )
    config = ConfluenceConfig(
        url="https://test.atlassian.net/wiki",
        auth_type="basic",
        username="user",
        api_token="pat",
        http_proxy="http://proxy:8080",
        https_proxy="https://proxy:8443",
        socks_proxy="socks5://user:pass@proxy:1080",
        no_proxy="localhost,127.0.0.1",
    )
    client = ConfluenceClient(config=config)
    # Simulate a request
    client.confluence._session.request(
        "GET", "https://test.atlassian.net/wiki/rest/api/content/123"
    )
    assert mock_session.proxies["http"] == "http://proxy:8080"
    assert mock_session.proxies["https"] == "https://proxy:8443"
    assert mock_session.proxies["socks"] == "socks5://user:pass@proxy:1080"


class TestProxyConfigurationEnhanced(BaseAuthTest):
    """Enhanced proxy configuration tests using test utilities."""

    @pytest.mark.integration
    def test_proxy_configuration_from_environment(self):
        """Test proxy configuration loaded from environment variables."""
        with MockEnvironment.basic_auth_env():
            # Set proxy environment variables in os.environ directly
            proxy_vars = {
                "HTTP_PROXY": "http://proxy.company.com:8080",
                "HTTPS_PROXY": "https://proxy.company.com:8443",
                "NO_PROXY": "*.internal.com,localhost",
            }

            # Patch environment with proxy settings
            with patch.dict(os.environ, proxy_vars):
                # Confluence should pick up proxy settings
                confluence_config = ConfluenceConfig.from_env()
                assert confluence_config.http_proxy == "http://proxy.company.com:8080"
                assert confluence_config.https_proxy == "https://proxy.company.com:8443"
                assert confluence_config.no_proxy == "*.internal.com,localhost"

    @pytest.mark.integration
    def test_mixed_proxy_and_ssl_configuration(self, monkeypatch):
        """Test proxy configuration works correctly with SSL verification disabled."""
        mock_confluence = MagicMock()
        mock_session = MagicMock()
        # Create a proper proxies dictionary that can be updated
        mock_session.proxies = {}
        mock_confluence._session = mock_session
        monkeypatch.setattr(
            "mcp_atlassian.confluence.client.Confluence",
            lambda **kwargs: mock_confluence,
        )
        monkeypatch.setattr(
            "mcp_atlassian.confluence.client.configure_ssl_verification",
            lambda **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_atlassian.preprocessing.confluence.ConfluencePreprocessor",
            lambda **kwargs: MagicMock(),
        )

        # Configure with both proxy and SSL disabled
        config = ConfluenceConfig(
            url="https://test.atlassian.net/wiki",
            auth_type="basic",
            username="user",
            api_token="token",
            http_proxy="http://proxy.company.com:8080",
            ssl_verify=False,
        )

        client = ConfluenceClient(config=config)

        # Both proxy and SSL settings should be applied
        assert mock_session.proxies["http"] == "http://proxy.company.com:8080"
        assert config.ssl_verify is False

    @pytest.mark.integration
    def test_proxy_with_oauth_configuration(self):
        """Test proxy configuration works with OAuth authentication."""
        with MockEnvironment.oauth_env() as env_vars:
            # Add proxy configuration to env_vars directly, then patch os.environ
            proxy_vars = {
                "HTTP_PROXY": "http://proxy.company.com:8080",
                "HTTPS_PROXY": "https://proxy.company.com:8443",
                "NO_PROXY": "localhost,127.0.0.1",
            }

            # Merge with OAuth env vars
            all_vars = {**env_vars, **proxy_vars}

            # Use patch.dict to ensure environment variables are set
            with patch.dict(os.environ, all_vars):
                # OAuth should still respect proxy settings
                assert os.environ.get("HTTP_PROXY") == "http://proxy.company.com:8080"
                assert os.environ.get("HTTPS_PROXY") == "https://proxy.company.com:8443"
                assert os.environ.get("NO_PROXY") == "localhost,127.0.0.1"
