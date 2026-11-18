# Sagemcom F3896 client review

## Repository scope

This package supplies an async Python client for Sagemcom F3896 endpoints and a Prometheus exporter. Review public client methods, response models, and exported metrics for compatibility with existing callers.

## Modem sessions and responses

Check login, authentication, logout and async-session ownership together. Keep the unauthenticated endpoint allowlist precise. Review success, malformed responses and cancellation or failures that happen after a session opens. Preserve explicit aliasing and defaults for firmware response fields.

## Exporter and profile messages

Check metric names, types, labels and unit conversions against existing output. Keep per-scrape registries isolated and preserve import and warning-filter order in the exporter. Treat profile-message or event-log reads as device interactions and check how parsing handles missing fields and unexpected records.

## Verification

Use recorded fixtures or a fake session for error cases. Match changes against the offline parser, model and session tests. For metric changes, look for focused coverage of the changed exporter behavior. The local gate is `just check`. Running the hardware tests requires an explicitly configured modem.

## Public evidence

Keep modem credentials, tokens, device identifiers and real response bodies out of logs, examples and review evidence. Use sanitized fixtures that retain the shape needed to reproduce a failure.
