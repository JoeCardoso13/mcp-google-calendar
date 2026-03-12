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
mpak config set @JoeCardoso13/google-calendar api_key=your_api_key_here

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

# Set your API key
export GOOGLE_CALENDAR_API_KEY=your_api_key_here

# Run the server
uv run python -m mcp_google_calendar.server
```

## Configuration

### Getting Your API Key

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new API key
3. Copy the key

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
