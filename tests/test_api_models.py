"""Tests for Google Calendar API models."""

from mcp_google_calendar.api_models import (
    Attendee,
    CalendarListEntry,
    CalendarListResponse,
    DateTimeEntry,
    Event,
    EventListResponse,
    FreeBusyCalendar,
    FreeBusyResponse,
)


def test_date_time_entry_datetime() -> None:
    """Test DateTimeEntry with dateTime."""
    data = {"dateTime": "2026-03-15T10:00:00-05:00", "timeZone": "America/New_York"}
    entry = DateTimeEntry(**data)
    assert entry.date_time == "2026-03-15T10:00:00-05:00"
    assert entry.time_zone == "America/New_York"
    assert entry.date is None


def test_date_time_entry_date() -> None:
    """Test DateTimeEntry with all-day date."""
    entry = DateTimeEntry(date="2026-03-15")
    assert entry.date == "2026-03-15"
    assert entry.date_time is None


def test_event_full() -> None:
    """Test Event model with all major fields."""
    data = {
        "id": "event_123",
        "status": "confirmed",
        "summary": "Team Meeting",
        "description": "Weekly sync",
        "location": "Conference Room A",
        "htmlLink": "https://calendar.google.com/event?eid=abc",
        "start": {"dateTime": "2026-03-15T10:00:00Z"},
        "end": {"dateTime": "2026-03-15T11:00:00Z"},
        "created": "2026-03-01T00:00:00Z",
        "updated": "2026-03-10T00:00:00Z",
        "attendees": [
            {"email": "alice@example.com", "responseStatus": "accepted"},
            {"email": "bob@example.com", "displayName": "Bob", "responseStatus": "tentative"},
        ],
        "organizer": {"email": "alice@example.com", "displayName": "Alice"},
        "hangoutLink": "https://meet.google.com/abc-def-ghi",
    }
    event = Event(**data)
    assert event.id == "event_123"
    assert event.summary == "Team Meeting"
    assert event.start is not None
    assert event.start.date_time == "2026-03-15T10:00:00Z"
    assert event.end is not None
    assert event.end.date_time == "2026-03-15T11:00:00Z"
    assert event.attendees is not None
    assert len(event.attendees) == 2
    assert event.attendees[0].email == "alice@example.com"
    assert event.organizer is not None
    assert event.organizer.display_name == "Alice"
    assert event.hangout_link == "https://meet.google.com/abc-def-ghi"


def test_event_minimal() -> None:
    """Test Event model with only ID."""
    event = Event(id="event_456")
    assert event.id == "event_456"
    assert event.summary is None
    assert event.attendees is None


def test_event_all_day() -> None:
    """Test Event with all-day dates."""
    data = {
        "id": "allday_1",
        "summary": "Vacation",
        "start": {"date": "2026-03-20"},
        "end": {"date": "2026-03-25"},
    }
    event = Event(**data)
    assert event.start is not None
    assert event.start.date == "2026-03-20"
    assert event.start.date_time is None


def test_attendee_model() -> None:
    """Test Attendee model."""
    data = {
        "email": "test@example.com",
        "displayName": "Test User",
        "responseStatus": "accepted",
        "optional": True,
    }
    attendee = Attendee(**data)
    assert attendee.email == "test@example.com"
    assert attendee.display_name == "Test User"
    assert attendee.response_status == "accepted"
    assert attendee.optional is True


def test_event_list_response() -> None:
    """Test EventListResponse model."""
    data = {
        "items": [
            {"id": "1", "summary": "Event 1"},
            {"id": "2", "summary": "Event 2"},
        ],
        "nextPageToken": "token_abc",
        "summary": "My Calendar",
        "timeZone": "America/New_York",
    }
    response = EventListResponse(**data)
    assert len(response.items) == 2
    assert response.items[0].summary == "Event 1"
    assert response.next_page_token == "token_abc"
    assert response.time_zone == "America/New_York"


def test_event_list_response_empty() -> None:
    """Test EventListResponse with no events."""
    response = EventListResponse()
    assert response.items == []
    assert response.next_page_token is None


def test_calendar_list_entry() -> None:
    """Test CalendarListEntry model."""
    data = {
        "id": "primary",
        "summary": "My Calendar",
        "primary": True,
        "timeZone": "America/New_York",
        "accessRole": "owner",
        "backgroundColor": "#4285f4",
    }
    entry = CalendarListEntry(**data)
    assert entry.id == "primary"
    assert entry.summary == "My Calendar"
    assert entry.primary is True
    assert entry.access_role == "owner"


def test_calendar_list_response() -> None:
    """Test CalendarListResponse model."""
    data = {
        "items": [
            {"id": "primary", "summary": "My Calendar"},
            {"id": "work@group.calendar.google.com", "summary": "Work"},
        ],
        "nextPageToken": "page2",
    }
    response = CalendarListResponse(**data)
    assert len(response.items) == 2
    assert response.next_page_token == "page2"


def test_freebusy_response() -> None:
    """Test FreeBusyResponse model."""
    data = {
        "timeMin": "2026-03-15T00:00:00Z",
        "timeMax": "2026-03-16T00:00:00Z",
        "calendars": {
            "primary": {
                "busy": [
                    {"start": "2026-03-15T10:00:00Z", "end": "2026-03-15T11:00:00Z"},
                ]
            }
        },
    }
    response = FreeBusyResponse(**data)
    assert response.time_min == "2026-03-15T00:00:00Z"
    assert "primary" in response.calendars
    assert len(response.calendars["primary"].busy) == 1


def test_freebusy_calendar_empty() -> None:
    """Test FreeBusyCalendar with no busy times."""
    cal = FreeBusyCalendar()
    assert cal.busy == []
    assert cal.errors is None
