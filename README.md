# Google Calendar MCP Server

An MCP (Model Context Protocol) server that provides access to the Google Calendar API, allowing AI assistants to interact with Google Calendar data.

## Features

- List and retrieve items from the Google Calendar API
- Async HTTP client with error handling
- Typed responses with Pydantic models

## Installation

### Using mpak (Recommended)

```bash
# Configure your API key
mpak config set @JoeCardoso13/google-calendar access_token=your_oauth_token_here

# Run the server
mpak run @JoeCardoso13/google-calendar
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/NimbleBrainInc/mcp-google-calendar.git
cd mcp-google-calendar

# Install dependencies with uv
uv sync

# Set your OAuth access token
export GOOGLE_CALENDAR_ACCESS_TOKEN=your_oauth_token_here

# Run the server
uv run python -m mcp_google_calendar.server
```

## Configuration

### Getting Your Access Token

Google Calendar requires OAuth 2.0 access tokens (not API keys). The easiest way to get one for testing:

1. Go to https://developers.google.com/oauthplayground/
2. Select "Google Calendar API v3" and check the scopes you need
3. Click "Authorize APIs" and sign in with your Google account
4. Click "Exchange authorization code for tokens"
5. Copy the access token (expires after 1 hour)

### Claude Desktop Configuration

Add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "google-calendar": {
      "command": "mpak",
      "args": ["run", "@JoeCardoso13/google-calendar"]
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_items` | List items from the API with optional limit |
| `get_item` | Get a single item by its ID |

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format src/ tests/

# Lint
uv run ruff check src/ tests/

# Type check
uv run ty check src/

# Run all checks
make check
```

## License

MIT
