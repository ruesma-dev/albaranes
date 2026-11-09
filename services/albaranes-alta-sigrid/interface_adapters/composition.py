# interface_adapters/composition.py
"""Composition root de sv9: de ``Settings`` a ``AltaSigridService``.

ÚNICO punto que construye el servicio: todo parámetro del constructor sale de
``Settings`` (un parámetro que no llega es un interruptor silencioso; lección
de F-051). El engine de SQLAlchemy es perezoso: no conecta hasta la primera
consulta. sv9 no crea la BBDD ni el esquema (la tabla la crea sv3).
"""
from __future__ import annotations

import logging
from datetime import timedelta

from ruesma_comun.db.session_factory import SessionFactoryDesdeEngine
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from application.alta_sigrid_service import AltaSigridService
from config.settings import Settings
from domain.models.alta_models import ModoAlta
from domain.ports.pdf_port import PdfAlbaranPort
from domain.ports.sigrid_alta_port import SigridAltaPort
from domain.services.validador_alta import ConfigAlta
from infrastructure.database.sql_alta_repository import SqlAltaRepository
from infrastructure.sharepoint.pdf_sharepoint import (
    PdfSharePoint,
    SharePointAlbaranDownloader,
)
from infrastructure.sigrid.sigrid_api_alta_client import construir_desde_settings

logger = logging.getLogger(__name__)


def _pdf(settings: Settings) -> PdfAlbaranPort:
    return PdfSharePoint(SharePointAlbaranDownloader(
        graph_key=settings.graph_key,
        timeout_s=settings.graph_timeout_s,
        mode=settings.sharepoint_mode,
        hostname=settings.sharepoint_hostname,
        site_path=settings.sharepoint_site_path,
        drive_name=settings.sharepoint_drive_name,
        drive_id=settings.sharepoint_drive_id,
        folder_url=settings.sharepoint_folder_url,
    ))


def construir_servicio(
    settings: Settings,
    *,
    engine: Engine | None = None,
    sigrid: SigridAltaPort | None = None,
    pdf: PdfAlbaranPort | None = None,
) -> AltaSigridService:
    engine = engine or create_engine(settings.database_url, future=True, pool_pre_ping=True)
    return AltaSigridService(
        repo=SqlAltaRepository(SessionFactoryDesdeEngine(engine)),
        sigrid=sigrid or construir_desde_settings(settings),
        pdf=pdf or _pdf(settings),
        config=ConfigAlta(mapeo=settings.mapeo_producto, enviar_dto=settings.enviar_dto),
        usuario_respaldo=settings.usuario_respaldo,
        modo=ModoAlta(settings.modo),
        desde=settings.desde,
        espera=timedelta(minutes=settings.espera_incierto_min),
        tolerancia_eur=settings.tolerancia_eur,
        avisos_bloqueantes=settings.avisos_bloqueantes,
        equivalencias=settings.equivalencias,
    )
