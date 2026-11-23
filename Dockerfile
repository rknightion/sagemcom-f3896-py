FROM python:3.15-alpine@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd AS builder

WORKDIR /usr/src/app

COPY pyproject.toml README.md uv.lock ./
COPY sagemcom_f3896_client/ sagemcom_f3896_client/

COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d /uv /usr/local/bin/uv

RUN uv sync --frozen --no-dev --no-editable --no-managed-python --python 3.15

FROM python:3.15-alpine@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd

WORKDIR /usr/src/app

# The builder supplies the installed virtual environment. Keep pip out of the runtime.
RUN python -m pip uninstall --yes pip \
    && addgroup -S app \
    && adduser -S app -G app

COPY --from=builder /usr/src/app/.venv /usr/src/app/.venv

ENV PATH="/usr/src/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8080

USER app

CMD ["python", "-m", "sagemcom_f3896_client.exporter", "-v"]
