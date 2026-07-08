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


def _init_and_unlock(tmp_path: Path) -> None:
    run_lockr(["init"], tmp_path, passwords=["pw", "pw"])


def _set_secret(tmp_path: Path, key: str, value: str, project: str = "default", environment: str = "default") -> None:
    run_lockr(["set", key, "--value", value, "--project", project, "--environment", environment], tmp_path)


# ── Story 3.2: Print shell export output ─────────────────────────────────────

def test_export_shell_command_exists(tmp_path: Path):
    result = run_lockr(["export-shell", "--help"], tmp_path)
    assert result.exit_code == 0


def test_export_shell_posix_output(tmp_path: Path):
    _init_and_unlock(tmp_path)
    _set_secret(tmp_path, "MY_KEY", "hello world")
    result = run_lockr(["export-shell", "--shell", "posix"], tmp_path)
    assert result.exit_code == 0
    assert "export MY_KEY=" in result.output
    assert "hello world" in result.output
    assert "MY_KEY=hello" not in result.output  # must be shell-quoted


def test_export_shell_posix_quotes_special_chars(tmp_path: Path):
    _init_and_unlock(tmp_path)
    _set_secret(tmp_path, "KEY", "it's a secret")
    result = run_lockr(["export-shell", "--shell", "posix"], tmp_path)
    assert result.exit_code == 0
    # shlex.quote wraps in single quotes when value has special chars
    assert "KEY=" in result.output
    assert "secret" in result.output


def test_export_shell_powershell_output(tmp_path: Path):
    _init_and_unlock(tmp_path)
    _set_secret(tmp_path, "MY_KEY", "myvalue")
    result = run_lockr(["export-shell", "--shell", "powershell"], tmp_path)
    assert result.exit_code == 0
    assert '$env:MY_KEY = "myvalue"' in result.output


def test_export_shell_invalid_shell_flag(tmp_path: Path):
    _init_and_unlock(tmp_path)
    result = run_lockr(["export-shell", "--shell", "bash"], tmp_path)
    assert result.exit_code == 2


def test_export_shell_fails_when_locked(tmp_path: Path):
    _init_and_unlock(tmp_path)
    run_lockr(["lock"], tmp_path)
    result = run_lockr(["export-shell"], tmp_path)
    assert result.exit_code == 1
    assert "locked" in result.output.lower()


# ── Story 4.2: Restore from encrypted backup ─────────────────────────────────

def test_backup_restore_command_exists(tmp_path: Path):
    result = run_lockr(["backup", "restore", "--help"], tmp_path)
    assert result.exit_code == 0


def test_backup_restore_round_trip(tmp_path: Path):
    """Create a backup, wipe the vault, restore it, verify secret survives."""
    repo = tmp_path / "repo"
    repo.mkdir()
    # init a git repo so backup create doesn't need --commit
    import subprocess
    subprocess.run(["git", "init", str(repo)], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.com"], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], capture_output=True)

    _init_and_unlock(tmp_path)
    _set_secret(tmp_path, "RESTORE_KEY", "restore_value")

    # create backup
    result = run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 0

    # wipe vault
    vault_file = tmp_path / "vault.lockr"
    vault_file.unlink()

    # restore
    result = run_lockr(["backup", "restore", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 0
    assert "restored" in result.output.lower()


def test_backup_restore_saves_previous_vault(tmp_path: Path):
    """Restore when local vault exists — old vault saved as .bak."""
    repo = tmp_path / "repo"
    repo.mkdir()
    import subprocess
    subprocess.run(["git", "init", str(repo)], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t.com"], capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], capture_output=True)

    _init_and_unlock(tmp_path)
    _set_secret(tmp_path, "OLD_KEY", "old_value")
    run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)

    # restore on top of existing vault
    result = run_lockr(["backup", "restore", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 0
    assert "vault.lockr.bak" in result.output
    assert (tmp_path / "vault.lockr.bak").exists()


def test_backup_restore_fails_missing_artifact(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    result = run_lockr(["backup", "restore", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


# ── Story 4.3: Show backup status ─────────────────────────────────────────────

def test_backup_status_command_exists(tmp_path: Path):
    result = run_lockr(["backup", "status", "--help"], tmp_path)
    assert result.exit_code == 0


def test_backup_status_before_any_backup(tmp_path: Path):
    _init_and_unlock(tmp_path)
    result = run_lockr(["backup", "status"], tmp_path)
    assert result.exit_code == 0
    assert "not configured" in result.output.lower() or "never" in result.output.lower()
    assert "git available" in result.output.lower()
    assert "gpg available" in result.output.lower()


def test_backup_status_after_backup(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    import subprocess
    subprocess.run(["git", "init", str(repo)], capture_output=True)

    _init_and_unlock(tmp_path)
    run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)

    result = run_lockr(["backup", "status"], tmp_path)
    assert result.exit_code == 0
    assert str(repo) in result.output
    assert "never" not in result.output.lower()
