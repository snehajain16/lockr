from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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


def _git_mocks():
    return (
        patch("lockr.integrations.git_backup.check_git_available"),
        patch("lockr.integrations.git_backup.check_gpg_available"),
    )


def test_backup_create_copies_vault_file(tmp_path: Path):
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    _init_and_unlock(tmp_path)
    with patch("lockr.integrations.git_backup.check_git_available"):
        with patch("lockr.integrations.git_backup.check_gpg_available"):
            result = run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 0, result.output
    assert (repo / "lockr-vault.lockr").exists()


def test_backup_artifact_contains_no_plaintext(tmp_path: Path):
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    _init_and_unlock(tmp_path)
    run_lockr(["set", "MY_SECRET", "--value", "supersecret123"], tmp_path)
    with patch("lockr.integrations.git_backup.check_git_available"):
        with patch("lockr.integrations.git_backup.check_gpg_available"):
            run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    artifact = (repo / "lockr-vault.lockr").read_bytes()
    assert b"supersecret123" not in artifact


def test_backup_create_with_commit_flag(tmp_path: Path):
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    _init_and_unlock(tmp_path)
    with patch("lockr.integrations.git_backup.check_git_available"):
        with patch("lockr.integrations.git_backup.check_gpg_available"):
            with patch("lockr.integrations.git_backup.git_add_and_commit") as mock_commit:
                result = run_lockr(
                    ["backup", "create", "--repo", str(repo), "--commit"], tmp_path
                )
    assert result.exit_code == 0, result.output
    mock_commit.assert_called_once()


def test_backup_create_without_commit_flag(tmp_path: Path):
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    _init_and_unlock(tmp_path)
    with patch("lockr.integrations.git_backup.check_git_available"):
        with patch("lockr.integrations.git_backup.check_gpg_available"):
            with patch("lockr.integrations.git_backup.git_add_and_commit") as mock_commit:
                result = run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 0, result.output
    mock_commit.assert_not_called()


def test_backup_fails_if_vault_not_initialized(tmp_path: Path):
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    result = run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 1


def test_backup_fails_if_git_missing(tmp_path: Path):
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    _init_and_unlock(tmp_path)
    from lockr.integrations.git_backup import BackupError as GitBackupError
    with patch(
        "lockr.integrations.git_backup.check_git_available",
        side_effect=GitBackupError("git is not available"),
    ):
        with patch("lockr.integrations.git_backup.check_gpg_available"):
            result = run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 1
    assert "git" in result.output.lower()


def test_backup_fails_if_gpg_missing(tmp_path: Path):
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    _init_and_unlock(tmp_path)
    from lockr.integrations.git_backup import BackupError as GitBackupError
    with patch("lockr.integrations.git_backup.check_git_available"):
        with patch(
            "lockr.integrations.git_backup.check_gpg_available",
            side_effect=GitBackupError("gpg is not available"),
        ):
            result = run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    assert result.exit_code == 1
    assert "gpg" in result.output.lower()


def test_backup_persists_config(tmp_path: Path):
    import json
    repo = tmp_path / "backup-repo"
    repo.mkdir()
    _init_and_unlock(tmp_path)
    with patch("lockr.integrations.git_backup.check_git_available"):
        with patch("lockr.integrations.git_backup.check_gpg_available"):
            run_lockr(["backup", "create", "--repo", str(repo)], tmp_path)
    config_file = tmp_path / "backup.json"
    assert config_file.exists()
    data = json.loads(config_file.read_text())
    assert data["repo"] == str(repo)
    assert "last_backup_at" in data
