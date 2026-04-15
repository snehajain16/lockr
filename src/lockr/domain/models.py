from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass
class SecretRecord:
    key: str
    value: str
    project: str = "default"
    environment: str = "default"
    description: str = ""
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    last_rotated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecretRecord":
        return cls(**data)


@dataclass
class VaultData:
    version: int = 1
    secrets: list[SecretRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "secrets": [secret.to_dict() for secret in self.secrets],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VaultData":
        return cls(
            version=data.get("version", 1),
            secrets=[SecretRecord.from_dict(item) for item in data.get("secrets", [])],
        )
