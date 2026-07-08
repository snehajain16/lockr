from __future__ import annotations

import sys
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


def _init_and_set(tmp_path: Path, key: str, value: str, project: str = "myapp", env: str = "dev") -> None:
    run_lockr(["init"], tmp_path, passwords=["pw", "pw"])
    run_lockr(
        ["set", key, "--value", value, "--project", project, "--environment", env],
        tmp_path,
    )


def test_run_injects_secrets_into_child(tmp_path: Path):
    _init_and_set(tmp_path, "MY_SECRET", "hunter2")
    outfile = tmp_path / "out.txt"
    result = run_lockr(
        [
            "run",
            "--project", "myapp",
            "--environment", "dev",
            "--",
            sys.executable, "-c",
            f"import os; open('{outfile}', 'w').write(os.environ.get('MY_SECRET', 'MISSING'))",
        ],
        tmp_path,
    )
    assert result.exit_code == 0
    assert outfile.read_text() == "hunter2"


def test_run_preserves_child_exit_code(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["pw", "pw"])
    result = run_lockr(
        ["run", "--", sys.executable, "-c", "raise SystemExit(42)"],
        tmp_path,
    )
    assert result.exit_code == 42


def test_run_fails_when_vault_locked(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["pw", "pw"])
    run_lockr(["lock"], tmp_path)
    result = run_lockr(["run", "--", sys.executable, "-c", "pass"], tmp_path)
    assert result.exit_code == 1
    assert "locked" in result.output.lower()


def test_run_no_command_exits_2(tmp_path: Path):
    run_lockr(["init"], tmp_path, passwords=["pw", "pw"])
    result = run_lockr(["run"], tmp_path)
    assert result.exit_code == 2


def test_run_does_not_persist_secrets(tmp_path: Path):
    _init_and_set(tmp_path, "MY_SECRET", "hunter2")
    run_lockr(
        [
            "run",
            "--project", "myapp",
            "--environment", "dev",
            "--",
            sys.executable, "-c", "pass",
        ],
        tmp_path,
    )
    for f in tmp_path.iterdir():
        if f.is_file():
            content = f.read_text(encoding="utf-8", errors="ignore")
            assert "hunter2" not in content, f"Secret found in plaintext in {f}"


def test_run_empty_scope_injects_nothing(tmp_path: Path):
    _init_and_set(tmp_path, "MY_SECRET", "hunter2", project="myapp", env="dev")
    outfile = tmp_path / "out.txt"
    result = run_lockr(
        [
            "run",
            "--project", "other",
            "--environment", "prod",
            "--",
            sys.executable, "-c",
            f"import os; open('{outfile}', 'w').write(os.environ.get('MY_SECRET', 'MISSING'))",
        ],
        tmp_path,
    )
    assert result.exit_code == 0
    assert outfile.read_text() == "MISSING"


def test_run_vault_not_initialized(tmp_path: Path):
    result = run_lockr(["run", "--", sys.executable, "-c", "pass"], tmp_path)
    assert result.exit_code == 1
