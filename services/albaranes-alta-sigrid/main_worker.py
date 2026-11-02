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

Visibilidad de la cola (review fase 1 · O1): por encima del peor caso de UN
mensaje, calculado con los timeouts de la configuración. Con 600 s (el defecto
común), un mensaje que acaba pasados los 10 min volvería a entregarse.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path

from pydantic import ValidationError
from ruesma_comun.colas import COLA_FEEDBACK
from ruesma_comun.colas.arranque import ejecutar_worker
from ruesma_comun.configuracion import motivos_configuracion

from config.logging_config import configure_logging
from config.settings import Settings
from domain.services.usuario_sigrid import VARIABLE_LISTA
from infrastructure.sigrid.sigrid_api_alta_client import (
    ESPERA_BASE_S,
    ESPERA_MAX_S,
    INTENTOS_POR_DEFECTO,
    TIMEOUT_GRABACION_S,
)
from interface_adapters.composition import construir_servicio
from interface_adapters.worker.alta_worker import construir_handler_alta

logger = logging.getLogger(__name__)

NOMBRE_WORKER = "ca-sv9-alta-sigrid"

#: Token de Graph (``ruesma_comun.graph.token_provider.GraphTokenProvider``):
#: intentos y tope de la espera entre ellos. Un test los ata a comun.
GRAPH_TOKEN_INTENTOS = 5
GRAPH_TOKEN_ESPERA_MAX_S = 20.0
#: Peticiones Graph de una descarga en el peor modo (``site_path``): sitio,
#: drive, descarga y su redirección.
GRAPH_PETICIONES_DESCARGA = 4
#: Holgura sobre el peor caso: BBDD (reclamar, leer, guardar) y arranque.
MARGEN_VISIBILIDAD_S = 300


def _con_reintentos_s(timeout_s: float) -> float:
    """Una llamada a sigrid-api con reintentos (R24): cada intento acotado por
    su timeout y, entre intentos, la espera exponencial de tenacity."""
    esperas = sum(
        min(ESPERA_MAX_S, ESPERA_BASE_S * 2 ** (n - 1)) for n in range(1, INTENTOS_POR_DEFECTO)
    )
    return INTENTOS_POR_DEFECTO * timeout_s + esperas


#: F-069 R19: lecturas de la resolución de una petición nueva, cada una con sus
#: reintentos: ``dbo.usu`` (Entrada y Login) y ``dbo.emp`` (Entrada y correo).
LECTURAS_RESOLUCION = 4


def peor_caso_mensaje_s(settings: Settings) -> float:
    """Peor caso de UN mensaje en modo real: las lecturas de la resolución
    (F-069 R19), lectura de R14, previa, grabación (una vez), PDF desde
    SharePoint y adjunto."""
    sigrid = _con_reintentos_s(settings.sigrid_api_timeout_s)
    token = (GRAPH_TOKEN_INTENTOS * settings.graph_timeout_s
             + (GRAPH_TOKEN_INTENTOS - 1) * GRAPH_TOKEN_ESPERA_MAX_S)
    pdf = token + GRAPH_PETICIONES_DESCARGA * settings.graph_timeout_s
    resolucion = LECTURAS_RESOLUCION * sigrid
    return resolucion + sigrid + sigrid + TIMEOUT_GRABACION_S + pdf + sigrid


def visibilidad_cola_s(settings: Settings) -> int:
    """Peor caso más el margen, redondeado al minuto (2460 s con los defectos)."""
    return int(math.ceil((peor_caso_mensaje_s(settings) + MARGEN_VISIBILIDAD_S) / 60) * 60)


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
        logger.error("[%s] configuración inválida, no arranco: %s", NOMBRE_WORKER,
                     motivos_configuracion(exc))
        return 2

    configure_logging(Path(settings.log_dir), settings.log_level)
    logging.getLogger("azure").setLevel(logging.WARNING)
    visibilidad_s = visibilidad_cola_s(settings)
    logger.info(
        "[%s] modo=%s desde=%s espera_min=%s tolerancia_eur=%s avisos_bloqueantes=%s "
        "visibilidad_s=%s",
        NOMBRE_WORKER, settings.modo, settings.desde, settings.espera_incierto_min,
        settings.tolerancia_eur, sorted(settings.avisos_bloqueantes), visibilidad_s,
    )
    # F-110 R5: si la petición lleva el ``dto`` de las líneas con descuento.
    logger.info("[%s] ALTA_SIGRID_ENVIAR_DTO %s", NOMBRE_WORKER,
                "encendida: las líneas con descuento van con precio bruto y dto"
                if settings.enviar_dto else "apagada: precio neto, sin dto (F-106)")
    # F-069 R3: solo el número (las Entradas son excepciones; vacía es lo normal).
    logger.info("[%s] Lista de equivalencias (%s): %s Entradas", NOMBRE_WORKER,
                VARIABLE_LISTA, len(settings.equivalencias))
    if settings.desde is None:
        logger.warning("[%s] ALTA_SIGRID_DESDE_UTC vacía: confirmo los mensajes sin hacer nada",
                       NOMBRE_WORKER)
    if settings.commit_real:
        logger.warning("[%s] MODO REAL: las altas se GRABAN en Sigrid", NOMBRE_WORKER)
    if settings.desde is not None and not settings.usuario_respaldo.strip():
        logger.warning(
            "[%s] ALTA_SIGRID_USUARIO_RESPALDO vacío: las altas de quien no case con un "
            "login de Sigrid irán a error (usuario_no_resuelto, R48)", NOMBRE_WORKER,
        )

    servicio = construir_servicio(settings)
    return ejecutar_worker(
        nombre_cola=COLA_FEEDBACK,
        tipo_mensaje="feedback",
        handler=construir_handler_alta(servicio=servicio),
        emitido_por=NOMBRE_WORKER,
        visibilidad_s=visibilidad_s,
    )


if __name__ == "__main__":
    raise SystemExit(main())
