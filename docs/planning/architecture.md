---
artifact: architecture
project: Lockr
owner_role: architect
phase: solutioning
workflow: architecture
status: drafted
date: 2026-04-15
---

# Architecture

## 1. Architectural Goals

- maintain strong local-at-rest secret protection
- keep the CLI composable and script-friendly
- isolate security-critical logic from presentation layers
- support optional git backup without coupling vault operations to git state
- remain cross-platform for Windows, macOS, and Linux

## 2. Proposed Stack

- Language: Python 3.12+
- CLI: Typer
- TUI: Textual
- Crypto: `cryptography` with AES-256-GCM or XChaCha20-Poly1305 equivalent if supported by chosen library
- Config/Data Modeling: Pydantic or standard dataclasses with strict validation
- Storage: local filesystem with atomic writes
- Backup: Git CLI plus GPG CLI integration
- Testing: pytest

## 3. High-Level Components

### CLI Layer

Parses commands, validates flags, renders user output, and delegates work to application services.

### TUI Layer

Provides interactive browsing and guided workflows using the same application services as the CLI.

### Application Services

Implements use cases such as vault initialization, secret CRUD, `.env` import, environment injection, backup, and restore.

### Domain Layer

Owns secret entities, metadata models, policies, and validation rules independent of interface concerns.

### Security Layer

Handles key derivation, encryption/decryption, masking policy, secure temporary handling, and integrity verification.

### Persistence Layer

Manages encrypted vault file layout, lock state metadata, atomic writes, and migrations.

### Integration Layer

Wraps Git, GPG, shell output generation, and `.env` parsing.

## 4. Suggested Repository Layout

```text
lockr/
  pyproject.toml
  src/lockr/
    cli/
    tui/
    app/
    domain/
    security/
    storage/
    integrations/
    utils/
  tests/
    unit/
    integration/
    e2e/
  docs/
    planning/
```

## 5. Data Design

### Vault File

Use a single encrypted vault container in MVP to reduce synchronization complexity.

Suggested plaintext structure before encryption:

```json
{
  "version": 1,
  "vault": {
    "projects": {},
    "secrets": [
      {
        "id": "uuid",
        "key": "OPENAI_API_KEY",
        "value": "secret",
        "project": "lockr",
        "environment": "dev",
        "tags": ["api", "llm"],
        "description": "optional",
        "created_at": "timestamp",
        "updated_at": "timestamp",
        "last_rotated_at": "timestamp"
      }
    ]
  }
}
```

### Local Metadata

Store non-sensitive operational metadata separately if needed:

- active vault path
- backup repo path
- last backup timestamp
- shell integration preferences

Sensitive values must never live in plaintext metadata files.

## 6. Security Design

- derive an encryption key from the unlock secret using a hardened KDF such as scrypt or Argon2id
- encrypt the full vault payload with authenticated encryption
- use per-write random nonces
- verify authentication tag before any plaintext is accepted
- mask secret values in UI by default
- treat clipboard export as out of scope unless explicitly designed later

## 7. Primary Flows

### Initialize Vault

1. User runs `lockr init`
2. CLI collects master secret and confirms it
3. Security layer derives key material
4. Storage layer writes empty encrypted vault atomically
5. CLI returns success and next-step guidance

### Read Secret

1. User runs `lockr get KEY --project foo`
2. Vault unlock is requested if not already active
3. Security layer decrypts vault in memory
4. Domain layer resolves matching secret
5. CLI returns masked or explicit output based on mode

### Inject Environment

1. User runs `lockr run --project foo -- command`
2. App resolves relevant secrets
3. Child process receives an in-memory environment map
4. Parent process avoids persisting plaintext to disk

### Backup

1. User runs `lockr backup create`
2. App validates Git and GPG availability
3. Vault blob is exported or rewrapped as backup artifact
4. Artifact is encrypted for backup and written to repo
5. Git integration stages and optionally commits changes

## 8. Interface Contracts

- CLI output must support human-readable and JSON modes
- service interfaces must be UI-agnostic
- integration wrappers must surface structured errors instead of raw subprocess noise

## 9. Testing Strategy

- unit tests for domain logic, masking, parsing, and validation
- crypto round-trip and tamper detection tests
- integration tests for storage, git backup, and `.env` import
- e2e CLI tests for init, set, get, run, backup, and restore

## 10. Key Decisions

- single encrypted vault file for MVP simplicity
- shared service layer for CLI and TUI
- optional backup remains an integration, not a core dependency
- shell injection is command-scoped by default to reduce exposure

## 11. Outstanding Questions

- should unlock session caching exist, and if so for how long
- should secret history/versioning be recorded in MVP
- how much backup automation should happen by default after writes
