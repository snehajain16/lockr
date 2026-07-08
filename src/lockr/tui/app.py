from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Static

from lockr.app.vault_service import LockrError, VaultLockedError, VaultService
from lockr.paths import get_lockr_paths


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
        )
        yield Static(content, id="detail-content")


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
                item.project,
                item.environment,
                item.key,
                item.updated_at,
                key=f"{item.project}:{item.environment}:{item.key}",
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_key = event.row_key.value
        project, environment, key = row_key.split(":", 2)
        self.push_screen(DetailScreen(key=key, project=project, environment=environment))
