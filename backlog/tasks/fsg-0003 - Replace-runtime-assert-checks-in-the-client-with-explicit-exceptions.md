---
id: FSG-0003
title: Replace runtime assert checks in the client with explicit exceptions
status: To Do
assignee: []
created_date: '2026-11-07T18:57:00Z'
labels: []
dependencies: []
priority: medium
type: bug
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
sagemcom_f3896_client/client.py uses assert for runtime validation: line 49 (relative-URL check), line 112 (login status in 200/201/204), lines 130 and 140 (status checks). python -O strips assert, so login and request failures would pass silently. Replace with explicit raises of the client's own exception types, keeping authentication failure distinct from transport failure. The managed Kodus rule sagemcom-f3896-py-01 currently claims the code has no assert-dependent runtime safety and must be corrected alongside. Found by a Kodus rules-research pass on 2026-11-07, confirmed by reading the code.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 No assert statement guards external input or HTTP status in sagemcom_f3896_client
- [ ] #2 Tests cover a failed login and an unexpected status raising the client's exception under python -O
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 just check
<!-- DOD:END -->
