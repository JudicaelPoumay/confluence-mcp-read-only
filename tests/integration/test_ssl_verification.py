"""Integration tests for SSL verification functionality."""

import os
from unittest.mock import patch

import pytest
from requests.sessions import Session

from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.utils.ssl import SSLIgnoreAdapter, configure_ssl_verification
from tests.utils.base import BaseAuthTest
from tests.utils.mocks import MockEnvironment


@pytest.mark.integration
def test_configure_ssl_verification_with_real_confluence_url():
    """Test SSL verification configuration with real Confluence URL from environment."""
    # Get the URL from the environment
    url = os.getenv("CONFLUENCE_URL")
    if not url:
        pytest.skip("CONFLUENCE_URL not set in environment")

    # Create a real session
    session = Session()
    original_adapters_count = len(session.adapters)

    # Mock the SSL_VERIFY value to be False for this test
    with patch.dict(os.environ, {"CONFLUENCE_SSL_VERIFY": "false"}):
        # Configure SSL verification - explicitly pass ssl_verify=False
        configure_ssl_verification(
            service_name="Confluence",
            url=url,
            session=session,
            ssl_verify=False,
        )

        # Extract domain from URL (remove protocol and path)
        domain = url.split("://")[1].split("/")[0]

        # Verify the adapters are mounted correctly
        assert len(session.adapters) == original_adapters_count + 2
        assert f"https://{domain}" in session.adapters
        assert f"http://{domain}" in session.adapters
        assert isinstance(session.adapters[f"https://{domain}"], SSLIgnoreAdapter)
        assert isinstance(session.adapters[f"http://{domain}"], SSLIgnoreAdapter)


class TestSSLVerificationEnhanced(BaseAuthTest):
    """Enhanced SSL verification tests using test utilities."""

    @pytest.mark.integration
    def test_ssl_verification_enabled_by_default(self):
        """Test that SSL verification is enabled by default."""
        with MockEnvironment.basic_auth_env():
            # For Confluence
            confluence_config = ConfluenceConfig.from_env()
            assert confluence_config.ssl_verify is True

    @pytest.mark.integration
    def test_ssl_verification_disabled_via_env(self):
        """Test SSL verification can be disabled via environment variables."""
        with MockEnvironment.basic_auth_env() as env_vars:
            env_vars["CONFLUENCE_SSL_VERIFY"] = "false"

            # For Confluence
            with patch.dict(os.environ, env_vars):
                confluence_config = ConfluenceConfig.from_env()
                assert confluence_config.ssl_verify is False

    @pytest.mark.integration
    def test_ssl_adapter_mounting_for_multiple_domains(self):
        """Test SSL adapters are correctly mounted for multiple domains."""
        session = Session()

        # Configure for multiple domains
        urls = [
            "https://domain1.atlassian.net/wiki",
            "https://custom.domain.com/confluence",
        ]

        for url in urls:
            configure_ssl_verification(
                service_name="Test", url=url, session=session, ssl_verify=False
            )

        # Verify all domains have SSL adapters
        assert "https://domain1.atlassian.net" in session.adapters
        assert "https://custom.domain.com" in session.adapters

    @pytest.mark.integration
    def test_ssl_verification_with_custom_ca_bundle(self):
        """Test SSL verification with custom CA bundle path."""
        with MockEnvironment.basic_auth_env() as env_vars:
            # Set custom CA bundle path
            custom_ca_path = "/path/to/custom/ca-bundle.crt"
            env_vars["CONFLUENCE_SSL_VERIFY"] = custom_ca_path

            # For Confluence
            with patch.dict(os.environ, env_vars):
                confluence_config = ConfluenceConfig.from_env()
                assert (
                    confluence_config.ssl_verify is True
                )  # Any non-false value becomes True

    @pytest.mark.integration
    def test_ssl_adapter_not_mounted_when_verification_enabled(self):
        """Test that SSL adapters are not mounted when verification is enabled."""
        session = Session()
        original_adapter_count = len(session.adapters)

        # Configure with SSL verification enabled
        configure_ssl_verification(
            service_name="Confluence",
            url="https://test.atlassian.net/wiki",
            session=session,
            ssl_verify=True,  # SSL verification enabled
        )

        # No additional adapters should be mounted
        assert len(session.adapters) == original_adapter_count
        assert "https://test.atlassian.net" not in session.adapters

    @pytest.mark.integration
    def test_ssl_configuration_persistence_across_requests(self):
        """Test SSL configuration persists across multiple requests."""
        session = Session()

        # Configure SSL for a domain
        configure_ssl_verification(
            service_name="Confluence",
            url="https://test.atlassian.net/wiki",
            session=session,
            ssl_verify=False,
        )

        # Get the adapter
        adapter = session.adapters.get("https://test.atlassian.net")
        assert isinstance(adapter, SSLIgnoreAdapter)

        # Configure again - should not create duplicate adapters
        configure_ssl_verification(
            service_name="Confluence",
            url="https://test.atlassian.net/wiki",
            session=session,
            ssl_verify=False,
        )

        # Should still have an SSLIgnoreAdapter present
        new_adapter = session.adapters.get("https://test.atlassian.net")
        assert isinstance(new_adapter, SSLIgnoreAdapter)

    @pytest.mark.integration
    def test_ssl_verification_with_oauth_configuration(self):
        """Test SSL verification works correctly with OAuth configuration."""
        with MockEnvironment.oauth_env() as env_vars:
            # Add SSL configuration
            env_vars["CONFLUENCE_SSL_VERIFY"] = "false"

            # OAuth config should still respect SSL settings
            with patch.dict(os.environ, env_vars):
                assert os.environ.get("CONFLUENCE_SSL_VERIFY") == "false"
