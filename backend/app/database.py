"""Database helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import Settings
from .models import Base


def create_engine_from_settings(settings: Settings, *, testing: bool = False):
    """Create an SQLAlchemy engine based on app settings."""
    database_url = settings.database_url
    connect_args = {}
    engine_kwargs = {"future": True}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if testing:
            engine_kwargs["poolclass"] = StaticPool
            database_url = "sqlite+pysqlite:///:memory:"

    engine = create_engine(database_url, connect_args=connect_args, **engine_kwargs)
    return engine


def create_session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


@contextmanager
def session_scope(SessionLocal) -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database(engine):
    Base.metadata.create_all(engine)
