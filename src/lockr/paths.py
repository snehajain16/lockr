from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LockrPaths:
    home: Path
    vault_file: Path
    session_file: Path
    backup_config_file: Path


def get_lockr_paths() -> LockrPaths:
    configured = os.environ.get("LOCKR_HOME")
    home = Path(configured).expanduser() if configured else Path.home() / ".lockr"
    return LockrPaths(
        home=home,
        vault_file=home / "vault.lockr",
        session_file=home / "session.json",
        backup_config_file=home / "backup.json",
    )
