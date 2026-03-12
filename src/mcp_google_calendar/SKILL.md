---
name: mcp-google-calendar-service
description: Provides knowledge of how to use MCP Google Calendar most effectively. It's loaded into the agent's context when running the MCP.
---

# Google Calendar MCP Server — Skill Guide

## Tools

| Tool | Use when... |
|------|-------------|
| `list_calendars` | You need to see which calendars the user has |
| `get_calendar` | You need details about a specific calendar |
| `list_events` | You need to browse events in a time range |
| `get_event` | You have an event ID and need full details |
| `create_event` | You need to schedule a new event with specific details |
| `update_event` | You need to change an existing event |
| `delete_event` | You need to remove an event |
| `quick_add_event` | The user describes an event in natural language |
| `search_events` | You need to find events by keyword |
| `query_freebusy` | You need to check availability before scheduling |

## Context Reuse

- Use the `id` from `list_events` or `search_events` results when calling `get_event`, `update_event`, or `delete_event`
- Use calendar IDs from `list_calendars` when targeting a specific calendar
- Default calendar ID is `"primary"` — you don't need to call `list_calendars` first for the user's main calendar

## Tool Selection

- Prefer `quick_add_event` when the user describes an event conversationally (e.g. "lunch with Bob tomorrow at noon") — it handles natural language parsing
- Use `create_event` when you need precise control over start/end times, attendees, recurrence, or location
- Use `query_freebusy` before `create_event` when you need to find an available time slot
- Use `search_events` instead of `list_events` when the user is looking for a specific event by keyword

## Workflows

### 1. Schedule a Meeting
1. `query_freebusy` to check availability
2. `create_event` with attendees, time, and location

### 2. Find and Update an Event
1. `search_events` to find the event by keyword
2. `update_event` with the event ID and new details

### 3. Daily Agenda
1. `list_events` with `time_min` = start of day, `time_max` = end of day

### 4. Quick Scheduling
1. `quick_add_event` with the user's natural language description
