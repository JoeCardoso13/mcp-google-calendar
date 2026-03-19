# Google Calendar MCP Server

MCP server providing Google Calendar API functionality via FastMCP.

## Architecture

```
src/mcp_google_calendar/
├── server.py      # MCP tools (FastMCP) + entrypoints
├── api_client.py  # Async HTTP client for Google Calendar API
└── api_models.py  # Pydantic models for API responses
```

## Critical

- Package name: `@JoeCardoso13/google-calendar` (npm-style scope, matches GitHub org)
- Manifest uses module execution: `python -m mcp_google_calendar.server`
- Server needs both entrypoints:
  ```python
  app = mcp.http_app()  # HTTP deployment
  if __name__ == "__main__":
      mcp.run()  # Stdio for Claude Desktop / mpak
  ```
- All logs to stderr (stdout is reserved for JSON-RPC)

## user_config

OAuth access token configured via manifest `user_config`, not hardcoded:
```json
{
  "user_config": {
    "access_token": {
      "type": "string",
      "sensitive": true,
      "required": true
    }
  },
  "server": {
    "mcp_config": {
      "env": { "GOOGLE_CALENDAR_ACCESS_TOKEN": "${user_config.access_token}" }
    }
  }
}
```

## Tooling

- **Package manager**: uv (not pip)
- **Linting/formatting**: ruff (not flake8, black, isort)
- **Type checking**: ty (not mypy, pyright)
- **Testing**: pytest with pytest-asyncio

## Commands

```bash
uv sync --dev               # Install dependencies
uv run ruff format src/ tests/   # Format
uv run ruff check src/ tests/    # Lint
uv run ty check src/             # Type check
uv run pytest tests/ -v          # Test
make check                       # All of the above
```

## Version Management

Version lives in four files that MUST stay in sync:

| File | Field |
|------|-------|
| `manifest.json` | `version` |
| `server.json` | `version` |
| `pyproject.toml` | `version` |
| `src/mcp_google_calendar/__init__.py` | `__version__` |

Bump all at once: `make bump VERSION=0.2.0`

## Releasing

```bash
make bump VERSION=0.2.0
git add -A && git commit -m "Bump version to 0.2.0"
git tag v0.2.0 && git push origin main v0.2.0
gh release create v0.2.0 --title "v0.2.0" --notes "- changelog"
```

GitHub Actions builds and uploads MCPB bundles automatically on release.

## Adding New Tools

1. Add response model to `api_models.py`
2. Add client method to `api_client.py`
3. Add `@mcp.tool()` function to `server.py`
4. Add tests to `tests/`
5. Run `make check` to verify
