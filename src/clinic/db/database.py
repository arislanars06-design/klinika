"""Database engine, session factory, and lightweight schema bootstrap.

For the skeleton milestone we use ``Base.metadata.create_all`` so the app runs
out of the box. Alembic will take over version-controlled migrations once the
schema starts evolving.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from clinic.config import settings
from clinic.db.models import Base


def _make_engine() -> Engine:
    engine = create_engine(
        settings.db_url,
        echo=settings.debug,
        future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_pragmas(dbapi_conn, _connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


engine: Engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create schema on first run and ensure data directories exist."""
    settings.ensure_dirs()
    logger.info("Initializing database at {}", settings.db_path)
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield a session that commits on success and rolls back on error."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
