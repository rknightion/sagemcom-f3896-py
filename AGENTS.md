# sagemcom-f3896-py

Python async client for the Sagemcom F3896 cable modem REST API, with a Prometheus metrics exporter
and CLI.

## Task interface

`just check` is the gate and must pass before you commit. It mirrors the `lint` and `test` jobs in
`.github/workflows/python.yaml`, whose single required status check is `ci-success`.

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

## Tracking work

Work is tracked in this repository's GitHub issues; they are the only queue. Do not add a checklist
file beside them.

- A pull request body says how it relates to an issue, on a line of its own: `Closes #N` with the
  `Acceptance evidence` table from `.github/pull_request_template.md` (one row for each acceptance
  criterion of that issue), `Refs #N` when it only relates to one, or `Task: none, <reason>`.
- A pull request that changes `.github/workflows/` or `.github/actions/` carries no closing keyword:
  write `Task: none, <reason>`, with `Refs #N` beside it if you like.
- Contributors never need the project board or the tracker tooling; a maintainer handles both.
- Issues and pull requests are public, so they never carry real identifiers. For this project that
  means no modem MAC addresses, serial numbers, CM/CMTS identifiers, boot file names, ISP account or
  subscriber IDs, WAN IP addresses, or `/rest/v1/...` response bodies pasted verbatim off a live
  modem. Write the shape, not the instance - `<mac>`, `<serial>`, `<flow-id>`. Aggregate counts,
  channel counts, timings and structural findings are fine. Pull request CI sweeps the lines a pull
  request adds.
- Older commits, docs and tests cite legacy board ids such as `FSG-0001`. `just issue <ID>` prints
  the issue each one became; `.github/tracker/id-map.json` is the map. The retired board's documents
  are in `.github/tracker/history/`.
