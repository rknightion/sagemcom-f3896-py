# sagemcom-f3896-py

Python async client for the Sagemcom F3896 cable modem REST API, with a Prometheus metrics
exporter and CLI.

This file is canonical for contributor and agent instructions. `CLAUDE.md` imports it, so Claude
Code and Codex read the same text and cannot drift apart.

## Commands

```bash
uv sync                       # Install dependencies
uv run pytest tests           # Run tests (integration tests skip without MODEM_PASSWORD)
uv run pytest -x -q           # Quick run, stop on first failure

uv run ruff check .           # Lint
uv run ruff format --check .  # Formatting gate (CI runs --check, not a rewrite)
pre-commit run --all-files    # Same ruff pair, via the hook config

uv run python -m sagemcom_f3896_client.cli --help   # CLI
uv run python -m sagemcom_f3896_client.exporter -v  # Exporter, port 8080
```

The three gate commands are also `definition_of_done` in `backlog/config.yml`, so every new task
inherits them as a checklist. They mirror the `lint` and `test` jobs in
`.github/workflows/python.yaml`, whose single required status check is `ci-success`.

## Architecture

- `sagemcom_f3896_client/client.py` — async aiohttp client (`SagemcomModemClient`,
  `SagemcomModemSessionClient`) for the modem REST API
- `sagemcom_f3896_client/models.py` — dataclass models for API responses
- `sagemcom_f3896_client/exporter.py` — Prometheus metrics exporter
- `sagemcom_f3896_client/cli.py` — Click CLI for modem status, logs, reboot
- `sagemcom_f3896_client/log_parser.py` — parses modem event log messages
- `sagemcom_f3896_client/profile_messages.py` — tracks DOCSIS profile change messages

## Environment variables

- `MODEM_PASSWORD` — required for authenticated endpoints and integration tests
- `MODEM_URL` — modem base URL (default `http://192.168.100.1`)

## Code style

Ruff only — `ruff` for lint and `ruff format` for formatting, and nothing else. An earlier version
of these instructions listed black, flake8 and isort; that was **wrong**, and
`.pre-commit-config.yaml` has only ever configured the two ruff hooks. Do not reintroduce the other
three or write config for them.

- `line-length = 88`, `E501` ignored (see `[tool.ruff]` in `pyproject.toml`)
- `requires-python = ">=3.14"`
- `exporter.py` is exempt from `E402` on purpose: it must call `warnings.filterwarnings()` before
  importing `prometheus_async`, which emits a `SyntaxWarning` at import on Python 3.14+. Moving
  those imports to the top of the file reintroduces the warning.

## Gotchas

- Integration tests in `tests/test_client.py` and `tests/test_client_session.py` need a real modem.
  They read `MODEM_PASSWORD` from the environment and **skip** cleanly without it, so a green local
  run is not the same coverage as a run against hardware. Say which one you got.
- The client auto-manages login/logout sessions. Some REST endpoints need no auth — see
  `UNAUTHORIZED_ENDPOINTS` in `client.py`.
- pytest-asyncio provides the async test support.

## Task tracking

Work is tracked with [Backlog.md](https://github.com/MrLesk/Backlog.md) in `backlog/`, driven
through its CLI. `backlog task list --plain` is the queue; `backlog doc list --plain` is the durable
documentation.

Read the **Agent fan-out protocol (canonical)** doc before designing a wave, and the **Wave
operating model** doc for this project's own rules. Both are in `backlog/docs/`; view them with
`backlog doc view <id> --plain`.

### Non-negotiable rules

These sit outside the tool-managed marker block below so upstream instruction updates leave them
alone.

**`backlog/` is committed to git, so tasks and docs must never contain real identifiers.** For this
project that specifically means: no modem MAC addresses, serial numbers, CM/CMTS identifiers, boot
file names, ISP account or subscriber IDs, WAN IP addresses, or captured `/rest/v1/...` response
bodies pasted verbatim from a live modem. Write the shape, not the instance — `<mac>`, `<serial>`,
`<flow-id>`. Aggregate counts, channel counts, timings and structural findings are fine. Sweep
before committing:

```bash
grep -rniE "rknightion|rob-knight|m7kni|@gmail|([0-9a-f]{2}:){5}[0-9a-f]{2}" backlog/ && echo "PII FOUND"
```

**Never use `--notes` or `--plan` bare.** They *silently replace* the whole section — another
session's writes vanish with no warning and exit 0. Use `--append-notes` and `--append-plan`. This
is an open upstream bug, not a misunderstanding. A global `PreToolUse` hook in the agent config denies the bare
forms at `PreToolUse` rather than trusting anyone to remember.

**Finalize in one call**, so an interrupted agent cannot leave finished work looking unfinished:

```bash
backlog task edit FSG-0001 --check-ac 1 --check-ac 2 -s Done
```

The shipped guides check criteria at one step and set status several steps later. Anything
interrupting in between — a context limit, a session ending — leaves the task inconsistent.

**Never hand-edit task, draft, doc, decision or milestone markdown.** Section boundaries are
HTML-comment markers; break one and the section is *silently dropped* at exit 0, with the data
still in the file but invisible to the CLI until the next write destroys it for real. There is no
repair command — `backlog doctor` only fixes duplicate task IDs. The guard hook blocks writes to
those directories. `backlog/config.yml` is the one exception and may be edited by hand, because
list-valued keys cannot be set through `backlog config set`.

**Never let two agents edit the same task.** v1.50.x fixed the concurrent-write race in the edit
funnel but not in reorder, draft saves, the TUI edit path, `doc update` or decision updates.

<!-- BACKLOG.MD GUIDELINES START -->
<!-- backlog.md-instructions-version: 1.50.1 -->
<CRITICAL_INSTRUCTION>

## Backlog.md Workflow

This project uses Backlog.md for task and project management.

**For every user request in this project, run `backlog instructions overview` before answering or taking action.**

Use the overview to decide whether to search, read, create, or update Backlog tasks.

Before task lifecycle actions, read the matching detailed guide:
- `backlog instructions task-creation` before creating or splitting tasks
- `backlog instructions task-execution` before planning, changing status or assignee, adding a plan or implementation notes, or implementing task work
- `backlog instructions task-finalization` before checking acceptance criteria, writing final summaries, or moving tasks to terminal statuses

Use `backlog <command> --help` before running unfamiliar commands. Help shows options, fields, and examples.

Do not edit Backlog task, draft, document, decision, or milestone markdown files directly. Use the `backlog` CLI so metadata, relationships, and history stay consistent.

</CRITICAL_INSTRUCTION>
<!-- BACKLOG.MD GUIDELINES END -->
