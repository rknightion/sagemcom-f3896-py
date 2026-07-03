## 2024-08-31 (v0.6.1)

  * Fix bug in channel profile store: while it would not happen in practice, 
    downstream and upstream channels with same number would cause messages to be kept
    while channel would be gone for their channel type.
  * Improved tests of channel profile store.
  * **removed `modem_downstream_errors` and `modem_upstream_timeouts`.

## [0.7.0](https://github.com/rknightion/sagemcom-f3896-py/compare/v0.6.2...v0.7.0) (2026-07-03)


### Features

* add modem_registration, modem_software_update, modem_mode client methods ([2ce961d](https://github.com/rknightion/sagemcom-f3896-py/commit/2ce961d9a12748d52ea4d9adb5553ac2377dccd7))
* add RegistrationResult, SoftwareUpdateResult, ModemModeResult models ([28711a4](https://github.com/rknightion/sagemcom-f3896-py/commit/28711a41399e532d66f4f135fea87b78ca50457d))
* enrich modem_info with docsis_version, status, provisioning labels ([c68c451](https://github.com/rknightion/sagemcom-f3896-py/commit/c68c451e9d97f3fcdd4d17ea0adb2120872d5bb2))
* export registration, software update, and modem mode metrics ([7e13cd9](https://github.com/rknightion/sagemcom-f3896-py/commit/7e13cd985ba4ea9f92e6d6ae7a7c75195facbed5))
* export service flow metrics (max rate, burst, reserved rate, schedule type) ([915c93d](https://github.com/rknightion/sagemcom-f3896-py/commit/915c93d10a5edb56f501ad2e082bfac44105f4cc))


### Bug Fixes

* **deps:** update dependency prometheus-async to v26 ([#9](https://github.com/rknightion/sagemcom-f3896-py/issues/9)) ([409dae0](https://github.com/rknightion/sagemcom-f3896-py/commit/409dae08337983c647c61ef625cc8817b3010cd7))
* Dockerfile to reduce vulnerabilities ([dd057c6](https://github.com/rknightion/sagemcom-f3896-py/commit/dd057c6c2f5474838bcaf674fd858ced13012621))
* suppress prometheus_async SyntaxWarning on Python 3.14 ([afd7d2a](https://github.com/rknightion/sagemcom-f3896-py/commit/afd7d2acaa4947a956abcead4649b56b108d59a9))


### Documentation

* add design spec for additional Prometheus metrics ([6d3bc68](https://github.com/rknightion/sagemcom-f3896-py/commit/6d3bc681541832d959a11eac98ed3aaf33237b03))
* add implementation plan for additional Prometheus metrics ([fd715f3](https://github.com/rknightion/sagemcom-f3896-py/commit/fd715f34a05fadf40a1cfc849cf26432d7e695e4))


### Build & CI

* add hadolint + trivy Docker security scans ([7a0f5a0](https://github.com/rknightion/sagemcom-f3896-py/commit/7a0f5a038ee08a8ede2b757c8e38cc73bb6ba06f))
* add OpenSSF Scorecard via shared reusable workflow ([de2f982](https://github.com/rknightion/sagemcom-f3896-py/commit/de2f982b89c724e71d61b1e0319b376ab644d1d8))
* add Snyk -&gt; Snyk Cloud monitor (SCA/SAST/IaC/container) ([e0b7d55](https://github.com/rknightion/sagemcom-f3896-py/commit/e0b7d552d3028d88af1a09360b950c5ce7720029))
* adopt release-please; publish via shared container-publish reusable ([46236ae](https://github.com/rknightion/sagemcom-f3896-py/commit/46236ae8a7576c083962274987a6b1476e3c2f49))
* adopt shared rknightion/.github reusable security workflows ([10c636c](https://github.com/rknightion/sagemcom-f3896-py/commit/10c636ced5f3ee277ec67c2e90dec9a08322e971))
* auto-assign maintainer on new issues (notify by email) ([9954bc8](https://github.com/rknightion/sagemcom-f3896-py/commit/9954bc802ea98c38df2b8a6e7eeb4369313fc03f))
* bump shared rknightion reusables to v1.3.1 ([90c2058](https://github.com/rknightion/sagemcom-f3896-py/commit/90c2058f8c6d216da97f4f609d58dd7caf7157fe))
* drop CodeQL pull_request trigger to trim Actions fan-out ([7fb9ce7](https://github.com/rknightion/sagemcom-f3896-py/commit/7fb9ce7f9ae3c78ca45c1291b63474b2ea4d7ef5))
* fix Renovate automerge stall + add required ci-success gate ([01fad2b](https://github.com/rknightion/sagemcom-f3896-py/commit/01fad2bcb8a55df34e27dac98bbb966f0fd9e409))
* ignore E402 in exporter.py ([8d3ea2e](https://github.com/rknightion/sagemcom-f3896-py/commit/8d3ea2e5f2e68f25d90379f777f75a5a2f235248))
* migrate from Poetry to modern pyproject.toml ([e510dda](https://github.com/rknightion/sagemcom-f3896-py/commit/e510dda9214daa20a1b32701a5d6c71ef92ed38c))
* pin shared rknightion reusables to v1.0.0 ([55b047c](https://github.com/rknightion/sagemcom-f3896-py/commit/55b047ce981a89edf1ef5e0dcdec9174987e948a))
* reference rknightion/.github reusables [@main](https://github.com/main) (unpin from digest) ([1f23fd1](https://github.com/rknightion/sagemcom-f3896-py/commit/1f23fd14b208451d5e3874cf187528ff5cc6f3e3))
* remove notify-maintainer-on-new-issue workflow ([15dd6a8](https://github.com/rknightion/sagemcom-f3896-py/commit/15dd6a896342db0c7462f7b66385c2f8b6b2a5e9))
* resolve actionlint/shellcheck + zizmor workflow findings ([87e7a5e](https://github.com/rknightion/sagemcom-f3896-py/commit/87e7a5e2366e7dd1449a9b729f3de06c18cadda6))

## 2024-8-29 (v0.6.0)

  * Update dependencies
  * Document `MODEM_URL` option
  * Add `node_boot_time_seconds` metric calculated from uptime.
  * Add `modem_downstream_errors_total` that will replace
    `modem_downstream_errors` metric (clearer name).
  * **deprecated** the `modem_downstream_errors` metric. Will be removed on or after 1-7-2024.

## 2024-03-09 (v0.5.0)

  * Enable dependabot dependency management
  * Add `modem_upstream_timeout_count` metric that will replace
    `modem_upstream_timeouts` metric (clearer name).
  * **deprecated** `modem_upstream_timeouts` metric. Will be removed on or after 1-5-20204.

## 2024-02-17 (v0.4.1)

  * fix: `modem_upstream_ofdm` metric is now called `modem_upstream_ofdma`
  * fix: Return metrics when login fails (main cause: concurrent login)

## 2024-02-xx (v0.4.0)

  * 10 second timeout for fetching data
  * Keep previous metrics when a fetch fails (or times out).
  * Metrics duration now tracks fetching time, not web request delay.
  * Uses locking to prevent concurrent update requests

## 2024-02-09 (v0.3.1)

  * Container based on python 3.12
  * Parse more sample log messages
  * Updated dependencies

## 2023-12-30 (v0.3.0):

  * Fixed a bug where the metrics endpoint would break if the modem forgot
    about the session (for example: reboot while a session was active).
  * Updated pre-commit hooks
  * cli `logs` command prints all log entries (except for logins), not first 10.

## 2023-12-19 (v0.2.1)

  * Filter the "login success" messages by default.

## 2023-12-11 (v0.2.0)

  * Add a stable sort for event log items and use it in the web
    index page.
  * Build with Python 3.12
  * Update pre-commit settings
  * Log new modem log items with `f3896.eventlog` tag:
```
INFO:f3896.eventlog:2023-12-09T19:46:45+00:00 [notice]: US profile assignment change. US Chan ID: 27; Previous Profile: 10 13; New Profile: 11 13.;CM-MAC=44:05:de:ad:be:ef;CMTS-MAC=00:01:de:ad:be:ef;CM-QOS=1.1;CM-VER=3.1;
INFO:f3896.eventlog:2023-12-09T18:36:26+00:00 [notice]: US profile assignment change. US Chan ID: 27; Previous Profile: 9 13; New Profile: 10 13.;CM-MAC=44:05:de:ad:be:ef;CMTS-MAC=00:01:de:ad:be:ef;CM-QOS=1.1;CM-VER=3.1;
```
  * Log these messages in chronological order (newest last)
