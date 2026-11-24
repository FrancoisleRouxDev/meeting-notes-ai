from cryptography.fernet import Fernet, InvalidToken
from pydantic_settings import BaseSettings, SettingsConfigDict


class CryptoSettings(BaseSettings):
    # Read from the environment or backend/.env. Keep the key out of the repo.
    encryption_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


crypto_settings = CryptoSettings()


class EncryptionUnavailable(Exception):
    """The encryption key is missing or invalid, or a saved value can't be read with it."""


def _fernet() -> Fernet:
    if not crypto_settings.encryption_key:
        raise EncryptionUnavailable("ENCRYPTION_KEY is not set in backend/.env")
    try:
        return Fernet(crypto_settings.encryption_key.encode())
    except ValueError as exc:
        raise EncryptionUnavailable("ENCRYPTION_KEY is not a valid key") from exc


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise EncryptionUnavailable(
            "The saved Slack channel can't be read. Reconnect it on your Account page."
        ) from exc
