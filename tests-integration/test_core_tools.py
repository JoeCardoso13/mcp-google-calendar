"""
Core tools integration tests.

Tests basic API functionality with real API calls against Google Calendar.
Requires GOOGLE_CALENDAR_ACCESS_TOKEN (an OAuth 2.0 access token) to be set.
"""

from datetime import UTC, datetime, timedelta

import pytest

from mcp_google_calendar.api_client import GoogleCalendarClient

# ============================================================================
# Calendar List
# ============================================================================


class TestListCalendars:
    @pytest.mark.asyncio
    async def test_list_calendars(self, client: GoogleCalendarClient):
        result = await client.list_calendars()
        assert len(result.items) >= 1
        # Every account has at least a primary calendar
        ids = {cal.id for cal in result.items}
        print(f"Found {len(result.items)} calendars: {ids}")
        # Primary calendar should be present
        primary = [cal for cal in result.items if cal.primary]
        assert len(primary) == 1
        assert primary[0].id is not None


class TestGetCalendar:
    @pytest.mark.asyncio
    async def test_get_primary_calendar(self, client: GoogleCalendarClient):
        result = await client.get_calendar("primary")
        assert result.id is not None
        assert result.access_role is not None
        print(f"Primary calendar: {result.summary} ({result.id})")


# ============================================================================
# Events — Read
# ============================================================================


class TestListEvents:
    @pytest.mark.asyncio
    async def test_list_events(self, client: GoogleCalendarClient):
        now = datetime.now(UTC).isoformat()
        result = await client.list_events(
            calendar_id="primary",
            time_min=now,
            max_results=5,
        )
        # Response shape is correct even if no upcoming events
        assert result.items is not None
        print(f"Found {len(result.items)} upcoming events")


class TestSearchEvents:
    @pytest.mark.asyncio
    async def test_search_events(self, client: GoogleCalendarClient):
        result = await client.search_events(
            query="meeting",
            calendar_id="primary",
            max_results=5,
        )
        assert result.items is not None
        print(f"Search returned {len(result.items)} events matching 'meeting'")


class TestGetEvent:
    @pytest.mark.asyncio
    async def test_get_event(self, client: GoogleCalendarClient):
        """Get an event by listing first, then fetching by ID."""
        now = datetime.now(UTC)
        # Look back 30 days to increase chance of finding an event
        time_min = (now - timedelta(days=30)).isoformat()
        time_max = (now + timedelta(days=30)).isoformat()
        events = await client.list_events(
            calendar_id="primary",
            time_min=time_min,
            time_max=time_max,
            max_results=5,
        )
        if not events.items:
            pytest.skip("No events found to test get_event")

        event_id = events.items[0].id
        assert event_id is not None
        result = await client.get_event(event_id, calendar_id="primary")
        assert result.id == event_id
        print(f"Fetched event: {result.summary} ({result.id})")


# ============================================================================
# Events — Write (CRUD lifecycle)
# ============================================================================


class TestEventCRUD:
    @pytest.mark.asyncio
    async def test_event_lifecycle(self, client: GoogleCalendarClient):
        """Create -> update -> verify -> delete an event."""
        event = None
        try:
            # Create
            now = datetime.now(UTC)
            start = (now + timedelta(hours=1)).isoformat()
            end = (now + timedelta(hours=2)).isoformat()

            event = await client.create_event(
                calendar_id="primary",
                summary="integration-test-event",
                description="Created by integration test — safe to delete",
                start_datetime=start,
                end_datetime=end,
                start_timezone="UTC",
                end_timezone="UTC",
            )
            assert event.id is not None
            assert event.summary == "integration-test-event"
            print(f"Created event: {event.id}")

            # Update
            updated = await client.update_event(
                event_id=event.id,
                calendar_id="primary",
                summary="integration-test-event-updated",
                location="Test Location",
            )
            assert updated.id == event.id
            assert updated.summary == "integration-test-event-updated"
            assert updated.location == "Test Location"
            print(f"Updated event: {updated.id}")

            # Get to verify
            fetched = await client.get_event(event.id, calendar_id="primary")
            assert fetched.id == event.id
            assert fetched.summary == "integration-test-event-updated"
            print(f"Verified event: {fetched.summary}")

        finally:
            if event and event.id:
                await client.delete_event(event.id, calendar_id="primary")
                print(f"Cleaned up event: {event.id}")


class TestQuickAddEvent:
    @pytest.mark.asyncio
    async def test_quick_add_event(self, client: GoogleCalendarClient):
        """Create an event via natural language, then delete it."""
        event = None
        try:
            event = await client.quick_add_event(
                text="Integration test meeting tomorrow at 3pm",
                calendar_id="primary",
            )
            assert event.id is not None
            print(f"Quick-added event: {event.summary} ({event.id})")
        finally:
            if event and event.id:
                await client.delete_event(event.id, calendar_id="primary")
                print(f"Cleaned up event: {event.id}")


# ============================================================================
# Free/Busy
# ============================================================================


class TestQueryFreebusy:
    @pytest.mark.asyncio
    async def test_query_freebusy(self, client: GoogleCalendarClient):
        now = datetime.now(UTC)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=7)).isoformat()

        result = await client.query_freebusy(
            time_min=time_min,
            time_max=time_max,
            calendar_ids=["primary"],
        )
        assert result.calendars is not None
        assert "primary" in result.calendars
        busy_count = len(result.calendars["primary"].busy)
        print(f"Free/busy query returned {busy_count} busy blocks in next 7 days")
