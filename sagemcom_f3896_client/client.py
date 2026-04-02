import asyncio
import logging
import time
import ssl
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional

import aiohttp

from sagemcom_f3896_client.exception import LoginFailedException
from .models import (
    EventLogItem,
    ModemATDMAUpstreamChannelResult,
    ModemModeResult,
    ModemOFDMAUpstreamChannelResult,
    ModemOFDMDownstreamChannelResult,
    ModemQAMDownstreamChannelResult,
    ModemServiceFlowResult,
    ModemStateResult,
    RegistrationResult,
    SoftwareUpdateResult,
    SystemInfoResult,
    SystemProvisioningResponse,
    UserAuthorisationResult,
    UserTokenResult,
)

LOG = logging.getLogger(__name__)

UNAUTHORIZED_ENDPOINTS = set(
    [
        "rest/v1/user/login",
        "rest/v1/cablemodem/downstream/primary_",
        "rest/v1/cablemodem/state_",
        "rest/v1/cablemodem/downstream",
        "rest/v1/cablemodem/upstream",
        "rest/v1/cablemodem/eventlog",
        "rest/v1/cablemodem/serviceflows",
        "rest/v1/cablemodem/registration",
        "rest/v1/system/gateway/provisioning",
        "rest/v1/system/softwareupdate",
        "rest/v1/system/modemmode",
        "rest/v1/echo",
    ]
)

for endpoint in UNAUTHORIZED_ENDPOINTS:
    assert not endpoint.startswith("/"), "URLs should be relative"


def requires_auth(path: str) -> bool:
    return path not in UNAUTHORIZED_ENDPOINTS


class SagemcomModemSessionClient:
    __session: aiohttp.ClientSession
    base_url: str
    password: str
    authorization: Optional[Any] = None

    __login_semaphore = asyncio.Semaphore(1)

    def __init__(
        self, session: aiohttp.ClientSession, base_url: str, password: str
    ) -> None:
        """
        Initialize the session client.
        """
        self.__session = session
        self.base_url = base_url
        self.password = password

    def __headers(self) -> Dict[str, str]:
        return {
            "Accept": "*/*",
            "Referer": self.base_url,
            "Origin": self.base_url,
        }

    #    async def _login(self) -> None:
    #        payload = {"password": self.password}
    #        try:
    #            async with self.__session.post("/rest/v1/user/login", json=payload) as res:
    #                assert res.status in (200, 201, 204), f"Login failed with {res.status}"
    #                body = await res.json()
    #                self.authorization = UserAuthorisationResult.build(body)
    #        except Exception as e:
    #            raise LoginFailedException(f"Failed to login to modem at {self.base_url}") from e

    async def _login(self) -> None:
        # DEBUG: See what password is being sent (Careful: this shows in logs!)
        LOG.debug(
            "Attempting login at %s with password length: %s",
            self.base_url,
            len(self.password),
        )

        payload = {"password": self.password}
        try:
            # We use the base_url we know works and strip any trailing slashes
            target_url = f"{self.base_url.rstrip('/')}/rest/v1/user/login"
            async with self.__session.post(target_url, json=payload) as res:
                #            async with self.__session.post("/rest/v1/user/login", json=payload) as res:
                # DEBUG: See the exact HTTP status code from the modem
                LOG.debug("Modem login response status: %s", res.status)

                if res.status != 200:
                    body_text = await res.text()
                    LOG.debug("Modem error body: %s", body_text)

                assert res.status in (200, 201, 204), f"Login failed with {res.status}"
                body = await res.json()
                self.authorization = UserAuthorisationResult.build(body)
                LOG.debug("Login successful, token acquired.")
        except Exception as e:
            # DEBUG: More descriptive error
            LOG.error("Login CRASHED. URL: %s, Error: %s", self.base_url, str(e))
            raise LoginFailedException(
                f"Failed to login to modem at {self.base_url}"
            ) from e

    async def user_tokens(self, user_id, password) -> UserTokenResult:
        async with self.__request(
            "POST",
            f"/rest/v1/user/{user_id}/tokens",
            {"password": password},
            disable_auth=True,
        ) as res:
            assert res.status == 201
            result = UserTokenResult.build(await res.json())
            if self.authorization and self.authorization.user_id == user_id:
                self.authorization.token = result.token
            return result

    async def delete_token(self, user_id, token) -> None:
        async with self.__request(
            "DELETE", f"/rest/v1/user/{user_id}/token/{token}"
        ) as res:
            assert res.status == 204

    async def _logout(self) -> None:
        async with self.__login_semaphore:
            if self.authorization:
                try:
                    LOG.debug(
                        "Logging out session userId=%d", self.authorization.user_id
                    )
                    await self.delete_token(
                        self.authorization.user_id, self.authorization.token
                    )
                except Exception:
                    LOG.info(
                        "Failure during logout request, still deleting session token.",
                        exc_info=True,
                    )
                finally:
                    self.authorization = None

    @asynccontextmanager
    async def __request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        json: Optional[object] = None,
        raise_for_status: bool = True,
        disable_auth: bool = False,
    ) -> AsyncGenerator[aiohttp.ClientResponse, None]:
        path = path[1:] if path.startswith("/") else path
        url = f"{self.base_url.rstrip('/')}/{path}"

        headers = self.__headers()
        if not disable_auth and requires_auth(path):
            if not self.authorization:
                async with self.__login_semaphore:
                    if not self.authorization:
                        LOG.debug(
                            "logging in because '%s' requires authentication", path
                        )
                        await self._login()
            headers["Authorization"] = f"Bearer {self.authorization.token}"

        if json:
            headers["Content-Type"] = "application/json"

        t0 = time.time()
        async with self.__session.request(
            method, url, headers=headers, json=json, raise_for_status=raise_for_status
        ) as resp:
            LOG.debug(
                "%s %s %s %.3f %s",
                method,
                url,
                resp.status,
                time.time() - t0,
                resp.reason,
            )
            yield resp

    async def echo(self, body: object) -> object:
        async with self.__request("POST", "/rest/v1/echo", json=body) as resp:
            return await resp.json()

    async def modem_event_log(self) -> List[EventLogItem]:
        async with self.__request("GET", "/rest/v1/cablemodem/eventlog") as resp:
            res = await resp.json()
            return sorted(
                (EventLogItem.build(e) for e in res["eventlog"]), reverse=True
            )

    async def modem_service_flows(self) -> List[ModemServiceFlowResult]:
        async with self.__request("GET", "/rest/v1/cablemodem/serviceflows") as resp:
            res = await resp.json()
            return [ModemServiceFlowResult.build(e) for e in res["serviceFlows"]]

    async def system_info(self) -> SystemInfoResult:
        async with self.__request("GET", "/rest/v1/system/info") as resp:
            return SystemInfoResult.build(await resp.json())

    async def modem_primary_downstream(self) -> ModemQAMDownstreamChannelResult:
        async with self.__request(
            "GET", "/rest/v1/cablemodem/downstream/primary_"
        ) as resp:
            data = await resp.json()
            return ModemQAMDownstreamChannelResult.build(data["channel"])

    async def system_state(self) -> ModemStateResult:
        async with self.__request("GET", "/rest/v1/cablemodem/state_") as resp:
            return ModemStateResult.build(await resp.json())

    async def system_reboot(self) -> bool:
        async with self.__request(
            "POST", "/rest/v1/system/reboot", json={"reboot": {"enable": True}}
        ) as resp:
            body = await resp.json()
            if "accepted" in body:
                self.authorization = None
                return True
            return False

    async def modem_downstreams(
        self,
    ) -> List[ModemQAMDownstreamChannelResult | ModemOFDMDownstreamChannelResult]:
        async with self.__request("GET", "/rest/v1/cablemodem/downstream") as resp:
            return [
                (
                    ModemQAMDownstreamChannelResult.build(e)
                    if e["channelType"] == "sc_qam"
                    else ModemOFDMDownstreamChannelResult.build(e)
                )
                for e in (await resp.json())["downstream"]["channels"]
            ]

    async def modem_upstreams(
        self,
    ) -> List[ModemATDMAUpstreamChannelResult | ModemOFDMAUpstreamChannelResult]:
        async with self.__request("GET", "/rest/v1/cablemodem/upstream") as resp:
            return [
                (
                    ModemATDMAUpstreamChannelResult.build(e)
                    if e["channelType"] == "atdma"
                    else ModemOFDMAUpstreamChannelResult.build(e)
                )
                for e in (await resp.json())["upstream"]["channels"]
            ]

    async def system_provisioning(self) -> SystemProvisioningResponse:
        async with self.__request(
            "GET", "/rest/v1/system/gateway/provisioning"
        ) as resp:
            return SystemProvisioningResponse.build(await resp.json())

    async def modem_registration(self) -> RegistrationResult:
        async with self.__request("GET", "/rest/v1/cablemodem/registration") as resp:
            return RegistrationResult.build(await resp.json())

    async def modem_software_update(self) -> SoftwareUpdateResult:
        async with self.__request("GET", "/rest/v1/system/softwareupdate") as resp:
            return SoftwareUpdateResult.build(await resp.json())

    async def modem_mode(self) -> ModemModeResult:
        async with self.__request("GET", "/rest/v1/system/modemmode") as resp:
            return ModemModeResult.build(await resp.json())


class SagemcomModemClient:
    base_url: str
    password: str
    timeout: int
    session: ContextVar[aiohttp.ClientSession] = ContextVar("session")
    client: ContextVar[SagemcomModemSessionClient] = ContextVar("client")

    def __init__(self, base_url: str, password: str, timeout: int = 15) -> None:
        self.base_url = base_url
        self.password = password
        self.timeout = timeout

    async def __aenter__(self) -> SagemcomModemSessionClient:
        # Create SSL context to bypass self-signed certificate verification
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        timeout_cfg = aiohttp.ClientTimeout(total=self.timeout)
        conn = aiohttp.TCPConnector(limit_per_host=30, force_close=True, ssl=ssl_ctx)

        new_session = aiohttp.ClientSession(timeout=timeout_cfg, connector=conn)
        self.session.set(new_session)

        new_client = SagemcomModemSessionClient(
            new_session, self.base_url, self.password
        )
        self.client.set(new_client)
        return new_client

    async def __aexit__(self, *args) -> None:
        try:
            client_inst = self.client.get()
            await client_inst._logout()
        except Exception:
            LOG.debug("Error during logout", exc_info=True)
        finally:
            session_inst = self.session.get()
            await session_inst.close()
