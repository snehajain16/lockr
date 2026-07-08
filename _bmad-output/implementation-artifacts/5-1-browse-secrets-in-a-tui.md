---
baseline_commit: 6b454fd4e34487692f557175f12cf6d2654940aa
---

# Story 5.1: Browse Secrets in a TUI

Status: review

## Story

As a developer,
I want an interactive terminal UI to browse my secrets,
so that I can manage them without memorising every CLI command.

## Acceptance Criteria

1. `lockr tui` launches a Textual app that lists all secrets across all projects/environments without showing plaintext values.
2. The user can navigate rows with arrow keys and press Enter to view a detail panel showing full metadata (key, project, environment, description, created_at, updated_at) — still no plaintext value.
3. The TUI reuses `VaultService` via the same `service()` factory used by CLI commands. No vault logic is re-implemented inside the TUI.
4. If the vault is locked or not initialised, the TUI exits cleanly with a clear error message (no traceback).
5. Press `q` or `Escape` to quit the app.

## Tasks / Subtasks

- [x] Task 1: Add `textual` dependency to `pyproject.toml` (AC: 1)
  - [x] Add `textual>=0.80.0` to `[project] dependencies`
  - [x] Run `uv sync` or verify install: textual 0.82.8 confirmed

- [x] Task 2: Create `src/lockr/tui/` package (AC: 1–3)
  - [x] Create `src/lockr/tui/__init__.py` (empty)
  - [x] Create `src/lockr/tui/app.py` with `LockrTuiApp(App)` class

- [x] Task 3: Implement `LockrTuiApp` with secrets table (AC: 1, 3, 5)
  - [x] `compose()`: `Header()`, `DataTable(id="secrets-table")`, `Footer()`
  - [x] `on_mount()`: call `VaultService(get_lockr_paths()).list_secrets()`, populate `DataTable` with columns project/environment/key/updated_at
  - [x] `BINDINGS`: `q` → quit, `escape` → quit
  - [x] Handle `VaultLockedError` / `LockrError` in `on_mount()`: call `self.exit()` after printing error

- [x] Task 4: Add detail panel for metadata (AC: 2)
  - [x] `on_data_table_row_selected()`: reads row key, calls `get_secret()`, shows `DetailScreen`
  - [x] `DetailScreen`: `ModalScreen` with `Static` widget — metadata only, no `.value`

- [x] Task 5: Add `lockr tui` CLI command (AC: 1, 4)
  - [x] In `src/lockr/cli/main.py`, added `@app.command("tui")`
  - [x] Command imports `LockrTuiApp` lazily and calls `.run()`
  - [x] Catches `(LockrError, VaultLockedError)` → `render_error()` + `Exit(1)`

- [x] Task 6: Write tests in `tests/test_epic5_tui.py` (AC: 1–5)
  - [x] `test_tui_command_exists` — passes
  - [x] `test_tui_fails_when_vault_locked` — passes
  - [x] `test_tui_fails_when_vault_not_initialized` — passes
  - [x] `test_tui_app_loads_secrets` — passes
  - [x] `test_detail_screen_hides_value` — passes

- [x] Task 7: Run full test suite confirming no regressions
  - [x] 20 passed, 0 failed

## Dev Notes

### Architecture Constraints (MUST follow)

- **TUI layer** belongs in `src/lockr/tui/` — the architecture directory structure explicitly reserves this location. Do NOT put TUI code in `cli/`, `app/`, or anywhere else.
- **Shared service layer** — TUI uses `service()` from `lockr.cli.main` (or re-creates `VaultService(get_lockr_paths())` directly). No vault logic in TUI. Architecture requirement: "TUI reuses the same application services as the CLI."
- **No plaintext values** — `DataTable` and `DetailScreen` must never display `secret.value`. Only show key, project, environment, description, timestamps.
- **Textual** is the mandated TUI library per architecture (`docs/planning/architecture.md#2. Proposed Stack`). Do NOT use curses, urwid, rich, or any other terminal UI library.

### New Dependency: Textual

Add to `pyproject.toml`:
```toml
dependencies = [
  "cryptography>=45.0.0",
  "typer>=0.16.0",
  "textual>=0.80.0",
]
```

Textual key APIs for this story:
- `from textual.app import App, ComposeResult`
- `from textual.widgets import DataTable, Header, Footer, Static`
- `from textual.screen import Screen, ModalScreen`
- `from textual.binding import Binding`
- `app.compose()` → yields widgets
- `app.on_mount()` → called after compose, use for data loading
- `DataTable.add_columns(*labels)` then `DataTable.add_row(*values, key=row_key)`
- `DataTable.on_row_selected(event)` or `on_data_table_row_selected` — `event.row_key.value` is the key
- `self.push_screen(DetailScreen(...))` to show detail
- `self.exit()` to quit programmatically
- `App.run()` — blocking call that runs the TUI event loop

### What Already Exists — Do NOT Reinvent

| Symbol | File | Purpose |
|---|---|---|
| `VaultService.list_secrets()` | `vault_service.py:131` | returns `list[ListResult]` with `.key`, `.project`, `.environment`, `.updated_at` |
| `VaultService.get_secret()` | `vault_service.py:119` | returns full `SecretRecord` (key, project, environment, description, created_at, updated_at) |
| `ListResult` | `vault_service.py:43` | dataclass: key, project, environment, updated_at |
| `SecretRecord` | `domain/models.py:14` | full secret — never expose `.value` in TUI |
| `service()` | `cli/main.py:25` | factory — use this or replicate its one-liner `VaultService(get_lockr_paths())` |
| `LockrError`, `VaultLockedError` | `vault_service.py:20–24` | catch both for vault failures |
| `render_error()` | `cli/main.py:41` | error output in CLI command only |

### New Files to Create

| File | Purpose |
|---|---|
| `src/lockr/tui/__init__.py` | Package marker |
| `src/lockr/tui/app.py` | `LockrTuiApp` + `DetailScreen` |
| `tests/test_epic5_tui.py` | Story 5.1 tests |

### Files to Modify

| File | Change |
|---|---|
| `pyproject.toml` | Add `textual>=0.80.0` dependency |
| `src/lockr/cli/main.py` | Add `@app.command("tui")` |

### `LockrTuiApp` Implementation Pattern

```python
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header
from textual.binding import Binding

from lockr.app.vault_service import LockrError, VaultLockedError, VaultService
from lockr.paths import get_lockr_paths


class LockrTuiApp(App):
    TITLE = "Lockr — Secrets Vault"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="secrets-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Project", "Environment", "Key", "Updated")
        try:
            svc = VaultService(get_lockr_paths())
            secrets = svc.list_secrets()
        except (LockrError, VaultLockedError) as exc:
            self.exit(message=str(exc))
            return
        for item in secrets:
            table.add_row(
                item.project, item.environment, item.key, item.updated_at,
                key=f"{item.project}:{item.environment}:{item.key}",
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        parts = event.row_key.value.split(":", 2)
        project, environment, key = parts[0], parts[1], parts[2]
        self.push_screen(DetailScreen(key=key, project=project, environment=environment))
```

### `DetailScreen` Implementation Pattern

```python
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.binding import Binding


class DetailScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("enter", "dismiss", "Close"),
    ]

    def __init__(self, key: str, project: str, environment: str) -> None:
        super().__init__()
        self._key = key
        self._project = project
        self._environment = environment

    def compose(self) -> ComposeResult:
        svc = VaultService(get_lockr_paths())
        try:
            secret = svc.get_secret(self._key, project=self._project, environment=self._environment)
        except (LockrError, VaultLockedError):
            yield Static("Error loading secret metadata.")
            return
        content = (
            f"Key:         {secret.key}\n"
            f"Project:     {secret.project}\n"
            f"Environment: {secret.environment}\n"
            f"Description: {secret.description or '(none)'}\n"
            f"Created:     {secret.created_at}\n"
            f"Updated:     {secret.updated_at}\n"
            f"Rotated:     {secret.last_rotated_at or '(never)'}\n"
            # NOTE: value is intentionally omitted
        )
        yield Static(content, id="detail-content")
```

### CLI Command Pattern

```python
@app.command("tui")
def tui_command() -> None:
    """Launch the interactive TUI browser."""
    try:
        from lockr.tui.app import LockrTuiApp
        LockrTuiApp().run()
    except (LockrError, VaultLockedError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc
```

### Testing Approach

Textual provides `App.run_async` + `Pilot` for headless testing. However, for CI simplicity, use a mix:

1. **CLI-level tests** (easy, use existing `CliRunner` pattern): test that `lockr tui --help` works, that locked/uninit vaults exit 1 gracefully by mocking `LockrTuiApp.run` to raise the relevant error.
2. **Textual Pilot tests** (for AC 1–2 verification): use `async def test_...` with `pytest-asyncio` OR use Textual's built-in sync test helper `App.run(headless=True)` with short timeout.

For the Pilot approach, the simplest pattern that avoids flakiness:
```python
from unittest.mock import patch, MagicMock

def test_tui_fails_when_vault_locked(tmp_path):
    # Mock LockrTuiApp.run to raise VaultLockedError so CLI handles it
    from lockr.app.vault_service import VaultLockedError
    with patch("lockr.tui.app.LockrTuiApp.run", side_effect=VaultLockedError("Vault is locked...")):
        result = run_lockr(["tui"], tmp_path)
    assert result.exit_code == 1
    assert "locked" in result.output.lower()
```

For `test_tui_app_loads_secrets`: mock `VaultService.list_secrets` and use `App.run_async` with Pilot:
```python
import pytest

@pytest.mark.asyncio  # if using pytest-asyncio
async def test_tui_app_loads_secrets(tmp_path):
    from lockr.tui.app import LockrTuiApp
    from lockr.app.vault_service import ListResult
    mock_secrets = [ListResult(key="FOO", project="myapp", environment="dev", updated_at="2026-01-01T00:00:00+00:00")]
    with patch("lockr.tui.app.VaultService.list_secrets", return_value=mock_secrets):
        async with LockrTuiApp().run_async(headless=True) as pilot:
            table = pilot.app.query_one(DataTable)
            assert table.row_count == 1
```

If `pytest-asyncio` is not available, use simpler CLI-level mock tests only — avoid blocking the story on async test setup.

**Safest approach**: mock `LockrTuiApp.run` at the CLI level for all error-path tests, and for the "loads secrets" test, instantiate the app directly and call `on_mount` with mocked service. This avoids any async test infrastructure.

### `LOCKR_HOME` in TUI

The TUI calls `VaultService(get_lockr_paths())` directly. `get_lockr_paths()` reads `LOCKR_HOME` from env. In tests, set `LOCKR_HOME` via `os.environ` or by constructing `VaultService(LockrPaths(...))` with mock paths. Do NOT assume `~/.lockr` in tests.

### Project Structure Notes

- `src/lockr/tui/` must exist as a Python package (needs `__init__.py`)
- setuptools finds packages automatically via `find: where = ["src"]` — no extra config needed
- No new CLI entry point — `lockr tui` is a subcommand of the existing `app`

### References

- Architecture TUI layer: [Source: docs/planning/architecture.md#3. High-Level Components — TUI Layer]
- Architecture stack: [Source: docs/planning/architecture.md#2. Proposed Stack]
- Story ACs: [Source: docs/planning/stories.md#Story 5.1]
- VaultService.list_secrets: [Source: src/lockr/app/vault_service.py:131]
- ListResult: [Source: src/lockr/app/vault_service.py:43]
- SecretRecord (never expose .value): [Source: src/lockr/domain/models.py:14]
- CLI command pattern: [Source: src/lockr/cli/main.py]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Added `textual>=0.80.0` to pyproject.toml (installed as 0.82.8)
- Created `src/lockr/tui/` package with `LockrTuiApp` (DataTable, Header, Footer, q/escape bindings)
- `DetailScreen` (ModalScreen) shows full metadata — `.value` intentionally excluded
- `lockr tui` CLI command added with lazy import and full error handling
- 5 new tests; 20 total passing, no regressions

### File List

- pyproject.toml (modified)
- src/lockr/tui/__init__.py (new)
- src/lockr/tui/app.py (new)
- src/lockr/cli/main.py (modified)
- tests/test_epic5_tui.py (new)
- _bmad-output/implementation-artifacts/5-1-browse-secrets-in-a-tui.md (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
