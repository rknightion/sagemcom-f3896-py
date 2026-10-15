# Loop: sagemcom-f3896-py
tier: guarded
gate: just check
ci-required: ci-success
grafana-stack: none

`backlog/` is committed: write the shape, not the instance (`<mac>`, `<serial>`, `<flow-id>`). The PII
sweep is in `AGENTS.md`. Run `just` with stdin from `/dev/null`.

## Credentials

- `MODEM_PASSWORD` for the single physical modem on the owner's line is the root's. A lane never needs
  it: build against recorded response shapes.

## Traps

- With no `MODEM_PASSWORD` the integration tests in `tests/test_client.py` and
  `tests/test_client_session.py` skip themselves and the gate still exits 0. A lane reporting the gate
  green states exactly which run it got (passed and skipped counts, or the hardware run). A change to
  `client.py`, `models.py` or `conftest.py` needs hardware-backed verification before Done; with no
  modem available it is Parked, not Done.
- `tests/test_exporter.py` is an empty file, so `exporter.py` (the largest module, holding all metric
  naming, label and aggregation logic) has no regression net: a lane adding metrics writes its own tests.
- Module-level metrics in `exporter.py` register into the global `REGISTRY` at import; a duplicate name
  fails as a collection error across the whole suite. Prefer the per-scrape `CollectorRegistry`; a new
  module-level metric is a shared-seam change.
- `exporter.py` imports are deliberately not at the top: the `warnings.filterwarnings` call must run
  before `prometheus_async` is imported, and `pyproject.toml` carries a per-file `E402` ignore for it.
  Never reorder or sort those lines.
- Check a claim in the instructions against the config that would implement it: ruff and ruff-format
  are the only formatters configured.

## Mutexes

- The modem is exclusive: one lane at a time, and only the root. It tracks one session server-side
  (the `conftest.py` fixture logs out in teardown), `cli.py` can reboot it and take the household
  offline, and event-log-derived state (`log_parser.py`, `ProfileMessageStore`) is destructive to read
  concurrently. No reboot unless it is the stated purpose and the only modem work in the run.
- `exporter.py` has one owning lane; metric work is serialised behind it, never split by metric family.
  Free seams: `log_parser.py`, `profile_messages.py`, `models.py` with their tests, and CI files.
  `client.py` and `models.py` in two lanes need the model dataclass signatures frozen first.
- `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml` and `.github/workflows/`: one lane or the
  wiring pass.
