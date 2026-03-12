"""Shared fixtures for unit tests."""

from unittest.mock import AsyncMock

import pytest

from mcp_google_calendar.api_models import (
    CalendarListEntry,
    CalendarListResponse,
    Event,
    EventListResponse,
    FreeBusyCalendar,
    FreeBusyResponse,
)
from mcp_google_calendar.server import mcp


@pytest.fixture
def mcp_server():
    """Return the MCP server instance."""
    return mcp


@pytest.fixture
def mock_client():
    """Create a mock API client with Google Calendar methods."""
    client = AsyncMock()

    # Calendar methods
    client.list_calendars = AsyncMock(
        return_value=CalendarListResponse(
            items=[
                CalendarListEntry(id="primary", summary="My Calendar"),
                CalendarListEntry(id="work@group.calendar.google.com", summary="Work"),
            ]
        )
    )
    client.get_calendar = AsyncMock(
        return_value=CalendarListEntry(
            id="primary", summary="My Calendar", **{"timeZone": "America/New_York"}
        )
    )

    # Event methods
    sample_event = Event(
        id="evt_1",
        summary="Test Event",
        status="confirmed",
        **{
            "start": {"dateTime": "2026-03-15T10:00:00Z"},
            "end": {"dateTime": "2026-03-15T11:00:00Z"},
            "htmlLink": "https://calendar.google.com/event?eid=abc",
        },
    )
    client.list_events = AsyncMock(return_value=EventListResponse(items=[sample_event]))
    client.get_event = AsyncMock(return_value=sample_event)
    client.create_event = AsyncMock(return_value=sample_event)
    client.update_event = AsyncMock(return_value=sample_event)
    client.delete_event = AsyncMock(return_value=None)
    client.quick_add_event = AsyncMock(return_value=sample_event)
    client.search_events = AsyncMock(return_value=EventListResponse(items=[sample_event]))

    # FreeBusy
    client.query_freebusy = AsyncMock(
        return_value=FreeBusyResponse(
            **{
                "timeMin": "2026-03-15T00:00:00Z",
                "timeMax": "2026-03-16T00:00:00Z",
            },
            calendars={
                "primary": FreeBusyCalendar(
                    busy=[{"start": "2026-03-15T10:00:00Z", "end": "2026-03-15T11:00:00Z"}]
                )
            },
        )
    )

    return client
