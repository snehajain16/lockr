---
baseline_commit: 6eb372b938e84af65f323d3dfb5f10a639353427
---

# Story 4.1: Create Encrypted Git Backup

Status: review

## Story

As a developer,
I want to create an encrypted backup of my vault in a git repository,
so that I can restore my secrets on another machine without exposing plaintext.

## Acceptance Criteria

1. `lockr backup create --repo <path>` validates that `git` and `gpg` are available on PATH before proceeding; exits 1 with a clear error if either is missing.
2. The backup artifact written to the repo contains no plaintext secrets (the already-AES-256-GCM-encrypted vault blob is copied as-is; it is the artifact).
3. The artifact is written to `<repo>/lockr-vault.lockr` (or configurable sub-path) inside the target git repository path.
4. A `--commit` flag enables auto-commit mode; without it the file is written but no `git` staging or committing occurs.
5. Vault must be initialized before backup; if not, exit 1 with a clear error.
6. On success, print a summary: artifact path and whether a commit was made.

## Tasks / Subtasks

- [x] Task 1: Add `backup_config_file` to `LockrPaths` (AC: 3, 6)
  - [x] Add `backup_config_file: Path` field to `LockrPaths` dataclass (= `home / "backup.json"`)
  - [x] Update `get_lockr_paths()` to populate the new field

- [x] Task 2: Create `src/lockr/integrations/git_backup.py` (AC: 1, 4)
  - [x] `check_git_available() -> None` — runs `git --version`, raises `BackupError` if not found
  - [x] `check_gpg_available() -> None` — runs `gpg --version`, raises `BackupError` if not found
  - [x] `git_add_and_commit(repo: Path, filepath: Path, message: str) -> None` — runs `git -C <repo> add <filepath>` then `git -C <repo> commit -m <message>`; raises `BackupError` on non-zero exit

- [x] Task 3: Add `BackupError` and `create_backup()` to `VaultService` (AC: 1, 2, 3, 5)
  - [x] Add `BackupError(LockrError)` to `vault_service.py`
  - [x] Add `BackupResult` dataclass: `artifact_path: Path`, `committed: bool`
  - [x] Add `VaultService.create_backup(repo: Path, commit: bool) -> BackupResult`:
    - Validate vault is initialized (`_read_encrypted_vault()` raises if not)
    - Call `check_git_available()` and `check_gpg_available()`
    - Copy `self.paths.vault_file` → `repo / "lockr-vault.lockr"` (use `shutil.copy2`)
    - If `commit=True`: call `git_add_and_commit()`
    - Persist `{"repo": str(repo), "last_backup_at": utc_now()}` to `self.paths.backup_config_file`
    - Return `BackupResult`

- [x] Task 4: Add `backup create` CLI sub-command (AC: 1–6)
  - [x] Create `backup_app = typer.Typer(help="Backup and recovery commands.")` in `cli/main.py`
  - [x] Register it: `app.add_typer(backup_app, name="backup")`
  - [x] Add `@backup_app.command("create")` with `--repo PATH` (required) and `--commit` (bool flag, default False)
  - [x] Call `service().create_backup(repo=Path(repo), commit=commit)`
  - [x] Catch `(LockrError, BackupError)` → `render_error()` + `Exit(1)`
  - [x] Print success summary on completion

- [x] Task 5: Write tests in `tests/test_epic4_backup_recovery.py` (AC: 1–6)
  - [x] `test_backup_create_copies_vault_file` — vault init + backup, verify artifact exists at `repo/lockr-vault.lockr`
  - [x] `test_backup_artifact_contains_no_plaintext` — read artifact bytes; assert secret value not in content
  - [x] `test_backup_create_with_commit_flag` — mock `git_add_and_commit`; verify it is called when `--commit` passed
  - [x] `test_backup_create_without_commit_flag` — mock `git_add_and_commit`; verify NOT called without `--commit`
  - [x] `test_backup_fails_if_vault_not_initialized` — no init, expect exit 1
  - [x] `test_backup_fails_if_git_missing` — mock `check_git_available` to raise; expect exit 1 with "git" in output
  - [x] `test_backup_fails_if_gpg_missing` — mock `check_gpg_available` to raise; expect exit 1 with "gpg" in output
  - [x] `test_backup_persists_config` — verify `backup.json` written with `repo` and `last_backup_at`

- [x] Task 6: Run full test suite and confirm no regressions
  - [x] `uv run --python 3.12 --with pytest --with typer pytest -q` — 23 passed

## Dev Notes

### Architecture Constraints (MUST follow)

- **Integration layer** (`src/lockr/integrations/`) is the correct home for git/gpg subprocess wrappers — same pattern as `shell.py` (subprocess) and `env_files.py` (parsing). Do NOT put subprocess calls in `vault_service.py` directly.
- **No `shell=True`** in any subprocess call — pass command as a list, same as `shell.py`.
- **Service layer** (`vault_service.py`) orchestrates: it calls integration helpers and manages file I/O. CLI commands call the service, not integrations directly.
- **`render_error()` only** for error output — never bare `print()` or `typer.echo(..., err=False)`.
- **`atomic_write_json()`** from `lockr.storage.files` for writing `backup.json` (same pattern as session file).
- **`utc_now()`** from `lockr.domain.models` for timestamps.

### What Already Exists — Do NOT Reinvent

| Symbol | File | Purpose |
|---|---|---|
| `VaultService` | `src/lockr/app/vault_service.py:70` | all vault operations |
| `service()` | `src/lockr/cli/main.py:25` | factory — always use this |
| `LockrError` | `vault_service.py:20` | base error — `BackupError` should subclass this |
| `render_error()` | `cli/main.py:41` | all error output |
| `atomic_write_json()` | `src/lockr/storage/files.py:22` | atomic JSON writes |
| `atomic_write_text()` | `src/lockr/storage/files.py:14` | atomic text writes |
| `utc_now()` | `src/lockr/domain/models.py` | UTC timestamp string |
| `LockrPaths` | `src/lockr/paths.py:9` | frozen dataclass with `home`, `vault_file`, `session_file` |
| `get_lockr_paths()` | `src/lockr/paths.py:15` | path factory via `LOCKR_HOME` env var |
| `run_with_injected_env()` | `src/lockr/integrations/shell.py` | subprocess pattern to follow |
| `EncryptedVault` | `src/lockr/security/crypto.py:20` | vault blob — already AES-256-GCM encrypted |

### New Files to Create

| File | Purpose |
|---|---|
| `src/lockr/integrations/git_backup.py` | `check_git_available()`, `check_gpg_available()`, `git_add_and_commit()` |
| `tests/test_epic4_backup_recovery.py` | All story 4.1 tests |

### Files to Modify

| File | Change |
|---|---|
| `src/lockr/paths.py` | Add `backup_config_file` field to `LockrPaths` |
| `src/lockr/app/vault_service.py` | Add `BackupError`, `BackupResult`, `VaultService.create_backup()` |
| `src/lockr/cli/main.py` | Add `backup_app` sub-typer and `backup create` command |

### The Backup Artifact: No Double-Encryption Needed

The vault file (`vault.lockr`) is already AES-256-GCM encrypted. Copying it directly means:
- No plaintext is exposed at any point.
- GPG availability is validated (future stories may use GPG for recipient-based encryption); for 4.1 we validate presence only.
- The copied file is the artifact — self-contained, opaque, restorable.

### `LockrPaths` Extension Pattern

```python
@dataclass(frozen=True)
class LockrPaths:
    home: Path
    vault_file: Path
    session_file: Path
    backup_config_file: Path   # NEW

def get_lockr_paths() -> LockrPaths:
    configured = os.environ.get("LOCKR_HOME")
    home = Path(configured).expanduser() if configured else Path.home() / ".lockr"
    return LockrPaths(
        home=home,
        vault_file=home / "vault.lockr",
        session_file=home / "session.json",
        backup_config_file=home / "backup.json",   # NEW
    )
```

### `git_backup.py` Pattern (follow `shell.py`)

```python
from __future__ import annotations
import subprocess
from pathlib import Path

class BackupError(Exception):
    pass

def check_git_available() -> None:
    result = subprocess.run(["git", "--version"], capture_output=True)
    if result.returncode != 0:
        raise BackupError("git is not available. Install git and ensure it is on PATH.")

def check_gpg_available() -> None:
    result = subprocess.run(["gpg", "--version"], capture_output=True)
    if result.returncode != 0:
        raise BackupError("gpg is not available. Install gpg and ensure it is on PATH.")

def git_add_and_commit(repo: Path, filepath: Path, message: str) -> None:
    for cmd in (
        ["git", "-C", str(repo), "add", str(filepath)],
        ["git", "-C", str(repo), "commit", "-m", message],
    ):
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise BackupError(f"git command failed: {result.stderr.decode().strip()}")
```

**Note:** `BackupError` in `git_backup.py` is separate from `BackupError(LockrError)` in `vault_service.py`. The service-layer one inherits `LockrError` for CLI catch-all handling. The integration-layer one is a plain `Exception`. The service catches the integration's `BackupError` and re-raises as the service's `BackupError(LockrError)`.

### `VaultService.create_backup()` Pattern

```python
import shutil
from lockr.integrations.git_backup import (
    BackupError as GitBackupError,
    check_git_available,
    check_gpg_available,
    git_add_and_commit,
)

@dataclass
class BackupResult:
    artifact_path: Path
    committed: bool

def create_backup(self, repo: Path, commit: bool = False) -> BackupResult:
    self._read_encrypted_vault()   # raises LockrError if vault not initialized
    try:
        check_git_available()
        check_gpg_available()
    except GitBackupError as exc:
        raise BackupError(str(exc)) from exc
    artifact = repo / "lockr-vault.lockr"
    shutil.copy2(self.paths.vault_file, artifact)
    if commit:
        try:
            git_add_and_commit(repo, artifact, "lockr: update vault backup")
        except GitBackupError as exc:
            raise BackupError(str(exc)) from exc
    atomic_write_json(self.paths.backup_config_file, {"repo": str(repo), "last_backup_at": utc_now()})
    return BackupResult(artifact_path=artifact, committed=commit)
```

### CLI Sub-Typer Pattern

```python
backup_app = typer.Typer(help="Backup and recovery commands.")
app.add_typer(backup_app, name="backup")

@backup_app.command("create")
def backup_create_command(
    repo: Annotated[Path, typer.Option("--repo", help="Path to git repository for backup.")],
    commit: Annotated[bool, typer.Option("--commit", help="Stage and commit after writing artifact.")] = False,
) -> None:
    try:
        result = service().create_backup(repo=repo, commit=commit)
    except (LockrError, BackupError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Backup written to {result.artifact_path}.")
    if result.committed:
        typer.echo("Changes committed to git repository.")
```

### Testing Pattern

```python
from unittest.mock import patch

def test_backup_create_copies_vault_file(tmp_path):
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    _init_and_unlock(tmp_path)
    with patch("lockr.integrations.git_backup.check_git_available"):
        with patch("lockr.integrations.git_backup.check_gpg_available"):
            result = run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 0
    assert (repo / "lockr-vault.lockr").exists()
```

- Mock `check_git_available` and `check_gpg_available` at the integration module level in tests (avoids needing git/gpg on CI).
- Mock `git_add_and_commit` when testing commit flag behaviour.
- For `test_backup_artifact_contains_no_plaintext`: actually set a secret, run backup, read artifact bytes, assert secret value not in `bytes.decode(errors="ignore")`.

### Test Helper

Reuse the same `run_lockr()` + `fake_getpass` pattern from `tests/test_epic3_runtime_injection.py`. No need to import from there — copy the helper into the new test file.

```python
def _init_and_unlock(tmp_path: Path) -> None:
    run_lockr(["init"], tmp_path, passwords=["pw", "pw"])
```

### Error Behaviour Table

| Situation | Exit code | Output |
|---|---|---|
| Vault not initialized | 1 | stderr via `render_error()` |
| git not on PATH | 1 | stderr: "git is not available..." |
| gpg not on PATH | 1 | stderr: "gpg is not available..." |
| git commit fails | 1 | stderr: "git command failed: ..." |
| Success (no commit) | 0 | artifact path to stdout |
| Success (with commit) | 0 | artifact path + commit confirmation |

### Import Note for `vault_service.py`

Add `import shutil` at the top. Add the import of `git_backup` integration inside `create_backup()` (lazy import — same pattern as `shell.py` in the `run` command) or at the module top — either is fine.

Also import `BackupError` from `git_backup` **with an alias** to avoid name collision with the service-layer `BackupError(LockrError)`:

```python
from lockr.integrations.git_backup import BackupError as GitBackupError
```

### Project Structure Notes

- `src/lockr/integrations/` already has `__init__.py`, `env_files.py`, `shell.py` — add `git_backup.py` here.
- All tests live flat in `tests/` (not in `tests/unit/` or `tests/integration/` subdirectories yet).
- `pyproject.toml` does not need changes — `shutil` is stdlib.

### References

- Architecture backup flow: [Source: docs/planning/architecture.md#7. Primary Flows — Backup]
- Architecture integration layer: [Source: docs/planning/architecture.md#3. High-Level Components — Integration Layer]
- Story ACs: [Source: docs/planning/stories.md#Story 4.1]
- Shell integration pattern: [Source: src/lockr/integrations/shell.py]
- LockrPaths: [Source: src/lockr/paths.py]
- VaultService: [Source: src/lockr/app/vault_service.py:70]
- atomic_write_json: [Source: src/lockr/storage/files.py:22]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### Completion Notes List

- Implemented `lockr backup create --repo <path> [--commit]` end-to-end
- `src/lockr/integrations/git_backup.py`: git/gpg availability checks and git commit helper (no shell=True)
- `BackupError(LockrError)` + `BackupResult` added to vault_service; `create_backup()` uses shutil.copy2 — no plaintext ever written
- `backup_app` Typer sub-app registered on main `app`; all errors route through `render_error()`
- backup.json persisted to LOCKR_HOME with repo path and timestamp for story 4.3 (status)
- 8 new tests; 23 total — all pass, no regressions

### File List

- src/lockr/paths.py (modified)
- src/lockr/integrations/git_backup.py (new)
- src/lockr/app/vault_service.py (modified)
- src/lockr/cli/main.py (modified)
- tests/test_epic4_backup_recovery.py (new)
- _bmad-output/implementation-artifacts/4-1-create-encrypted-git-backup.md (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
