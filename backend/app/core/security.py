import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2 is a memory-hard hash, which is the current recommended choice for passwords.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def new_session_token() -> str:
    # 32 random bytes from the OS. Guessing one is not practical.
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    # Fast hash is fine here because the token is already random, unlike a password.
    return hashlib.sha256(token.encode()).hexdigest()
