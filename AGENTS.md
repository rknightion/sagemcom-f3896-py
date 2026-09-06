# sagemcom-f3896-py

Python async client for the Sagemcom F3896 cable modem REST API, with a Prometheus metrics exporter
and CLI.

## Task interface

`just check` is the gate and must pass before you commit. It is also the `definition_of_done` in
`backlog/config.yml`, so every new task inherits it as a checklist, and it mirrors the `lint` and
`test` jobs in `.github/workflows/python.yaml` whose single required status check is `ci-success`.

- Run `just` with stdin from `/dev/null`. `just clean` is `[confirm]`-gated and destroys `.venv`,
  `dist/`, `htmlcov/` and the caches; ask before running it and never pass `--yes` or `JUST_YES=1`.
- No recipe covers running the programs; do that directly:

      uv run python -m sagemcom_f3896_client.cli --help
      uv run python -m sagemcom_f3896_client.exporter -v   # listens on 8080

## Environment

- `MODEM_PASSWORD` - required for authenticated endpoints and integration tests.
- `MODEM_URL` - modem base URL, default `https://192.168.100.1`. It is HTTPS with a self-signed
  certificate, so the test fixture disables hostname checking and verification.

## Code style

Ruff only: `ruff` for lint, `ruff format` for formatting. Do not add black, flake8 or isort, and do
not write config for them - `.pre-commit-config.yaml` configures the two ruff hooks and nothing else.

- `line-length = 88` with `E501` ignored, in `[tool.ruff]` in `pyproject.toml`.
- `requires-python = ">=3.14"`.
- `exporter.py` is exempt from `E402` on purpose. It must call `warnings.filterwarnings()` before
  importing `prometheus_async`, which otherwise emits a `SyntaxWarning` at import from its Twisted
  module. Moving those imports to the top of the file reintroduces the warning.

## Gotchas

- The integration tests in `tests/test_client.py` and `tests/test_client_session.py` need a real
  modem. `requires_modem_password()` in `tests/util.py` skips them cleanly when `MODEM_PASSWORD` is
  unset, so a green local run is not the same coverage as a run against hardware. Say which one you
  got.
- The client auto-manages login and logout sessions. Some REST endpoints need no auth; the set is
  `UNAUTHORIZED_ENDPOINTS` in `client.py`.

## Task tracking

- `backlog/` is committed, so tasks and docs never carry real identifiers. For this project that
  means no modem MAC addresses, serial numbers, CM/CMTS identifiers, boot file names, ISP account or
  subscriber IDs, WAN IP addresses, or `/rest/v1/...` response bodies pasted verbatim off a live
  modem. Write the shape, not the instance - `<mac>`, `<serial>`, `<flow-id>`. Aggregate counts,
  channel counts, timings and structural findings are fine. Sweep before committing:

      grep -rniE "rknightion|rob-knight|m7kni|@gmail|([0-9a-f]{2}:){5}[0-9a-f]{2}" backlog/ && echo "PII FOUND"

- `backlog/config.yml` is the one file exempt from driving the tracker through its CLI, because
  list-valued keys cannot be set through `backlog config set`.
- Finalize in one call: `backlog task edit FSG-0001 --check-ac 1 --check-ac 2 -s Done`. The shipped
  guides check criteria at one step and set status several steps later, so anything interrupting in
  between leaves the task inconsistent.
- Never let two agents edit the same task. The upstream concurrent-write fix covers the edit funnel
  but not reorder, draft saves, the TUI edit path, `doc update` or decision updates.

Read the `Agent fan-out protocol (canonical)` doc before designing a wave, and `Wave operating model`
for this project's own rules. Both are in `backlog/docs/`; view with `backlog doc view <id> --plain`.

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
