---
id: FSG-0002
title: Migrate the repo task surface to just and retire Makefiles and ad-hoc scripts
status: To Do
assignee: []
created_date: '2026-08-28 19:26'
updated_date: '2026-08-29 09:18'
labels:
  - 'wave:2-fleet'
dependencies: []
priority: medium
type: chore
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
# Migrate sagemcom-f3896-py task surface to `just`

Fleet-wide `just` migration per the frozen standard (§0–§13). This repo has **no Makefile and no
shell/task scripts to absorb or keep** — the whole job is: author a top-level `justfile`, point
`.github/workflows/python.yaml` at it, and update the three doc surfaces that currently name raw
`uv run` commands (`AGENTS.md`, `backlog/config.yml`'s `definition_of_done`). Do not re-litigate the
standard; this file is fully self-contained.

## 1. Outcome

`sagemcom-f3896-py` has one top-level `justfile` defining the seven mandatory recipes plus `build`
(package artifact, matches the CI test job) and `image`/`clean` (optional, repo has a Dockerfile).
`.github/workflows/python.yaml`'s `lint` and `test` jobs call `just <recipe>` instead of raw
`uv run …` commands; `ci-success`, `permissions:`, `concurrency:`, `persist-credentials: false` and
the matrix are untouched. `AGENTS.md`'s Commands section and `backlog/config.yml`'s
`definition_of_done` name `just` recipes instead of raw `uv run` invocations. No Makefile existed to
delete and no script existed to absorb or keep — confirm that inventory holds at execution time
(`find . -iname Makefile -o -iname GNUmakefile`, `git ls-files | grep -E '\.(sh|bash|zsh|ps1)$'`)
before skipping those steps.

## 2. The complete justfile

Drop this at the repo root as `justfile`. Real commands only — every body line here is taken
verbatim from `AGENTS.md`'s existing Commands section and `.github/workflows/python.yaml`. No
`typecheck` recipe: the repo has no mypy/pyright config anywhere (`pyproject.toml` has no
`[tool.mypy]`/`[tool.pyright]` section and no such dependency is declared).

```just
set shell := ["bash", "-euo", "pipefail", "-c"]

# show the task surface
default:
    @just --list

# install dependencies into .venv (idempotent)
[group('dev')]
setup:
    uv sync --all-groups

# format source in place
[group('check')]
fmt:
    uv run ruff format .

# verify formatting (source + justfile), never mutates
[group('check')]
fmt-check:
    uv run ruff format --check .
    just --fmt --check

# lint with ruff
[group('check')]
[no-exit-message]
lint:
    uv run ruff check .

# run the test suite (integration tests skip without MODEM_PASSWORD)
[group('check')]
[no-exit-message]
test filter="":
    uv run pytest {{ if filter == "" { "" } else { "-k " + filter } }} -q tests

# the full local gate — exactly what CI enforces
[group('check')]
check: fmt-check lint test

# build the sdist+wheel into dist/ (mirrors the CI test job's build step)
[group('build')]
build:
    uv build

# build the runtime container image locally
[group('build')]
image tag="sagemcom-f3896-client:dev":
    docker build -t {{ tag }} .

# remove build/test artifacts and the local venv (everything setup+build can reproduce)
[group('dev')]
[confirm('remove .venv, dist/, htmlcov/, .pytest_cache, .ruff_cache — proceed?')]
clean:
    rm -rf .venv dist htmlcov .pytest_cache .ruff_cache
```

Notes on this exact body:

- `test filter=""` — pytest's `-k` flag is the natural filter mechanism; empty filter runs the full
  suite. The conditional interpolation is one line, no multi-line control flow, so it's safe in a
  line-based recipe per §10.
- `[no-exit-message]` on `lint` and `test` — ruff and pytest both already print a clear failure
  summary; just's own `error: recipe … failed` line is redundant noise on top of it (§5.5).
- `check` omits `build` deliberately — building the sdist/wheel isn't a correctness gate, it's an
  artifact step the CI test job happens to also do. Folding it into `check` would make every local
  `just check` slower for no safety gain. This matches §1's rule about `check` being complete for
  what must pass, not a dump of everything CI ever runs.
- No `ci` superset recipe — CI's `lint` job and `test` job map 1:1 onto existing recipes
  (`fmt-check`+`lint`, and `test`+`build`); there's no CI-only step that needs a home. Don't add one
  speculatively.
- `image` and `clean` are optional-vocabulary recipes (§2), included because the repo has a
  `Dockerfile` (`/Users/rob/repos/sagemcom-f3896-py/Dockerfile`) and accumulates local artifacts
  worth clearing. `image` is not `[confirm]` — it only builds locally, doesn't push. Do not add a
  `push`/`publish` recipe: the real GHCR publish path is the reusable
  `.github/workflows/publish.yml` → `rknightion/.github/.github/workflows/container-publish.yml`
  workflow (multi-arch, cosign, provenance, SBOM) and must stay a GitHub-native workflow (§8, §13).

## 3. Makefile disposition

None. No `Makefile` or `GNUmakefile` exists anywhere in the repo (verified: `find . -iname Makefile
-o -iname GNUmakefile` returns nothing, excluding `.venv/`). No `git rm` needed for this step —
confirm this still holds before closing the task and record it as a no-op, don't skip verifying.

## 4. Script disposition

None. `git ls-files | grep -E '\.(sh|bash|zsh|ps1)$'` returns nothing — no shell scripts tracked.
There is no `scripts/` directory and no non-trivial Python/Go helper script used as a dev/CI task
(`sagemcom_f3896_client/` is the library itself, not a task script). Nothing to ABSORB, nothing to
KEEP-and-wrap.

## 5. CI changes

Only `.github/workflows/python.yaml` needs edits. Every other workflow file
(`actionlint.yml`, `arm-automerge.yml`, `auto-rc.yml`, `codeql.yml`, `dependency-review.yml`,
`docker-security.yml`, `ghcr-cleanup.yml`, `publish.yml`, `release-please.yml`, `scorecard.yml`,
`zizmor.yml`) has zero build/test/lint `run:` blocks — they are either GitHub-native actions or thin
`uses:` calls into `rknightion/.github` reusables. Do not touch any of them (§8, §13, and see
Out of scope §10 below).

### `.github/workflows/python.yaml` — exact edits

Current file (for reference, do not recreate — edit the live file):

```yaml
name: Python

on: [push, pull_request]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Lint
        run: uv run ruff check --output-format=github .
      - name: Check formatting
        run: uv run ruff format --check .

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.14"]
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
        with:
          enable-cache: true
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest --cov sagemcom_f3896_client --cov-report html -qq -o console_output_style=count -p no:sugar tests
      - name: Build package
        run: uv build
      - name: Save artifacts
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7
        with:
          name: dist-${{ matrix.python-version }}
          path: dist

  ci-success:
    name: ci-success
    runs-on: ubuntu-latest
    if: always()
    needs: [lint, test]
    steps:
      - name: Fail if any required job did not pass
        if: ${{ contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') }}
        run: |
          echo "A required job failed or was cancelled: ${{ join(needs.*.result, ', ') }}"
          exit 1
      - name: All required jobs passed
        run: echo "ci-success — ${{ join(needs.*.result, ', ') }}"
```

Two problems with a literal `just <recipe>` swap here that need a decision before editing:

1. **`lint` job's ruff step uses `--output-format=github`** for inline annotations. The justfile's
   `lint` recipe runs plain `uv run ruff check .` (no GitHub annotation format), because a recipe
   must behave identically for a human and for CI. **Resolution: keep the annotation format as a CI
   convenience by NOT collapsing this one step into `just lint`.** Leave `Lint` as
   `run: uv run ruff check --output-format=github .` verbatim — this is a legitimate CI-only
   superset per §1 ("Where a genuine CI-only superset exists … add `ci`"), but a single flag
   difference doesn't warrant a whole `ci` recipe. Document this exception right here so nobody
   "fixes" it later by force-collapsing it. `just lint` (plain output) still exists and is what
   local dev and `just check` use.
2. **`test` job's pytest invocation has flags the justfile's `test` recipe does not**
   (`--cov sagemcom_f3896_client --cov-report html -qq -o console_output_style=count -p no:sugar`
   vs `-q`). Same resolution: this is CI-specific coverage/output tuning, not gate logic. Either (a)
   fold these flags into the `test` recipe's default so `just test` and CI match exactly (preferred
   — makes local `just check` a truer preview of CI), or (b) leave the `test` step as raw
   `uv run pytest …` like the `lint` step above. **Take option (a):** replace the justfile's `test`
   recipe body with the CI-matching invocation so the workflow step becomes a real `just test` call
   and local/CI stay identical. Updated recipe:

   ```just
   # run the test suite (integration tests skip without MODEM_PASSWORD)
   [group('check')]
   [no-exit-message]
   test filter="":
       uv run pytest --cov sagemcom_f3896_client --cov-report html -qq -o console_output_style=count -p no:sugar {{ if filter == "" { "" } else { "-k " + filter } }} tests
   ```

   Use this version in the justfile from §2, not the shorter `-q` one — this note supersedes that
   recipe body.

Resulting `python.yaml` (only the two job bodies change; `ci-success` job is untouched verbatim):

```yaml
name: Python

on: [push, pull_request]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - uses: extractions/setup-just@<RESOLVE_SHA> # v4
        with:
          just-version: '1.58.0'
      - name: Lint
        run: uv run ruff check --output-format=github .
      - name: Check formatting
        run: just fmt-check

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.14"]
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7
        with:
          persist-credentials: false
      - uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
        with:
          enable-cache: true
      - uses: extractions/setup-just@<RESOLVE_SHA> # v4
        with:
          just-version: '1.58.0'
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      - name: Install dependencies
        run: just setup
      - name: Run tests
        run: just test
      - name: Build package
        run: just build
      - name: Save artifacts
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7
        with:
          name: dist-${{ matrix.python-version }}
          path: dist

  ci-success:
    name: ci-success
    runs-on: ubuntu-latest
    if: always()
    needs: [lint, test]
    steps:
      - name: Fail if any required job did not pass
        if: ${{ contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') }}
        run: |
          echo "A required job failed or was cancelled: ${{ join(needs.*.result, ', ') }}"
          exit 1
      - name: All required jobs passed
        run: echo "ci-success — ${{ join(needs.*.result, ', ') }}"
```

`<RESOLVE_SHA>`: resolve the current pinned SHA for `extractions/setup-just` v4 at execution time —
```bash
gh api repos/extractions/setup-just/git/refs/tags/v4 --jq .object.sha
```
(or the equivalent tag-to-commit lookup if `v4` is a moving major tag — check whether another
already-migrated rknightion/m7kni repo has this action pinned already and reuse that exact SHA for
fleet consistency, per §8's "pin the action itself by SHA … matching the fleet's existing
convention").

**Do NOT change**: `permissions:` block, `concurrency:` block, `ci-success` job (name, `if: always()`,
`needs: [lint, test]`, both steps verbatim), the `python-version` matrix, `persist-credentials:
false`, the `actions/checkout` and `actions/upload-artifact` SHA pins, `astral-sh/setup-uv` SHA pin,
or the artifact name/path.

## 6. Docs and agent-contract changes

### `AGENTS.md` (canonical; `CLAUDE.md` is a one-line `@AGENTS.md` import, no separate edit needed)

Current Commands section (`AGENTS.md:11-22`):

```markdown
## Commands

\`\`\`bash
uv sync                       # Install dependencies
uv run pytest tests           # Run tests (integration tests skip without MODEM_PASSWORD)
uv run pytest -x -q           # Quick run, stop on first failure

uv run ruff check .           # Lint
uv run ruff format --check .  # Formatting gate (CI runs --check, not a rewrite)
pre-commit run --all-files    # Same ruff pair, via the hook config

uv run python -m sagemcom_f3896_client.cli --help   # CLI
uv run python -m sagemcom_f3896_client.exporter -v  # Exporter, port 8080
\`\`\`

The three gate commands are also \`definition_of_done\` in \`backlog/config.yml\`, so every new task
inherits them as a checklist. They mirror the \`lint\` and \`test\` jobs in
\`.github/workflows/python.yaml\`, whose single required status check is \`ci-success\`.
```

Replace with the standard's §9 Task interface block, keeping the CLI/exporter run lines (they're
one-off dev commands, not gate recipes — leave them as raw `uv run` since there's no `run`/`serve`
justfile verb defined for them and inventing one isn't in scope):

```markdown
## Task interface

This repo's task surface is a `justfile`. Discover it, don't guess it:

    just --list                        # human-readable
    just --dump --dump-format json     # machine-readable
    just --show <recipe>               # what a recipe actually runs

- `just check` is the full gate and is exactly what CI enforces. It must pass before you commit.
- Prefer `just <recipe>` over the underlying tool. If you are typing `pytest`, you want `just test`.
- Run `just` with stdin from /dev/null. Recipes marked `[confirm]` are destructive — stop and ask
  before running one; never pass `--yes` or `JUST_YES=1`.
- If a task you need does not exist, add a recipe with a `#` doc comment and a `[group(...)]`
  rather than running a bare command.

Ad-hoc commands not covered by a recipe:

\`\`\`bash
uv run python -m sagemcom_f3896_client.cli --help   # CLI
uv run python -m sagemcom_f3896_client.exporter -v  # Exporter, port 8080
\`\`\`

The gate is also \`definition_of_done\` in \`backlog/config.yml\`, so every new task inherits it as
a checklist. It mirrors the \`lint\` and \`test\` jobs in \`.github/workflows/python.yaml\`, whose
single required status check is \`ci-success\`.
```

Do not paste the recipe list itself into `AGENTS.md` (§9) — the block above deliberately doesn't
enumerate `fmt`/`lint`/`test`/etc.

The "Code style" section's ruff-only note stays untouched — that's about which linters exist, not
how to invoke them.

### `.pre-commit-config.yaml`

Leave it alone. It's a local git-hook config, not a CI or `just` task; `pre-commit run --all-files`
still works standalone and isn't part of the mandatory vocabulary. (It's dropped from the AGENTS.md
Commands list above only because that list is being replaced by discovery-first language per §9 —
if a repo maintainer wants `pre-commit` findable via `just`, that's a future addition, not part of
this task.)

### README.md, CONTRIBUTING.md

No edits needed. `grep -n "make \|make%\|\./scripts" README.md` and equivalent over the repo root
found no references to `make <target>` or a script path anywhere outside `AGENTS.md` (there is no
`CONTRIBUTING.md`). Confirm this still holds before closing the task.

## 7. `backlog/config.yml`

Current `definition_of_done` (`backlog/config.yml:4-7`):

```yaml
definition_of_done:
  - "uv run ruff check ."
  - "uv run ruff format --check ."
  - "uv run pytest tests"
```

Replace with:

```yaml
definition_of_done:
  - "just check"
```

`backlog/config.yml` is the one file in `backlog/` that may be hand-edited (per `AGENTS.md`'s own
non-negotiable rules — list-valued keys aren't settable through `backlog config set`). Edit it
directly with a text editor, not through the `backlog` CLI.

## 8. Order of work

1. Add the `justfile` at repo root (§2, with the CI-matching `test` recipe body from §5).
2. Run `just --fmt --check` — must pass with no reformatting needed on first write (write it already
   formatted; if not, run `just --fmt` once and re-check).
3. Locally run `just check` (needs `uv` on PATH) and `just build`, `just image` — confirm each
   passes/produces the expected artifact before touching CI.
4. Resolve `<RESOLVE_SHA>` for `extractions/setup-just@v4` (§5) and edit
   `.github/workflows/python.yaml` per the exact diff in §5. Push to a point where CI runs and
   confirm `lint`, `test`, `ci-success` are all green — this is the only step that needs a live CI
   run before proceeding, since it's the point where a mistake would silently break the required
   status check.
5. Edit `AGENTS.md` (§6) and `backlog/config.yml` (§7).
6. Final verification pass (§ acceptance criteria) — `just --list`, re-run `just check`,
   `git ls-files` sweep confirming no Makefile/script existed to delete in the first place.

There is no "deletions last" step here beyond the doc-content deletions in §6 — this repo has no
Makefile or script files to remove, so steps 4–6 can't break a still-referenced file.

## 9. Traps specific to this repo

- **`requires-python = ">=3.14"`** — whatever environment runs `just setup`/`just check` locally
  needs a 3.14 toolchain; `uv python install` isn't in the `setup` recipe body (CI does its own
  explicit `uv python install ${{ matrix.python-version }}` step before `just setup`/`just test`
  run — that step is deliberately left as-is in §5, not folded into `just setup`, so `setup` stays a
  pure dependency-install idempotent recipe and doesn't silently reach out to install a Python
  interner across every dev machine).
- **`exporter.py`'s `E402` exemption** (`pyproject.toml`'s `lint.per-file-ignores`) is config, not a
  recipe concern — `just lint` picks it up automatically via ruff's own config resolution. Don't
  hand-code the exemption into the recipe.
- **Integration tests skip silently without `MODEM_PASSWORD`.** `just test` and `just check` will
  report green locally without ever touching a real modem — this is existing, documented behavior
  (`AGENTS.md`'s Gotchas section), not something the migration changes or needs to flag differently.
  Preserve the existing AGENTS.md Gotchas section verbatim; §6 only replaces the Commands section.
- **The `lint` job's `--output-format=github` and the `test` job's coverage/quiet flags are
  deliberately NOT identical to a naive "just collapse every run: line" pass** — see §5's numbered
  resolution. Getting this wrong either breaks GitHub's inline annotations or makes `just test`
  diverge from what CI actually runs (the latter is worse: it breaks the `check` contract in §1).
- **`docs/superpowers/`** exists in this repo's working tree (`docs/superpowers/plans/...`) — per
  the fleet operating model this directory must be gitignored and is planning scratch. It is
  unrelated to this migration; do not touch it, do not treat any file under it as a repo doc to
  update.
- No `[working-directory(...)]` or multi-shell concerns — every recipe is a single-line body, no
  `cd` needed anywhere in this repo's toolchain.

## 10. Out of scope

- `.github/workflows/actionlint.yml`, `arm-automerge.yml`, `auto-rc.yml`, `codeql.yml`,
  `dependency-review.yml`, `docker-security.yml`, `ghcr-cleanup.yml`, `publish.yml`,
  `release-please.yml`, `scorecard.yml`, `zizmor.yml` — all GitHub-native or thin reusable-workflow
  calls into `rknightion/.github`. Do not fold any of them into `just` or touch their `uses:` lines.
- `publish.yml`'s image publish path (`container-publish.yml` reusable) — the new `just image`
  recipe is a local-build convenience only, never wired into this workflow.
- `Dockerfile` itself — not touched, only referenced by the new `image` recipe.
- `.pre-commit-config.yaml` — left as-is (§6).
- `docs/superpowers/` — planning scratch, not a docs surface for this task.
- `CHANGELOG.md`, `release-please-config.json`, `.release-please-manifest.json` — release-please
  owned, untouched.
- `renovate.json` — untouched.
- `backlog/tasks/`, `backlog/docs/`, `backlog/decisions/` — never hand-edited; only
  `backlog/config.yml` is touched, and only its `definition_of_done` key.
- No `typecheck` recipe — no mypy/pyright config exists in this repo; do not add one speculatively
  as part of this migration.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Top-level justfile exists with all seven mandatory recipes (default, setup, fmt, fmt-check, lint, test, check) plus build, image, clean, each with a doc comment and [group(...)]
- [ ] #2 just check passes locally and its component recipes (fmt-check, lint, test) are exactly what the lint and test jobs in .github/workflows/python.yaml run, modulo the documented --output-format=github exception on the lint job
- [ ] #3 just --fmt --check passes against the committed justfile
- [ ] #4 just --list shows a doc comment and group for every public recipe
- [ ] #5 No Makefile or GNUmakefile exists in the repo (none existed before this task; confirm the inventory still holds)
- [ ] #6 No shell/task script exists to absorb or keep (none existed before this task; confirm git ls-files has no tracked .sh/.bash/.zsh/.ps1 files)
- [ ] #7 .github/workflows/python.yaml's lint and test jobs call just <recipe> per the exact diff in the task body, with extractions/setup-just pinned by resolved SHA and just-version 1.58.0, and the ci-success job, permissions, concurrency, persist-credentials and matrix are unchanged
- [ ] #8 AGENTS.md's Commands section is replaced by the Task interface block naming just check as the gate, per the task body
- [ ] #9 backlog/config.yml's definition_of_done is just ["just check"]
- [ ] #10 README.md and CONTRIBUTING.md still contain no references to make or a script path (confirmed, not just assumed)
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv run ruff check .
- [ ] #2 uv run ruff format --check .
- [ ] #3 uv run pytest tests
<!-- DOD:END -->

## Comments

<!-- COMMENTS:BEGIN -->
author: campaign-ordering
created: 2026-08-29 09:18
---
## Fleet ordering — WAVE 2. Starts after the Wave 0 pilot (`sf2loki` / SFL-0073) and the Wave 1 hubs land.

Within Wave 2 the order is free — these repos do not depend on each other. Batching by language is worthwhile so one lane reuses its Makefile-to-recipe mapping across similar repos.

Do not start before the pilot reports. The standard may be amended off the back of it, and picking this up early risks coding against a superseded seam.

**Provisioning `just` in CI.** Which mechanism depends on the runner, and the two must not be mixed:

| Runner | Mechanism |
| --- | --- |
| `arc-arm64` (m7kni self-hosted) | `just` is **baked into the runner image** by `m7kni/ci-tools` (`runner-image/Dockerfile`, `ARG JUST_VERSION`). Do **not** add `extractions/setup-just`, and delete the step if this repo already has one — it installs a second `just` earlier on `PATH` and turns the image pin into a lie. |
| GitHub-hosted (all `rknightion` repos) | `extractions/setup-just`, SHA-pinned, with an explicit `just-version:`. |

Both sides currently sit on **1.58.0** and are Renovate-managed. `ci-tools`' `Tool version drift` workflow fails if the Dockerfile `ARG` and the published image ever disagree, and lists any repo still carrying a second pin.

**While you are in the workflow files, check the hub pin.** On 2026-08-29 Renovate was unfrozen for `rknightion/.github` in `m7kni/renovate-config` — it had been `enabled: false` on the mistaken belief that callers tracked `@main`, which froze the fleet across 19 different hub SHAs (v1.3.1 June → v1.9.7 August) so that no hub fix ever propagated. Bumps now arrive as one grouped, CI-gated, automerged PR per repo. **A `uses:` whose comment is not a real `# vX.Y.Z` still cannot be bumped** (it resolves to a digest-only update, which the fleet rules disable) — if you find one, repair the comment as part of this task.
---
<!-- COMMENTS:END -->
