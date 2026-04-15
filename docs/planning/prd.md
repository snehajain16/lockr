---
artifact: prd
project: Lockr
owner_role: pm
phase: planning
workflow: prd
status: drafted
date: 2026-04-15
---

# Product Requirements Document

## 1. Executive Summary

Lockr is a terminal-based secrets vault designed for developers who need secure local secret storage, ergonomic CLI workflows, `.env` integration, and optional encrypted git backup. The product should prioritize safety, scriptability, and clarity over broad enterprise scope.

## 2. Objectives

- provide a trustworthy local vault for development secrets
- reduce insecure secret handling in files and shell history
- make secret retrieval and injection fast enough for daily CLI use
- enable optional encrypted backup and recovery with git plus GPG
- support project-scoped secret organization and `.env` workflows

## 3. Non-Goals

- replace enterprise cloud secret managers
- support production secret orchestration
- provide collaborative admin workflows in v1
- act as a general password manager for consumers

## 4. Users and Jobs To Be Done

### Solo Developer

Needs a quick way to store and retrieve secrets across projects without copying plaintext between notes, shell profiles, and `.env` files.

### Small Team Developer

Needs a repeatable way to bootstrap local development secrets from an encrypted backup without committing plaintext into a repository.

### Security-Conscious Power User

Needs verifiable encryption behavior, explicit audit actions, and minimized plaintext exposure when viewing or injecting secrets.

## 5. User Stories

- As a developer, I want to initialize a local vault so I can begin storing secrets securely.
- As a developer, I want to add and update secrets from the CLI so I can automate workflows.
- As a developer, I want to organize secrets by project and environment so I can avoid collisions.
- As a developer, I want to import existing `.env` files so I can migrate from insecure storage.
- As a developer, I want to inject secrets into a shell or command session so I can run tools without rewriting configs.
- As a developer, I want to back up my encrypted vault to git so I can recover my setup on another machine.
- As a developer, I want to inspect audit metadata so I can see when a secret was created, changed, or rotated.

## 6. Functional Requirements

### Vault Management

- initialize a vault with a master password or key material flow
- lock and unlock the vault explicitly
- add, update, delete, list, and read secrets
- tag secrets by project, environment, and type
- support metadata fields such as description, created_at, updated_at, and last_rotated_at

### Security

- encrypt secrets at rest using modern authenticated encryption
- never store plaintext secrets in the vault on disk
- minimize plaintext exposure in terminal output
- provide confirmation or masked output modes for sensitive reads
- clear temporary plaintext files or buffers where feasible

### CLI Experience

- provide consistent subcommands and help output
- support non-interactive scripting modes
- support machine-readable output for automation
- return stable exit codes

### TUI Experience

- browse projects and secrets
- create and edit entries with masked inputs
- inspect metadata and backup status
- guide users through import, backup, and recovery tasks

### `.env` Integration

- import `.env` key-value pairs into the vault
- generate redacted previews before import
- export selected secrets back into `.env` format when explicitly requested
- map vault entries to project-specific `.env` templates

### Environment Injection

- run commands with injected environment variables
- print shell-compatible export output when requested
- support temporary session injection with clear warnings

### Git Backup

- create encrypted backup artifacts suitable for git storage
- integrate with local git repos or a dedicated backup repo
- support backup status, restore, and verification commands
- require GPG availability for git backup flows

## 7. Non-Functional Requirements

### Security

- encryption implementation must rely on vetted libraries, not custom crypto
- secret values must not appear in logs, debug output, or standard traces by default
- restore and backup flows must verify integrity before acceptance

### Reliability

- operations should fail safely without corrupting the vault
- writes should be atomic where possible
- backup and restore should be resumable or rollback-safe

### Usability

- first-run setup should complete in under 5 minutes for a developer with existing secrets
- common read/write operations should take under 300 ms for a small local vault
- help text and error messages must be actionable

### Portability

- v1 should support Windows, macOS, and Linux
- shell integration should at minimum support PowerShell and bash-compatible shells

## 8. Success Metrics

- user can initialize vault, add a secret, and retrieve it in under 3 minutes
- user can import an existing `.env` file with preview and confirmation
- user can run a command with injected secrets without leaving plaintext on disk
- user can create an encrypted git backup and restore it on a second machine

## 9. Release Scope

### MVP

- local vault initialization and unlock flow
- CRUD secret operations via CLI
- project/environment tagging
- `.env` import
- command/session injection
- encrypted git backup and restore
- minimal TUI browser/editor

### Post-MVP

- rotation reminders and health checks
- secret search and filters
- richer audit history
- plugin/provider integrations

## 10. Open Decisions

- whether the vault unlock model is password-derived only or supports external key files
- whether TUI ships in MVP or as milestone 1.1
- whether backup format is a single encrypted archive or structured encrypted records
- whether team-sharing documentation is included even if collaborative features are not

## 11. Dependencies

- Python runtime and packaging strategy
- cryptographic library support
- GPG installation for backup workflows
- Git installation for backup workflows

## 12. Risks and Mitigations

- Crypto misuse risk.
  Mitigation: use vetted libraries, constrain cipher choices, add strong tests around encrypt/decrypt and tamper detection.
- Cross-platform shell complexity.
  Mitigation: define a thin abstraction and ship PowerShell plus POSIX support first.
- Backup misunderstanding.
  Mitigation: make backup status explicit and document exactly what is encrypted and committed.
