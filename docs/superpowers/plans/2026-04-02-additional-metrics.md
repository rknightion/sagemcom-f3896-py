# Additional Prometheus Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose service flow, registration, software update, modem mode, and enriched modem_info metrics from the Sagemcom F3896 REST API.

**Architecture:** Three new model dataclasses, three new client methods, two new UNAUTHORIZED_ENDPOINTS entries, and an expanded exporter gather + metric creation loop. All new endpoints are unauthenticated except `system_provisioning` which already exists and is unauthenticated.

**Tech Stack:** Python 3.10+, aiohttp, prometheus_client, pytest, pytest-asyncio

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `sagemcom_f3896_client/models.py` | Modify | Add `RegistrationResult`, `SoftwareUpdateResult`, `ModemModeResult` dataclasses |
| `sagemcom_f3896_client/client.py` | Modify | Add 3 new client methods, 2 new `UNAUTHORIZED_ENDPOINTS` entries |
| `sagemcom_f3896_client/exporter.py` | Modify | Expand gather, add service flow / registration / software update / modem mode metrics, enrich `modem_info` |
| `tests/test_models.py` | Create | Unit tests for all 3 new model `build()` methods |
| `tests/test_client.py` | Modify | Integration tests for 3 new client methods |

---

### Task 1: New Models

**Files:**
- Modify: `sagemcom_f3896_client/models.py:265-278` (append after `SystemProvisioningResponse`)
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests for the 3 new models**

Create `tests/test_models.py`:

```python
from sagemcom_f3896_client.models import (
    ModemModeResult,
    RegistrationResult,
    SoftwareUpdateResult,
)


def test_registration_result_build():
    raw = {
        "registration": {
            "registrationComplete": True,
            "downstreamLocked": True,
        }
    }
    result = RegistrationResult.build(raw)
    assert result.registration_complete is True
    assert result.downstream_locked is True


def test_registration_result_build_false():
    raw = {
        "registration": {
            "registrationComplete": False,
            "downstreamLocked": False,
        }
    }
    result = RegistrationResult.build(raw)
    assert result.registration_complete is False
    assert result.downstream_locked is False


def test_software_update_result_build():
    raw = {"softwareUpdate": {"status": "complete_from_management"}}
    result = SoftwareUpdateResult.build(raw)
    assert result.status == "complete_from_management"


def test_modem_mode_result_build():
    raw = {"modemmode": {"enable": True}}
    result = ModemModeResult.build(raw)
    assert result.enabled is True


def test_modem_mode_result_build_disabled():
    raw = {"modemmode": {"enable": False}}
    result = ModemModeResult.build(raw)
    assert result.enabled is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_models.py -v`
Expected: FAIL with `ImportError` — the classes don't exist yet.

- [ ] **Step 3: Implement the 3 new model dataclasses**

Append to `sagemcom_f3896_client/models.py` after the `SystemProvisioningResponse` class (after line 278):

```python
@dataclass
class RegistrationResult:
    registration_complete: bool
    downstream_locked: bool

    @staticmethod
    def build(body: Dict[str, str]) -> "RegistrationResult":
        return RegistrationResult(
            registration_complete=body["registration"]["registrationComplete"],
            downstream_locked=body["registration"]["downstreamLocked"],
        )


@dataclass
class SoftwareUpdateResult:
    status: str

    @staticmethod
    def build(body: Dict[str, str]) -> "SoftwareUpdateResult":
        return SoftwareUpdateResult(
            status=body["softwareUpdate"]["status"],
        )


@dataclass
class ModemModeResult:
    enabled: bool

    @staticmethod
    def build(body: Dict[str, str]) -> "ModemModeResult":
        return ModemModeResult(
            enabled=body["modemmode"]["enable"],
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_models.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add sagemcom_f3896_client/models.py tests/test_models.py
git commit -m "feat: add RegistrationResult, SoftwareUpdateResult, ModemModeResult models"
```

---

### Task 2: New Client Methods

**Files:**
- Modify: `sagemcom_f3896_client/client.py:28-41` (add to `UNAUTHORIZED_ENDPOINTS`)
- Modify: `sagemcom_f3896_client/client.py:214-216` (add methods after `system_provisioning`)
- Modify: `tests/test_client.py` (add integration tests)

- [ ] **Step 1: Write failing integration tests**

Append to `tests/test_client.py`:

```python
@requires_modem_password()
@pytest.mark.asyncio
async def test_modem_registration(
    client: SagemcomModemSessionClient, caplog: LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    registration = await client.modem_registration()
    assert isinstance(registration.registration_complete, bool)
    assert isinstance(registration.downstream_locked, bool)


@requires_modem_password()
@pytest.mark.asyncio
async def test_modem_software_update(
    client: SagemcomModemSessionClient, caplog: LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    software_update = await client.modem_software_update()
    assert isinstance(software_update.status, str)
    assert len(software_update.status) > 0


@requires_modem_password()
@pytest.mark.asyncio
async def test_modem_mode(
    client: SagemcomModemSessionClient, caplog: LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)

    modem_mode = await client.modem_mode()
    assert isinstance(modem_mode.enabled, bool)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_client.py::test_modem_registration tests/test_client.py::test_modem_software_update tests/test_client.py::test_modem_mode -v`
Expected: FAIL with `AttributeError` — the methods don't exist yet.

- [ ] **Step 3: Add new entries to UNAUTHORIZED_ENDPOINTS**

In `sagemcom_f3896_client/client.py`, add these two entries to the `UNAUTHORIZED_ENDPOINTS` set (after line 39, before the closing `]`):

```python
        "rest/v1/system/softwareupdate",
        "rest/v1/system/modemmode",
```

- [ ] **Step 4: Add import for new models**

In `sagemcom_f3896_client/client.py`, add the 3 new model imports to the existing import block from `.models` (line 13-24):

```python
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
```

- [ ] **Step 5: Add 3 new client methods**

Append after the `system_provisioning` method (after line 216) in `SagemcomModemSessionClient`:

```python
    async def modem_registration(self) -> RegistrationResult:
        async with self.__request("GET", "/rest/v1/cablemodem/registration") as resp:
            return RegistrationResult.build(await resp.json())

    async def modem_software_update(self) -> SoftwareUpdateResult:
        async with self.__request("GET", "/rest/v1/system/softwareupdate") as resp:
            return SoftwareUpdateResult.build(await resp.json())

    async def modem_mode(self) -> ModemModeResult:
        async with self.__request("GET", "/rest/v1/system/modemmode") as resp:
            return ModemModeResult.build(await resp.json())
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_client.py::test_modem_registration tests/test_client.py::test_modem_software_update tests/test_client.py::test_modem_mode -v`
Expected: PASS (if `MODEM_PASSWORD` is set), SKIP otherwise.

Also run model tests to make sure nothing broke:
Run: `uv run pytest tests/test_models.py -v`
Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add sagemcom_f3896_client/client.py tests/test_client.py
git commit -m "feat: add modem_registration, modem_software_update, modem_mode client methods"
```

---

### Task 3: Service Flow Metrics in Exporter

**Files:**
- Modify: `sagemcom_f3896_client/exporter.py:27` (add `ModemServiceFlowResult` import — already imported but not used by exporter; verify it's accessible)
- Modify: `sagemcom_f3896_client/exporter.py:130-210` (expand `update_metrics`)

- [ ] **Step 1: Add service flow metrics to the exporter**

In `sagemcom_f3896_client/exporter.py`, make these changes inside `update_metrics()`:

First, add new metric declarations after the existing `metric_node_boot_time` Gauge (after line 147, before the `# gather metrics in parallel` comment):

```python
            metric_service_flow_max_traffic_rate = Gauge(
                "modem_service_flow_max_traffic_rate",
                "Provisioned max traffic rate in bps",
                ["direction", "flow_id"],
                registry=registry,
            )
            metric_service_flow_max_traffic_burst = Gauge(
                "modem_service_flow_max_traffic_burst",
                "Max traffic burst in bytes",
                ["direction", "flow_id"],
                registry=registry,
            )
            metric_service_flow_min_reserved_rate = Gauge(
                "modem_service_flow_min_reserved_rate",
                "Min reserved rate in bps",
                ["direction", "flow_id"],
                registry=registry,
            )
            metric_service_flow_max_concatenated_burst = Gauge(
                "modem_service_flow_max_concatenated_burst",
                "Max concatenated burst in bytes",
                ["direction", "flow_id"],
                registry=registry,
            )
            metric_service_flow_info = Info(
                "modem_service_flow",
                "Service flow information",
                ["direction", "flow_id"],
                registry=registry,
            )
```

Next, expand the `asyncio.gather` call. Change lines 162-167 from:

```python
                state, _, _, _ = await asyncio.gather(
                    self.client.system_state(),
                    self.__update_downstream_channel_metrics(registry),
                    self.__update_upstream_channel_metrics(registry),
                    self.__log_based_metrics(registry),
                )
```

to:

```python
                state, _, _, _, service_flows = await asyncio.gather(
                    self.client.system_state(),
                    self.__update_downstream_channel_metrics(registry),
                    self.__update_upstream_channel_metrics(registry),
                    self.__log_based_metrics(registry),
                    self.client.modem_service_flows(),
                )
```

Then, after the `metric_node_boot_time.set(self.__last_boot_time)` line (after line 189), add the service flow metric population loop:

```python
                for sf in service_flows:
                    labels = {
                        "direction": sf.direction,
                        "flow_id": str(sf.id),
                    }
                    metric_service_flow_max_traffic_rate.labels(**labels).set(
                        sf.max_traffic_rate
                    )
                    metric_service_flow_max_traffic_burst.labels(**labels).set(
                        sf.max_traffic_burst
                    )
                    metric_service_flow_min_reserved_rate.labels(**labels).set(
                        sf.min_reserved_rate
                    )
                    metric_service_flow_max_concatenated_burst.labels(**labels).set(
                        sf.max_concatenated_burst
                    )
                    metric_service_flow_info.labels(**labels).info(
                        {"schedule_type": sf.schedule_type}
                    )
```

- [ ] **Step 2: Verify the exporter still starts**

Run: `uv run python -c "from sagemcom_f3896_client.exporter import Exporter; print('import OK')"`
Expected: `import OK`

- [ ] **Step 3: Commit**

```bash
git add sagemcom_f3896_client/exporter.py
git commit -m "feat: export service flow metrics (max rate, burst, reserved rate, schedule type)"
```

---

### Task 4: Registration, Software Update, Modem Mode Metrics in Exporter

**Files:**
- Modify: `sagemcom_f3896_client/exporter.py:17-27` (add imports)
- Modify: `sagemcom_f3896_client/exporter.py` (expand `update_metrics` — metric declarations, gather, population)

- [ ] **Step 1: Add new model imports to exporter**

In `sagemcom_f3896_client/exporter.py`, update the import from `sagemcom_f3896_client.models` (lines 23-27) to include the new types:

```python
from sagemcom_f3896_client.models import (
    EventLogItem,
    ModemDownstreamChannelResult,
    ModemModeResult,
    ModemUpstreamChannelResult,
    RegistrationResult,
    SoftwareUpdateResult,
)
```

(Note: `ModemModeResult`, `RegistrationResult`, `SoftwareUpdateResult` are imported for type clarity but the exporter accesses them via client method return values. The import ensures the types are available if needed for type hints.)

- [ ] **Step 2: Add metric declarations**

Add these metric declarations alongside the existing ones inside `update_metrics()`, after the service flow metrics added in Task 3:

```python
            metric_registration_complete = Gauge(
                "modem_registration_complete",
                "1 if DOCSIS registration complete",
                registry=registry,
            )
            metric_downstream_registration_locked = Gauge(
                "modem_downstream_registration_locked",
                "1 if downstream locked",
                registry=registry,
            )
            metric_software_update_info = Info(
                "modem_software_update",
                "Software update status",
                registry=registry,
            )
            metric_modem_mode_enabled = Gauge(
                "modem_mode_enabled",
                "1 if modem mode enabled",
                registry=registry,
            )
```

- [ ] **Step 3: Expand asyncio.gather**

Change the gather from Task 3's version:

```python
                state, _, _, _, service_flows = await asyncio.gather(
                    self.client.system_state(),
                    self.__update_downstream_channel_metrics(registry),
                    self.__update_upstream_channel_metrics(registry),
                    self.__log_based_metrics(registry),
                    self.client.modem_service_flows(),
                )
```

to:

```python
                (
                    state,
                    _,
                    _,
                    _,
                    service_flows,
                    registration,
                    software_update,
                    modem_mode,
                    provisioning,
                ) = await asyncio.gather(
                    self.client.system_state(),
                    self.__update_downstream_channel_metrics(registry),
                    self.__update_upstream_channel_metrics(registry),
                    self.__log_based_metrics(registry),
                    self.client.modem_service_flows(),
                    self.client.modem_registration(),
                    self.client.modem_software_update(),
                    self.client.modem_mode(),
                    self.client.system_provisioning(),
                )
```

- [ ] **Step 4: Populate the new metrics**

After the service flow loop added in Task 3, add:

```python
                metric_registration_complete.set(
                    1 if registration.registration_complete else 0
                )
                metric_downstream_registration_locked.set(
                    1 if registration.downstream_locked else 0
                )
                metric_software_update_info.info({"status": software_update.status})
                metric_modem_mode_enabled.set(1 if modem_mode.enabled else 0)
```

- [ ] **Step 5: Verify the exporter still imports**

Run: `uv run python -c "from sagemcom_f3896_client.exporter import Exporter; print('import OK')"`
Expected: `import OK`

- [ ] **Step 6: Commit**

```bash
git add sagemcom_f3896_client/exporter.py
git commit -m "feat: export registration, software update, and modem mode metrics"
```

---

### Task 5: Enrich `modem_info` Labels

**Files:**
- Modify: `sagemcom_f3896_client/exporter.py` (expand `info_labels` dict in `update_metrics`)

- [ ] **Step 1: Enrich info_labels from ModemStateResult**

In `update_metrics()`, find the existing `info_labels` dict (currently around lines 169-176 before our changes). Change it from:

```python
                info_labels = {
                    "mac": state.mac_address,
                    "serial": state.serial_number,
                    "boot_file_name": state.boot_file_name,
                }
                if system_info:
                    info_labels["software_version"] = system_info.software_version
                    info_labels["hardware_version"] = system_info.hardware_version
```

to:

```python
                info_labels = {
                    "mac": state.mac_address,
                    "serial": state.serial_number,
                    "boot_file_name": state.boot_file_name,
                    "docsis_version": state.docsis_version,
                    "status": state.status,
                    "max_cpes": str(state.max_cpes),
                    "access_allowed": str(state.access_allowed).lower(),
                    "baseline_privacy_enabled": str(
                        state.baseline_privacy_enabled
                    ).lower(),
                    "provisioning_mode": provisioning.provisioning_mode,
                    "ds_lite_enabled": str(provisioning.ds_lite_enabled).lower(),
                }
                if system_info:
                    info_labels["software_version"] = system_info.software_version
                    info_labels["hardware_version"] = system_info.hardware_version
```

- [ ] **Step 2: Verify the exporter still imports**

Run: `uv run python -c "from sagemcom_f3896_client.exporter import Exporter; print('import OK')"`
Expected: `import OK`

- [ ] **Step 3: Commit**

```bash
git add sagemcom_f3896_client/exporter.py
git commit -m "feat: enrich modem_info with docsis_version, status, provisioning labels"
```

---

### Task 6: Lint and Final Verification

**Files:**
- All modified files

- [ ] **Step 1: Run linting**

Run: `uv run pre-commit run --all-files`
Expected: All checks pass. If any fail, fix the formatting issues and re-run.

- [ ] **Step 2: Run all unit tests**

Run: `uv run pytest tests/test_models.py tests/test_log_parser.py tests/test_profile_messages.py -v`
Expected: All PASS.

- [ ] **Step 3: Run integration tests (if modem available)**

Run: `uv run pytest tests/test_client.py -v`
Expected: All PASS (or SKIP if no `MODEM_PASSWORD`).

- [ ] **Step 4: Commit any lint fixes**

```bash
git add -u
git commit -m "style: fix lint issues from pre-commit"
```

(Skip this step if there were no lint fixes needed.)
