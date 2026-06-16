"""Site channel inference and dashboard API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.core.exceptions import NotFoundError
from app.schemas.site import (
    ChannelEventsResponse,
    ChannelTimelineResponse,
    LocalitiesResponse,
    LteRankingResponse,
    LteUsageTimelineResponse,
    SiteDetailSchema,
    SiteListResponse,
    SitesSummarySchema,
    TrafficHistoryResponse,
)
from app.services import sites_service

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get(
    "/summary",
    response_model=SitesSummarySchema,
    summary="KPIs del dashboard de sitios",
    description=(
        "Resumen de sitios por canal (LTE/Fibra/Down) basado en inferencia "
        "de tráfico de la ventana configurada."
    ),
)
def get_sites_summary(db: DbSession) -> SitesSummarySchema:
    """KPIs para el dashboard general de sitios."""
    return sites_service.get_sites_summary(db)


@router.get(
    "",
    response_model=SiteListResponse,
    summary="Lista de sitios con canal actual",
    description=(
        "Lista todos los sitios activos del catálogo con canal inferido, "
        "métricas de tráfico y metadatos. Soporta filtros por canal, "
        "localidad y búsqueda parcial."
    ),
)
def list_sites(
    db: DbSession,
    channel: Optional[str] = Query(
        None,
        pattern="^(LTE|FIBRA|DOWN)$",
        description="Filtrar por canal actual",
    ),
    locality: Optional[str] = Query(None, description="Filtrar por localidad (exact match)"),
    search: Optional[str] = Query(None, description="Buscar en tunnel_name o site_name"),
) -> SiteListResponse:
    """Lista de sitios con canal actual y métricas."""
    return sites_service.list_sites(
        db, channel=channel, locality=locality, search=search
    )


@router.get(
    "/localities",
    response_model=LocalitiesResponse,
    summary="Localidades disponibles",
    description="Lista distinct de localidades del catálogo para filtros del frontend.",
)
def get_localities(db: DbSession) -> LocalitiesResponse:
    """Localidades para popular filtro del frontend."""
    return sites_service.get_localities(db)


@router.get(
    "/lte-usage-timeline",
    response_model=LteUsageTimelineResponse,
    summary="Timeline de uso LTE de la flota",
    description=(
        "Serie temporal del porcentaje de sitios en LTE, Fibra y Down "
        "en buckets de 15 minutos."
    ),
)
def lte_usage_timeline(
    db: DbSession,
    hours: int = Query(24, ge=1, le=168, description="Horas hacia atrás"),
) -> LteUsageTimelineResponse:
    """Porcentaje de sitios en LTE a lo largo del tiempo."""
    return sites_service.lte_usage_timeline(db, hours=hours)


@router.get(
    "/lte-ranking",
    response_model=LteRankingResponse,
    summary="Ranking de sitios por uso LTE",
    description=(
        "Top N sitios que más tiempo han pasado en LTE en los últimos N días. "
        "Útil para identificar sitios problemáticos con la fibra."
    ),
)
def lte_ranking(
    db: DbSession,
    days: int = Query(7, ge=1, le=30, description="Días hacia atrás"),
    limit: int = Query(20, ge=1, le=100, description="Cantidad de resultados"),
) -> LteRankingResponse:
    """Top sitios por minutos en LTE."""
    return sites_service.lte_ranking(db, days=days, limit=limit)


@router.get(
    "/{tunnel_name}/traffic-history",
    response_model=TrafficHistoryResponse,
    summary="Historial de tráfico del sitio",
    description="Serie temporal de tráfico con canal inferido por punto.",
)
def get_site_traffic_history(
    tunnel_name: str,
    db: DbSession,
    hours: int = Query(24, ge=1, le=168),
) -> TrafficHistoryResponse:
    """Serie temporal de tráfico para gráfica de detalle."""
    try:
        return sites_service.get_site_traffic_history(db, tunnel_name, hours=hours)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get(
    "/{tunnel_name}/channel-timeline",
    response_model=ChannelTimelineResponse,
    summary="Timeline de canal del sitio",
    description="Buckets temporales con canal inferido (LTE/Fibra/Down/Unknown).",
)
def get_site_channel_timeline(
    tunnel_name: str,
    db: DbSession,
    hours: int = Query(24, ge=1, le=168),
) -> ChannelTimelineResponse:
    """Barras LTE/Fibra/Down en el tiempo."""
    try:
        return sites_service.get_site_channel_timeline(db, tunnel_name, hours=hours)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get(
    "/{tunnel_name}/events",
    response_model=ChannelEventsResponse,
    summary="Eventos de cambio de canal",
    description="Detecta transiciones LTE↔Fibra↔Down en la ventana de tiempo.",
)
def get_site_events(
    tunnel_name: str,
    db: DbSession,
    hours: int = Query(24, ge=1, le=168),
) -> ChannelEventsResponse:
    """Eventos de cambio de canal del sitio."""
    try:
        return sites_service.get_site_events(db, tunnel_name, hours=hours)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.get(
    "/{tunnel_name}",
    response_model=SiteDetailSchema,
    summary="Detalle completo del sitio",
    description=(
        "Estado actual, catálogo, estadísticas de canal hoy y en la última semana."
    ),
)
def get_site_detail(tunnel_name: str, db: DbSession) -> SiteDetailSchema:
    """Detalle completo de un sitio."""
    try:
        return sites_service.get_site_detail(db, tunnel_name)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
