---
id: FSG-0001
title: Replace the hand-concatenated two-registry /metrics response
status: To Do
assignee: []
created_date: '2026-08-14 16:57'
labels: []
dependencies: []
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The exporter serves two registries: module-level collectors live in prometheus_client's global REGISTRY, per-scrape collectors live in a fresh CollectorRegistry. metrics() in exporter.py joins them by decoding both to text, stripping the first, and concatenating with a newline. The FIXME at exporter.py:127 marks it as hacky and it has outlived the comment. Text-level joining bypasses the exposition-format machinery: it hardcodes the assumption that the negotiated format is line-oriented text, so a future content-type negotiation (OpenMetrics) silently produces a malformed body rather than an error, and the strip/newline handling is doing by hand what a registry merge does correctly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The /metrics body is produced without string-concatenating two separately generated payloads
- [ ] #2 The exposition format is chosen by the same content negotiation as before, not assumed to be line-oriented text
- [ ] #3 Every metric present in the current output is still present, with unchanged names, labels and HELP/TYPE lines
- [ ] #4 The FIXME comment at exporter.py:127 is removed rather than reworded
- [ ] #5 tests/test_exporter.py covers the merged output, since that file is currently empty
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 uv run ruff check .
- [ ] #2 uv run ruff format --check .
- [ ] #3 uv run pytest tests
<!-- DOD:END -->
