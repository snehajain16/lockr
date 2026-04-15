---
artifact: tech_spec
project: Lockr
owner_role: architect-dev
phase: solutioning
workflow: tech-spec
status: drafted
date: 2026-04-15
epic: 2
---

# Epic 2 Tech Spec: Project and Environment Workflow

## Scope

Implement stories 2.1 through 2.3 only:

- project and environment scoped secret workflows
- `.env` import with preview and conflict handling
- controlled `.env` export to file or stdout

Excluded from this slice:

- runtime injection
- git backup
- TUI
- secret rotation workflows

## Design Decisions

- Keep Epic 1 vault model unchanged: one encrypted vault file rewritten atomically.
- Reuse the existing `project` and `environment` fields already present on `SecretRecord`.
- Add dedicated `.env` parsing and rendering helpers under an integration module.
- Make `.env` import a two-step explicit flow:
  - `import-env --preview` for redacted inspection
  - `import-env --apply` for writing to the vault
- Require explicit destination or stdout for export; never silently write plaintext files.

## File Plan

- `src/lockr/integrations/env_files.py`
  Parse `.env` files, normalize lines, redact preview values, and render export payloads.
- `src/lockr/app/vault_service.py`
  Add import preview, import apply, and export selection use cases.
- `src/lockr/cli/main.py`
  Add `import-env` and `export-env` commands plus project/environment options.
- `tests/test_epic2_env_workflow.py`
  Cover import preview, conflict handling, project/environment mapping, and export behavior.
- `docs/planning/validation_epic2.md`
  Record Epic 2 validation evidence after implementation.

## CLI Contract

### `lockr import-env`

Given a valid `.env` file  
When the user runs `lockr import-env PATH --project foo --environment dev --preview`  
Then Lockr prints the candidate keys and redacted values without changing the vault.

Given a valid `.env` file and `--apply`  
When the user runs `lockr import-env PATH --project foo --environment dev --apply`  
Then Lockr imports the keys into the selected project/environment scope.

Given a key conflict  
When the user runs `lockr import-env ... --apply` without overwrite  
Then conflicting keys are skipped and reported.

Given a key conflict and `--overwrite`  
When the user runs `lockr import-env ... --apply --overwrite`  
Then conflicting keys are updated in place.

### `lockr export-env`

Given stored secrets for a project/environment  
When the user runs `lockr export-env --project foo --environment dev --stdout`  
Then Lockr prints `.env` formatted plaintext to stdout.

Given an explicit path  
When the user runs `lockr export-env --project foo --environment dev --output PATH`  
Then Lockr writes the plaintext `.env` payload to the given destination and warns about plaintext export.

## Data and Parsing Rules

- Support basic `.env` syntax: `KEY=value`, blank lines, and comment lines beginning with `#`.
- Trim surrounding whitespace from keys and values.
- Preserve raw value content after the first `=`.
- Ignore malformed lines during preview and apply, but report them in the command summary.
- Import maps every parsed entry into the chosen project/environment scope.

## Validation Requirements

- Import preview must not write to the vault.
- Import apply must report counts for imported, updated, skipped, and malformed entries.
- Export must only include secrets matching the selected project/environment filter.
- Export file writes must be explicit and must emit a plaintext warning.

## Risks

- `.env` parsing can become surprisingly broad if quoting and interpolation semantics are expanded too early.
- Plaintext export is inherently risky, so the CLI must make it explicit and noisy.

## Implementation Notes

- Keep the first implementation to a conservative `.env` subset rather than trying to match every shell dialect.
- Prefer deterministic command summaries because Epic 2 will feed later automation and runtime-injection work.
