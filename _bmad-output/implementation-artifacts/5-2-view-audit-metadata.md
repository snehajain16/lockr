---
baseline_commit: 24bd8cd
---

# Story 5.2: View Audit Metadata

Status: done

## Story

As a developer,
I want audit-friendly metadata so that I can track changes and rotation hygiene.

## Acceptance Criteria

1. `lockr audit` lists all secrets with audit metadata (project, environment, key, description, created_at, updated_at, last_rotated_at) — never exposes `value`.
2. `--project` and `--environment` filters work (same as `list`).
3. `--json` flag outputs a JSON array of audit records.
4. If the vault is locked or not initialized, the command exits 1 with a clear error message.
5. The audit view never exposes the decrypted secret value in any code path.

## Tasks / Subtasks

- [x] Task 1: Add `AuditResult` dataclass and `list_audit()` method to `VaultService` (AC: 1, 5)
  - [x] Add `AuditResult` dataclass to `vault_service.py` with fields: key, project, environment, description, created_at, updated_at, last_rotated_at (NO value)
  - [x] Add `list_audit(project, environment)` method that returns `list[AuditResult]`

- [x] Task 2: Add `lockr audit` CLI command (AC: 1–4)
  - [x] Add `@app.command("audit")` in `cli/main.py`
  - [x] Accept `--project`, `--environment`, `--json` options
  - [x] Default output: one line per secret showing key, project/env, created_at, updated_at, last_rotated_at
  - [x] JSON output: array of audit record dicts

- [x] Task 3: Write tests in `tests/test_epic5_tui.py` (AC: 1–5)
  - [x] `test_audit_command_exists`
  - [x] `test_audit_lists_metadata_without_value`
  - [x] `test_audit_json_output`
  - [x] `test_audit_filter_by_project`
  - [x] `test_audit_fails_when_vault_locked`
  - [x] `test_audit_never_exposes_value`

- [x] Task 4: Update sprint status; run full test suite (26 passed, 0 failed)

## Dev Notes

### Architecture Constraints

- **No `value` in `AuditResult`** — the dataclass must not have a `value` field at all, not just hide it.
- **Service layer** — all logic in `VaultService.list_audit()`. CLI is a thin wrapper.
- `SecretRecord` already has all needed fields: `key`, `project`, `environment`, `description`, `created_at`, `updated_at`, `last_rotated_at`.

### What Already Exists — Do NOT Reinvent

| Symbol | File | Purpose |
|---|---|---|
| `SecretRecord` | `src/lockr/domain/models.py:14` | Full secret — has all audit fields |
| `VaultService.list_secrets()` | `vault_service.py:131` | Returns `list[ListResult]` — lacks created_at/description/last_rotated_at |
| `ListResult` | `vault_service.py:43` | key, project, environment, updated_at only |
| `service()` | `cli/main.py:28` | Factory |
| `LockrError`, `VaultLockedError` | `vault_service.py:20–24` | Catch both |
| `render_error()` | `cli/main.py:44` | Error output |

### `AuditResult` and `list_audit()` Pattern

```python
@dataclass
class AuditResult:
    key: str
    project: str
    environment: str
    description: str
    created_at: str
    updated_at: str
    last_rotated_at: str | None

def list_audit(
    self,
    project: str | None = None,
    environment: str | None = None,
) -> list[AuditResult]:
    vault = self._require_session()
    results = []
    for s in vault.secrets:
        if project and s.project != project:
            continue
        if environment and s.environment != environment:
            continue
        results.append(AuditResult(
            key=s.key,
            project=s.project,
            environment=s.environment,
            description=s.description,
            created_at=s.created_at,
            updated_at=s.updated_at,
            last_rotated_at=s.last_rotated_at,
        ))
    return results
```

### CLI Command Pattern

```python
@app.command("audit")
def audit_command(
    project: Annotated[str | None, typer.Option("--project")] = None,
    environment: Annotated[str | None, typer.Option("--environment")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List secrets with audit metadata (no values exposed)."""
    try:
        items = service().list_audit(project=project, environment=environment)
    except (VaultLockedError, LockrError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps([item.__dict__ for item in items], indent=2))
        return
    if not items:
        typer.echo("No secrets found.")
        return
    for item in items:
        rotated = item.last_rotated_at or "never"
        typer.echo(
            f"{item.project}/{item.environment} {item.key} "
            f"created={item.created_at} updated={item.updated_at} rotated={rotated}"
        )
```

### Testing Pattern

```python
def test_audit_lists_metadata_without_value(tmp_path):
    _init_and_unlock(tmp_path)
    run_lockr(["set", "MY_KEY", "--value", "secret123"], tmp_path)
    result = run_lockr(["audit"], tmp_path)
    assert result.exit_code == 0
    assert "MY_KEY" in result.output
    assert "secret123" not in result.output

def test_audit_never_exposes_value(tmp_path):
    from lockr.app.vault_service import AuditResult, VaultService
    # AuditResult must not have a value field
    import dataclasses
    field_names = {f.name for f in dataclasses.fields(AuditResult)}
    assert "value" not in field_names
```

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Completion Notes List

- Added `AuditResult` dataclass (no `value` field) and `list_audit()` method to `vault_service.py`
- Added `lockr audit` CLI command with `--project`, `--environment`, `--json` flags
- 6 new tests; 26 total passing, no regressions

### File List

- src/lockr/app/vault_service.py (modified)
- src/lockr/cli/main.py (modified)
- tests/test_epic5_tui.py (modified)
- _bmad-output/implementation-artifacts/5-2-view-audit-metadata.md (new)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
