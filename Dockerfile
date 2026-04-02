FROM python:3.13-alpine AS builder

WORKDIR /usr/src/app

COPY pyproject.toml README.md uv.lock ./
COPY sagemcom_f3896_client/ sagemcom_f3896_client/

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --no-editable

FROM python:3.13-alpine

WORKDIR /usr/src/app

RUN addgroup -S app && adduser -S app -G app

COPY --from=builder /usr/src/app/.venv /usr/src/app/.venv

ENV PATH="/usr/src/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8080

USER app

CMD ["python", "-m", "sagemcom_f3896_client.exporter", "-v"]
