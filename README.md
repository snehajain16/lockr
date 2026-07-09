# Lockr

A terminal-first secrets vault for developers who want local encrypted secret storage, project-scoped organization, and ergonomic CLI workflows — without cloud dependencies.

## Features

- **Encrypted local vault** — AES-256-GCM encryption via the `cryptography` package
- **Project & environment scoping** — organize secrets by project and environment (dev/staging/prod)
- **`.env` import/export** — preview, apply, and export `.env` files with conflict control
- **Runtime injection** — run any command with secrets injected as environment variables
- **Shell export** — print POSIX or PowerShell export statements for sourcing into your shell
- **Git backup & restore** — encrypted vault backup to a git repo, with atomic restore
- **Interactive TUI** — browse secrets in a Textual terminal UI (no plaintext values shown)
- **Audit metadata** — view created/updated/rotated timestamps without exposing values

## Install

Requirements: Python 3.12+

```bash
pip install -e .
```

After installation the CLI is available as `lockr`:

```bash
lockr --help
```

## Quick Start

```bash
# Initialize and unlock vault
lockr init

# Store a secret
lockr set OPENAI_API_KEY --value sk-... --project myapp --environment dev

# Read (masked by default)
lockr get OPENAI_API_KEY --project myapp --environment dev

# Read raw value
lockr get OPENAI_API_KEY --project myapp --environment dev --raw

# List secrets
lockr list --project myapp --environment dev

# Lock / unlock
lockr lock
lockr unlock
```

## Command Reference

### Vault

```bash
lockr init [--force]
lockr unlock
lockr lock
```

### Secrets

```bash
lockr set KEY [--value VALUE] [--project NAME] [--environment NAME] [--description TEXT]
lockr get KEY [--project NAME] [--environment NAME] [--raw] [--json]
lockr list [--project NAME] [--environment NAME] [--json]
```

### `.env` Import / Export

```bash
# Preview import (redacted values, no writes)
lockr import-env .env --project myapp --environment dev --preview

# Apply import
lockr import-env .env --project myapp --environment dev --apply [--overwrite]

# Export as .env
lockr export-env --project myapp --environment dev --stdout
lockr export-env --project myapp --environment dev --output .env.local
```

### Runtime Injection

```bash
# Run a command with secrets injected as env vars
lockr run --project myapp --environment dev -- python app.py

# Print shell export statements
lockr export-shell --project myapp --environment dev --shell posix
lockr export-shell --project myapp --environment dev --shell powershell

# Source into current shell (POSIX)
eval "$(lockr export-shell --project myapp --environment dev)"
```

### Backup & Restore

```bash
# Write encrypted backup artifact to a git repo
lockr backup create --repo /path/to/backup-repo
lockr backup create --repo /path/to/backup-repo --commit

# Restore vault from backup
lockr backup restore --repo /path/to/backup-repo

# Check backup status and dependency availability
lockr backup status
```

### TUI & Audit

```bash
# Interactive TUI browser (no plaintext values shown)
lockr tui

# List secrets with full audit metadata (no values)
lockr audit [--project NAME] [--environment NAME] [--json]
```

## Storage

| File | Purpose |
|------|---------|
| `$LOCKR_HOME/vault.lockr` | AES-256-GCM encrypted vault |
| `$LOCKR_HOME/session.json` | Session key cache (while unlocked) |
| `$LOCKR_HOME/backup.json` | Backup configuration |

`LOCKR_HOME` defaults to `~/.lockr` when not set.

## Security Notes

- Vault is encrypted at rest with AES-256-GCM; key derived via Scrypt
- Secret values are masked by default in all CLI output
- The TUI and `audit` command never display plaintext values
- `.env` export is intentionally plaintext and requires an explicit `--stdout` or `--output` flag
- Session key is cached locally while unlocked — lock explicitly when done

## Development

```bash
# Run tests
uv run --python 3.12 --with pytest --with typer --with textual pytest -q

# Project layout
src/lockr/
  app/           application services (VaultService)
  cli/           Typer CLI commands
  domain/        core models (SecretRecord, VaultData)
  integrations/  .env parsing, shell injection, git backup
  security/      AES-256-GCM encryption and Scrypt KDF
  storage/       atomic file persistence
  tui/           Textual TUI app
tests/           CLI and integration tests
```

## License

No license has been added yet.
