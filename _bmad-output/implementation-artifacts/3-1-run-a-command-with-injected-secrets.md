# Story 3.1: Run a Command with Injected Secrets

**Status:** ready-for-dev
**Epic:** 3 – Runtime Injection
**Story ID:** 3.1
**Date:** 2026-07-08

---

## User Story

As a developer, I want to run a process with secrets injected so that I do not need to edit shell profiles or local files.

---

## Acceptance Criteria

- `lockr run -- <command>` injects selected environment variables into the child process
- injection does not persist secrets beyond the child process by default
- command exit code is preserved and forwarded to the caller
- errors distinguish command failure from vault failure

---

## Dev Context & Guardrails

### What already exists — do not reinvent

| Symbol | File | Purpose |
|---|---|---|
| `VaultService` | `src/lockr/app/vault_service.py:70` | all vault operations |
| `service()` | `src/lockr/cli/main.py:25` | factory — always use this, never construct VaultService directly |
| `VaultService.list_secrets()` | `vault_service.py:131` | returns `list[ListResult]` filtered by project/environment |
| `VaultService.get_secret()` | `vault_service.py:119` | returns full `SecretRecord` including `.value` |
| `VaultService._load_vault()` | `vault_service.py:223` | internal — use public methods |
| `render_error()` | `src/lockr/cli/main.py:41` | prints error to stderr — always use this for error output |
| `LockrError`, `VaultLockedError` | `vault_service.py:20-24` | catch both on vault operations |
| `LockrPaths` / `get_lockr_paths()` | `src/lockr/paths.py` | path resolution via `LOCKR_HOME` env var |

### New files to create

| File | Purpose |
|---|---|
| `src/lockr/integrations/shell.py` | `run_with_secrets()` helper — subprocess execution with env injection |
| `tests/test_epic3_runtime_injection.py` | CLI + service tests for story 3.1 |

### Files to modify

| File | Change |
|---|---|
| `src/lockr/cli/main.py` | Add `run` command (Typer) |
| `src/lockr/app/vault_service.py` | Add `run_with_secrets()` service method |

---

## Implementation Specification

### 1. Service method — `vault_service.py`

Add to `VaultService`:

```python
def get_secrets_for_injection(
    self,
    project: str = "default",
    environment: str = "default",
) -> dict[str, str]:
    """Return {KEY: value} for all secrets in the given scope."""
    vault = self._load_vault()
    return {
        s.key: s.value
        for s in vault.secrets
        if s.project == project and s.environment == environment
    }
```

### 2. Integration helper — `src/lockr/integrations/shell.py` (NEW)

```python
from __future__ import annotations

import os
import subprocess


def run_with_injected_env(command: list[str], extra_env: dict[str, str]) -> int:
    """Run command with extra_env merged into the current process environment.

    Returns the child process exit code. Secrets live only in the child's env;
    they are never written to disk.
    """
    env = {**os.environ, **extra_env}
    result = subprocess.run(command, env=env)
    return result.returncode
```

Key decisions:
- `{**os.environ, **extra_env}` merges secrets on top of the current env so the child process works normally (PATH etc. intact)
- `subprocess.run()` (not `execve`) so we remain in control and can cleanly forward the exit code
- No `shell=True` — command must be passed as a list to avoid shell injection

### 3. CLI command — `cli/main.py`

```python
@app.command("run")
def run_command(
    command: Annotated[list[str], typer.Argument(help="Command and arguments to run.")],
    project: Annotated[str, typer.Option("--project", help="Project name.")] = "default",
    environment: Annotated[str, typer.Option("--environment", help="Environment name.")] = "default",
) -> None:
    if not command:
        typer.echo("No command provided.", err=True)
        raise typer.Exit(code=2)
    try:
        secrets = service().get_secrets_for_injection(project=project, environment=environment)
    except (LockrError, VaultLockedError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc

    from lockr.integrations.shell import run_with_injected_env
    exit_code = run_with_injected_env(command, secrets)
    raise typer.Exit(code=exit_code)
```

Import note: add `run_with_injected_env` import inside the function (lazy) or at the top of `main.py` alongside other integration imports. Either is fine — match whichever style is already present.

---

## Error Behaviour

| Situation | Exit code | Output |
|---|---|---|
| Vault locked | 1 | stderr via `render_error()` |
| Vault not initialised | 1 | stderr via `render_error()` |
| No command given | 2 | `"No command provided."` to stderr |
| Command itself fails | child's exit code (e.g. 127) | passthrough — no extra output |
| Command succeeds | 0 | passthrough |

The distinguishing rule: exit codes 1 and 2 are Lockr's own failures; any other code is the child's.

---

## Testing Requirements

Test file: `tests/test_epic3_runtime_injection.py`

Follow the exact pattern from `tests/test_epic2_env_workflow.py`:
- Use `CliRunner` from `typer.testing`
- Use the `run_lockr(args, home, passwords)` helper (copy it into the new test file or import from a shared conftest)
- Use `tmp_path` fixture for isolation
- Patch `getpass.getpass` via the same `fake_getpass` pattern for `init`

### Test cases

```python
def test_run_injects_secrets_into_child(tmp_path):
    # init vault, set a secret, then run `env` and check it appears
    ...
    result = run_lockr(
        ["run", "--project", "myapp", "--environment", "dev", "--", "env"],
        tmp_path,
    )
    assert result.exit_code == 0
    assert "MY_SECRET=hunter2" in result.stdout  # env prints KEY=VALUE lines


def test_run_preserves_child_exit_code(tmp_path):
    # `python3 -c "raise SystemExit(42)"` should give exit_code == 42
    ...
    result = run_lockr(["run", "--", "python3", "-c", "raise SystemExit(42)"], tmp_path)
    assert result.exit_code == 42


def test_run_fails_with_vault_locked(tmp_path):
    # init, lock, then run — should exit 1 with vault locked message
    ...
    result = run_lockr(["run", "--", "env"], tmp_path)
    assert result.exit_code == 1
    assert "locked" in result.output.lower()


def test_run_no_command_exits_2(tmp_path):
    run_lockr(["init"], tmp_path, passwords=["pw", "pw"])
    result = run_lockr(["run"], tmp_path)
    assert result.exit_code == 2


def test_run_does_not_persist_secrets(tmp_path):
    # After run completes, no plaintext file in LOCKR_HOME should contain the secret value
    ...
    for f in tmp_path.iterdir():
        assert "hunter2" not in f.read_text(encoding="utf-8", errors="ignore")
```

---

## Architecture Compliance Checklist

- [ ] New CLI command registered with `@app.command("run")` in `cli/main.py`
- [ ] Business logic lives in `VaultService`, not in the CLI command
- [ ] Shell subprocess logic lives in `src/lockr/integrations/shell.py`, not in the service
- [ ] No `shell=True` in `subprocess.run()`
- [ ] Secrets never written to disk during injection
- [ ] `render_error()` used for all error output (never `print()` or bare `typer.echo(..., err=False)`)
- [ ] Exit codes match the table above
- [ ] Tests use `CliRunner` + `LOCKR_HOME` env isolation, not a real `~/.lockr`
- [ ] No new third-party dependencies — `subprocess` and `os` are stdlib

---

## Dev Notes

- `CliRunner` from Typer captures stdout; the child process launched by `subprocess.run()` inherits the real stdout by default and its output will **not** be captured by the runner in tests. Use `python3 -c "import os; print(os.environ.get('KEY', 'MISSING'))"` or redirect via `subprocess.run(..., capture_output=False)` to keep test output visible. For asserting env var presence, rely on the child's printed output.
- The `--` separator is standard Typer/Click behaviour for argument lists; Typer will collect everything after `--` into the `command: list[str]` argument automatically.
- `LOCKR_HOME` is resolved in `get_lockr_paths()` — tests must set it via `env={"LOCKR_HOME": str(tmp_path)}` in `runner.invoke()`, consistent with existing tests.
- Do not add `--keys` filtering in this story. Story 3.1 injects all secrets for the given scope. Selective injection is not in the acceptance criteria.
