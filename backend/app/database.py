"""Database engine and session management."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.base import Base


def _build_connect_args() -> dict:
    """Build PyMySQL connect_args, including RDS SSL when configured."""
    if not settings.DATABASE_SSL_CA:
        return {}
    ca_path = Path(settings.DATABASE_SSL_CA)
    if not ca_path.is_file():
        return {}
    return {"ssl": {"ca": str(ca_path)}}


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    connect_args=_build_connect_args(),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
