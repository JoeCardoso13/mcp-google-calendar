"""Unit tests for the Google Calendar API client."""

import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from mcp_google_calendar.api_client import GoogleCalendarAPIError, GoogleCalendarClient


@pytest_asyncio.fixture
async def mock_client():
    """Create a GoogleCalendarClient with mocked session."""
    client = GoogleCalendarClient(api_key="test_key")
    client._session = AsyncMock()
    yield client
    await client.close()


class TestClientInitialization:
    """Test client creation and configuration."""

    def test_init_with_explicit_key(self):
        """Client accepts an explicit API key."""
        client = GoogleCalendarClient(api_key="explicit_key")
        assert client.api_key == "explicit_key"

    def test_init_with_env_var(self):
        """Client falls back to GOOGLE_CALENDAR_API_KEY env var."""
        os.environ["GOOGLE_CALENDAR_API_KEY"] = "env_key"
        try:
            client = GoogleCalendarClient()
            assert client.api_key == "env_key"
        finally:
            del os.environ["GOOGLE_CALENDAR_API_KEY"]

    def test_init_without_key_raises(self):
        """Client raises ValueError when no key is available."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_CALENDAR_API_KEY", None)
            with pytest.raises(ValueError, match="GOOGLE_CALENDAR_API_KEY is required"):
                GoogleCalendarClient()

    def test_custom_timeout(self):
        """Client accepts a custom timeout."""
        client = GoogleCalendarClient(api_key="key", timeout=60.0)
        assert client.timeout == 60.0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Client works as an async context manager."""
        async with GoogleCalendarClient(api_key="test") as client:
            assert client._session is not None
        assert client._session is None

    def test_base_url(self):
        """Client uses correct Google Calendar API base URL."""
        client = GoogleCalendarClient(api_key="key")
        assert client.BASE_URL == "https://www.googleapis.com/calendar/v3"


class TestClientMethods:
    """Test API client methods with mocked responses."""

    @pytest.mark.asyncio
    async def test_list_events(self, mock_client):
        """Test list_events returns EventListResponse."""
        mock_response = {
            "items": [
                {"id": "1", "summary": "Event 1"},
                {"id": "2", "summary": "Event 2"},
            ]
        }
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.list_events(calendar_id="primary")
        assert len(result.items) == 2
        assert result.items[0].summary == "Event 1"

    @pytest.mark.asyncio
    async def test_get_event(self, mock_client):
        """Test get_event returns Event."""
        mock_response = {"id": "1", "summary": "Test Event", "status": "confirmed"}
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.get_event("1")
        assert result.id == "1"
        assert result.summary == "Test Event"

    @pytest.mark.asyncio
    async def test_create_event(self, mock_client):
        """Test create_event sends correct body."""
        mock_response = {"id": "new_1", "summary": "New Event"}
        with patch.object(mock_client, "_request", return_value=mock_response) as mock_req:
            result = await mock_client.create_event(
                summary="New Event",
                start_datetime="2026-03-15T10:00:00Z",
                end_datetime="2026-03-15T11:00:00Z",
                attendees=["alice@example.com"],
            )
        assert result.id == "new_1"
        call_args = mock_req.call_args
        body = call_args.kwargs["json_data"]
        assert body["summary"] == "New Event"
        assert body["attendees"] == [{"email": "alice@example.com"}]

    @pytest.mark.asyncio
    async def test_delete_event(self, mock_client):
        """Test delete_event makes DELETE request."""
        with patch.object(mock_client, "_request", return_value={}) as mock_req:
            await mock_client.delete_event("evt_1")
        mock_req.assert_called_once_with("DELETE", "/calendars/primary/events/evt_1")

    @pytest.mark.asyncio
    async def test_quick_add_event(self, mock_client):
        """Test quick_add_event sends text as param."""
        mock_response = {"id": "qa_1", "summary": "Lunch"}
        with patch.object(mock_client, "_request", return_value=mock_response) as mock_req:
            result = await mock_client.quick_add_event("Lunch tomorrow at noon")
        assert result.id == "qa_1"
        call_args = mock_req.call_args
        assert call_args.kwargs["params"] == {"text": "Lunch tomorrow at noon"}

    @pytest.mark.asyncio
    async def test_list_calendars(self, mock_client):
        """Test list_calendars returns CalendarListResponse."""
        mock_response = {"items": [{"id": "primary", "summary": "My Calendar"}]}
        with patch.object(mock_client, "_request", return_value=mock_response):
            result = await mock_client.list_calendars()
        assert len(result.items) == 1
        assert result.items[0].id == "primary"

    @pytest.mark.asyncio
    async def test_query_freebusy(self, mock_client):
        """Test query_freebusy sends correct body."""
        mock_response = {
            "timeMin": "2026-03-15T00:00:00Z",
            "timeMax": "2026-03-16T00:00:00Z",
            "calendars": {"primary": {"busy": []}},
        }
        with patch.object(mock_client, "_request", return_value=mock_response) as mock_req:
            result = await mock_client.query_freebusy(
                time_min="2026-03-15T00:00:00Z",
                time_max="2026-03-16T00:00:00Z",
            )
        assert "primary" in result.calendars
        body = mock_req.call_args.kwargs["json_data"]
        assert body["items"] == [{"id": "primary"}]


class TestErrorHandling:
    """Test error handling for API errors."""

    @pytest.mark.asyncio
    async def test_401_unauthorized(self, mock_client):
        """Test handling of unauthorized errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=GoogleCalendarAPIError(401, "Invalid API key"),
        ):
            with pytest.raises(GoogleCalendarAPIError) as exc_info:
                await mock_client.list_events()
            assert exc_info.value.status == 401

    @pytest.mark.asyncio
    async def test_429_rate_limit(self, mock_client):
        """Test handling of rate limit errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=GoogleCalendarAPIError(429, "Rate limit exceeded"),
        ):
            with pytest.raises(GoogleCalendarAPIError) as exc_info:
                await mock_client.list_events()
            assert exc_info.value.status == 429

    @pytest.mark.asyncio
    async def test_network_error(self, mock_client):
        """Test handling of network errors."""
        with patch.object(
            mock_client,
            "_request",
            side_effect=GoogleCalendarAPIError(500, "Network error: Connection failed"),
        ):
            with pytest.raises(GoogleCalendarAPIError) as exc_info:
                await mock_client.list_events()
            assert exc_info.value.status == 500
            assert "Network error" in exc_info.value.message

    def test_error_string_representation(self):
        """Test error string format."""
        err = GoogleCalendarAPIError(401, "Unauthorized", {"id": "auth_error"})
        assert "401" in str(err)
        assert "Unauthorized" in str(err)
        assert err.details == {"id": "auth_error"}
