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
    _apply_light_migrations()


def _apply_light_migrations() -> None:
    """Idempotent, forward-only column additions for pre-Alembic upgrades.

    ``create_all`` only creates missing tables; it never adds columns to
    existing ones. Each block below inspects ``PRAGMA table_info`` and
    issues an ``ALTER TABLE ADD COLUMN`` when needed, so upgrades don't
    require the operator to delete their database.
    """
    from sqlalchemy import text

    def _columns(conn, table: str) -> set[str]:
        rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
        return {row[1] for row in rows}

    with engine.begin() as conn:
        if "cashier_records" in Base.metadata.tables:
            cols = _columns(conn, "cashier_records")
            if "payment_type" not in cols:
                conn.execute(text(
                    "ALTER TABLE cashier_records "
                    "ADD COLUMN payment_type VARCHAR(16) NOT NULL DEFAULT 'cash'"
                ))
                logger.info("Migration: added cashier_records.payment_type")


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
