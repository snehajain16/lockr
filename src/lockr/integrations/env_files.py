from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class EnvEntry:
    key: str
    value: str
    line_number: int


@dataclass
class EnvParseResult:
    entries: list[EnvEntry]
    malformed_lines: list[int]


def parse_env_file(path: Path) -> EnvParseResult:
    entries: list[EnvEntry] = []
    malformed_lines: list[int] = []

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in raw_line:
            malformed_lines.append(line_number)
            continue
        raw_key, raw_value = raw_line.split("=", 1)
        key = raw_key.strip()
        value = raw_value.strip()
        if not key:
            malformed_lines.append(line_number)
            continue
        entries.append(EnvEntry(key=key, value=value, line_number=line_number))

    return EnvParseResult(entries=entries, malformed_lines=malformed_lines)


def redact_value(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def render_preview(result: EnvParseResult) -> str:
    lines = [f"{entry.key}={redact_value(entry.value)}" for entry in result.entries]
    if result.malformed_lines:
        lines.append(f"malformed_lines={','.join(str(line) for line in result.malformed_lines)}")
    return "\n".join(lines)


def render_env(entries: list[tuple[str, str]]) -> str:
    return "\n".join(f"{key}={value}" for key, value in entries) + ("\n" if entries else "")
