"""FortiGate VPN Monitor — FastAPI application entry point."""

import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, internal, metrics, sites, tunnels
from app.config import settings
from app.core.logging import get_logger, setup_logging

# Apply timezone before any datetime operations in this process
os.environ["TZ"] = settings.TZ
if hasattr(time, "tzset"):
    time.tzset()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: logging, scheduler init/shutdown."""
    setup_logging()
    logger.info(
        "application_starting",
        environment=settings.ENVIRONMENT,
        scheduler_enabled=settings.SCHEDULER_ENABLED,
    )

    if not settings.FORTIGATE_VERIFY_SSL:
        logger.warning(
            "fortigate_ssl_verification_disabled",
            message="FORTIGATE_VERIFY_SSL=false — acceptable for lab, use CA cert in production",
        )

    scheduler = None
    if settings.SCHEDULER_ENABLED:
        # Guard against double scheduler when uvicorn reloads or multiple workers
        # are accidentally started. Production MUST use --workers 1 because
        # APScheduler runs in-process and duplicate workers = duplicate snapshots.
        existing = getattr(app.state, "scheduler", None)
        if existing is not None and existing.running:
            logger.warning("scheduler_already_running", action="skipping_init")
        else:
            from app.jobs.scheduler import start_scheduler

            scheduler = start_scheduler()
            app.state.scheduler = scheduler
            logger.info("scheduler_iniciado")

    yield

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tunnels.router)
app.include_router(metrics.router)
app.include_router(sites.router)
app.include_router(internal.router)
