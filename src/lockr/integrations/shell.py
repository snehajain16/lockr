from __future__ import annotations

import os
import subprocess


def run_with_injected_env(command: list[str], extra_env: dict[str, str]) -> int:
    """Run command with extra_env merged on top of the current process environment.

    Secrets live only in the child's env and are never written to disk.
    Returns the child process exit code.
    """
    env = {**os.environ, **extra_env}
    result = subprocess.run(command, env=env)
    return result.returncode
