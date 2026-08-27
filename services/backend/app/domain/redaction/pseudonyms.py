from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from cryptography.fernet import Fernet, InvalidToken


class PseudonymError(ValueError):
    """Safe reversible-pseudonym error without plaintext values."""


@dataclass(frozen=True, slots=True)
class EncryptedMapping:
    placeholder: str
    ciphertext: bytes
    key_version: int
    expires_at: datetime


class MappingRepository(Protocol):
    async def store(self, mapping: EncryptedMapping) -> None: ...


class PseudonymCipher:
    def __init__(self, key: bytes, *, key_version: int = 1) -> None:
        if key_version < 1:
            raise PseudonymError("Key version must be positive")
        try:
            self._fernet = Fernet(key)
        except (TypeError, ValueError) as error:
            raise PseudonymError("Invalid pseudonym encryption key") from error
        self.key_version = key_version

    def encrypt(
        self,
        placeholder: str,
        plaintext: str,
        *,
        ttl: timedelta = timedelta(days=7),
        now: datetime | None = None,
    ) -> EncryptedMapping:
        if not placeholder.startswith("[PSEUDONYM_") or not plaintext:
            raise PseudonymError("Invalid pseudonym mapping")
        timestamp = now or datetime.now(UTC)
        return EncryptedMapping(
            placeholder=placeholder,
            ciphertext=self._fernet.encrypt(plaintext.encode("utf-8")),
            key_version=self.key_version,
            expires_at=timestamp + ttl,
        )

    def decrypt(self, mapping: EncryptedMapping, *, now: datetime | None = None) -> str:
        timestamp = now or datetime.now(UTC)
        if mapping.key_version != self.key_version or mapping.expires_at <= timestamp:
            raise PseudonymError("Pseudonym mapping is unavailable")
        try:
            return self._fernet.decrypt(mapping.ciphertext).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError) as error:
            raise PseudonymError("Pseudonym mapping is unavailable") from error
