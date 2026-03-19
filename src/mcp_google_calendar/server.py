"""Google Calendar MCP Server - FastMCP Implementation."""

import logging
import os
import sys
from importlib.resources import files

from fastmcp import Context, FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_google_calendar.api_client import GoogleCalendarAPIError, GoogleCalendarClient
from mcp_google_calendar.api_models import Event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_google_calendar")

SKILL_CONTENT = files("mcp_google_calendar").joinpath("SKILL.md").read_text()

mcp = FastMCP(
    "Google Calendar",
    instructions=(
        "Before using tools, read the skill://google-calendar/usage resource "
        "for tool selection guidance and workflow patterns."
    ),
)

_client: GoogleCalendarClient | None = None


def get_client(ctx: Context | None = None) -> GoogleCalendarClient:
    global _client
    if _client is None:
        access_token = os.environ.get("GOOGLE_CALENDAR_ACCESS_TOKEN")
        if not access_token:
            raise ValueError("GOOGLE_CALENDAR_ACCESS_TOKEN environment variable is required")
        _client = GoogleCalendarClient(access_token=access_token)
    return _client


@mcp.resource("skill://google-calendar/usage")
def get_skill() -> str:
    """Tool selection guide and workflow patterns for this server."""
    return SKILL_CONTENT


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "mcp-google-calendar"})


# ============================================================================
# Calendar Tools
# ============================================================================


@mcp.tool()
async def list_calendars(
    page_token: str | None = None,
    ctx: Context | None = None,
) -> str:
    """List all calendars the user has access to.

    Args:
        page_token: Token for fetching the next page of results
        ctx: MCP context

    Returns:
        JSON list of calendars with id, summary, timezone, and access role
    """
    client = get_client(ctx)
    try:
        result = await client.list_calendars(page_token=page_token)
        calendars = [
            {
                "id": c.id,
                "summary": c.summary,
                "primary": c.primary,
                "timeZone": c.time_zone,
                "accessRole": c.access_role,
            }
            for c in result.items
        ]
        response: dict = {"calendars": calendars}
        if result.next_page_token:
            response["nextPageToken"] = result.next_page_token
        return _to_json(response)
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def get_calendar(
    calendar_id: str,
    ctx: Context | None = None,
) -> str:
    """Get metadata for a specific calendar.

    Args:
        calendar_id: Calendar ID (use 'primary' for the user's primary calendar)
        ctx: MCP context

    Returns:
        JSON object with calendar details
    """
    client = get_client(ctx)
    try:
        c = await client.get_calendar(calendar_id)
        return _to_json(
            {
                "id": c.id,
                "summary": c.summary,
                "description": c.description,
                "primary": c.primary,
                "timeZone": c.time_zone,
                "accessRole": c.access_role,
            }
        )
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# Event Tools
# ============================================================================


@mcp.tool()
async def list_events(
    calendar_id: str = "primary",
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int | None = None,
    page_token: str | None = None,
    order_by: str | None = "startTime",
    ctx: Context | None = None,
) -> str:
    """List events from a calendar within a time range.

    Args:
        calendar_id: Calendar ID (default: 'primary')
        time_min: Start of time range (RFC3339, e.g. '2026-03-01T00:00:00Z')
        time_max: End of time range (RFC3339)
        max_results: Maximum number of events to return
        page_token: Token for next page of results
        order_by: Sort order: 'startTime' (default) or 'updated'
        ctx: MCP context

    Returns:
        JSON list of events with summary, time, location, and attendees
    """
    client = get_client(ctx)
    try:
        result = await client.list_events(
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            page_token=page_token,
            order_by=order_by,
        )
        events = [_format_event(e) for e in result.items]
        response: dict = {"events": events}
        if result.next_page_token:
            response["nextPageToken"] = result.next_page_token
        return _to_json(response)
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def get_event(
    event_id: str,
    calendar_id: str = "primary",
    ctx: Context | None = None,
) -> str:
    """Get a single event by ID.

    Args:
        event_id: The event ID
        calendar_id: Calendar ID (default: 'primary')
        ctx: MCP context

    Returns:
        JSON object with full event details
    """
    client = get_client(ctx)
    try:
        event = await client.get_event(event_id, calendar_id=calendar_id)
        return _to_json(_format_event(event))
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def create_event(
    summary: str,
    start_datetime: str | None = None,
    start_date: str | None = None,
    end_datetime: str | None = None,
    end_date: str | None = None,
    description: str | None = None,
    location: str | None = None,
    timezone: str | None = None,
    attendees: list[str] | None = None,
    recurrence: list[str] | None = None,
    calendar_id: str = "primary",
    ctx: Context | None = None,
) -> str:
    """Create a new calendar event.

    For timed events, provide start_datetime and end_datetime (RFC3339).
    For all-day events, provide start_date and end_date (yyyy-mm-dd).

    Args:
        summary: Event title
        start_datetime: Start time (RFC3339, e.g. '2026-03-15T10:00:00-05:00')
        start_date: Start date for all-day events (yyyy-mm-dd)
        end_datetime: End time (RFC3339)
        end_date: End date for all-day events (yyyy-mm-dd, exclusive)
        description: Event description
        location: Event location
        timezone: IANA timezone (e.g. 'America/New_York')
        attendees: List of attendee email addresses
        recurrence: RRULE strings (e.g. ['RRULE:FREQ=WEEKLY;COUNT=10'])
        calendar_id: Calendar ID (default: 'primary')
        ctx: MCP context

    Returns:
        JSON object with the created event details
    """
    client = get_client(ctx)
    try:
        event = await client.create_event(
            calendar_id=calendar_id,
            summary=summary,
            description=description,
            location=location,
            start_datetime=start_datetime,
            start_date=start_date,
            start_timezone=timezone,
            end_datetime=end_datetime,
            end_date=end_date,
            end_timezone=timezone,
            attendees=attendees,
            recurrence=recurrence,
        )
        return _to_json(_format_event(event))
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def update_event(
    event_id: str,
    summary: str | None = None,
    start_datetime: str | None = None,
    start_date: str | None = None,
    end_datetime: str | None = None,
    end_date: str | None = None,
    description: str | None = None,
    location: str | None = None,
    timezone: str | None = None,
    attendees: list[str] | None = None,
    calendar_id: str = "primary",
    ctx: Context | None = None,
) -> str:
    """Update an existing calendar event. Only provided fields are changed.

    Args:
        event_id: The event ID to update
        summary: New event title
        start_datetime: New start time (RFC3339)
        start_date: New start date for all-day events (yyyy-mm-dd)
        end_datetime: New end time (RFC3339)
        end_date: New end date for all-day events (yyyy-mm-dd)
        description: New description
        location: New location
        timezone: IANA timezone
        attendees: New list of attendee email addresses (replaces existing)
        calendar_id: Calendar ID (default: 'primary')
        ctx: MCP context

    Returns:
        JSON object with the updated event details
    """
    client = get_client(ctx)
    try:
        event = await client.update_event(
            event_id=event_id,
            calendar_id=calendar_id,
            summary=summary,
            description=description,
            location=location,
            start_datetime=start_datetime,
            start_date=start_date,
            start_timezone=timezone,
            end_datetime=end_datetime,
            end_date=end_date,
            end_timezone=timezone,
            attendees=attendees,
        )
        return _to_json(_format_event(event))
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def delete_event(
    event_id: str,
    calendar_id: str = "primary",
    ctx: Context | None = None,
) -> str:
    """Delete a calendar event.

    Args:
        event_id: The event ID to delete
        calendar_id: Calendar ID (default: 'primary')
        ctx: MCP context

    Returns:
        Confirmation message
    """
    client = get_client(ctx)
    try:
        await client.delete_event(event_id, calendar_id=calendar_id)
        return _to_json({"status": "deleted", "eventId": event_id})
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def quick_add_event(
    text: str,
    calendar_id: str = "primary",
    ctx: Context | None = None,
) -> str:
    """Create an event from a natural language string.

    Examples: "Lunch with Bob tomorrow at noon", "Team standup every weekday 9am"

    Args:
        text: Natural language description of the event
        calendar_id: Calendar ID (default: 'primary')
        ctx: MCP context

    Returns:
        JSON object with the created event details
    """
    client = get_client(ctx)
    try:
        event = await client.quick_add_event(text, calendar_id=calendar_id)
        return _to_json(_format_event(event))
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


@mcp.tool()
async def search_events(
    query: str,
    calendar_id: str = "primary",
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int | None = None,
    ctx: Context | None = None,
) -> str:
    """Full-text search across event summaries, descriptions, and locations.

    Args:
        query: Search text
        calendar_id: Calendar ID (default: 'primary')
        time_min: Start of time range (RFC3339)
        time_max: End of time range (RFC3339)
        max_results: Maximum number of events to return
        ctx: MCP context

    Returns:
        JSON list of matching events
    """
    client = get_client(ctx)
    try:
        result = await client.search_events(
            query=query,
            calendar_id=calendar_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
        )
        events = [_format_event(e) for e in result.items]
        return _to_json({"events": events, "query": query})
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# Free/Busy Tool
# ============================================================================


@mcp.tool()
async def query_freebusy(
    time_min: str,
    time_max: str,
    calendar_ids: list[str] | None = None,
    ctx: Context | None = None,
) -> str:
    """Check free/busy status for one or more calendars in a time range.

    Args:
        time_min: Start of time range (RFC3339)
        time_max: End of time range (RFC3339)
        calendar_ids: List of calendar IDs to check (default: ['primary'])
        ctx: MCP context

    Returns:
        JSON object with busy time ranges per calendar
    """
    client = get_client(ctx)
    try:
        result = await client.query_freebusy(
            time_min=time_min,
            time_max=time_max,
            calendar_ids=calendar_ids,
        )
        return _to_json(
            {
                "timeMin": result.time_min,
                "timeMax": result.time_max,
                "calendars": {
                    cal_id: {"busy": cal.busy} for cal_id, cal in result.calendars.items()
                },
            }
        )
    except GoogleCalendarAPIError as e:
        if ctx:
            await ctx.error(f"API error: {e.message}")
        raise


# ============================================================================
# Helpers
# ============================================================================


def _format_event(event: Event) -> dict:
    """Format an event for tool output."""

    result: dict = {"id": event.id, "summary": event.summary}
    if event.start:
        result["start"] = event.start.date_time or event.start.date
    if event.end:
        result["end"] = event.end.date_time or event.end.date
    if event.location:
        result["location"] = event.location
    if event.description:
        result["description"] = event.description
    if event.status:
        result["status"] = event.status
    if event.html_link:
        result["htmlLink"] = event.html_link
    if event.attendees:
        result["attendees"] = [
            {
                "email": a.email,
                "displayName": a.display_name,
                "responseStatus": a.response_status,
            }
            for a in event.attendees
        ]
    if event.organizer:
        result["organizer"] = {
            "email": event.organizer.email,
            "displayName": event.organizer.display_name,
        }
    if event.hangout_link:
        result["meetLink"] = event.hangout_link
    if event.recurrence:
        result["recurrence"] = event.recurrence
    return result


def _to_json(data: dict) -> str:
    """Serialize a dict to JSON string."""
    import json

    return json.dumps(data, indent=2, default=str)


# ASGI app for HTTP deployment
app = mcp.http_app()

# Stdio entrypoint for Claude Desktop / mpak
if __name__ == "__main__":
    mcp.run()
