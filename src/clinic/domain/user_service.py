"""Web-user CRUD service.

Kept intentionally small: create, list, get, update, deactivate, reset password,
and — for auth — ``authenticate`` which returns the user on a valid login and
updates ``last_login_at``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from clinic.db.database import session_scope
from clinic.db.models import WebUser
from clinic.infrastructure.validators import ValidationError
from clinic.web.security import VALID_ROLES, hash_password, verify_password


@dataclass
class WebUserDTO:
    id: int
    username: str
    role: str
    full_name: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None

    @classmethod
    def from_orm(cls, row: WebUser) -> WebUserDTO:
        return cls(
            id=row.id,
            username=row.username,
            role=row.role,
            full_name=row.full_name or "",
            is_active=row.is_active,
            created_at=row.created_at,
            last_login_at=row.last_login_at,
        )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


def list_all(*, active_only: bool = False) -> list[WebUserDTO]:
    with session_scope() as session:
        stmt = select(WebUser).order_by(WebUser.username)
        if active_only:
            stmt = stmt.where(WebUser.is_active.is_(True))
        return [WebUserDTO.from_orm(row) for row in session.scalars(stmt)]


def get(user_id: int) -> WebUserDTO | None:
    with session_scope() as session:
        row = session.get(WebUser, user_id)
        return WebUserDTO.from_orm(row) if row else None


def get_by_username(username: str) -> WebUserDTO | None:
    with session_scope() as session:
        row = session.scalars(
            select(WebUser).where(WebUser.username == username.strip().lower())
        ).first()
        return WebUserDTO.from_orm(row) if row else None


def user_count() -> int:
    """Total number of users (active + inactive)."""
    from sqlalchemy import func

    with session_scope() as session:
        return int(session.scalar(select(func.count(WebUser.id))) or 0)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate(*, username: str, role: str, full_name: str) -> tuple[str, str, str]:
    errors = ValidationError()
    u = (username or "").strip().lower()
    if not u:
        errors.add("username", "validation.required")
    elif len(u) < 3 or len(u) > 64:
        errors.add("username", "validation.length_range", min=3, max=64)
    r = (role or "").strip()
    if r not in VALID_ROLES:
        errors.add("role", "validation.invalid_choice")
    fn = (full_name or "").strip()
    if errors.errors:
        raise errors
    return u, r, fn


def _validate_password(password: str) -> str:
    p = password or ""
    if len(p) < 4:
        err = ValidationError()
        err.add("password", "validation.length_min", min=4)
        raise err
    return p


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


def create(*, username: str, password: str, role: str = "staff", full_name: str = "") -> WebUserDTO:
    """Persist a new user. Fails if the username already exists."""
    u, r, fn = _validate(username=username, role=role, full_name=full_name)
    _validate_password(password)

    with session_scope() as session:
        existing = session.scalars(select(WebUser).where(WebUser.username == u)).first()
        if existing is not None:
            errors = ValidationError()
            errors.add("username", "validation.taken")
            raise errors
        row = WebUser(
            username=u,
            password_hash=hash_password(password),
            role=r,
            full_name=fn,
            is_active=True,
        )
        session.add(row)
        session.flush()
        return WebUserDTO.from_orm(row)


def update(user_id: int, *, role: str, full_name: str) -> WebUserDTO | None:
    """Update role + display name. Username and password are edited separately."""
    with session_scope() as session:
        row = session.get(WebUser, user_id)
        if row is None:
            return None
        _, r, fn = _validate(username=row.username, role=role, full_name=full_name)
        row.role = r
        row.full_name = fn
        session.flush()
        return WebUserDTO.from_orm(row)


def reset_password(user_id: int, new_password: str) -> bool:
    _validate_password(new_password)
    with session_scope() as session:
        row = session.get(WebUser, user_id)
        if row is None:
            return False
        row.password_hash = hash_password(new_password)
        return True


def set_active(user_id: int, is_active: bool) -> WebUserDTO | None:
    with session_scope() as session:
        row = session.get(WebUser, user_id)
        if row is None:
            return None
        row.is_active = is_active
        session.flush()
        return WebUserDTO.from_orm(row)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def authenticate(username: str, password: str) -> WebUserDTO | None:
    """Return the user DTO on a successful login, updating ``last_login_at``."""
    u = (username or "").strip().lower()
    if not u or not password:
        return None
    with session_scope() as session:
        row = session.scalars(select(WebUser).where(WebUser.username == u)).first()
        if row is None or not row.is_active:
            return None
        if not verify_password(password, row.password_hash):
            return None
        row.last_login_at = datetime.utcnow()
        session.flush()
        return WebUserDTO.from_orm(row)


def ensure_default_admin(username: str, password: str, full_name: str = "Administrator") -> WebUserDTO | None:
    """Idempotently create a starter admin account.

    Returns the newly created user, or ``None`` if a user already exists (no
    change was needed). Used at first boot so the operator has a way in.
    """
    if user_count() > 0:
        return None
    return create(
        username=username,
        password=password,
        role="admin",
        full_name=full_name,
    )


__all__ = [
    "WebUserDTO",
    "authenticate",
    "create",
    "ensure_default_admin",
    "get",
    "get_by_username",
    "list_all",
    "reset_password",
    "set_active",
    "update",
    "user_count",
]
