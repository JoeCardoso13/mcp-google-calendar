"""Pydantic models for Google Calendar API responses."""

from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Common / Nested Models
# ============================================================================


class DateTimeEntry(BaseModel):
    """Start or end time for an event."""

    model_config = {"populate_by_name": True}

    date: str | None = Field(None, description="All-day date (yyyy-mm-dd)")
    date_time: str | None = Field(None, alias="dateTime", description="RFC3339 timestamp")
    time_zone: str | None = Field(None, alias="timeZone", description="IANA timezone")


class Person(BaseModel):
    """Creator or organizer of an event."""

    model_config = {"populate_by_name": True}

    email: str | None = Field(None, description="Email address")
    display_name: str | None = Field(None, alias="displayName", description="Display name")
    self_: bool | None = Field(None, alias="self", description="Whether this is the current user")


class Attendee(BaseModel):
    """An event attendee."""

    model_config = {"populate_by_name": True}

    email: str = Field(..., description="Attendee email")
    display_name: str | None = Field(None, alias="displayName", description="Display name")
    response_status: str | None = Field(
        None,
        alias="responseStatus",
        description="needsAction, declined, tentative, or accepted",
    )
    optional: bool | None = Field(None, description="Whether attendance is optional")


class ReminderOverride(BaseModel):
    """A custom reminder override."""

    method: str = Field(..., description="email or popup")
    minutes: int = Field(..., description="Minutes before event")


class Reminders(BaseModel):
    """Reminder settings for an event."""

    model_config = {"populate_by_name": True}

    use_default: bool | None = Field(None, alias="useDefault", description="Use calendar defaults")
    overrides: list[ReminderOverride] | None = Field(None, description="Custom reminders (max 5)")


class ConferenceEntryPoint(BaseModel):
    """An entry point to a conference."""

    model_config = {"populate_by_name": True}

    entry_point_type: str | None = Field(
        None, alias="entryPointType", description="video, phone, sip, more"
    )
    uri: str | None = Field(None, description="URI to join")
    label: str | None = Field(None, description="Display label")


class ConferenceData(BaseModel):
    """Conference/meeting data attached to an event."""

    model_config = {"populate_by_name": True}

    conference_id: str | None = Field(None, alias="conferenceId", description="Conference ID")
    entry_points: list[ConferenceEntryPoint] | None = Field(
        None, alias="entryPoints", description="Ways to join"
    )


# ============================================================================
# Event Model
# ============================================================================


class Event(BaseModel):
    """A Google Calendar event."""

    model_config = {"populate_by_name": True}

    id: str | None = Field(None, description="Event ID")
    status: str | None = Field(None, description="confirmed, tentative, or cancelled")
    summary: str | None = Field(None, description="Event title")
    description: str | None = Field(None, description="Event description")
    location: str | None = Field(None, description="Event location")
    html_link: str | None = Field(None, alias="htmlLink", description="Link to Google Calendar UI")
    start: DateTimeEntry | None = Field(None, description="Start time")
    end: DateTimeEntry | None = Field(None, description="End time")
    created: str | None = Field(None, description="Creation timestamp")
    updated: str | None = Field(None, description="Last modification timestamp")
    creator: Person | None = Field(None, description="Event creator")
    organizer: Person | None = Field(None, description="Event organizer")
    attendees: list[Attendee] | None = Field(None, description="Event attendees")
    recurrence: list[str] | None = Field(None, description="RRULE/EXRULE recurrence rules")
    recurring_event_id: str | None = Field(
        None, alias="recurringEventId", description="Parent recurring event ID"
    )
    color_id: str | None = Field(None, alias="colorId", description="Color ID")
    visibility: str | None = Field(None, description="default, public, private, confidential")
    transparency: str | None = Field(None, description="opaque (busy) or transparent (free)")
    reminders: Reminders | None = Field(None, description="Reminder settings")
    conference_data: ConferenceData | None = Field(
        None, alias="conferenceData", description="Conference/meeting data"
    )
    event_type: str | None = Field(None, alias="eventType", description="Event type")
    hangout_link: str | None = Field(None, alias="hangoutLink", description="Google Meet link")


# ============================================================================
# List / FreeBusy Response Models
# ============================================================================


class EventListResponse(BaseModel):
    """Response from events.list."""

    model_config = {"populate_by_name": True}

    items: list[Event] = Field(default_factory=list)
    next_page_token: str | None = Field(None, alias="nextPageToken")
    summary: str | None = Field(None, description="Calendar summary")
    time_zone: str | None = Field(None, alias="timeZone", description="Calendar timezone")


class CalendarListEntry(BaseModel):
    """A calendar in the user's calendar list."""

    model_config = {"populate_by_name": True}

    id: str = Field(..., description="Calendar ID")
    summary: str | None = Field(None, description="Calendar title")
    description: str | None = Field(None, description="Calendar description")
    primary: bool | None = Field(None, description="Whether this is the primary calendar")
    time_zone: str | None = Field(None, alias="timeZone", description="Calendar timezone")
    access_role: str | None = Field(
        None,
        alias="accessRole",
        description="Effective access role: freeBusyReader, reader, writer, owner",
    )
    background_color: str | None = Field(
        None, alias="backgroundColor", description="Background color hex"
    )
    foreground_color: str | None = Field(
        None, alias="foregroundColor", description="Foreground color hex"
    )


class CalendarListResponse(BaseModel):
    """Response from calendarList.list."""

    model_config = {"populate_by_name": True}

    items: list[CalendarListEntry] = Field(default_factory=list)
    next_page_token: str | None = Field(None, alias="nextPageToken")


class FreeBusyCalendar(BaseModel):
    """Free/busy info for a single calendar."""

    busy: list[dict[str, Any]] = Field(default_factory=list, description="Busy time ranges")
    errors: list[dict[str, Any]] | None = Field(None, description="Errors for this calendar")


class FreeBusyResponse(BaseModel):
    """Response from freebusy.query."""

    model_config = {"populate_by_name": True}

    time_min: str | None = Field(None, alias="timeMin")
    time_max: str | None = Field(None, alias="timeMax")
    calendars: dict[str, FreeBusyCalendar] = Field(default_factory=dict)
