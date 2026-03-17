from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError


pwd_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False
