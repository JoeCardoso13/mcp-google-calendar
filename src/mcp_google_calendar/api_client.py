"""Async HTTP client for Google Calendar API."""

import os
from typing import Any

import aiohttp
from aiohttp import ClientError

from .api_models import (
    CalendarListEntry,
    CalendarListResponse,
    Event,
    EventListResponse,
    FreeBusyResponse,
)


class GoogleCalendarAPIError(Exception):
    """Exception raised for Google Calendar API errors."""

    def __init__(self, status: int, message: str, details: dict[str, Any] | None = None) -> None:
        self.status = status
        self.message = message
        self.details = details
        super().__init__(f"Google Calendar API Error {status}: {message}")


class GoogleCalendarClient:
    """Async client for Google Calendar API."""

    BASE_URL = "https://www.googleapis.com/calendar/v3"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("GOOGLE_CALENDAR_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_CALENDAR_API_KEY is required")
        self.timeout = timeout
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "GoogleCalendarClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def _ensure_session(self) -> None:
        if not self._session:
            headers = {
                "User-Agent": "mcp-server-google-calendar/0.1.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            self._session = aiohttp.ClientSession(
                headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: Any | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Google Calendar API."""
        await self._ensure_session()
        url = f"{self.BASE_URL}{path}"

        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            if not self._session:
                raise RuntimeError("Session not initialized")

            kwargs: dict[str, Any] = {}
            if json_data is not None:
                kwargs["json"] = json_data
            if params:
                kwargs["params"] = params

            async with self._session.request(method, url, **kwargs) as response:
                if response.status == 204:
                    return {}

                result = await response.json()

                if response.status >= 400:
                    error_msg = "Unknown error"
                    if isinstance(result, dict):
                        if "error" in result:
                            error_obj = result["error"]
                            if isinstance(error_obj, dict):
                                error_msg = error_obj.get("message", str(error_obj))
                            else:
                                error_msg = str(error_obj)
                        elif "message" in result:
                            error_msg = result["message"]

                    raise GoogleCalendarAPIError(response.status, error_msg, result)

                return result

        except ClientError as e:
            raise GoogleCalendarAPIError(500, f"Network error: {str(e)}") from e

    # ========================================================================
    # Calendar List
    # ========================================================================

    async def list_calendars(self, page_token: str | None = None) -> CalendarListResponse:
        """List all calendars the user has access to."""
        params: dict[str, Any] = {}
        if page_token:
            params["pageToken"] = page_token
        data = await self._request("GET", "/users/me/calendarList", params=params or None)
        return CalendarListResponse(**data)

    async def get_calendar(self, calendar_id: str) -> CalendarListEntry:
        """Get metadata for a specific calendar."""
        data = await self._request("GET", f"/users/me/calendarList/{calendar_id}")
        return CalendarListEntry(**data)

    # ========================================================================
    # Events
    # ========================================================================

    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: str | None = None,
        time_max: str | None = None,
        max_results: int | None = None,
        page_token: str | None = None,
        single_events: bool = True,
        order_by: str | None = "startTime",
        q: str | None = None,
    ) -> EventListResponse:
        """List events from a calendar."""
        params: dict[str, Any] = {"singleEvents": str(single_events).lower()}
        if time_min:
            params["timeMin"] = time_min
        if time_max:
            params["timeMax"] = time_max
        if max_results:
            params["maxResults"] = str(max_results)
        if page_token:
            params["pageToken"] = page_token
        if order_by and single_events:
            params["orderBy"] = order_by
        if q:
            params["q"] = q
        data = await self._request("GET", f"/calendars/{calendar_id}/events", params=params)
        return EventListResponse(**data)

    async def get_event(self, event_id: str, calendar_id: str = "primary") -> Event:
        """Get a single event by ID."""
        data = await self._request("GET", f"/calendars/{calendar_id}/events/{event_id}")
        return Event(**data)

    async def create_event(
        self,
        calendar_id: str = "primary",
        summary: str | None = None,
        description: str | None = None,
        location: str | None = None,
        start_datetime: str | None = None,
        start_date: str | None = None,
        start_timezone: str | None = None,
        end_datetime: str | None = None,
        end_date: str | None = None,
        end_timezone: str | None = None,
        attendees: list[str] | None = None,
        recurrence: list[str] | None = None,
    ) -> Event:
        """Create a new calendar event."""
        body: dict[str, Any] = {}
        if summary:
            body["summary"] = summary
        if description:
            body["description"] = description
        if location:
            body["location"] = location

        start: dict[str, str] = {}
        if start_datetime:
            start["dateTime"] = start_datetime
        elif start_date:
            start["date"] = start_date
        if start_timezone:
            start["timeZone"] = start_timezone
        if start:
            body["start"] = start

        end: dict[str, str] = {}
        if end_datetime:
            end["dateTime"] = end_datetime
        elif end_date:
            end["date"] = end_date
        if end_timezone:
            end["timeZone"] = end_timezone
        if end:
            body["end"] = end

        if attendees:
            body["attendees"] = [{"email": email} for email in attendees]
        if recurrence:
            body["recurrence"] = recurrence

        data = await self._request("POST", f"/calendars/{calendar_id}/events", json_data=body)
        return Event(**data)

    async def update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: str | None = None,
        description: str | None = None,
        location: str | None = None,
        start_datetime: str | None = None,
        start_date: str | None = None,
        start_timezone: str | None = None,
        end_datetime: str | None = None,
        end_date: str | None = None,
        end_timezone: str | None = None,
        attendees: list[str] | None = None,
    ) -> Event:
        """Update an existing event (PATCH)."""
        body: dict[str, Any] = {}
        if summary is not None:
            body["summary"] = summary
        if description is not None:
            body["description"] = description
        if location is not None:
            body["location"] = location

        start: dict[str, str] = {}
        if start_datetime:
            start["dateTime"] = start_datetime
        elif start_date:
            start["date"] = start_date
        if start_timezone:
            start["timeZone"] = start_timezone
        if start:
            body["start"] = start

        end: dict[str, str] = {}
        if end_datetime:
            end["dateTime"] = end_datetime
        elif end_date:
            end["date"] = end_date
        if end_timezone:
            end["timeZone"] = end_timezone
        if end:
            body["end"] = end

        if attendees is not None:
            body["attendees"] = [{"email": email} for email in attendees]

        data = await self._request(
            "PATCH", f"/calendars/{calendar_id}/events/{event_id}", json_data=body
        )
        return Event(**data)

    async def delete_event(self, event_id: str, calendar_id: str = "primary") -> None:
        """Delete an event."""
        await self._request("DELETE", f"/calendars/{calendar_id}/events/{event_id}")

    async def quick_add_event(self, text: str, calendar_id: str = "primary") -> Event:
        """Create an event from a natural language string."""
        data = await self._request(
            "POST",
            f"/calendars/{calendar_id}/events/quickAdd",
            params={"text": text},
        )
        return Event(**data)

    async def search_events(
        self,
        query: str,
        calendar_id: str = "primary",
        time_min: str | None = None,
        time_max: str | None = None,
        max_results: int | None = None,
    ) -> EventListResponse:
        """Full-text search across events."""
        return await self.list_events(
            calendar_id=calendar_id,
            q=query,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
        )

    # ========================================================================
    # Free/Busy
    # ========================================================================

    async def query_freebusy(
        self,
        time_min: str,
        time_max: str,
        calendar_ids: list[str] | None = None,
    ) -> FreeBusyResponse:
        """Query free/busy status for calendars."""
        items = [{"id": cid} for cid in (calendar_ids or ["primary"])]
        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": items,
        }
        data = await self._request("POST", "/freeBusy", json_data=body)
        return FreeBusyResponse(**data)
