from __future__ import annotations

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


def test_import_preview_does_not_write(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["secret-pass", "secret-pass"])
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=super-secret\nBROKEN_LINE\n", encoding="utf-8")

    preview = run_lockr(["import-env", str(env_file), "--preview"], tmp_path)
    assert preview.exit_code == 0
    assert "API_KEY=" in preview.stdout
    assert "super-secret" not in preview.stdout
    assert "Malformed lines: 2" in preview.stdout

    listed = run_lockr(["list"], tmp_path)
    assert "No secrets found." in listed.stdout


def test_import_apply_and_export_stdout(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["secret-pass", "secret-pass"])
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=super-secret\nDB_URL=postgres://local\n", encoding="utf-8")

    applied = run_lockr(
        ["import-env", str(env_file), "--project", "lockr", "--environment", "dev", "--apply"],
        tmp_path,
    )
    assert applied.exit_code == 0
    assert "imported=2" in applied.stdout

    exported = run_lockr(
        ["export-env", "--project", "lockr", "--environment", "dev", "--stdout"],
        tmp_path,
    )
    assert exported.exit_code == 0
    assert "API_KEY=super-secret" in exported.stdout
    assert "DB_URL=postgres://local" in exported.stdout


def test_import_conflict_skip_and_overwrite(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["secret-pass", "secret-pass"])
    first = tmp_path / "first.env"
    second = tmp_path / "second.env"
    first.write_text("API_KEY=old-value\n", encoding="utf-8")
    second.write_text("API_KEY=new-value\n", encoding="utf-8")

    run_lockr(["import-env", str(first), "--project", "app", "--environment", "dev", "--apply"], tmp_path)
    skipped = run_lockr(["import-env", str(second), "--project", "app", "--environment", "dev", "--apply"], tmp_path)
    assert "skipped=1" in skipped.stdout

    overwritten = run_lockr(
        ["import-env", str(second), "--project", "app", "--environment", "dev", "--apply", "--overwrite"],
        tmp_path,
    )
    assert "updated=1" in overwritten.stdout

    fetched = run_lockr(["get", "API_KEY", "--project", "app", "--environment", "dev", "--raw"], tmp_path)
    assert "new-value" in fetched.stdout


def test_export_to_file_warns_and_scopes_output(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["secret-pass", "secret-pass"])
    run_lockr(["set", "ONLY_DEV", "--value", "dev-secret", "--project", "proj", "--environment", "dev"], tmp_path)
    run_lockr(["set", "ONLY_PROD", "--value", "prod-secret", "--project", "proj", "--environment", "prod"], tmp_path)
    output = tmp_path / "export.env"

    result = run_lockr(
        ["export-env", "--project", "proj", "--environment", "dev", "--output", str(output)],
        tmp_path,
    )
    assert result.exit_code == 0
    assert "Warning: writing plaintext .env content to disk." in result.stderr
    content = output.read_text(encoding="utf-8")
    assert "ONLY_DEV=dev-secret" in content
    assert "ONLY_PROD" not in content
