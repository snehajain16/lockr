---
artifact: tech_spec
project: Lockr
owner_role: architect-dev
phase: solutioning
workflow: tech-spec
status: drafted
date: 2026-04-15
epic: 1
---

# Epic 1 Tech Spec: Vault Foundation

## Scope

Implement stories 1.1 through 1.4 only:

- vault initialization
- explicit unlock and lock behavior
- secret create/update flows
- secret read and list flows

Excluded from this slice:

- `.env` import/export
- shell injection
- git backup
- TUI

## Design Decisions

- Use a single encrypted vault file at `LOCKR_HOME/vault.lockr`.
- Use `LOCKR_HOME/session.json` as the local unlock-state cache for the derived vault key.
- Use scrypt for key derivation and AES-GCM for authenticated encryption through the `cryptography` package.
- Use Typer for the CLI surface.
- Persist the whole vault as one encrypted JSON document to keep MVP writes atomic and schema simple.

## File Plan

- `pyproject.toml`
  Add project metadata, runtime dependencies, and `lockr` console script.
- `src/lockr/paths.py`
  Resolve workspace paths from `LOCKR_HOME` or default home directory.
- `src/lockr/domain/models.py`
  Define vault and secret dataclasses plus serialization helpers.
- `src/lockr/security/crypto.py`
  Implement scrypt key derivation, AES-GCM encryption, and vault decryption.
- `src/lockr/storage/files.py`
  Implement atomic text and JSON writes plus file helpers.
- `src/lockr/app/vault_service.py`
  Implement Epic 1 application use cases and error types.
- `src/lockr/cli/main.py`
  Expose `init`, `unlock`, `lock`, `set`, `get`, and `list`.
- `tests/test_epic1_cli.py`
  Validate the Epic 1 acceptance criteria end to end.

## CLI Contract

### `lockr init`

Given no existing vault  
When the user confirms a master password  
Then the command creates the vault file, creates the unlock session, and returns success.

Given an existing vault and no `--force`  
When the user runs `lockr init`  
Then the command exits non-zero with a safe overwrite warning.

### `lockr unlock`

Given an initialized vault and a valid password  
When the user runs `lockr unlock`  
Then the command validates credentials and creates session state.

Given an invalid password  
When the user runs `lockr unlock`  
Then the command exits non-zero without modifying the vault.

### `lockr lock`

Given an unlocked vault  
When the user runs `lockr lock`  
Then the session file is removed and later access requires unlock again.

### `lockr set`

Given an unlocked vault  
When the user sets a key in a project/environment  
Then the secret is created or updated atomically.

### `lockr get`

Given a stored secret  
When the user runs `lockr get KEY`  
Then the default output is masked.

Given `--raw`  
When the user runs `lockr get KEY --raw`  
Then the plaintext value is printed.

Given `--json`  
When the user runs `lockr get KEY --json`  
Then metadata excluding the plaintext value is printed.

### `lockr list`

Given stored secrets  
When the user runs `lockr list` with optional filters  
Then matching metadata rows are returned without plaintext values.

## Risks

- Session key caching improves CLI ergonomics but stores the derived key locally while unlocked.
- Whole-vault rewrite semantics are simple for MVP but can become a scalability bottleneck later.

## Implementation Notes

- Session cache is acceptable for Epic 1, but must remain clearly documented as a local unlocked state artifact.
- The next implementation slice should decide whether to add session TTL or re-prompt behavior.
