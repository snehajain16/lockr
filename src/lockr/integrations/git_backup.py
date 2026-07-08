from __future__ import annotations

import subprocess
from pathlib import Path


class BackupError(Exception):
    pass


def check_git_available() -> None:
    result = subprocess.run(["git", "--version"], capture_output=True)
    if result.returncode != 0:
        raise BackupError("git is not available. Install git and ensure it is on PATH.")


def check_gpg_available() -> None:
    result = subprocess.run(["gpg", "--version"], capture_output=True)
    if result.returncode != 0:
        raise BackupError("gpg is not available. Install gpg and ensure it is on PATH.")


def git_add_and_commit(repo: Path, filepath: Path, message: str) -> None:
    for cmd in (
        ["git", "-C", str(repo), "add", str(filepath)],
        ["git", "-C", str(repo), "commit", "-m", message],
    ):
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise BackupError(f"git command failed: {result.stderr.decode().strip()}")
