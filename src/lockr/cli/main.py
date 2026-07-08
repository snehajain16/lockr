from __future__ import annotations

import getpass
import json
from pathlib import Path
from typing import Annotated

import typer

from lockr.app.vault_service import (
    AuditResult,
    BackupError,
    ExportResult,
    ImportApplyResult,
    LockrError,
    SecretNotFoundError,
    VaultAlreadyExistsError,
    VaultLockedError,
    VaultService,
    RestoreResult,
    BackupStatus,
)
from lockr.paths import get_lockr_paths
from lockr.storage.files import atomic_write_text

app = typer.Typer(help="Lockr secrets vault")
backup_app = typer.Typer(help="Backup and recovery commands.")
app.add_typer(backup_app, name="backup")


def service() -> VaultService:
    return VaultService(get_lockr_paths())


def prompt_password(confirm: bool = False) -> str:
    password = getpass.getpass("Master password: ")
    if not password:
        raise typer.Exit(code=2)
    if confirm:
        repeat = getpass.getpass("Confirm master password: ")
        if password != repeat:
            typer.echo("Passwords did not match.", err=True)
            raise typer.Exit(code=2)
    return password


def render_error(exc: Exception) -> None:
    typer.echo(str(exc), err=True)


def render_apply_summary(result: ImportApplyResult) -> str:
    return (
        f"imported={result.imported} updated={result.updated} "
        f"skipped={result.skipped} malformed={result.malformed}"
    )


@app.command("init")
def init_command(
    force: Annotated[bool, typer.Option("--force", help="Overwrite an existing vault.")] = False,
) -> None:
    try:
        password = prompt_password(confirm=True)
        service().init_vault(password=password, force=force)
        typer.echo("Vault initialized and unlocked.")
    except VaultAlreadyExistsError as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc


@app.command("unlock")
def unlock_command() -> None:
    try:
        password = prompt_password()
        service().unlock(password=password)
        typer.echo("Vault unlocked.")
    except LockrError as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc


@app.command("lock")
def lock_command() -> None:
    service().lock()
    typer.echo("Vault locked.")


@app.command("set")
def set_command(
    key: str,
    value: Annotated[str | None, typer.Option("--value", help="Secret value.")] = None,
    project: Annotated[str, typer.Option("--project", help="Project name.")] = "default",
    environment: Annotated[str, typer.Option("--environment", help="Environment name.")] = "default",
    description: Annotated[str, typer.Option("--description", help="Secret description.")] = "",
) -> None:
    try:
        secret_value = value if value is not None else getpass.getpass("Secret value: ")
        record = service().set_secret(key, secret_value, project=project, environment=environment, description=description)
        typer.echo(f"Stored secret {record.key} for {record.project}/{record.environment}.")
    except (LockrError, VaultLockedError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc


@app.command("get")
def get_command(
    key: str,
    project: Annotated[str, typer.Option("--project", help="Project name.")] = "default",
    environment: Annotated[str, typer.Option("--environment", help="Environment name.")] = "default",
    raw: Annotated[bool, typer.Option("--raw", help="Print the plaintext secret value.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Print metadata as JSON.")] = False,
) -> None:
    try:
        secret = service().get_secret(key, project=project, environment=environment)
    except (VaultLockedError, SecretNotFoundError, LockrError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc
    if raw:
        typer.echo(secret.value)
        return
    if json_output:
        typer.echo(
            json.dumps(
                {
                    "key": secret.key,
                    "project": secret.project,
                    "environment": secret.environment,
                    "description": secret.description,
                    "created_at": secret.created_at,
                    "updated_at": secret.updated_at,
                    "last_rotated_at": secret.last_rotated_at,
                },
                indent=2,
            )
        )
        return
    typer.echo(f"{secret.key}=******** ({secret.project}/{secret.environment})")


@app.command("list")
def list_command(
    project: Annotated[str | None, typer.Option("--project", help="Filter by project.")] = None,
    environment: Annotated[str | None, typer.Option("--environment", help="Filter by environment.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON output.")] = False,
) -> None:
    try:
        items = service().list_secrets(project=project, environment=environment)
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
        typer.echo(f"{item.project}/{item.environment} {item.key} updated={item.updated_at}")


@app.command("audit")
def audit_command(
    project: Annotated[str | None, typer.Option("--project", help="Filter by project.")] = None,
    environment: Annotated[str | None, typer.Option("--environment", help="Filter by environment.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Print JSON output.")] = False,
) -> None:
    """List secrets with audit metadata. Never exposes secret values."""
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


@app.command("import-env")
def import_env_command(
    env_path: Path,
    project: Annotated[str, typer.Option("--project", help="Project name.")] = "default",
    environment: Annotated[str, typer.Option("--environment", help="Environment name.")] = "default",
    preview: Annotated[bool, typer.Option("--preview", help="Show redacted preview only.")] = False,
    apply: Annotated[bool, typer.Option("--apply", help="Apply the import to the vault.")] = False,
    overwrite: Annotated[bool, typer.Option("--overwrite", help="Overwrite conflicting keys.")] = False,
) -> None:
    if preview == apply:
        typer.echo("Choose exactly one of --preview or --apply.", err=True)
        raise typer.Exit(code=2)
    try:
        if preview:
            result = service().preview_import_env(env_path)
            for entry in result.entries:
                masked = "*" * len(entry.value) if len(entry.value) <= 4 else f"{entry.value[:2]}{'*' * (len(entry.value) - 4)}{entry.value[-2:]}"
                typer.echo(f"{entry.key}={masked}")
            if result.malformed_lines:
                typer.echo(f"Malformed lines: {', '.join(str(line) for line in result.malformed_lines)}")
            return

        result = service().apply_import_env(env_path, project=project, environment=environment, overwrite=overwrite)
        typer.echo(render_apply_summary(result))
    except (LockrError, VaultLockedError, OSError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc


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


@backup_app.command("restore")
def backup_restore_command(
    repo: Annotated[Path, typer.Option("--repo", help="Path to git repository containing backup artifact.")],
) -> None:
    """Restore vault from an encrypted backup artifact."""
    try:
        result = service().restore_backup(repo=repo)
    except (LockrError, BackupError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Vault restored from {result.artifact_path}.")
    if result.previous_backed_up:
        typer.echo("Previous vault saved as vault.lockr.bak.")


@backup_app.command("status")
def backup_status_command() -> None:
    """Show backup configuration and dependency status."""
    try:
        status = service().backup_status()
    except (LockrError, BackupError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Backup repo:    {status.repo or '(not configured)'}")
    typer.echo(f"Last backup:    {status.last_backup_at or '(never)'}")
    typer.echo(f"git available:  {'yes' if status.git_available else 'NO - install git'}")
    typer.echo(f"gpg available:  {'yes' if status.gpg_available else 'NO - install gpg'}")


@app.command("export-shell")
def export_shell_command(
    project: Annotated[str, typer.Option("--project", help="Project name.")] = "default",
    environment: Annotated[str, typer.Option("--environment", help="Environment name.")] = "default",
    shell: Annotated[str, typer.Option("--shell", help="Shell syntax: posix or powershell.")] = "posix",
) -> None:
    """Print shell export statements for sourcing secrets into the current shell."""
    if shell not in ("posix", "powershell"):
        typer.echo("--shell must be 'posix' or 'powershell'.", err=True)
        raise typer.Exit(code=2)
    try:
        content = service().export_shell(project=project, environment=environment, shell=shell)
    except (LockrError, VaultLockedError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc
    typer.echo(content, nl=False)


@app.command("tui")
def tui_command() -> None:
    """Launch the interactive TUI browser."""
    try:
        from lockr.tui.app import LockrTuiApp
        LockrTuiApp().run()
    except (LockrError, VaultLockedError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc


@app.command("export-env")
def export_env_command(
    project: Annotated[str, typer.Option("--project", help="Project name.")] = "default",
    environment: Annotated[str, typer.Option("--environment", help="Environment name.")] = "default",
    stdout: Annotated[bool, typer.Option("--stdout", help="Print .env content to stdout.")] = False,
    output: Annotated[Path | None, typer.Option("--output", help="Write .env content to a file.")] = None,
) -> None:
    if stdout == (output is not None):
        typer.echo("Choose exactly one of --stdout or --output.", err=True)
        raise typer.Exit(code=2)
    try:
        result = service().export_env(project=project, environment=environment)
        if stdout:
            typer.echo(result.content, nl=False)
            return
        typer.echo("Warning: writing plaintext .env content to disk.", err=True)
        atomic_write_text(output, result.content)
        typer.echo(f"Exported {result.count} secrets to {output}.")
    except (LockrError, VaultLockedError, OSError) as exc:
        render_error(exc)
        raise typer.Exit(code=1) from exc
