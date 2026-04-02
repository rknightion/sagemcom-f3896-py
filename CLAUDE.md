# Sagemcom F3896 Client

Python async client for the Sagemcom F3896 cable modem REST API, with a Prometheus metrics exporter and CLI.

## Commands

```bash
uv sync                       # Install dependencies
uv run pytest                 # Run tests (some need MODEM_PASSWORD env var)
uv run pytest -x -q           # Quick test run, stop on first failure

# Lint (pre-commit hooks: black, flake8, isort, ruff)
pre-commit run --all-files

# Run CLI
uv run python -m sagemcom_f3896_client.cli --help

# Run Prometheus exporter
uv run python -m sagemcom_f3896_client.exporter -v
```

## Architecture

- `sagemcom_f3896_client/client.py` — Async aiohttp client (`SagemcomModemClient`, `SagemcomModemSessionClient`) for the modem REST API
- `sagemcom_f3896_client/models.py` — Dataclass models for API responses
- `sagemcom_f3896_client/exporter.py` — Prometheus metrics exporter (port 8080)
- `sagemcom_f3896_client/cli.py` — Click CLI for modem status, logs, reboot
- `sagemcom_f3896_client/log_parser.py` — Parses modem event log messages
- `sagemcom_f3896_client/profile_messages.py` — Tracks DOCSIS profile change messages

## Environment Variables

- `MODEM_PASSWORD` — Required for authenticated endpoints and integration tests
- `MODEM_URL` — Modem base URL (default: `http://192.168.100.1`)

## Code Style

- Formatter: black (target Python 3.10)
- Linter: ruff + flake8
- Import sorting: isort (black-compatible profile)

## Gotchas

- Integration tests in `tests/test_client.py` and `tests/test_client_session.py` require a real modem — they use `MODEM_PASSWORD` from env
- The client auto-manages login/logout sessions; some REST endpoints don't require auth (see `UNAUTHORIZED_ENDPOINTS` in `client.py`)
- pytest-asyncio is used for async test support
