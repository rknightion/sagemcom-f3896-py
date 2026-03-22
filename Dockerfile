FROM python:3.15-rc-alpine3.22

WORKDIR /usr/src/app

ENV PIP_ROOT_USER_ACTION=ignore \
    PYTHONUNBUFFERED=1

# 1. Copy the dependency files
COPY pyproject.toml README.md ./

# 2. Install ONLY the dependencies listed in the TOML
# We use 'poetry export' or just pip install the specific requirements
# to avoid the "empty element" error.
RUN pip install --no-cache-dir click aiohttp "prometheus-async[aiohttp]"

# 3. Now copy the rest of your source code
COPY . .

# 4. Install the current project without dependencies
# (This links your 'f3896-cli' command)
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8080

CMD ["python", "-m", "sagemcom_f3896_client.exporter", "-v"]
