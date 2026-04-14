import base64
import hashlib
import hmac
import logging
import os
import secrets
from functools import lru_cache
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from models.database import get_db

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 2
PASSWORD_HASH_NAME = "scrypt"
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
DEV_FALLBACK_SECRET = "dev-only-jwt-secret-change-me"

bearer_scheme = HTTPBearer(auto_error=False)


def _is_production() -> bool:
    environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "")).strip().lower()
    return environment in {"prod", "production"}


@lru_cache(maxsize=1)
def get_secret_key() -> str:
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret

    if _is_production():
        raise RuntimeError("JWT_SECRET environment variable is required in production")

    logger.warning(
        "JWT_SECRET is not set; using an insecure development fallback secret"
    )
    return DEV_FALLBACK_SECRET


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    key_b64 = base64.b64encode(derived_key).decode("ascii")
    return f"{PASSWORD_HASH_NAME}${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt_b64}${key_b64}"


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed.startswith(f"{PASSWORD_HASH_NAME}$"):
        legacy_hash = hashlib.sha256(plain.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_hash, hashed)

    try:
        algorithm, n, r, p, salt_b64, key_b64 = hashed.split("$", maxsplit=5)
        if algorithm != PASSWORD_HASH_NAME:
            return False
    except ValueError:
        return False

    derived_key = hashlib.scrypt(
        plain.encode("utf-8"),
        salt=base64.b64decode(salt_b64.encode("ascii")),
        n=int(n),
        r=int(r),
        p=int(p),
    )
    expected_key = base64.b64decode(key_b64.encode("ascii"))
    return hmac.compare_digest(derived_key, expected_key)


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])


def password_needs_rehash(hashed: str) -> bool:
    return not hashed.startswith(f"{PASSWORD_HASH_NAME}$")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db=Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("user_id")
        email = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication payload",
        )

    cursor = await db.execute(
        "SELECT id, email FROM users WHERE id = ? AND email = ?",
        (user_id, email),
    )
    user = await cursor.fetchone()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user was not found",
        )

    return dict(user)
