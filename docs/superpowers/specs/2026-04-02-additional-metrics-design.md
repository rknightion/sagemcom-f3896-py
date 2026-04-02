# Additional Prometheus Metrics for Sagemcom F3896 Exporter

**Date:** 2026-04-02
**Goal:** Expose additional cable-line-quality and ISP-accountability metrics from the modem REST API that are currently unused.

## Context

The exporter currently covers downstream/upstream channel metrics (frequency, power, SNR, MER, errors, lock status, timeouts), log-based metrics (profiles, reboots, OFDM failures), and basic modem info (mac, serial, boot file, software/hardware version, uptime, boot time).

Several REST API endpoints return useful data that is either already fetched but not exported, or available via lightweight unauthenticated calls. The modem is used in modem-only mode (not router), so WiFi, DHCP, connected devices, and MTA/telephony endpoints are out of scope.

## New Metrics

### Service Flows

**Source:** existing `modem_service_flows()` method, endpoint `GET /rest/v1/cablemodem/serviceflows` (no auth).

Shows ISP-provisioned speed tiers and QoS parameters. Useful for overlaying against actual throughput to verify you're getting what you pay for.

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `modem_service_flow_max_traffic_rate` | Gauge | `direction`, `flow_id` | Provisioned max rate in bps |
| `modem_service_flow_max_traffic_burst` | Gauge | `direction`, `flow_id` | Max traffic burst in bytes |
| `modem_service_flow_min_reserved_rate` | Gauge | `direction`, `flow_id` | Min reserved rate in bps |
| `modem_service_flow_max_concatenated_burst` | Gauge | `direction`, `flow_id` | Max concatenated burst in bytes |
| `modem_service_flow_info` | Info | `direction`, `flow_id` | `schedule_type` as info label |

### Registration Status

**Source:** new `modem_registration()` method, endpoint `GET /rest/v1/cablemodem/registration` (no auth, already in `UNAUTHORIZED_ENDPOINTS`).

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `modem_registration_complete` | Gauge | -- | 1 if DOCSIS registration complete, 0 otherwise |
| `modem_downstream_registration_locked` | Gauge | -- | 1 if downstream locked, 0 otherwise |

### Software Update Status

**Source:** new `modem_software_update()` method, endpoint `GET /rest/v1/system/softwareupdate` (no auth).

Useful for correlating firmware pushes with signal quality changes.

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `modem_software_update_info` | Info | -- | `status` label (e.g. `complete_from_management`) |

### Modem Mode

**Source:** new `modem_mode()` method, endpoint `GET /rest/v1/system/modemmode` (no auth).

Canary for unexpected configuration changes.

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `modem_mode_enabled` | Gauge | -- | 1 if modem mode enabled, 0 otherwise |

### Enriched `modem_info`

**Source:** existing `system_state()` (already fetched) and new call to existing `system_provisioning()` method.

Add the following labels to the existing `modem_info` Info metric:

From `ModemStateResult` (already fetched every scrape):
- `docsis_version` (string, e.g. `"3.1"`)
- `status` (string, e.g. `"operational"`)
- `max_cpes` (string from int)
- `access_allowed` (string `"true"`/`"false"`)
- `baseline_privacy_enabled` (string `"true"`/`"false"`)

From `SystemProvisioningResponse` (new call to existing method):
- `provisioning_mode` (string, e.g. `"disable"`)
- `ds_lite_enabled` (string `"true"`/`"false"`)

## Client Changes

### New methods on `SagemcomModemSessionClient`

**`modem_registration()`**
- `GET /rest/v1/cablemodem/registration`
- No auth required (already in `UNAUTHORIZED_ENDPOINTS`)
- Returns `RegistrationResult(registration_complete: bool, downstream_locked: bool)`

**`modem_software_update()`**
- `GET /rest/v1/system/softwareupdate`
- No auth required; add `rest/v1/system/softwareupdate` to `UNAUTHORIZED_ENDPOINTS`
- Returns `SoftwareUpdateResult(status: str)`

**`modem_mode()`**
- `GET /rest/v1/system/modemmode`
- No auth required; add `rest/v1/system/modemmode` to `UNAUTHORIZED_ENDPOINTS`
- Returns `ModemModeResult(enabled: bool)`

### New models in `models.py`

- `RegistrationResult` dataclass with `build()` static method
- `SoftwareUpdateResult` dataclass with `build()` static method
- `ModemModeResult` dataclass with `build()` static method

## Exporter Changes

### Fetch phase

The 5 new/existing calls are added to the existing `asyncio.gather` in `update_metrics()`:

```python
state, _, _, _, service_flows, registration, software_update, modem_mode, provisioning = await asyncio.gather(
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

`system_provisioning()` does not require auth (already in `UNAUTHORIZED_ENDPOINTS`), so this works even without a password.

### Metric creation

All new metrics are created on the per-scrape `CollectorRegistry`, following the existing pattern. No changes to the global registry or the `/metrics` endpoint handler.

### `modem_info` enrichment

The existing `info_labels` dict is extended with the additional fields from `state` and `provisioning`. Booleans are converted to `"true"`/`"false"` strings; integers to strings.

### Service flow metrics

A loop over service flow results, similar to the existing channel metric loops, keyed by `direction` and `flow_id`.

## Out of Scope

- WiFi metrics (modem mode only, no WiFi)
- Connected devices / network hosts
- DHCP / DNS settings
- MTA / telephony lines (not in use)
- Diagnostic tools (ping/traceroute)
- Any write/mutation endpoints

## Testing

- Unit tests for the 3 new model `build()` methods with sample JSON
- Unit tests for new client methods (mock HTTP responses)
- Integration test coverage follows existing pattern (requires `MODEM_PASSWORD` and real modem)
