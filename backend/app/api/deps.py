"""Shared FastAPI dependencies."""

from typing import Annotated, Generator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db as _get_db

DbSession = Annotated[Session, Depends(_get_db)]


def verify_internal_token(
    x_internal_token: Annotated[str | None, Header()] = None,
) -> None:
    """Validate the internal cron token for protected endpoints."""
    if not settings.INTERNAL_CRON_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal token not configured",
        )
    if x_internal_token != settings.INTERNAL_CRON_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )
