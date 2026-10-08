# DataAgentX

An evaluable and observable AI Agent platform for enterprise data analysis,
with RAG, tool calling, and long-term memory.

## Status

Currently under active development.

## Configuration

The `dataagentx` command reads these environment variables at startup:

| Variable | Default | Meaning |
| --- | --- | --- |
| `DATAAGENTX_HOST` | `127.0.0.1` | Server bind address |
| `DATAAGENTX_PORT` | `8000` | Integer port from 1 to 65535 |

```bash
DATAAGENTX_HOST=127.0.0.1 DATAAGENTX_PORT=9000 .venv/bin/dataagentx
```

Unset variables use their defaults. An empty or invalid port raises `ValueError`
before the server starts. Settings are read on each call to `load_settings()`;
no `.env` file is loaded automatically. These settings apply to the `dataagentx`
entry point; a direct `uvicorn` invocation uses its own command-line settings.

Run all tests with `.venv/bin/python -m pytest`.

## Roadmap

Project direction and progress are documented separately:

- [Project charter](docs/PROJECT_CHARTER.md): goals, boundaries, priorities, and success criteria
- [Roadmap](docs/ROADMAP.md): milestone-level progress
- [Architecture](docs/ARCHITECTURE.md): the currently implemented system
