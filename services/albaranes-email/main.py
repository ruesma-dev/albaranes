# main.py
from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

from application.pipelines.polling_pipeline import PollingPipeline
from config.logging_config import configure_logging
from config.settings import Settings
from infrastructure.colas.intake_cola_adapter import IntakeColaClient
from infrastructure.document.pdf_page_splitter import PdfPageSplitter
from infrastructure.graph.mail_client import GraphMailClient
from infrastructure.graph.token_provider import GraphTokenProvider

from ruesma_comun.blobs.almacen import construir_almacen_desde_entorno
from ruesma_comun.colas.arranque import construir_publicador
from ruesma_comun.db.session_factory import SessionFactoryDesdeEngine
from ruesma_comun.workflows.orm import crear_tablas
from ruesma_comun.workflows.repositorio import RepositorioWorkflows

logger = logging.getLogger(__name__)


def main() -> int:
    # Vuelca el .env a os.environ ANTES de construir nada. Settings ya lee
    # el .env por su cuenta (pydantic-settings), pero los builders de
    # ruesma_comun (construir_almacen_desde_entorno / construir_publicador)
    # leen de os.environ, así que COLAS_CONNECTION_STRING (blobs+colas),
    # BLOBS_* etc. deben estar en el entorno. Con override=False (por
    # defecto) NO pisa variables ya definidas en la Run Config o el sistema.
    load_dotenv(Path(__file__).resolve().parent / ".env")
    settings = Settings()
    configure_logging(Path(settings.log_dir), settings.log_level)
    logger.info("Arranque email-albaranes-ingestor (modo colas)")
    logger.info(
        "mailbox=%s poll=%ss source_folder=%s",
        settings.mailbox_address,
        settings.poll_interval_s,
        settings.source_folder,
    )

    # --- Buzón M365 (Microsoft Graph) — sin cambios ---
    token_provider = GraphTokenProvider(
        settings.graph_key,
        timeout_s=settings.graph_timeout_s,
    )
    mailbox = GraphMailClient(
        token_provider=token_provider,
        timeout_s=settings.graph_timeout_s,
    )

    # --- Intake por colas: workflow_runs (dedup) + blob input/ + q-extraccion ---
    engine = create_engine(
        settings.database_url, future=True, pool_pre_ping=True
    )
    crear_tablas(engine)  # DDL idempotente de workflow_runs.
    repositorio = RepositorioWorkflows(SessionFactoryDesdeEngine(engine))
    almacen = construir_almacen_desde_entorno()
    publicador = construir_publicador(emitido_por="ca-sv1-intake")
    orchestrator = IntakeColaClient(
        repositorio=repositorio,
        almacen=almacen,
        publicador=publicador,
    )

    PollingPipeline(
        mailbox=mailbox,
        orchestrator=orchestrator,
        pdf_splitter=PdfPageSplitter(),
    ).run_forever(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
