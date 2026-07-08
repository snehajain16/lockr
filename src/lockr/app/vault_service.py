from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from lockr.domain.models import SecretRecord, VaultData, utc_now
from lockr.integrations.env_files import EnvEntry, EnvParseResult, parse_env_file, render_env
from lockr.paths import LockrPaths
from lockr.security.crypto import (
    EncryptedVault,
    build_empty_encrypted_vault,
    decrypt_vault,
    derive_session_key,
    encrypt_vault_with_key,
)
from lockr.storage.files import atomic_write_json, atomic_write_text, ensure_directory, read_json, remove_file


class LockrError(Exception):
    pass


class VaultLockedError(LockrError):
    pass


class SecretNotFoundError(LockrError):
    pass


class VaultAlreadyExistsError(LockrError):
    pass


@dataclass
class SessionState:
    key: str
    created_at: str


@dataclass
class ListResult:
    key: str
    project: str
    environment: str
    updated_at: str


@dataclass
class ImportPreviewResult:
    entries: list[EnvEntry]
    malformed_lines: list[int]


@dataclass
class ImportApplyResult:
    imported: int
    updated: int
    skipped: int
    malformed: int


@dataclass
class ExportResult:
    content: str
    count: int


class VaultService:
    def __init__(self, paths: LockrPaths):
        self.paths = paths

    def init_vault(self, password: str, force: bool = False) -> None:
        if self.paths.vault_file.exists() and not force:
            raise VaultAlreadyExistsError("Vault already exists. Use --force to overwrite it.")
        ensure_directory(self.paths.home)
        encrypted = build_empty_encrypted_vault(password)
        atomic_write_text(self.paths.vault_file, encrypted.to_json())
        self._write_session(derive_session_key(password, encrypted.salt))

    def unlock(self, password: str) -> None:
        encrypted = self._read_encrypted_vault()
        key_b64 = derive_session_key(password, encrypted.salt)
        decrypt_vault(encrypted, key_b64)
        self._write_session(key_b64)

    def lock(self) -> None:
        remove_file(self.paths.session_file)

    def set_secret(
        self,
        key: str,
        value: str,
        project: str = "default",
        environment: str = "default",
        description: str = "",
    ) -> SecretRecord:
        vault = self._load_vault()
        existing = self._find_secret(vault, key, project, environment)
        if existing:
            existing.value = value
            existing.description = description or existing.description
            existing.updated_at = utc_now()
            existing.last_rotated_at = utc_now()
            record = existing
        else:
            record = SecretRecord(
                key=key,
                value=value,
                project=project,
                environment=environment,
                description=description,
            )
            vault.secrets.append(record)
        self._save_vault(vault)
        return record

    def get_secret(
        self,
        key: str,
        project: str = "default",
        environment: str = "default",
    ) -> SecretRecord:
        vault = self._load_vault()
        secret = self._find_secret(vault, key, project, environment)
        if not secret:
            raise SecretNotFoundError(f"Secret '{key}' was not found for project '{project}' and environment '{environment}'.")
        return secret

    def list_secrets(self, project: str | None = None, environment: str | None = None) -> list[ListResult]:
        vault = self._load_vault()
        items: list[ListResult] = []
        for secret in vault.secrets:
            if project and secret.project != project:
                continue
            if environment and secret.environment != environment:
                continue
            items.append(
                ListResult(
                    key=secret.key,
                    project=secret.project,
                    environment=secret.environment,
                    updated_at=secret.updated_at,
                )
            )
        return sorted(items, key=lambda item: (item.project, item.environment, item.key))

    def preview_import_env(self, env_path: Path) -> ImportPreviewResult:
        result = parse_env_file(env_path)
        return ImportPreviewResult(entries=result.entries, malformed_lines=result.malformed_lines)

    def apply_import_env(
        self,
        env_path: Path,
        project: str,
        environment: str,
        overwrite: bool = False,
    ) -> ImportApplyResult:
        parse_result = parse_env_file(env_path)
        vault = self._load_vault()
        imported = 0
        updated = 0
        skipped = 0

        for entry in parse_result.entries:
            existing = self._find_secret(vault, entry.key, project, environment)
            if existing and not overwrite:
                skipped += 1
                continue
            if existing:
                existing.value = entry.value
                existing.updated_at = utc_now()
                existing.last_rotated_at = utc_now()
                updated += 1
            else:
                vault.secrets.append(
                    SecretRecord(
                        key=entry.key,
                        value=entry.value,
                        project=project,
                        environment=environment,
                    )
                )
                imported += 1

        self._save_vault(vault)
        return ImportApplyResult(
            imported=imported,
            updated=updated,
            skipped=skipped,
            malformed=len(parse_result.malformed_lines),
        )

    def export_env(
        self,
        project: str,
        environment: str,
    ) -> ExportResult:
        vault = self._load_vault()
        selected = [
            (secret.key, secret.value)
            for secret in sorted(vault.secrets, key=lambda item: item.key)
            if secret.project == project and secret.environment == environment
        ]
        return ExportResult(content=render_env(selected), count=len(selected))

    def get_secrets_for_injection(
        self,
        project: str = "default",
        environment: str = "default",
    ) -> dict[str, str]:
        vault = self._load_vault()
        return {
            s.key: s.value
            for s in vault.secrets
            if s.project == project and s.environment == environment
        }

    def _write_session(self, key_b64: str) -> None:
        payload = {"key": key_b64, "created_at": utc_now()}
        atomic_write_json(self.paths.session_file, payload)

    def _require_session(self) -> SessionState:
        if not self.paths.session_file.exists():
            raise VaultLockedError("Vault is locked. Run 'lockr unlock' before accessing secrets.")
        payload = read_json(self.paths.session_file)
        return SessionState(key=payload["key"], created_at=payload["created_at"])

    def _read_encrypted_vault(self) -> EncryptedVault:
        if not self.paths.vault_file.exists():
            raise LockrError("Vault has not been initialized. Run 'lockr init' first.")
        return EncryptedVault.from_json(self.paths.vault_file.read_text(encoding="utf-8"))

    def _load_vault(self) -> VaultData:
        encrypted = self._read_encrypted_vault()
        session = self._require_session()
        return decrypt_vault(encrypted, session.key)

    def _save_vault(self, vault: VaultData) -> None:
        encrypted = self._read_encrypted_vault()
        session = self._require_session()
        key = base64.b64decode(session.key.encode("ascii"))
        salt = base64.b64decode(encrypted.salt.encode("ascii"))
        new_encrypted = encrypt_vault_with_key(vault, key, salt)
        atomic_write_text(self.paths.vault_file, new_encrypted.to_json())
        self._write_session(session.key)

    def _find_secret(self, vault: VaultData, key: str, project: str, environment: str) -> SecretRecord | None:
        for secret in vault.secrets:
            if secret.key == key and secret.project == project and secret.environment == environment:
                return secret
        return None
