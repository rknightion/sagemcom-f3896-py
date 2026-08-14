---
id: doc-0002
title: Wave operating model
type: guide
created_date: '2026-08-14 16:55'
updated_date: '2026-08-14 16:56'
---
This project's own rules. The campaign model itself — run contract, run modes, routing, the thread
pool, child lane briefs, contract freezing, the goal-file template, the pre-flight checklist — lives
in the **Agent fan-out protocol (canonical)** doc and is not repeated here. If something below could
be pasted into another repository unchanged, it is in the wrong document.

## The exclusive resource: there is one modem

`http://192.168.100.1` is a single physical Sagemcom F3896 on Rob's line. It is the only instance
that exists, it serves the household's actual internet connection, and it cannot be cloned,
containerised or stood up per lane.

**At most one lane may hold the modem at a time, and holding it is stated in the goal file, not
assumed.** Three properties make this stricter than a normal shared fixture:

- **The client authenticates with a session the modem tracks server-side.** `SagemcomModemSessionClient`
  logs in, and `conftest.py`'s fixture logs out in teardown. Two lanes authenticating concurrently
  contend for that session, so the failure shows up as an authentication or logout error in a lane
  that did nothing wrong — a misleading signal that costs a debugging cycle to attribute.
- **`cli.py` can reboot the modem.** A reboot drops the line for minutes and resets exactly the
  counters (uptime, error totals, profile history, event log) that another lane's assertions read.
  **No lane may issue a reboot without it being the lane's stated purpose and the only modem work in
  the wave.** A reboot also takes the household offline, which makes it a real-world action, not a
  test step.
- **Event-log-derived state is destructive to read against.** `log_parser.py` and
  `ProfileMessageStore` build state from a rolling modem event log. Two lanes exercising it see
  interleaved reality, and neither can tell which entries were its own.

For anything that is not specifically about talking to hardware, **do not take the modem** — build
against recorded response shapes instead.

## The trap that will bite a wave first: 64% of the suite skips silently

`uv run pytest tests` with no `MODEM_PASSWORD` in the environment reports **9 passed, 16 skipped**
(measured 2026-08-14). The integration tests in `tests/test_client.py` and
`tests/test_client_session.py` skip themselves when the variable is absent. Exit code 0. Green.

So a lane can change `client.py` substantially, run the gate, see it pass, and have exercised **none
of the code it touched**. This is the repo's most expensive failure mode because the wrong signal is
indistinguishable from the right one at a glance.

**Every lane that reports the gate green must state which run it got** — `9 passed, 16 skipped`
(no hardware) or the full run against the modem. A bare "tests pass" is not an acceptable lane
report here and should be sent back. When a change touches `client.py`, `models.py` or
`conftest.py`, hardware-backed verification is required before the task reaches `Done`; if the modem
was unavailable, that is a `Parked` task with the boundary recorded, not a `Done` one.

## Recurring defects in this codebase

**`tests/test_exporter.py` is an empty file — 0 lines.** `exporter.py` is 711 lines, the largest
module in the project and the one carrying all the metric-naming, label and aggregation logic, and
it has no unit tests at all. Two consequences for wave design: a lane adding metrics has no
regression net, so its own tests are part of the deliverable rather than optional; and the file's
emptiness is easy to mistake for coverage that exists, because the file *is* there and pytest
collects it without complaint.

**Module-level metrics register into the global `REGISTRY` at import.** `MODEM_METRICS_DURATION`,
`MODEM_UPDATE_COUNT` and `MODEM_LAST_UPDATE` are created at `exporter.py` module scope, so importing
the module has the side effect of registering three collectors globally. Per-scrape metrics go into
a fresh `CollectorRegistry` instead, and `metrics()` concatenates the two. Anything that imports
`exporter` twice, or that adds a module-level metric whose name already exists, raises a duplicate
registration error at import time — which surfaces as a collection error across the whole suite, not
as a failure in the file that caused it. **Prefer the per-scrape registry; adding a module-level
metric is a change to a shared seam and needs stating in the goal file.**

**`exporter.py`'s imports are deliberately not at the top of the file, and ruff is configured to
allow it.** `warnings.filterwarnings("ignore", message="'return' in a 'finally' block")` must run
before `prometheus_async` is imported, because its Twisted module emits a `SyntaxWarning` on Python
3.14+. `pyproject.toml` carries a per-file `E402` ignore for exactly this. A lane doing a tidy-up
pass — "move the imports to the top", "sort the imports" — silently reintroduces the warning while
leaving the linter happy. Do not reorder those lines. The commit that established this is `8d3ea2e`.

**The instructions themselves drifted and were wrong.** Until this migration, `CLAUDE.md` documented
the formatter as black with flake8 and isort. `.pre-commit-config.yaml` has only ever configured
ruff and ruff-format. A lane that trusted the instructions would have written config for three tools
the project does not use. `AGENTS.md` is now the single canonical file and `CLAUDE.md` imports it,
so that class of drift cannot recur — but the lesson generalises: **check a claim in the
instructions against the config file that would implement it before building on it.**

## Lane conventions

**`exporter.py` is a single-owner file for the whole wave.** At 711 lines it holds the gather loop,
every metric definition and every label decision, so parallel metric work converges on it by
construction. Either one lane owns all exporter changes, or metric work is serialised behind a
wiring pass. Do not split it by metric family and hope the edits do not overlap — they will, in the
gather block.

The natural parallel seams that do *not* collide: `log_parser.py` + `test_log_parser.py`,
`profile_messages.py` + `test_profile_messages.py`, `models.py` + `test_models.py`, and CI/workflow
files. `client.py` and `models.py` move together often enough that giving them to two lanes needs
the model dataclass signatures frozen in the goal file first.

**`pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml` and `.github/workflows/` are wiring files**
— one lane or the wiring pass, never concurrent. `uv.lock` in particular produces conflicts that are
tedious rather than interesting, and Renovate is already the main author of changes to it.

## Ownership and the escape hatch

A lane owns its files and does not edit outside them. **The escape hatch: when a lane finds that
finishing requires a change to a file it does not own, it stops and returns the question with the
specific file and the specific change.** It does not make the edit, and it does not silently narrow
its own task to the part that avoids the file. A boundary with no escape hatch is a stop condition
wearing a safety label.

**Only the root agent commits.** Lanes leave the working tree dirty and describe what they changed.
This matters more than usual here because the repo is on `main` with a push-straight-to-main policy
and no PR gate to catch a bad commit.

**If the working tree carries changes that are not the wave's, stage explicit pathspecs.** Never
`git add -A` or `git commit -a`.

## Run-end against this tracker

Task state is the record; nothing durable may live only in the terminal.

- Landed work: `Done`, with the commit SHA in the final summary, finalized in **one** call —
  `backlog task edit FSG-000N --check-ac 1 --check-ac 2 -s Done`.
- Blocked work: `Parked`, with a concrete resume boundary. "Needs the modem, which was in use" is a
  boundary. "Partially done" is not. Given the hardware constraint above, `Parked` will be a normal
  outcome in this repo rather than an exceptional one — that is what the status was added for.
- Untouched work stays `To Do` and needs no action.
- Work discovered mid-run becomes a new task labelled `needs-triage`. Do not fold it into the task
  that found it.

The covering note to the terminal carries only what no single task captures — what the run learned
about the codebase as a whole. It is the last unit of work, not a reply to a request.
