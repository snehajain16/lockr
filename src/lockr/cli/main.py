from __future__ import annotations

import getpass
import json
from typing import Annotated

import typer

from lockr.app.vault_service import (
    LockrError,
    SecretNotFoundError,
    VaultAlreadyExistsError,
    VaultLockedError,
    VaultService,
)
from lockr.paths import get_lockr_paths

app = typer.Typer(help="Lockr secrets vault")


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
