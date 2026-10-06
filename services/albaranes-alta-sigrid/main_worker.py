# main_worker.py
"""Entrypoint del WORKER de sv9 (ca-sv9-alta-sigrid, F-053).

Consume ``q-feedback`` (``MensajeFeedback``: ``document_id``, ``accion``) y da
de alta en Sigrid los albaranes aprobados vía sigrid-api. Sin HTTP propio.

Variables: las de ``config/settings.py`` (``ALTA_SIGRID_*``, ``SIGRID_API_*``,
``PG_*``, ``GRAPH_KEY``/``SHAREPOINT_*``) y las de colas
(``COLAS_CONNECTION_STRING`` en local/Azurite o ``COLAS_ACCOUNT_URL`` en la
nube). Al arrancar deja en el log el modo (``simulacion``/``real``) y DESDE.
Una configuración que no se puede leer (p. ej. el mapeo de productos sin
``*``, R44) NO arranca y dice por qué.

Máximo UNA réplica (KEDA, infra): la grabación no admite dos workers a la vez.
"""
from __future__ import annotations

import logging
from pathlib import Path

from pydantic import ValidationError
from ruesma_comun.colas import COLA_FEEDBACK
from ruesma_comun.colas.arranque import ejecutar_worker

from config.logging_config import configure_logging
from config.settings import Settings
from interface_adapters.composition import construir_servicio
from interface_adapters.worker.alta_worker import construir_handler_alta

logger = logging.getLogger(__name__)

NOMBRE_WORKER = "ca-sv9-alta-sigrid"


def _cargar_entorno() -> None:
    """Solo el ``.env`` de sv9 (en local); en Azure, las variables del recurso."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(Path(__file__).resolve().parent / ".env")


def main() -> int:
    _cargar_entorno()
    try:
        settings = Settings()
    except ValidationError as exc:
        logging.basicConfig(level=logging.INFO)
        logger.error("[%s] configuración inválida, no arranco: %s", NOMBRE_WORKER, exc)
        return 2

    configure_logging(Path(settings.log_dir), settings.log_level)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logger.info(
        "[%s] modo=%s desde=%s espera_min=%s tolerancia_eur=%s avisos_bloqueantes=%s",
        NOMBRE_WORKER, settings.modo, settings.desde, settings.espera_incierto_min,
        settings.tolerancia_eur, sorted(settings.avisos_bloqueantes),
    )
    if settings.desde is None:
        logger.warning("[%s] ALTA_SIGRID_DESDE_UTC vacía: confirmo los mensajes sin hacer nada",
                       NOMBRE_WORKER)
    if settings.commit_real:
        logger.warning("[%s] MODO REAL: las altas se GRABAN en Sigrid", NOMBRE_WORKER)
    if settings.desde is not None and not settings.usuario:
        logger.warning("[%s] ALTA_SIGRID_USUARIO vacío: sigrid-api rechazará las altas",
                       NOMBRE_WORKER)

    servicio = construir_servicio(settings)
    return ejecutar_worker(
        nombre_cola=COLA_FEEDBACK,
        tipo_mensaje="feedback",
        handler=construir_handler_alta(servicio=servicio),
        emitido_por=NOMBRE_WORKER,
    )


if __name__ == "__main__":
    raise SystemExit(main())
