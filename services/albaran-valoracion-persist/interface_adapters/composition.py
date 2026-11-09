# interface_adapters/composition.py
"""Composition root del WORKER de valoración (ca-valorador, sv5+sv6).

Replica el wiring de ``build_app`` (interface_adapters/api/app.py) pero SOLO
en lo que necesita el pipeline de valoración, omitiendo los endpoints FastAPI.
Este módulo es la entrada para el modo worker (consumidor de q-valoracion).
(F-076) ``construir_normalizador_partidas`` lo usan los DOS puntos de entrada:
el worker y ``build_app``. (F-111) ``construir_asignador_partida_residuos``,
también; los dos comparten la MISMA caché de partidas por proceso
(:func:`_puerto_partidas_obra`), así una obra se lee de sigrid-api una vez.

Igual que en HTTP, ``RunValuationPipeline`` llama al servicio 5 por HTTP
(``HttpValuationIaClient`` → ``VALUATION_API_BASE_URL``). En el piloto local,
sv5 sigue corriendo como su propio FastAPI; en despliegue ambos viven en el
mismo contenedor 'ca-valorador' y se hablan por localhost.
"""
from __future__ import annotations

import logging

from application.pipelines.run_valuation_pipeline import RunValuationPipeline
from application.services.almacen_politica import familias_destinadas_de_csv
from application.services.importe_calculator import ImporteCalculator
from application.services.normalizador_partidas import (
    MOTIVO_PARTIDAS_NO_DISPONIBLES,
    NormalizadorPartidas,
)
from application.services.partida_matcher import PartidaMatcher
from application.services.partida_residuos import (
    MOTIVO_SIN_LISTA,
    AsignadorPartidaResiduos,
)
from application.services.price_reconciler import PriceReconciler
from application.services.unit_category_guard import UnitCategoryGuard
from application.services.unit_converter import UnitConverter
from application.services.valuation_builder import ValuationBuilder
from config.settings import Settings
from infrastructure.clients.http_conciliacion_client import (
    HttpConciliacionClient,
)
from infrastructure.clients.http_partida_residuos_client import (
    HttpPartidaResiduosClient,
)
from infrastructure.clients.http_valuation_ia_client import (
    HttpValuationIaClient,
)
from infrastructure.database.schema_drift_check import (
    check_drift,
    log_drift_report,
)
from infrastructure.database.session_factory import SessionFactory
from infrastructure.database.sqlalchemy_valuation_repository import (
    SqlAlchemyValuationRepository,
)
from infrastructure.sigrid.sigrid_api_lector import SigridApiLector
from infrastructure.units.yaml_unit_registry import YamlUnitRegistry
from ruesma_comun.sigrid import CachePartidasObra

logger = logging.getLogger(__name__)

#: (F-111 R30) Una caché de partidas por configuración y proceso, compartida por
#: el normalizador (F-076) y el asignador de residuos (F-111).
_PUERTOS_COMPARTIDOS: dict[tuple, CachePartidasObra] = {}


def _puerto_partidas_obra(settings: Settings) -> CachePartidasObra:
    """El lector de sigrid-api y su caché, uno por configuración (R30).

    Solo se llama con ``sigrid_api_configurada``. La clave va en memoria, nunca
    al log.
    """
    clave = (
        settings.sigrid_api_base_url, settings.sigrid_api_function_key,
        settings.sigrid_api_database, settings.sigrid_api_timeout_s,
        settings.partidas_obra_ttl_s, settings.partidas_obra_max_obras,
        settings.partidas_obra_fallo_ttl_s,
    )
    if clave not in _PUERTOS_COMPARTIDOS:
        lector = SigridApiLector(
            base_url=settings.sigrid_api_base_url or "",
            function_key=settings.sigrid_api_function_key or "",
            database=settings.sigrid_api_database or "",
            timeout_s=settings.sigrid_api_timeout_s,
        )
        _PUERTOS_COMPARTIDOS[clave] = CachePartidasObra(
            lector,
            ttl_s=settings.partidas_obra_ttl_s,
            max_obras=settings.partidas_obra_max_obras,
            ttl_fallo_s=settings.partidas_obra_fallo_ttl_s,
        )
    return _PUERTOS_COMPARTIDOS[clave]


def construir_asignador_partida_residuos(settings: Settings) -> AsignadorPartidaResiduos:
    """(F-111 R29, R33) El asignador de partida de residuos.

    Encendido: la caché compartida con F-076 (si sigrid-api está configurado;
    si no, puerto ``None``, WARNING y las líneas a revisión con
    ``partida_residuos_sin_lista``) y el cliente de sv5 para elegir entre
    varias candidatas. Apagado: ni puerto ni cliente.
    """
    if not settings.partida_residuos_enabled:
        logger.info(
            "[svc6][wiring] F-111 partida de residuos APAGADA "
            "(PARTIDA_RESIDUOS_ENABLED=false)."
        )
        return AsignadorPartidaResiduos(
            partidas=None, elector=None,
            alm_codigo_partida=settings.alm_codigo_partida, activo=False,
        )
    puerto = None
    if settings.sigrid_api_configurada:
        puerto = _puerto_partidas_obra(settings)
    else:
        logger.warning(
            "[svc6][wiring] F-111: faltan SIGRID_API_BASE_URL, "
            "SIGRID_API_FUNCTION_KEY o SIGRID_API_DATABASE; las líneas de "
            "residuos sin partida irán a revisión (%s).",
            MOTIVO_SIN_LISTA,
        )
    logger.info("[svc6][wiring] F-111 partida de residuos ENCENDIDA.")
    return AsignadorPartidaResiduos(
        partidas=puerto,
        elector=HttpPartidaResiduosClient(
            base_url=settings.valuation_api_base_url,
            timeout_s=settings.valuation_api_timeout_s,
        ),
        alm_codigo_partida=settings.alm_codigo_partida,
        activo=True,
    )


def construir_normalizador_partidas(settings: Settings) -> NormalizadorPartidas:
    """(F-076 R11, R12, R17) El normalizador de partidas de la obra.

    Lector de sigrid-api y caché por proceso SOLO si el interruptor está
    encendido y hay URL, clave y base de datos. Sin ellas, puerto ``None`` y
    WARNING al arrancar: se valora como siempre, con el motivo de cabecera
    ``partidas_obra_no_disponibles``. Apagado: ni lector ni caché.
    """
    puerto = None
    if not settings.partidas_obra_normalizar_enabled:
        logger.info(
            "[svc6][wiring] F-076 normalizar partidas APAGADO "
            "(PARTIDAS_OBRA_NORMALIZAR_ENABLED=false)."
        )
    elif not settings.sigrid_api_configurada:
        logger.warning(
            "[svc6][wiring] F-076: faltan SIGRID_API_BASE_URL, "
            "SIGRID_API_FUNCTION_KEY o SIGRID_API_DATABASE; se valora sin "
            "normalizar la partida (%s).",
            MOTIVO_PARTIDAS_NO_DISPONIBLES,
        )
    else:
        puerto = _puerto_partidas_obra(settings)
        logger.info(
            "[svc6][wiring] F-076 normalizar partidas ENCENDIDO: ttl=%ss "
            "max_obras=%s fallo=%ss",
            settings.partidas_obra_ttl_s,
            settings.partidas_obra_max_obras,
            settings.partidas_obra_fallo_ttl_s,
        )
    return NormalizadorPartidas(
        partidas=puerto,
        alm_codigo_partida=settings.alm_codigo_partida,
        activo=settings.partidas_obra_normalizar_enabled,
        equivalente=settings.partida_equivalente_enabled,  # F-117 R19
    )


def build_run_valuation_pipeline(settings: Settings) -> RunValuationPipeline:
    """Construye el ``RunValuationPipeline`` con el mismo cableado que HTTP.

    Pasos (idénticos a ``build_app``, sin la capa FastAPI):
      1. SessionFactory + repository, e init ANSIOSO del schema (tolerante:
         si falla, cae a init perezosa — la primera valoración reintenta).
      2. Chequeo de drift ORM↔BBDD (solo informativo), si está habilitado.
      3. HttpValuationIaClient contra el servicio 5.
      4. ValuationBuilder con sus reglas deterministas.
      5. RunValuationPipeline(ia_client, repository, builder).
    """
    session_factory = SessionFactory(database_url=settings.database_url)
    repository = SqlAlchemyValuationRepository(session_factory)

    try:
        repository.initialize()
    except Exception:
        logger.warning(
            "[ca-valorador][worker-wiring] No se pudo inicializar el schema "
            "en arranque (¿BBDD no disponible? ¿tablas externas de sv3 aún "
            "no creadas?). Caemos a inicialización perezosa: la primera "
            "valoración reintentará.",
            exc_info=True,
        )

    if settings.schema_drift_check_enabled:
        try:
            report = check_drift(session_factory.engine, only_owned=True)
            log_drift_report(report, service_label="ca-valorador")
        except Exception:
            logger.exception(
                "[ca-valorador][worker-wiring] error ejecutando "
                "schema_drift_check (no crítico, seguimos)."
            )

    ia_client = HttpValuationIaClient(
        base_url=settings.valuation_api_base_url,
        timeout_s=settings.valuation_api_timeout_s,
    )
    conciliacion_client = HttpConciliacionClient(
        base_url=settings.valuation_api_base_url,
        timeout_s=settings.valuation_api_timeout_s,
    )

    unit_registry = YamlUnitRegistry(settings.unit_registry_yaml_path)

    builder = ValuationBuilder(
        unit_category_guard=UnitCategoryGuard(unit_registry=unit_registry),
        price_reconciler=PriceReconciler(
            tolerance_pct=settings.price_tolerance_pct,
        ),
        partida_matcher=PartidaMatcher(
            alm_codigo_partida=settings.alm_codigo_partida,
            # F-051 (R1, R8): sin partida en el albarán ⇒ almacén.
            almacen_sin_partida=settings.almacen_sin_partida_enabled,
        ),
        unit_converter=UnitConverter(registry=unit_registry),
        importe_calculator=ImporteCalculator(
            tolerance_pct=settings.importe_tolerance_pct,
        ),
        # F-051 (R4, R9): familias destinadas (revisión no bloqueante).
        familias_destinadas=familias_destinadas_de_csv(
            settings.familias_destinadas,
        ),
    )

    pipeline = RunValuationPipeline(
        ia_client=ia_client,
        repository=repository,
        builder=builder,
        conciliacion_client=conciliacion_client,
        # F-076: normalizar la partida contra las de la obra.
        normalizador=construir_normalizador_partidas(settings),
        # F-111: residuos sin partida ⇒ capítulo de gestión de residuos.
        asignador_residuos=construir_asignador_partida_residuos(settings),
    )
    logger.info(
        "[ca-valorador][worker-wiring] pipeline construido; "
        "sv5_base_url=%s schema_ready=%s",
        settings.valuation_api_base_url,
        repository.is_initialized,
    )
    return pipeline
