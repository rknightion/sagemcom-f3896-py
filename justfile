set shell := ["bash", "-euo", "pipefail", "-c"]

# show the task surface
default:
    @just --list

# install dependencies into .venv (idempotent)
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
lint output_format="":
    uv run ruff check {{ if output_format == "" { "" } else { "--output-format=" + output_format } }} .

# run the test suite (integration tests skip without MODEM_PASSWORD)
[group('check')]
[no-exit-message]
test filter="":
    uv run pytest --cov sagemcom_f3896_client --cov-report html -qq -o console_output_style=count -p no:sugar {{ if filter == "" { "" } else { "-k " + filter } }} tests

# run every gate that only needs the language toolchain
[group('check')]
check: fmt-check lint test build

# build the sdist+wheel into dist/
[group('build')]
build:
    uv build

# build the runtime container image locally
[group('build')]
image tag="sagemcom-f3896-client:dev":
    docker build -t {{ tag }} .

# remove build/test artifacts and the local venv
[confirm('remove .venv, dist/, htmlcov/, .pytest_cache, .ruff_cache — proceed?')]
[group('dev')]
clean:
    rm -rf .venv dist htmlcov .pytest_cache .ruff_cache
