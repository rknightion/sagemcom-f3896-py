import logging
import os
import ssl

import aiohttp
import pytest

from sagemcom_f3896_client.client import SagemcomModemSessionClient

LOG = logging.getLogger(__name__)


@pytest.fixture
def client(event_loop):
    """
    Build a client using settings from environment variable, without requiring a context manager.
    """
    modem_url = os.environ.get("MODEM_URL", None)
    if not modem_url:
        LOG.info("MODEM_URL environment variable is not set, using default")
        modem_url = "https://192.168.100.1"

    modem_password = os.environ.get("MODEM_PASSWORD")
    assert modem_password, "MODEM_PASSWORD environment variable is not set"

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    async def sessio():
        conn = aiohttp.TCPConnector(ssl=ssl_ctx)
        return aiohttp.ClientSession(connector=conn)

    session = event_loop.run_until_complete(sessio())
    client = SagemcomModemSessionClient(session, modem_url, modem_password)
    yield client

    event_loop.run_until_complete(client._logout())
