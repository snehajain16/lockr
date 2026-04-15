---
artifact: stories
project: Lockr
owner_role: pm-dev
phase: solutioning
workflow: stories
status: drafted
date: 2026-04-15
---

# Epics and Stories

## Epic 1: Vault Foundation

### Story 1.1: Initialize a vault

As a developer, I want to initialize a Lockr vault so that I can store secrets securely on my machine.

Acceptance Criteria:

- `lockr init` creates the required local vault structure
- user is prompted for master secret input without echoing plaintext
- an empty encrypted vault file is written atomically
- rerunning init on an existing vault requires explicit confirmation or aborts safely

### Story 1.2: Unlock and lock the vault

As a developer, I want to unlock and lock the vault so that secret access is explicit and controlled.

Acceptance Criteria:

- locked vault access attempts fail with actionable guidance
- unlock flow validates credentials without leaking sensitive details
- lock command clears active session state
- failed unlock attempts do not corrupt vault data

### Story 1.3: Add and update secrets

As a developer, I want to store and modify secrets so that the vault becomes my working source of truth.

Acceptance Criteria:

- `set` command supports key, project, environment, and value input
- updating an existing secret preserves metadata history fields appropriately
- values are never printed back in plaintext unless explicitly requested
- write operations are atomic

### Story 1.4: List and read secrets

As a developer, I want to discover and retrieve secrets so that I can use them in scripts and tools.

Acceptance Criteria:

- list view supports filtering by project and environment
- get command supports masked and raw modes
- missing secret lookups return clear non-zero exit codes
- metadata view excludes plaintext secret values

## Epic 2: Project and Environment Workflow

### Story 2.1: Organize secrets by project and environment

As a developer, I want project-scoped secret organization so that keys for different apps do not collide.

Acceptance Criteria:

- secrets support project and environment fields
- list and get resolution honor project/environment filters
- duplicate key names across projects are supported safely

### Story 2.2: Import `.env` files

As a developer, I want to import existing `.env` files so that I can migrate into Lockr quickly.

Acceptance Criteria:

- import command parses standard `.env` key-value pairs
- preview step shows keys to be imported without exposing full values by default
- conflicts are surfaced with overwrite or skip options
- imported secrets land in the selected project/environment scope

### Story 2.3: Export `.env` material intentionally

As a developer, I want controlled `.env` export so that I can interoperate with tools that still require files.

Acceptance Criteria:

- export requires explicit destination path or stdout mode
- export command warns when writing plaintext files
- exported content is limited to selected project/environment scope

## Epic 3: Runtime Injection

### Story 3.1: Run a command with injected secrets

As a developer, I want to run a process with secrets injected so that I do not need to edit shell profiles or local files.

Acceptance Criteria:

- `lockr run -- <command>` injects selected environment variables into the child process
- injection does not persist secrets beyond the child process by default
- command exit code is preserved
- errors distinguish command failure from vault failure

### Story 3.2: Print shell export output

As a developer, I want shell-compatible export output so that I can source secrets when needed.

Acceptance Criteria:

- export-shell supports PowerShell and POSIX syntax
- command is explicit about shell target
- output can be piped or evaluated without extra formatting noise

## Epic 4: Backup and Recovery

### Story 4.1: Create encrypted git backup

As a developer, I want encrypted backups in git so that I can restore my vault on another machine.

Acceptance Criteria:

- backup command validates git and gpg availability first
- backup artifact contains no plaintext secrets
- artifact can be written to configured repository path
- optional auto-commit mode is gated by explicit user flag

### Story 4.2: Restore from encrypted backup

As a developer, I want to restore my vault from backup so that machine migration is practical.

Acceptance Criteria:

- restore validates artifact integrity before replacing local state
- existing local vault state is backed up or confirmed before overwrite
- restore failures do not leave the vault half-written

### Story 4.3: Show backup status

As a developer, I want to inspect backup status so that I know whether my vault is recoverable.

Acceptance Criteria:

- status command shows configured backup target and last successful backup timestamp
- missing git or gpg dependencies are reported clearly

## Epic 5: TUI and Audit Visibility

### Story 5.1: Browse secrets in a TUI

As a developer, I want an interactive terminal UI so that I can manage secrets without memorizing every command.

Acceptance Criteria:

- TUI lists projects and secrets without showing plaintext values by default
- user can navigate to metadata and edit workflows
- TUI reuses the same service layer as CLI commands

### Story 5.2: View audit metadata

As a developer, I want audit-friendly metadata so that I can track changes and rotation hygiene.

Acceptance Criteria:

- metadata includes created and updated timestamps
- optional last rotated timestamp is supported
- audit view never exposes decrypted values accidentally

## Delivery Notes

- Epic 1 should be built first because all later workflows depend on a trustworthy vault core.
- Epic 2 and Epic 3 can proceed in parallel after Epic 1.
- Epic 4 depends on stable vault persistence contracts.
- Epic 5 can begin after shared service interfaces are established.
