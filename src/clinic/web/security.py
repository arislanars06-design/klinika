"""Password hashing and role-based access helpers.

Uses the stdlib PBKDF2-SHA256 (no third-party crypto dependency). The output
format is ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`` — the same shape
Django, Flask-Security and others emit, so operators recognise it at a glance.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import HTTPException, Request, status

PBKDF2_ITERATIONS = 260_000  # tuned for ~50 ms on a modern laptop
PBKDF2_ALGO = "sha256"


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return a serialized PBKDF2-SHA256 hash of ``password``."""
    if not password:
        raise ValueError("password must be non-empty")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        PBKDF2_ALGO,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Constant-time check of ``password`` against a stored hash."""
    if not password or not encoded:
        return False
    try:
        algo, iters_s, salt_hex, hash_hex = encoded.split("$", 3)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    try:
        iterations = int(iters_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac(
        PBKDF2_ALGO,
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate, expected)


# ---------------------------------------------------------------------------
# Role guard (FastAPI dependency)
# ---------------------------------------------------------------------------


VALID_ROLES = ("admin", "staff")


def require_role(*allowed: str):
    """Return a FastAPI dependency enforcing ``request.session['role']``."""

    def _dep(request: Request) -> str:
        session = getattr(request, "session", None) or {}
        user = session.get("user")
        role = session.get("role")
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="login_required",
            )
        if allowed and role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="insufficient_role",
            )
        return role or ""

    return _dep


__all__ = [
    "PBKDF2_ITERATIONS",
    "VALID_ROLES",
    "hash_password",
    "require_role",
    "verify_password",
]
