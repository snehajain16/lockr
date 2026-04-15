---
artifact: validation
project: Lockr
owner_role: tea
phase: validation
workflow: validation
status: drafted
date: 2026-04-15
scope: Epic 2
---

# Epic 2 Validation

## Validation Target

Stories 2.1 through 2.3 from Epic 2.

## Checks Run

- `pytest -q`
- `lockr --help`
- direct service-level verification for `.env` preview, apply, malformed-line reporting, and scoped export

## Results

- Automated tests passed: 8 passed.
- CLI command surface exposes `import-env` and `export-env`.
- Manual service verification succeeded:
  - preview parsed 2 valid entries
  - malformed line reporting returned line `2`
  - apply imported 2 entries and reported 1 malformed line
  - scoped export returned 2 matching secrets
  - exported content contained the expected plaintext key/value pairs

## Acceptance Coverage

- Story 2.1: covered by project/environment scoped import, export, and filtered secret retrieval tests.
- Story 2.2: covered by preview-only import, apply import, malformed-line reporting, and overwrite/skip conflict tests.
- Story 2.3: covered by stdout export, file export warning, and scoped file content tests.

## Residual Risks

- `.env` parsing intentionally supports only a conservative subset and does not yet handle quoting or interpolation semantics.
- Plaintext export remains a user-risky workflow even with explicit destination and warning behavior.

## Recommendation

Epic 2 is validated and ready to hand off for Epic 3 planning and implementation.
