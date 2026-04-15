from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from lockr.domain.models import VaultData


class CryptoError(Exception):
    pass


@dataclass
class EncryptedVault:
    version: int
    kdf: str
    salt: str
    nonce: str
    ciphertext: str

    def to_json(self) -> str:
        return json.dumps(
            {
                "version": self.version,
                "kdf": self.kdf,
                "salt": self.salt,
                "nonce": self.nonce,
                "ciphertext": self.ciphertext,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, raw: str) -> "EncryptedVault":
        data = json.loads(raw)
        return cls(**data)


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))


def derive_session_key(password: str, salt_b64: str) -> str:
    salt = base64.b64decode(salt_b64.encode("ascii"))
    return base64.b64encode(_derive_key(password, salt)).decode("ascii")


def build_empty_encrypted_vault(password: str) -> EncryptedVault:
    return encrypt_vault(VaultData(), password)


def encrypt_vault(vault: VaultData, password: str) -> EncryptedVault:
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    return encrypt_vault_with_key(vault, key, salt)


def encrypt_vault_with_key(vault: VaultData, key: bytes, salt: bytes) -> EncryptedVault:
    nonce = os.urandom(12)
    payload = json.dumps(vault.to_dict(), separators=(",", ":")).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, payload, None)
    return EncryptedVault(
        version=1,
        kdf="scrypt",
        salt=base64.b64encode(salt).decode("ascii"),
        nonce=base64.b64encode(nonce).decode("ascii"),
        ciphertext=base64.b64encode(ciphertext).decode("ascii"),
    )


def decrypt_vault(encrypted: EncryptedVault, key_b64: str) -> VaultData:
    try:
        key = base64.b64decode(key_b64.encode("ascii"))
        nonce = base64.b64decode(encrypted.nonce.encode("ascii"))
        ciphertext = base64.b64decode(encrypted.ciphertext.encode("ascii"))
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except (ValueError, InvalidTag) as exc:
        raise CryptoError("Unable to decrypt vault. The vault may be locked or the credentials are invalid.") from exc
    return VaultData.from_dict(json.loads(plaintext.decode("utf-8")))
