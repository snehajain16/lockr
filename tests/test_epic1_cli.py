from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from lockr.cli.main import app


runner = CliRunner()


def run_lockr(args: list[str], home: Path, passwords: list[str] | None = None):
    env = {"LOCKR_HOME": str(home)}
    if passwords:
        import lockr.cli.main as cli_main

        original = cli_main.getpass.getpass
        iterator = iter(passwords)

        def fake_getpass(prompt: str = "") -> str:
            return next(iterator)

        cli_main.getpass.getpass = fake_getpass
        try:
            return runner.invoke(app, args, env=env)
        finally:
            cli_main.getpass.getpass = original
    return runner.invoke(app, args, env=env)


def test_init_creates_vault_and_session(tmp_path: Path):
    result = run_lockr(["init"], tmp_path, passwords=["secret-pass", "secret-pass"])
    assert result.exit_code == 0
    assert (tmp_path / "vault.lockr").exists()
    assert (tmp_path / "session.json").exists()


def test_locked_access_fails_with_guidance(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["secret-pass", "secret-pass"])
    result = run_lockr(["lock"], tmp_path)
    assert result.exit_code == 0
    result = run_lockr(["list"], tmp_path)
    assert result.exit_code == 1
    assert "Vault is locked" in result.stderr


def test_set_get_and_list_secret(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["secret-pass", "secret-pass"])
    result = run_lockr(
        ["set", "OPENAI_API_KEY", "--value", "top-secret", "--project", "lockr", "--environment", "dev"],
        tmp_path,
    )
    assert result.exit_code == 0

    masked = run_lockr(["get", "OPENAI_API_KEY", "--project", "lockr", "--environment", "dev"], tmp_path)
    assert masked.exit_code == 0
    assert "********" in masked.stdout
    assert "top-secret" not in masked.stdout

    raw = run_lockr(["get", "OPENAI_API_KEY", "--project", "lockr", "--environment", "dev", "--raw"], tmp_path)
    assert raw.exit_code == 0
    assert "top-secret" in raw.stdout

    listed = run_lockr(["list", "--project", "lockr", "--environment", "dev", "--json"], tmp_path)
    assert listed.exit_code == 0
    payload = json.loads(listed.stdout)
    assert payload[0]["key"] == "OPENAI_API_KEY"


def test_unlock_and_missing_secret_behavior(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["secret-pass", "secret-pass"])
    run_lockr(["lock"], tmp_path)

    unlock = run_lockr(["unlock"], tmp_path, passwords=["secret-pass"])
    assert unlock.exit_code == 0

    missing = run_lockr(["get", "DOES_NOT_EXIST"], tmp_path)
    assert missing.exit_code == 1
    assert "was not found" in missing.stderr
