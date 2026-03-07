"""JWT authentication: password hashing, token creation, and FastAPI dependency."""

from __future__ import annotations

import hashlib
import hmac
import json
import base64
import secrets
import time
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ankithis_api.config import settings
from ankithis_api.db import get_db
from ankithis_api.models.user import User

_bearer = HTTPBearer(auto_error=False)

# ---------- Password hashing (PBKDF2-SHA256) ----------

_ITERATIONS = 260_000
_SALT_LEN = 16


def hash_password(password: str) -> str:
    salt = secrets.token_hex(_SALT_LEN)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    salt, dk_hex = hashed.split("$", 1)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS)
    return hmac.compare_digest(dk.hex(), dk_hex)


# ---------- JWT (HS256, no external lib) ----------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def create_access_token(user_id: str) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url_encode(
        json.dumps({
            "sub": user_id,
            "exp": int(time.time()) + settings.jwt_expiry_seconds,
            "iat": int(time.time()),
            "jti": uuid.uuid4().hex,
        }).encode()
    )
    sig_input = f"{header}.{payload}".encode()
    sig = hmac.new(settings.jwt_secret.encode(), sig_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64url_encode(sig)}"


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises ValueError on any problem."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    header_b, payload_b, sig_b = parts
    sig_input = f"{header_b}.{payload_b}".encode()
    expected_sig = hmac.new(settings.jwt_secret.encode(), sig_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid signature")

    payload = json.loads(_b64url_decode(payload_b))

    if payload.get("exp", 0) < time.time():
        raise ValueError("Token expired")

    return payload


# ---------- FastAPI dependency ----------

async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(creds.credentials)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
