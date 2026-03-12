"""Tests for Google Calendar MCP Server tools and skill resource."""

import json
from unittest.mock import patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from mcp_google_calendar.api_client import GoogleCalendarAPIError
from mcp_google_calendar.server import SKILL_CONTENT


def _get_text(result) -> str:
    """Extract text from a call_tool result (handles both list and CallToolResult)."""
    if isinstance(result, list):
        return result[0].text if hasattr(result[0], "text") else str(result[0])
    if hasattr(result, "content"):
        content = result.content
        if isinstance(content, list):
            return content[0].text if hasattr(content[0], "text") else str(content[0])
    if hasattr(result, "text"):
        return result.text
    return str(result)


class TestSkillResource:
    """Test the skill resource and server instructions."""

    @pytest.mark.asyncio
    async def test_initialize_returns_instructions(self, mcp_server):
        """Server instructions reference the skill resource."""
        async with Client(mcp_server) as client:
            result = await client.initialize()
            assert result.instructions is not None
            assert "skill://google-calendar/usage" in result.instructions

    @pytest.mark.asyncio
    async def test_skill_resource_listed(self, mcp_server):
        """skill://google-calendar/usage appears in resource listing."""
        async with Client(mcp_server) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert "skill://google-calendar/usage" in uris

    @pytest.mark.asyncio
    async def test_skill_resource_readable(self, mcp_server):
        """Reading the skill resource returns the full skill content."""
        async with Client(mcp_server) as client:
            contents = await client.read_resource("skill://google-calendar/usage")
            text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])
            assert "list_events" in text
            assert "create_event" in text

    @pytest.mark.asyncio
    async def test_skill_content_matches_constant(self, mcp_server):
        """Resource content matches the SKILL_CONTENT constant."""
        async with Client(mcp_server) as client:
            contents = await client.read_resource("skill://google-calendar/usage")
            text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])
            assert text == SKILL_CONTENT


class TestToolListing:
    """Test that all tools are registered and discoverable."""

    @pytest.mark.asyncio
    async def test_all_tools_listed(self, mcp_server):
        """All expected tools appear in tool listing."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            names = {t.name for t in tools}
            expected = {
                "list_calendars",
                "get_calendar",
                "list_events",
                "get_event",
                "create_event",
                "update_event",
                "delete_event",
                "quick_add_event",
                "search_events",
                "query_freebusy",
            }
            assert expected == names


class TestCalendarTools:
    """Test calendar-related tools."""

    @pytest.mark.asyncio
    async def test_list_calendars(self, mcp_server, mock_client):
        """Test list_calendars returns calendar list."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("list_calendars", {})
            parsed = json.loads(_get_text(result))
            assert len(parsed["calendars"]) == 2
            mock_client.list_calendars.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_calendar(self, mcp_server, mock_client):
        """Test get_calendar returns calendar details."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("get_calendar", {"calendar_id": "primary"})
            parsed = json.loads(_get_text(result))
            assert parsed["id"] == "primary"


class TestEventTools:
    """Test event-related tools."""

    @pytest.mark.asyncio
    async def test_list_events(self, mcp_server, mock_client):
        """Test list_events returns event list."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("list_events", {})
            parsed = json.loads(_get_text(result))
            assert len(parsed["events"]) == 1
            assert parsed["events"][0]["summary"] == "Test Event"

    @pytest.mark.asyncio
    async def test_get_event(self, mcp_server, mock_client):
        """Test get_event returns event details."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("get_event", {"event_id": "evt_1"})
            parsed = json.loads(_get_text(result))
            assert parsed["id"] == "evt_1"
            assert parsed["summary"] == "Test Event"

    @pytest.mark.asyncio
    async def test_create_event(self, mcp_server, mock_client):
        """Test create_event creates and returns an event."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "create_event",
                    {
                        "summary": "New Meeting",
                        "start_datetime": "2026-03-15T10:00:00Z",
                        "end_datetime": "2026-03-15T11:00:00Z",
                    },
                )
            assert result is not None
            mock_client.create_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_event(self, mcp_server, mock_client):
        """Test update_event updates an event."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "update_event",
                    {"event_id": "evt_1", "summary": "Updated Meeting"},
                )
            assert result is not None
            mock_client.update_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_event(self, mcp_server, mock_client):
        """Test delete_event deletes an event."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("delete_event", {"event_id": "evt_1"})
            parsed = json.loads(_get_text(result))
            assert parsed["status"] == "deleted"
            mock_client.delete_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_quick_add_event(self, mcp_server, mock_client):
        """Test quick_add_event creates from natural language."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "quick_add_event", {"text": "Lunch tomorrow at noon"}
                )
            assert result is not None
            mock_client.quick_add_event.assert_called_once_with(
                "Lunch tomorrow at noon", calendar_id="primary"
            )

    @pytest.mark.asyncio
    async def test_search_events(self, mcp_server, mock_client):
        """Test search_events performs text search."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool("search_events", {"query": "meeting"})
            parsed = json.loads(_get_text(result))
            assert parsed["query"] == "meeting"
            assert len(parsed["events"]) == 1


class TestFreeBusy:
    """Test free/busy tool."""

    @pytest.mark.asyncio
    async def test_query_freebusy(self, mcp_server, mock_client):
        """Test query_freebusy returns busy times."""
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "query_freebusy",
                    {
                        "time_min": "2026-03-15T00:00:00Z",
                        "time_max": "2026-03-16T00:00:00Z",
                    },
                )
            parsed = json.loads(_get_text(result))
            assert "primary" in parsed["calendars"]
            assert len(parsed["calendars"]["primary"]["busy"]) == 1


class TestErrorHandling:
    """Test error propagation from API."""

    @pytest.mark.asyncio
    async def test_list_events_api_error(self, mcp_server, mock_client):
        """Test list_events handles API errors."""
        mock_client.list_events.side_effect = GoogleCalendarAPIError(401, "Unauthorized")
        with patch("mcp_google_calendar.server.get_client", return_value=mock_client):
            async with Client(mcp_server) as client:
                with pytest.raises(ToolError, match="401"):
                    await client.call_tool("list_events", {})
