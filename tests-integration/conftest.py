"""
Shared fixtures and configuration for integration tests.

These tests require a valid GOOGLE_CALENDAR_ACCESS_TOKEN environment variable
(an OAuth 2.0 access token with Google Calendar API v3 scopes).
They make real API calls and should not be run in CI without proper setup.

To get an access token for testing, use Google's OAuth Playground:
  https://developers.google.com/oauthplayground/
Select "Google Calendar API v3" scopes, authorize, and exchange for an access token.
"""

import os

import pytest
import pytest_asyncio
from dotenv import load_dotenv

load_dotenv()

from mcp_google_calendar.api_client import GoogleCalendarClient


def pytest_configure(config):
    """Check for required environment variables before running tests."""
    if not os.environ.get("GOOGLE_CALENDAR_ACCESS_TOKEN"):
        pytest.exit(
            "ERROR: GOOGLE_CALENDAR_ACCESS_TOKEN environment variable is required.\n"
            "Set it before running integration tests:\n"
            "  export GOOGLE_CALENDAR_ACCESS_TOKEN=your_oauth_token_here\n"
            "  make test-integration\n\n"
            "Get a token from https://developers.google.com/oauthplayground/\n"
            "Select 'Google Calendar API v3' scopes, authorize, and exchange."
        )


@pytest.fixture
def access_token() -> str:
    """Get the OAuth access token from environment."""
    token = os.environ.get("GOOGLE_CALENDAR_ACCESS_TOKEN")
    if not token:
        pytest.skip("GOOGLE_CALENDAR_ACCESS_TOKEN not set")
    return token


@pytest_asyncio.fixture
async def client(access_token: str) -> GoogleCalendarClient:
    """Create a client for testing."""
    client = GoogleCalendarClient(access_token=access_token)
    yield client
    await client.close()
