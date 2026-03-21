"""
Smoke test: verify the LLM reads the skill resource and selects the correct tool.

Requires ANTHROPIC_API_KEY and GOOGLE_CALENDAR_ACCESS_TOKEN in environment.
"""

import os

import anthropic
import pytest
from fastmcp import Client

from mcp_google_calendar.server import mcp


def get_anthropic_client() -> anthropic.Anthropic:
    token = os.environ.get("ANTHROPIC_API_KEY")
    if not token:
        pytest.skip("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=token)


async def get_server_context() -> dict:
    """Extract instructions, skill content, and tool definitions from the MCP server."""
    async with Client(mcp) as client:
        init = await client.initialize()
        instructions = init.instructions

        resources = await client.list_resources()
        skill_text = ""
        for r in resources:
            if "skill://" in str(r.uri):
                contents = await client.read_resource(str(r.uri))
                skill_text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])

        tools_list = await client.list_tools()
        tools = []
        for t in tools_list:
            tool_def = {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema,
            }
            tools.append(tool_def)

        return {
            "instructions": instructions,
            "skill": skill_text,
            "tools": tools,
        }


async def call_llm(prompt: str) -> list:
    """Send a prompt to Claude Haiku with server context and return tool calls."""
    ctx = await get_server_context()
    client = get_anthropic_client()

    system = (
        "You are an assistant.\n\n"
        f"## Server Instructions\n{ctx['instructions']}\n\n"
        f"## Skill Resource\n{ctx['skill']}"
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"type": "custom", **t} for t in ctx["tools"]],
    )

    return [b for b in response.content if b.type == "tool_use"]


class TestSkillLLMInvocation:
    """Verify the skill resource guides the LLM to select the correct tool."""

    @pytest.mark.asyncio
    async def test_list_calendars_selected(self):
        """'What calendars do I have?' -> list_calendars"""
        tool_calls = await call_llm("What calendars do I have?")
        assert len(tool_calls) > 0, "LLM did not call any tool"
        assert tool_calls[0].name == "list_calendars"

    @pytest.mark.asyncio
    async def test_list_events_selected(self):
        """'What events do I have this week?' -> list_events"""
        tool_calls = await call_llm("What events do I have this week?")
        assert len(tool_calls) > 0, "LLM did not call any tool"
        assert tool_calls[0].name == "list_events"

    @pytest.mark.asyncio
    async def test_create_event_selected(self):
        """Specific meeting details -> create_event (not quick_add_event)"""
        tool_calls = await call_llm(
            "Schedule a team meeting tomorrow at 2pm to 3pm with attendees alice@example.com and bob@example.com"
        )
        assert len(tool_calls) > 0, "LLM did not call any tool"
        assert tool_calls[0].name == "create_event"

    @pytest.mark.asyncio
    async def test_quick_add_event_selected(self):
        """Conversational event description -> quick_add_event"""
        tool_calls = await call_llm("Add lunch with Sarah next Friday at noon")
        assert len(tool_calls) > 0, "LLM did not call any tool"
        assert tool_calls[0].name == "quick_add_event"

    @pytest.mark.asyncio
    async def test_query_freebusy_selected(self):
        """Availability check -> query_freebusy"""
        tool_calls = await call_llm(
            "Am I busy tomorrow afternoon?"
        )
        assert len(tool_calls) > 0, "LLM did not call any tool"
        assert tool_calls[0].name == "query_freebusy"
