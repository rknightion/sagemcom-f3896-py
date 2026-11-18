"""Exercise the packaged Sagemcom exporter on container loopback only."""

import hashlib
import importlib.metadata
import json
import os
import ssl
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import monotonic, sleep
from typing import ClassVar
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

EXPECTED_CMD = ["python", "-m", "sagemcom_f3896_client.exporter", "-v"]
VENV = Path("/usr/src/app/.venv")
REQUEST_PATH = "/rest/v1/cablemodem/eventlog"
OPENER = build_opener(ProxyHandler({}))


class Modem(BaseHTTPRequestHandler):
    requests: ClassVar[list[str]] = []

    def do_GET(self):
        self.requests.append(self.path)
        if self.path != REQUEST_PATH:
            self.send_error(404)
            return
        payload = b'{"eventlog":[]}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_):
        return


def main():
    if os.geteuid() == 0 or Path(sys.prefix) != VENV:
        raise RuntimeError("Exporter process must use the installed non-root runtime")
    subprocess.run(
        [sys.executable, "-m", "sagemcom_f3896_client.cli", "--help"],
        check=True,
        stdout=subprocess.DEVNULL,
        timeout=8,
    )
    with ThreadingHTTPServer(("127.0.0.1", 0), Modem) as fixture:
        thread = Thread(target=fixture.serve_forever, daemon=True)
        thread.start()
        env = {**os.environ, "MODEM_URL": f"http://127.0.0.1:{fixture.server_port}"}
        env.pop("MODEM_PASSWORD", None)
        with subprocess.Popen(
            EXPECTED_CMD,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        ) as exporter:
            try:
                deadline = monotonic() + 10
                while True:
                    if exporter.poll() is not None:
                        error = exporter.stderr.read()
                        raise RuntimeError(f"Exporter exited early\n{error}")
                    try:
                        with OPENER.open(
                            "http://127.0.0.1:8080/", timeout=1
                        ) as response:
                            if (
                                response.status != 200
                                or b"Sagemcom F3896" not in response.read()
                            ):
                                raise RuntimeError("Unexpected exporter response")
                            break
                    except TimeoutError, URLError:
                        if monotonic() >= deadline:
                            raise RuntimeError(
                                "Exporter did not serve the event log"
                            ) from None
                        sleep(0.1)
                if Modem.requests != [REQUEST_PATH]:
                    raise RuntimeError(
                        "Exporter did not make the expected synthetic modem request"
                    )
            finally:
                if exporter.poll() is None:
                    exporter.terminate()
                    try:
                        exporter.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        exporter.kill()
                        exporter.wait(timeout=3)
        fixture.shutdown()

    trust = ssl.create_default_context()
    anchors = sorted(
        hashlib.sha256(data).hexdigest()
        for data in trust.get_ca_certs(binary_form=True)
    )
    if not anchors:
        raise RuntimeError("Runtime default TLS trust is empty")
    distribution_versions = sorted(
        (dist.metadata["Name"].lower(), dist.version)
        for dist in importlib.metadata.distributions(
            path=[str(VENV / "lib/python3.15/site-packages")]
        )
    )
    print(
        json.dumps(
            {
                "uid": os.geteuid(),
                "gid": os.getegid(),
                "python": sys.version.split()[0],
                "required_shells": [
                    name for name in ("/bin/sh", "/bin/bash") if os.path.exists(name)
                ],
                "ca_anchors": anchors,
                "installed_runtime": distribution_versions,
                "command": EXPECTED_CMD,
                "exporter_http": 200,
                "modem_fixture_requests": len(Modem.requests),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
