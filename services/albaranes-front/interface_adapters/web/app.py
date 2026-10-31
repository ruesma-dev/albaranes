# interface_adapters/web/app.py
from __future__ import annotations

import calendar
import html
import json
import logging
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from fastapi import Body, FastAPI, Form, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from application.services.busqueda_contratos import aviso_de_guardado
from application.services.review_service import ReviewService
from config.settings import Settings
from domain.models.alta_sigrid_models import (
    AlbaranBloqueadoError,
    AlbaranSinValorarError,
    ValoracionDeOtroContratoError,
)
from domain.models.contrato_refetch_models import ContratoRefetchOutcome
from domain.models.review_models import (
    AlbaranAprobadoError,
    CabeceraIncompletaError,
    ConciliacionEditBody,
    ConciliacionOverridePayload,
    DivisionBody,
    DocumentDetailPayload,
    DocumentListFilters,
    FechaAlbaranNoValidaError,
    HealthResponse,
    LineaBloqueadaError,
    LineasIncompletasError,
    MergeDocumentUpdatePayload,
    NumeroAlbaranNoValidoError,
    RepartoInvalido,
    SaveResponse,
    TraerLineasBody,
    ValoracionCambiadaError,
    VIEW_MODE_MERGE,
    normalize_view_mode,
)
from domain.ports.contrato_refetch_port import ContratoRefetchClient
from domain.services.fecha_albaran import fecha_para_ver
from domain.ports.orchestrator_port import OrchestratorClient
from infrastructure.database.review_repository import AlbaranReviewRepository
from infrastructure.database.session_factory import SessionFactory
from infrastructure.database.workflow_runs_purger import WorkflowRunsPurger
from infrastructure.graph.token_provider import GraphTokenProvider
from infrastructure.colas.colas_orchestrator_client import ColasOrchestratorClient
from infrastructure.colas.colas_refetch_client import ColasRefetchClient
from infrastructure.sigrid.sigrid_lookup_client import (
    MINIMO_BUSQUEDA_PROVEEDOR,
    SigridLookupClient,
    opciones_partida,
)
from infrastructure.sigrid.sigrid_api_contrato_client import (
    SigridApiContratoClient,
)
from infrastructure.sigrid.local_refetch_client import (
    LocalContratoRefetchClient,
)
from ruesma_comun.colas import construir_publicador
from ruesma_comun.colas.arranque import ConfiguracionColasAusenteError
from ruesma_comun.colas.publicador import PublicadorBestEffort
from ruesma_comun.edicion_manual import NoDespejable, PrecioEImporte
from ruesma_comun.sigrid import CachePartidasObra

logger = logging.getLogger(__name__)


VIEW_LABELS = {
    VIEW_MODE_MERGE: "Consolidado (merge)",
    "openai": "OpenAI",
    "gemini": "Gemini",
    "claude": "Claude",
}


def _view_label(view_mode: str) -> str:
    return VIEW_LABELS.get(view_mode, view_mode.replace("_", " ").title())


# ------------------------------------------------------------------ #
# Filtros Jinja2 para formatear en servidor.
# ------------------------------------------------------------------ #
def _format_fecha_int_iso(value: Any) -> str:
    """INT YYYYMMDD (20260115) -> 'YYYY-MM-DD' (2026-01-15). 0/None -> '—'."""
    if value is None or value == "" or value == 0 or value == "0":
        return "—"
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "—"
    if n < 1_000_00_01 or n > 9999_12_31:
        return "—"
    year = n // 10000
    month = (n // 100) % 100
    day = n % 100
    if month < 1 or month > 12 or day < 1 or day > 31:
        return "—"
    return f"{year:04d}-{month:02d}-{day:02d}"


def _format_importe_eur(value: Any) -> str:
    """float -> '335.370,42 €' (locale es-ES determinista). None/'' -> '—'."""
    if value is None or value == "":
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    formatted = "{:,.2f}".format(number)
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"


def _madrid_local(dt_utc: datetime) -> datetime:
    """UTC aware -> hora local de Madrid (CET/CEST) aplicando la regla DST
    de la UE, SIN depender de la base de datos de zonas (tzdata): así
    funciona igual en local y en Azure Functions. DST: del último domingo
    de marzo (01:00 UTC) al último domingo de octubre (01:00 UTC) -> UTC+2;
    el resto del año -> UTC+1.
    """
    def _last_sunday_0100(year: int, month: int) -> datetime:
        last_day = calendar.monthrange(year, month)[1]
        d = datetime(year, month, last_day, 1, 0, tzinfo=timezone.utc)
        # weekday(): lunes=0 … domingo=6. Retrocede hasta el domingo.
        return d - timedelta(days=(d.weekday() - 6) % 7)

    year = dt_utc.year
    dst_start = _last_sunday_0100(year, 3)
    dst_end = _last_sunday_0100(year, 10)
    offset_h = 2 if dst_start <= dt_utc < dst_end else 1
    return dt_utc + timedelta(hours=offset_h)


def _format_fecha_hora_local(value: Any) -> str:
    """ISO UTC ('2026-03-09T13:32:45.123+00:00') -> 'DD/MM/YYYY HH:MM' en
    hora de Madrid. Vacío / None / no parseable -> '' (cadena vacía, para
    que la plantilla pueda omitir la línea).
    """
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).strip())
    except (TypeError, ValueError):
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return _madrid_local(dt).strftime("%d/%m/%Y %H:%M")


def _format_fecha_local(value: Any) -> str:
    """ISO UTC -> 'DD/MM/YYYY' en hora de Madrid ('' si no parsea).
    (jul 2026) Para la columna 'Fecha recepcion' de la bandeja."""
    txt = _format_fecha_hora_local(value)
    return txt.split(" ")[0] if txt else ""


def _format_hora_local(value: Any) -> str:
    """ISO UTC -> 'HH:MM' en hora de Madrid ('' si no parsea)."""
    txt = _format_fecha_hora_local(value)
    return txt.split(" ")[1] if txt and " " in txt else ""


# NOTA REFACTOR (mayo 2026): se eliminó aquí
# ``_build_contrato_pdf_storage`` y todos los imports/clases asociadas
# (SharePointContratoPdfStorage, SigridApiContratoClient,
# ContratoRefetchService local). El sv4 ya NO descarga ni sube PDFs
# de contrato — esa responsabilidad la tiene íntegramente el sv3,
# que lo hace durante el refetch (a través del endpoint
# /v1/albaranes/{id}/re-fetch-contratos). El sv4 solo conserva la
# preview del PDF del albarán propio, no del contrato asociado.


class ProductoSigridBody(BaseModel):
    """(F-053 R41) Body del POST del producto de una línea sin vincular:
    el código elegido o ``null`` = por defecto. A nivel de módulo por lo
    mismo que ``ConciliacionEditBody``."""

    producto: str | None = None


#: (F-053 R30, R28) Mensaje de la ficha según lo que pasó al pedir el alta.
MENSAJES_ALTA = {
    "alta": {
        "pedida": "Alta en Sigrid pedida: refresca en unos segundos para ver el resultado.",
        "no_publicada": "El alta en Sigrid no se pudo pedir (cola no disponible): reintenta.",
        "no_procede": "El alta en Sigrid no procede ahora (mira su estado en la ficha).",
        "apagada": "El alta en Sigrid está desactivada (ALTA_SIGRID_DESDE_UTC vacía).",
    },
    "reintentar_adjunto": {
        "pedida": "Reintento del adjunto pedido: refresca en unos segundos para ver el resultado.",
        "no_publicada": "El reintento del adjunto no se pudo pedir (cola no disponible): reintenta.",
        "no_procede": "El reintento del adjunto no procede (mira el estado del alta en la ficha).",
        "apagada": "El alta en Sigrid está desactivada (ALTA_SIGRID_DESDE_UTC vacía).",
    },
    "verificar_anulacion": {
        "pedida": (
            "Comprobación pedida: si ya no está en Sigrid, el alta pasará a «anulado». "
            "Refresca en unos segundos."
        ),
        "no_publicada": "La comprobación no se pudo pedir (cola no disponible): reintenta.",
        "no_procede": "La comprobación no procede: el alta no está registrada en Sigrid.",
        "apagada": "El alta en Sigrid está desactivada (ALTA_SIGRID_DESDE_UTC vacía).",
    },
}

#: (F-053 R41) Por qué no se guardó el producto (400).
MENSAJES_PRODUCTO = {
    "no_admitido": "Producto no admitido: elige uno de la lista.",
    "linea_ajena": "La línea no es de este albarán.",
    "vinculada": "La línea está vinculada al contrato: lleva el producto de su línea de contrato.",
    "apagada": "El alta en Sigrid está desactivada (ALTA_SIGRID_DESDE_UTC vacía).",
}


def _a_la_ficha(document_id: str, texto: str) -> RedirectResponse:
    """Vuelve a la ficha del documento con un mensaje."""
    return RedirectResponse(
        url=f"/documents/{document_id}?{urlencode({'message': texto})}",
        status_code=303,
    )


def _redirigir_a_lista(redirect_query: str, texto: str) -> RedirectResponse:
    """Vuelve a la bandeja con sus filtros y un mensaje."""
    query = redirect_query.strip()
    message = urlencode({"message": texto})
    if query:
        return RedirectResponse(
            url=f"/documents?{query}&{message}".replace("?&", "?"),
            status_code=303,
        )
    return RedirectResponse(url=f"/documents?{message}", status_code=303)


class _PublicadorColasNulo:
    """Publicador no-op para correr el portal en LOCAL sin colas (sin
    Azurite ni workers): ``solo-front``.

    Cumple la MISMA interfaz que ``PublicadorBestEffort`` (``.publicar(...)``
    devuelve ``bool``) y SIEMPRE devuelve ``False``: el dato fundamental ya
    se persiste en BBDD antes de publicar, y los endpoints informan con
    honestidad de que no se encoló (no dicen "encolada" si no lo está). Se
    usa solo como fallback cuando NO hay ``COLAS_CONNECTION_STRING`` ni
    ``COLAS_ACCOUNT_URL`` en el entorno; en producción JAMÁS se usa (allí
    ``COLAS_ACCOUNT_URL`` está definida por el Container App).
    """

    def publicar(self, nombre_cola: str, mensaje: Any) -> bool:
        logger.warning(
            "[colas] publicador NULO (modo solo-front): descarto mensaje "
            "tipo=%s document_id=%s -> %s. Define COLAS_CONNECTION_STRING "
            "(local) o COLAS_ACCOUNT_URL (nube) para encolar de verdad.",
            getattr(mensaje, "tipo", "?"),
            getattr(mensaje, "document_id", "?"),
            nombre_cola,
        )
        return False


def build_app(settings: Settings) -> FastAPI:
    session_factory = SessionFactory(
        database_url=settings.database_url,
        admin_database_url=settings.admin_database_url,
        target_database_name=settings.pg_db,
        auto_create_database=settings.auto_create_database,
    )
    repository = AlbaranReviewRepository(session_factory)

    app = FastAPI(
        title=settings.app_title,
        version=settings.service_version,
    )
    app.state.settings = settings
    app.state.graph_token_provider = (
        GraphTokenProvider(settings.graph_key, settings.graph_timeout_s)
        if settings.preview_enabled and settings.graph_key
        else None
    )

    # ------------------------------------------------------------------ #
    # Publicador de COLAS (sustituye a los clientes HTTP a sv7 y sv3).
    #
    # ``construir_publicador`` lee del ENTORNO:
    #   - COLAS_ACCOUNT_URL        (managed identity en Azure), o
    #   - COLAS_CONNECTION_STRING  (local/Azurite).
    # Se envuelve en PublicadorBestEffort: el dato fundamental
    # (selected_contrato_codigo, approved=true, hard-delete) YA está en
    # BBDD antes de publicar; el mensaje es solo el disparador y su
    # pérdida es recuperable a mano. Si no publica, el endpoint informa
    # al revisor con honestidad (no dice "encolada" si no lo está).
    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    # FALLBACK solo-front (jun 2026): si NO hay COLAS_* en el entorno, el
    # portal arranca igualmente con un publicador NULO. Asi puedes correr
    # SOLO el front (uvicorn / main.py) contra el Postgres de dev para
    # iterar la UI, SIN Azurite ni workers. Las acciones que encolan
    # (valorar/refetch/aprobar) no enviaran mensajes — el dato se guarda en
    # BBDD y el endpoint lo dice con honestidad. En produccion siempre hay
    # COLAS_ACCOUNT_URL, asi que se usa el publicador real.
    # ------------------------------------------------------------------ #
    try:
        publicador = PublicadorBestEffort(
            construir_publicador(emitido_por="ca-sv4-front")
        )
    except ConfiguracionColasAusenteError:
        logger.warning(
            "[colas][wiring] COLAS_* no configuradas -> publicador NULO "
            "(modo solo-front, sin Azurite ni workers). El portal arranca y "
            "guarda en BBDD; las acciones que encolan no enviaran mensajes. "
            "Define COLAS_CONNECTION_STRING (local) o COLAS_ACCOUNT_URL (nube) "
            "para activarlas."
        )
        publicador = _PublicadorColasNulo()

    # Re-fetch de contratos (antes Sv3RefetchClient → sv3 HTTP síncrono).
    # Ahora re-publica q-persistencia con force=True (sv3 re-ejecuta su
    # enrichment con force_refetch=True). ASÍNCRONO: el outcome lleva
    # status="queued" y el front debe avisar "refresca en unos segundos".
    sv3_refetch_client: ContratoRefetchClient = ColasRefetchClient(
        publicador=publicador,
    )
    # ------------------------------------------------------------------ #
    # FALLBACK solo-front (jun 2026): si NO hay colas (publicador NULO)
    # pero SÍ hay credenciales Sigrid, el re-fetch de contratos se hace
    # LOCAL y SÍNCRONO (Sigrid directo → persiste contratos+líneas en
    # BBDD), para poder ASOCIAR contratos sin sv3 ni Azurite. Así, al
    # elegir un contrato encontrado en vivo, queda cacheado y el PUT ya
    # no anula la selección (se acaba el 409 "sin contrato"). OJO: esto
    # NO lanza la valoración — el orquestador también va por cola; en
    # solo-front el /valuate informará de que no se encoló. En producción
    # (con COLAS_*) se mantiene el ColasRefetchClient (asíncrono → sv3).
    # ------------------------------------------------------------------ #
    if isinstance(publicador, _PublicadorColasNulo) and settings.sigrid_lookup_enabled:
        try:
            _contrato_client = SigridApiContratoClient(
                base_url=settings.sigrid_api_base_url,
                function_key=settings.sigrid_api_function_key,
                database=settings.sigrid_api_database,
                timeout_s=settings.sigrid_api_timeout_s,
            )
            sv3_refetch_client = LocalContratoRefetchClient(
                sigrid_client=_contrato_client,
                repository=repository,
            )
            logger.info(
                "[contrato-refetch][wiring] FALLBACK LOCAL activado "
                "(solo-front + Sigrid): re-fetch síncrono sin sv3."
            )
        except Exception:
            logger.exception(
                "[contrato-refetch][wiring] no se pudo activar el fallback "
                "local; se mantiene el de cola (no operativo en solo-front)."
            )
    app.state.sv3_refetch_client = sv3_refetch_client

    # Orquestador (antes HttpOrchestratorClient → sv7, disuelto). Ahora:
    #   - contract-selected → MensajeValoracion(force=True) → q-valoracion
    #   - document-approved → MensajeFeedback → q-feedback
    #   - document-purged   → limpieza directa de workflow_runs (BBDD),
    #     que desbloquea el dedup por contenido tras el hard-delete.
    workflow_runs_purger = WorkflowRunsPurger(session_factory)
    orchestrator_client: OrchestratorClient = ColasOrchestratorClient(
        publicador=publicador,
        workflow_runs_purger=workflow_runs_purger,
    )
    app.state.orchestrator_client = orchestrator_client
    logger.info(
        "[colas][wiring] publicador best-effort + adapters de cola "
        "CABLEADOS (emitido_por=ca-sv4-front)"
    )

    # ------------------------------------------------------------------ #
    # Cliente de SOLO LECTURA a Sigrid para los desplegables de cabecera
    # (elegir proveedor con contrato en la obra / elegir obra). Se
    # construye solo si hay credenciales (SIGRID_API_*). Si no, queda
    # None y los endpoints /api/sigrid/* responden ok=false (el front
    # mantiene la entrada manual).
    #
    # Nota de arquitectura: el camino de ESCRITURA de contratos
    # (UPSERT/PDF) sigue yendo por sv3. Esto es un lookup de referencia
    # de solo lectura para la UI; no reintroduce aquel acoplamiento.
    # ------------------------------------------------------------------ #
    sigrid_lookup_client: SigridLookupClient | None = None
    if settings.sigrid_lookup_enabled:
        sigrid_lookup_client = SigridLookupClient(
            base_url=settings.sigrid_api_base_url,
            function_key=settings.sigrid_api_function_key,
            database=settings.sigrid_api_database,
            timeout_s=settings.sigrid_api_timeout_s,
        )
        logger.info(
            "[sigrid-lookup][wiring] CABLEADO base_url=%s database=%s",
            settings.sigrid_api_base_url,
            settings.sigrid_api_database,
        )
    else:
        logger.info(
            "[sigrid-lookup][wiring] DESACTIVADO (faltan SIGRID_API_*); "
            "los desplegables de cabecera quedaran en entrada manual."
        )
    app.state.sigrid_lookup_client = sigrid_lookup_client

    # F-098 R27: la lista de partidas por obra, en una caché por réplica (la
    # de comun) sobre el lector del cliente. La leen el selector
    # (``/api/sigrid/partidas``) y la ficha (código completo, ✓/⚠, traducir
    # lo que se guarda). Sin cliente, sin caché: todo como antes de F-098.
    partidas_obra: CachePartidasObra | None = None
    if sigrid_lookup_client is not None:
        partidas_obra = CachePartidasObra(
            sigrid_lookup_client.lector_partidas,
            ttl_s=settings.partidas_obra_ttl_s,
            max_obras=settings.partidas_obra_max_obras,
            ttl_fallo_s=settings.partidas_obra_fallo_ttl_s,
        )
    app.state.partidas_obra = partidas_obra

    # F-053: el servicio de revisión publica el alta en Sigrid al pasar a
    # aprobado (R1-R4) con la configuración del alta (DESDE, Espera, mapeo;
    # DESDE vacía = feature apagada, R3). Posicionales a propósito; F-098
    # añade la caché de partidas (``None`` sin Sigrid), por eso el cliente de
    # Sigrid se construye antes.
    config_alta = settings.config_alta_sigrid
    review_service = ReviewService(
        repository, settings.default_reviewer, orchestrator_client, config_alta,
        partidas_obra,
    )
    app.state.review_service = review_service
    app.state.config_alta = config_alta
    app.state.tables_ready = review_service.initialize()
    logger.info(
        "[alta-sigrid][wiring] %s (desde=%s espera_min=%s productos=%s)",
        "ACTIVA" if config_alta.activa else "APAGADA (DESDE vacía)",
        config_alta.desde, settings.alta_sigrid_espera_incierto_min,
        sorted(config_alta.admitidos),
    )

    templates = Jinja2Templates(
        directory=str(Path(__file__).resolve().parents[2] / "templates")
    )
    templates.env.filters["tojson_pretty"] = lambda value: json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
    )
    templates.env.filters["fecha_int_iso"] = _format_fecha_int_iso
    templates.env.filters["importe_eur"] = _format_importe_eur
    templates.env.filters["fecha_hora_local"] = _format_fecha_hora_local
    templates.env.filters["fecha_local"] = _format_fecha_local
    templates.env.filters["hora_local"] = _format_hora_local
    # F-108 R4: la fecha del albarán guardada (AAAA-MM-DD), en dd/mm/aaaa.
    templates.env.filters["fecha_albaran_ver"] = fecha_para_ver
    templates.env.globals["view_label"] = _view_label
    # Cache-buster para CSS/JS: un valor único por arranque del
    # servicio. Cuando reiniciamos sv4, los navegadores ven una URL
    # nueva (...styles.css?v=1715000000) y recargan el archivo en vez
    # de servir la versión cacheada. En desarrollo es indispensable
    # — sin esto, Ctrl+R no basta y hay que Ctrl+F5 cada vez.
    import time as _time
    templates.env.globals["asset_version"] = str(int(_time.time()))
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parents[2] / "static")),
        name="static",
    )

    # ------------------------------------------------------------------ #
    # Identidad del revisor desde Easy Auth (Entra ID).
    #
    # Container Apps con Easy Auth inyecta el UPN del usuario autenticado
    # en la cabecera ``X-MS-CLIENT-PRINCIPAL-NAME`` en cada petición. La
    # usamos para atribuir quién aprueba/purga/valora/elimina. Fallback a
    # ``default_reviewer`` en local (sin Easy Auth) o si la cabecera no
    # llega.
    #
    # F-053 v8 (R49): la cabecera MANDA. El navegador no puede ponerla (la
    # inyecta la plataforma), pero sí el formulario o el cuerpo: ``propuesto``
    # (lo que trae la petición) solo cuenta sin cabecera, en local. De
    # ``approved_by`` sale el usuario de Sigrid del alta (sv9, R47).
    # ------------------------------------------------------------------ #
    def _reviewer_from_request(request: Request, propuesto: str | None = None) -> str | None:
        principal = request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME")
        if principal and principal.strip():
            return principal.strip()
        if propuesto and propuesto.strip():
            return propuesto.strip()
        # Recortado como en el servicio: lo que se publica en q-feedback es
        # lo mismo que queda en el merge (review v8, cambio 3).
        return (settings.default_reviewer or "").strip() or None

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        ready = review_service.initialize()
        app.state.tables_ready = ready
        return HealthResponse(
            ok=True,
            service="albaranes-review-web",
            version=settings.service_version,
            tables_ready=ready,
            details={
                "database": settings.pg_db,
                "default_page_size": settings.default_page_size,
                "max_page_size": settings.max_page_size,
                "preview_enabled": settings.preview_enabled,
                "refetch_mode": "async-via-q-persistencia",
            },
        )

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/documents", status_code=302)

    # ------------------------------------------------------------------ #
    # Desplegables de cabecera: lookups de SOLO LECTURA a Sigrid.
    #   GET /api/sigrid/proveedores?obra={codigo}
    #   GET /api/sigrid/obras
    # Devuelven {ok, items:[...]} o {ok:false, error:...} (200 con ok=false
    # para que el front muestre aviso y mantenga la entrada manual, sin
    # romper la pagina).
    # ------------------------------------------------------------------ #
    @app.get("/api/sigrid/proveedores", include_in_schema=False)
    def sigrid_proveedores(obra: str = Query(default="")) -> JSONResponse:
        client = app.state.sigrid_lookup_client
        if client is None:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4 "
                 "(faltan SIGRID_API_*).", "items": []}
            )
        codigo = (obra or "").strip()
        if not codigo:
            return JSONResponse(
                {"ok": False, "error": "Falta el codigo de obra.", "items": []}
            )
        try:
            proveedores = client.fetch_proveedores_por_obra(codigo_obra=codigo)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sigrid-lookup] proveedores obra=%s fallo: %r", codigo, exc)
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}", "items": []}
            )
        items = [{"cif": p.cif, "nombre": p.nombre} for p in proveedores]
        return JSONResponse({"ok": True, "items": items})

    # (F-114) Búsqueda global: proveedores VIVOS de Sigrid (con.tip 5, emp 1,
    # fecbaj 0) por nombre o CIF, para el combo con «Solo de la obra»
    # desmarcado. Mismo patrón de errores que la lista de la obra (R14).
    @app.get("/api/sigrid/proveedores/todos", include_in_schema=False)
    def sigrid_proveedores_todos(q: str = Query(default="")) -> JSONResponse:
        client = app.state.sigrid_lookup_client
        if client is None:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4 "
                 "(faltan SIGRID_API_*).", "items": []}
            )
        texto = (q or "").strip()
        if len(texto) < MINIMO_BUSQUEDA_PROVEEDOR:
            return JSONResponse(
                {"ok": False, "items": [], "error": (
                    f"Escribe al menos {MINIMO_BUSQUEDA_PROVEEDOR} letras "
                    "del nombre o del CIF."
                )}
            )
        try:
            busqueda = client.buscar_proveedores(texto=texto)
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sigrid-lookup] proveedores_todos q=%r fallo: %r", texto, exc)
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}", "items": []}
            )
        items = [
            {"cif": p.cif, "nombre": p.nombre, "fichas": p.fichas}
            for p in busqueda.items
        ]
        return JSONResponse({"ok": True, "items": items, "mas": busqueda.mas})

    @app.get("/api/sigrid/obras", include_in_schema=False)
    def sigrid_obras() -> JSONResponse:
        client = app.state.sigrid_lookup_client
        if client is None:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4 "
                 "(faltan SIGRID_API_*).", "items": []}
            )
        try:
            obras = client.fetch_obras()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[sigrid-lookup] obras fallo: %r", exc)
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}", "items": []}
            )
        items = [{"codigo": o.codigo, "nombre": o.nombre} for o in obras]
        return JSONResponse({"ok": True, "items": items})

    @app.get("/api/sigrid/partidas", include_in_schema=False)
    def sigrid_partidas(obra: str = Query(default="")) -> JSONResponse:
        # Partidas HOJA del presupuesto de la obra en Sigrid (obrparpar),
        # para el desplegable de partida de la fila salmón. SOLO lectura.
        # (F-098 R14) Por la caché de sv4 (R27), con el código completo, el
        # capítulo de cada hoja y los capítulos de la obra para los chips.
        cache = app.state.partidas_obra
        if app.state.sigrid_lookup_client is None or cache is None:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4 "
                 "(faltan SIGRID_API_*).", "items": [], "capitulos": []}
            )
        codigo = (obra or "").strip()
        if not codigo:
            return JSONResponse(
                {"ok": False, "error": "Falta el codigo de obra.", "items": [], "capitulos": []}
            )
        lista, ok = cache.consultar(codigo)
        if not ok or lista is None:
            # La causa ya la registró la caché (WARNING con la obra): aquí no
            # se repite ni se manda al navegador.
            return JSONResponse(
                {"ok": False, "error": "No se pudo leer la lista de partidas de Sigrid.",
                 "items": [], "capitulos": []}
            )
        items = [
            {
                "ide": p.ide,
                "codigo": p.codigo,
                "codigo_completo": p.codigo_completo,
                "capitulo": p.capitulo,
                "descripcion": p.descripcion,
                "descripcion_agregada": p.descripcion_agregada,
                "cod_repetido": p.cod_repetido,
            }
            for p in opciones_partida(lista)
        ]
        capitulos = [
            {"codigo": c.codigo, "descripcion": c.descripcion, "n": c.n_hojas}
            for c in lista.capitulos
        ]
        return JSONResponse({"ok": True, "items": items, "capitulos": capitulos})

    @app.get("/api/sigrid/contratos", include_in_schema=False)
    def sigrid_contratos(
        obra: str = Query(default=""),
        cif: str = Query(default=""),
    ) -> JSONResponse:
        # Búsqueda EN VIVO de contratos en Sigrid por obra (+ cif opcional),
        # igual que los desplegables de obra/proveedor. SOLO lectura; el
        # cacheo de líneas (para poder valorar) lo hace el re-fetch de sv3
        # cuando el front confirma la selección.
        client = app.state.sigrid_lookup_client
        if client is None:
            return JSONResponse(
                {"ok": False, "error": "Sigrid no configurado en el sv4 "
                 "(faltan SIGRID_API_*).", "items": []}
            )
        codigo = (obra or "").strip()
        if not codigo:
            return JSONResponse(
                {"ok": False, "error": "Falta el codigo de obra.", "items": []}
            )
        try:
            contratos = client.fetch_contratos(
                codigo_obra=codigo,
                cif=(cif or "").strip() or None,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[sigrid-lookup] contratos obra=%s fallo: %r", codigo, exc
            )
            return JSONResponse(
                {"ok": False, "error": f"Error consultando Sigrid: {exc}", "items": []}
            )
        items = [
            {
                "codigo": c.codigo,
                "nombre": c.nombre,
                "cif": c.cif,
                "nombre_proveedor": c.nombre_proveedor,
            }
            for c in contratos
        ]
        return JSONResponse({"ok": True, "items": items})

    @app.get("/documents", response_class=HTMLResponse)
    def documents_list(
        request: Request,
        search: str | None = Query(default=None),
        proveedor: str | None = Query(default=None),
        fecha: str | None = Query(default=None),
        recepcion: str | None = Query(default=None),
        obra: str | None = Query(default=None),
        # Filtros EXACTOS de las vistas Obra/Proveedor (jul 2026).
        obra_codigo: str | None = Query(default=None),
        proveedor_cif: str | None = Query(default=None),
        albaran: str | None = Query(default=None),
        contrato: str | None = Query(default=None),
        lineas: str | None = Query(default=None),
        min_importe: str | None = Query(default=None),
        max_importe: str | None = Query(default=None),
        approved: str = Query(default="pending"),
        review_required: str = Query(default="all"),
        min_confidence: str | None = Query(default=None),
        max_confidence: str | None = Query(default=None),
        sort_by: str = Query(default="confidence_pct_calc"),
        sort_dir: str = Query(default="asc"),
        vista: str = Query(default="activos"),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(
            default=settings.default_page_size,
            ge=1,
            le=settings.max_page_size,
        ),
        message: str | None = Query(default=None),
    ) -> HTMLResponse:
        filters = DocumentListFilters(
            search=search,
            proveedor=proveedor,
            fecha=fecha,
            recepcion=recepcion,
            obra=obra,
            obra_codigo=obra_codigo,
            proveedor_cif=proveedor_cif,
            albaran=albaran,
            contrato=contrato,
            lineas=lineas,
            min_importe=_parse_optional_float(min_importe, field_name="min_importe"),
            max_importe=_parse_optional_float(max_importe, field_name="max_importe"),
            approved=approved,
            review_required=review_required,
            min_confidence=_parse_optional_float(min_confidence, field_name="min_confidence"),
            max_confidence=_parse_optional_float(max_confidence, field_name="max_confidence"),
            sort_by=sort_by,
            sort_dir=sort_dir,
            vista=vista,
            page=page,
            page_size=page_size,
        )
        result = review_service.list_documents(filters)
        current_query = _query_string(filters)
        context = {
            "request": request,
            "title": settings.app_title,
            "filters": filters,
            "result": result,
            "message": message,
            "current_query": current_query,
            # F-053 R31 / R3: el estado del alta solo se pinta con DESDE.
            "alta_sigrid_activa": app.state.config_alta.activa,
            "build_sort_query": lambda column: _query_string(
                filters,
                {
                    "sort_by": column,
                    "sort_dir": (
                        "desc"
                        if filters.sort_by == column and filters.sort_dir == "asc"
                        else "asc"
                    ),
                    "page": 1,
                },
            ),
            "build_page_query": lambda new_page: _query_string(
                filters,
                {"page": new_page},
            ),
        }
        return templates.TemplateResponse(
            request=request,
            name="documents_list.html",
            context=context,
        )

    # ---------------------------------------------------------------- #
    # Vistas agregadas (jul 2026): Obras y Proveedores. Cada fila enlaza
    # a la bandeja YA filtrada (filtros exactos obra_codigo /
    # proveedor_cif); el detalle del albaran es el mismo de siempre.
    # ---------------------------------------------------------------- #
    @app.get("/obras", response_class=HTMLResponse)
    def obras_list(
        request: Request,
        search: str | None = Query(default=None),
    ) -> HTMLResponse:
        items = review_service.list_obras_resumen(search=search)
        return templates.TemplateResponse(
            request=request,
            name="obras_list.html",
            context={
                "request": request,
                "title": settings.app_title,
                "items": items,
                "search": (search or "").strip(),
            },
        )

    @app.get("/proveedores", response_class=HTMLResponse)
    def proveedores_list(
        request: Request,
        search: str | None = Query(default=None),
    ) -> HTMLResponse:
        items = review_service.list_proveedores_resumen(search=search)
        return templates.TemplateResponse(
            request=request,
            name="proveedores_list.html",
            context={
                "request": request,
                "title": settings.app_title,
                "items": items,
                "search": (search or "").strip(),
            },
        )

    @app.post("/documents/{document_id}/approve", include_in_schema=False)
    def approve_from_list(
        document_id: str,
        request: Request,
        redirect_query: str = Form(default=""),
        approved_by: str = Form(default=""),
    ) -> RedirectResponse:
        try:
            resultado = review_service.approve_document(
                document_id=document_id,
                # R49: cabecera de Easy Auth > formulario > DEFAULT_REVIEWER.
                approved_by=_reviewer_from_request(request, approved_by),
            )
        except (
            AlbaranSinValorarError, LineasIncompletasError, ValoracionDeOtroContratoError,
            CabeceraIncompletaError,
        ) as exc:
            # F-053 R37, F-065 R20, F-115 R13 y F-108 R11: no se aprueba lo no
            # valorado, ni con filas sin cantidad o importe, ni con la
            # valoración de otro contrato, ni sin fecha válida o sin número;
            # nada cambia.
            return _redirigir_a_lista(redirect_query, exc.aviso)
        aviso = getattr(resultado, "aviso", None)
        texto = f"Documento aprobado, pero {aviso}" if aviso else "Documento aprobado"
        return _redirigir_a_lista(redirect_query, texto)

    @app.post("/documents/{document_id}/unapprove", include_in_schema=False)
    def unapprove_from_list(
        document_id: str,
        redirect_query: str = Form(default=""),
        volver: str = Form(default=""),
    ) -> RedirectResponse:
        # F-065 R5: «Desaprobar para editar» de la ficha vuelve a la ficha.
        a_la_ficha = volver == "ficha"
        try:
            review_service.unapprove_document(document_id=document_id)
        except AlbaranBloqueadoError as exc:
            # F-053 R25: desaprobar un albarán con alta bloqueante, no.
            if a_la_ficha:
                return _a_la_ficha(document_id, exc.aviso)
            return _redirigir_a_lista(redirect_query, exc.aviso)
        if a_la_ficha:
            return _a_la_ficha(document_id, "Documento desaprobado: ya se puede editar")
        query = redirect_query.strip()
        message = urlencode({"message": "Documento marcado como pendiente"})
        if query:
            return RedirectResponse(
                url=f"/documents?{query}&{message}".replace("?&", "?"),
                status_code=303,
            )
        return RedirectResponse(url=f"/documents?{message}", status_code=303)

    # ------------------------------------------------------------------ #
    # Soft-delete (jun 2026): borrar (a papelera) y restaurar.
    # ------------------------------------------------------------------ #
    @app.post("/documents/{document_id}/delete", include_in_schema=False)
    def delete_from_list(
        document_id: str,
        request: Request,
        redirect_query: str = Form(default=""),
        deleted_by: str = Form(default=""),
    ) -> RedirectResponse:
        try:
            review_service.delete_document(
                document_id=document_id,
                deleted_by=deleted_by.strip() or _reviewer_from_request(request),
            )
        except AlbaranBloqueadoError as exc:
            # F-053 R25: borrar un albarán con alta bloqueante, no.
            return _redirigir_a_lista(redirect_query, exc.aviso)
        query = redirect_query.strip()
        message = urlencode({"message": "Albarán movido a la papelera"})
        if query:
            return RedirectResponse(
                url=f"/documents?{query}&{message}".replace("?&", "?"),
                status_code=303,
            )
        return RedirectResponse(url=f"/documents?{message}", status_code=303)

    @app.post("/documents/bulk-delete", include_in_schema=False)
    def bulk_delete_from_list(
        request: Request,
        ids: str = Form(default=""),
        redirect_query: str = Form(default=""),
        deleted_by: str = Form(default=""),
    ) -> RedirectResponse:
        # Borrado en BLOQUE (jul 2026): la bandeja envia los ids
        # seleccionados separados por comas. Soft-delete (papelera),
        # igual que el borrado individual.
        # F-053 R27: los que tienen un alta en Sigrid bloqueante se saltan
        # y se dice cuántos.
        id_list = [i.strip() for i in ids.split(",") if i.strip()]
        movidos = saltados = 0
        if id_list:
            resultado = review_service.bulk_delete_documents_con_saltos(
                document_ids=id_list,
                deleted_by=(
                    deleted_by.strip() or _reviewer_from_request(request)
                ),
            )
            movidos, saltados = resultado.movidos, resultado.saltados
        if movidos or saltados:
            texto = f"{movidos} albarán(es) movidos a la papelera"
            if saltados:
                texto += (
                    f"; {saltados} saltado(s) por estar registrados en "
                    "Sigrid (o con el alta en curso)"
                )
        else:
            texto = "Ningún albarán seleccionado"
        query = redirect_query.strip()
        message = urlencode({"message": texto})
        if query:
            return RedirectResponse(
                url=f"/documents?{query}&{message}".replace("?&", "?"),
                status_code=303,
            )
        return RedirectResponse(url=f"/documents?{message}", status_code=303)

    @app.post("/documents/{document_id}/restore", include_in_schema=False)
    def restore_from_list(
        document_id: str,
        redirect_query: str = Form(default=""),
    ) -> RedirectResponse:
        review_service.restore_document(document_id=document_id)
        query = redirect_query.strip()
        message = urlencode({"message": "Albarán restaurado"})
        if query:
            return RedirectResponse(
                url=f"/documents?{query}&{message}".replace("?&", "?"),
                status_code=303,
            )
        return RedirectResponse(url=f"/documents?{message}", status_code=303)

    # ------------------------------------------------------------------ #
    # Vaciar papelera (jul 2026): purga TODOS los albaranes borrados.
    # Reutiliza hard_delete_document por documento (y su limpieza de
    # dedup vía orquestador), en vez de un DELETE masivo que duplicaría
    # el plan de borrado hijos→padres del repositorio.
    # ------------------------------------------------------------------ #
    @app.post("/documents/trash/empty", include_in_schema=False)
    def empty_trash(request: Request) -> RedirectResponse:
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        orch: OrchestratorClient = app.state.orchestrator_client
        purged_by = _reviewer_from_request(request)

        ids = review_service.list_trash_document_ids()
        purgados = 0
        fallidos = 0
        saltados = 0
        for doc_id in ids:
            try:
                source_sha256 = review_service.hard_delete_document(
                    document_id=doc_id,
                )
            except AlbaranBloqueadoError:
                # F-053 R27: un alta en Sigrid bloqueante no se purga.
                saltados += 1
                continue
            except Exception:  # noqa: BLE001 - seguir con el resto
                logger.exception(
                    "[empty-trash] fallo purgando doc=%s; se continúa",
                    doc_id,
                )
                fallidos += 1
                continue
            purgados += 1
            outcome = orch.notify_document_purged(
                document_id=doc_id,
                source_sha256=source_sha256,
                purged_by=purged_by,
                purged_at_utc=now_utc,
            )
            if outcome is None:
                logger.warning(
                    "[empty-trash] no se confirmó la limpieza de dedup "
                    "doc=%s; el borrado local SÍ se aplicó.",
                    doc_id,
                )

        if fallidos:
            texto = (
                f"Papelera: {purgados} albarán(es) eliminados; "
                f"{fallidos} fallaron (reintenta)."
            )
        else:
            texto = f"Papelera vaciada: {purgados} albarán(es) eliminados."
        if saltados:
            texto += (
                f" {saltados} saltado(s) por estar registrados en Sigrid "
                "(o con el alta en curso)."
            )
        message = urlencode({"message": texto})
        return RedirectResponse(
            url=f"/documents?vista=papelera&approved=all&{message}",
            status_code=303,
        )

    @app.post("/documents/{document_id}/purge", include_in_schema=False)
    def purge_from_list(
        document_id: str,
        request: Request,
        redirect_query: str = Form(default=""),
    ) -> RedirectResponse:
        # Hard-delete: borrado físico irreversible. Solo desde la papelera.
        try:
            source_sha256 = review_service.hard_delete_document(
                document_id=document_id,
            )
        except AlbaranBloqueadoError as exc:
            # F-053 R25: purgar un albarán con alta bloqueante, no.
            return _redirigir_a_lista(redirect_query, exc.aviso)

        # ------------------------------------------------------------ #
        # Limpieza del dedup tras la purga.
        #
        # Sin esto, las filas de workflow_runs seguían vivas tras el
        # hard-delete y su dedup por attachment_sha256 respondía "PDF ya
        # procesado" al reenviar el mismo albarán, aunque ya no existía
        # en el portal. Ahora el adapter de colas borra esas filas
        # directamente (misma BBDD). Best-effort: si falla, la purga
        # local YA está hecha y se puede reintentar.
        # ------------------------------------------------------------ #
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        orch: OrchestratorClient = app.state.orchestrator_client
        outcome = orch.notify_document_purged(
            document_id=document_id,
            source_sha256=source_sha256,
            purged_by=_reviewer_from_request(request),
            purged_at_utc=now_utc,
        )
        if outcome is None:
            logger.warning(
                "[purge] no se confirmó la limpieza de dedup doc=%s; el "
                "borrado local SÍ se aplicó. Si reenvías el mismo PDF y "
                "aparece como duplicado, revisa el log del purger "
                "(tabla/columna de workflow_runs) y reintenta la purga.",
                document_id,
            )

        query = redirect_query.strip()
        message = urlencode({"message": "Albarán eliminado definitivamente"})
        if query:
            return RedirectResponse(
                url=f"/documents?{query}&{message}".replace("?&", "?"),
                status_code=303,
            )
        return RedirectResponse(url=f"/documents?{message}", status_code=303)

    @app.get("/documents/{document_id}", response_class=HTMLResponse)
    def document_detail(
        request: Request,
        document_id: str,
        view: str = Query(default=VIEW_MODE_MERGE),
        message: str | None = Query(default=None),
        buscando: bool = Query(default=False),
    ) -> HTMLResponse:
        requested_view = normalize_view_mode(view)
        document = review_service.get_document(
            document_id,
            view_mode=requested_view,
        )
        if document is None:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        # -------------------------------------------------------------- #
        # Navegacion anterior/siguiente (jun 2026): recorre el MISMO
        # conjunto ordenado+filtrado de la bandeja (cruzando paginas). Los
        # filtros viajan en la query del enlace que abrio este detalle
        # (ver documents_list.html). Si no hay query (acceso directo al
        # detalle), se usan los filtros por defecto del modelo.
        # -------------------------------------------------------------- #
        nav_filters = _filters_from_query(
            request, default_page_size=settings.default_page_size
        )
        nav_query = _query_string(nav_filters)
        prev_id, next_id = review_service.get_neighbor_ids(
            document_id=document_id, filters=nav_filters
        )

        def _detail_url(doc_id: str) -> str:
            extra: dict[str, Any] = {}
            if requested_view != VIEW_MODE_MERGE:
                extra["view"] = requested_view
            tail = urlencode(extra)
            q = "&".join(part for part in (nav_query, tail) if part)
            return f"/documents/{doc_id}?{q}" if q else f"/documents/{doc_id}"

        context = {
            "request": request,
            "title": settings.app_title,
            "document": document,
            "document_json": json.dumps(document.model_dump(), ensure_ascii=False),
            "message": message,
            # F-052 D4-A: «Guardar» relanzó la búsqueda de contratos.
            "buscando": buscando,
            "preview_enabled": settings.preview_enabled,
            "document_preview_url": f"/documents/{document.id}/preview",
            "current_view": document.view_mode,
            "available_views": document.available_views,
            "view_label": _view_label,
            "back_to_list_url": f"/documents?{nav_query}" if nav_query else "/documents",
            "nav_prev_url": _detail_url(prev_id) if prev_id else None,
            "nav_next_url": _detail_url(next_id) if next_id else None,
        }
        return templates.TemplateResponse(
            request=request,
            name="document_detail.html",
            context=context,
        )

    @app.get("/documents/{document_id}/contrato-pdf")
    def document_contrato_pdf(document_id: str) -> Response:
        """Abre el PDF del contrato en SharePoint. Resuelve la URL por
        consulta directa a BBDD y redirige (302). Asi el boton del front
        funciona aunque el web_url no llegue al payload del detalle."""
        url = review_service.get_contrato_pdf_url(document_id)
        if not url:
            raise HTTPException(
                status_code=404,
                detail="Este albaran no tiene PDF de contrato en SharePoint.",
            )
        return RedirectResponse(url, status_code=302)

    @app.get("/documents/{document_id}/preview", response_class=Response)
    def document_preview(document_id: str) -> Response:
        document = review_service.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        if not settings.preview_enabled:
            return _preview_error_response(
                title="Vista previa no configurada",
                message=(
                    "Faltan GRAPH_KEY o SHAREPOINT_DRIVE_ID en el .env del servicio."
                ),
                external_url=document.document_url,
            )

        relative_path = (document.document_storage_ref or "").strip()
        if not relative_path:
            return _preview_error_response(
                title="Documento sin referencia interna",
                message=(
                    "El registro no tiene document_storage_ref y no se puede leer "
                    "el archivo desde SharePoint por Graph."
                ),
                external_url=document.document_url,
            )

        token_provider: GraphTokenProvider | None = app.state.graph_token_provider
        if token_provider is None:
            return _preview_error_response(
                title="Token provider no disponible",
                message="No se pudo inicializar el acceso a Microsoft Graph.",
                external_url=document.document_url,
            )

        encoded_path = quote(relative_path.lstrip("/"), safe="/")
        metadata_url = (
            f"https://graph.microsoft.com/v1.0/drives/{settings.sharepoint_drive_id}"
            f"/root:/{encoded_path}"
        )

        try:
            token = token_provider.get_token()
            headers = {"Authorization": f"Bearer {token}"}
            timeout = httpx.Timeout(
                settings.graph_timeout_s,
                connect=min(20, settings.graph_timeout_s),
            )
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                metadata_response = client.get(metadata_url, headers=headers)
                if metadata_response.status_code >= 300:
                    logger.warning(
                        "Preview metadata error. status=%s body=%s path=%s",
                        metadata_response.status_code,
                        metadata_response.text[:500],
                        relative_path,
                    )
                    return _preview_error_response(
                        title="No se pudo localizar el archivo",
                        message=(
                            f"Graph devolvió {metadata_response.status_code} al "
                            f"resolver el documento en SharePoint."
                        ),
                        external_url=document.document_url,
                    )

                payload = metadata_response.json()
                item_id = str(payload["id"])
                content_url = (
                    f"https://graph.microsoft.com/v1.0/drives/"
                    f"{settings.sharepoint_drive_id}/items/{item_id}/content"
                )
                content_response = client.get(content_url, headers=headers)
                if content_response.status_code >= 300:
                    logger.warning(
                        "Preview content error. status=%s body=%s item_id=%s path=%s",
                        content_response.status_code,
                        content_response.text[:500],
                        item_id,
                        relative_path,
                    )
                    return _preview_error_response(
                        title="No se pudo descargar el archivo",
                        message=(
                            f"Graph devolvió {content_response.status_code} al "
                            f"descargar el documento."
                        ),
                        external_url=document.document_url,
                    )

                media_type = _guess_media_type(document.source_filename or relative_path)
                return Response(
                    content=content_response.content,
                    media_type=media_type,
                    headers={
                        "Content-Disposition": (
                            "inline; "
                            f'filename="{document.source_filename or Path(relative_path).name}"'
                        ),
                        "Cache-Control": "no-store",
                    },
                )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                "Error obteniendo preview desde SharePoint. document_id=%s path=%s",
                document_id,
                relative_path,
            )
            return _preview_error_response(
                title="Error obteniendo vista previa",
                message=str(exc),
                external_url=document.document_url,
            )

    @app.get("/api/documents/{document_id}", response_model=DocumentDetailPayload)
    def document_detail_api(
        document_id: str,
        view: str = Query(default=VIEW_MODE_MERGE),
    ) -> DocumentDetailPayload:
        document = review_service.get_document(
            document_id,
            view_mode=normalize_view_mode(view),
        )
        if document is None:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        return document

    @app.put("/api/documents/{document_id}", response_model=SaveResponse)
    async def save_document_api(
        document_id: str,
        payload: MergeDocumentUpdatePayload,
        request: Request,
        buscar_si_cambia: bool = Query(default=False),
    ) -> SaveResponse:
        # F-052 D4-A: solo el botón «Guardar» pide ``buscar_si_cambia``; si
        # el CIF o la obra guardados ya no son los del último rastro, se
        # relanza la re-búsqueda (q-persistencia, force=True). Los demás
        # PUT del portal (valorar, elegir contrato, «Guardar y volver a
        # buscar») no lo piden: ya buscan ellos o no deben hacerlo.
        # F-053: con alta bloqueante (R25) o al aprobar sin valorar (R37)
        # el servicio lanza y el manejador responde 409 con el aviso.
        # F-053 v8 (R49): quien aprueba es la cabecera de Easy Auth; el
        # ``approved_by`` del cuerpo solo cuenta sin ella (local).
        payload.approved_by = _reviewer_from_request(request, payload.approved_by)
        try:
            resultado = review_service.guardar(
                document_id=document_id,
                payload=payload,
                refetch_client=(
                    app.state.sv3_refetch_client if buscar_si_cambia else None
                ),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        detail, busqueda = resultado.detail, resultado.busqueda

        # F-115 R11: si el guardado quitó el contrato (proveedor u obra
        # cambiados), el aviso lo dice.
        message, buscando = aviso_de_guardado(
            aprobado=detail.approved, busqueda=busqueda,
            contrato_retirado=resultado.contrato_retirado, cambio=resultado.cambio,
        )
        if resultado.aprobacion.aviso:
            # F-053 R4: aprobado, pero el alta no se pidió.
            message = f"{message} Atención: {resultado.aprobacion.aviso}."
        query = {"message": message, **({"buscando": "1"} if buscando else {})}
        return SaveResponse(
            ok=True,
            document_id=detail.id,
            approved=detail.approved,
            redirect_url=f"/documents/{detail.id}?{urlencode(query)}",
            message=message,
            busqueda_relanzada=busqueda is not None,
        )

    # ------------------------------------------------------------------ #
    # Re-fetch manual de contratos desde el portal.
    #
    # Delega íntegramente en el sv3 vía HTTP. El sv3 es ahora el
    # único responsable de hablar con Sigrid y persistir contratos.
    # El sv4 sigue exponiendo el mismo path para no romper el front.
    #
    # Códigos de respuesta:
    #   * 200 + outcome JSON — el sv3 procesó correctamente la
    #     petición (con o sin contratos encontrados). El campo
    #     outcome.status detalla.
    #   * 404 — el documento no existe en BBDD.
    #   * 5xx — fallo irrecuperable (raro: el cliente HTTP traduce
    #     casi todos los fallos a outcomes con status=sigrid_error).
    # ------------------------------------------------------------------ #
    @app.post("/api/documents/{document_id}/re-fetch-contratos")
    def refetch_contratos_api(document_id: str) -> dict:
        # Pre-validamos que el documento existe LOCALMENTE para dar
        # un 404 rápido sin pegarle al sv3 con peticiones inútiles.
        preview = review_service.get_document(document_id)
        if preview is None:
            raise HTTPException(
                status_code=404,
                detail="Documento no encontrado",
            )
        # F-053 R25: volver a buscar re-enriquece y revalora; con alta
        # bloqueante, no se publica (design §11: se mira sin cerrojo). F-065
        # R4: tampoco sobre un aprobado.
        review_service.comprobar_editable(document_id)

        client: ContratoRefetchClient = app.state.sv3_refetch_client
        try:
            outcome: ContratoRefetchOutcome = client.refetch(
                document_id=document_id,
            )
        except KeyError as exc:
            # El sv3 dijo 404 (no debería pasar si la pre-validación
            # local pasó, pero por si las moscas — race condition con
            # un delete entre la pre-validación y la llamada).
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        logger.info(
            "[contrato-refetch][api] document_id=%s outcome=%s count=%s "
            "selected=%s",
            document_id,
            outcome.status,
            outcome.count,
            outcome.selected_contrato_codigo,
        )
        return {
            "status": outcome.status,
            "count": outcome.count,
            "selected_contrato_codigo": outcome.selected_contrato_codigo,
            "message": outcome.message,
            "cif": outcome.cif,
            "obra_codigo": outcome.obra_codigo,
        }

    # ------------------------------------------------------------------ #
    # ENDPOINT: Botón "Valorar ahora" del portal.
    #
    # Flujo:
    #   1. El revisor selecciona un contrato (o ya lo tenía seleccionado).
    #   2. Pulsa "Valorar ahora".
    #   3. El sv4 emite ContractSelectedEvent al sv7.
    #   4. El sv7 transita el workflow a VALUING y lanza la valoración
    #      en background (sv6 → sv5 → genera líneas sintéticas).
    #   5. El front muestra toast "Valoración encolada" y el revisor
    #      refresca tras unos segundos.
    #
    # Semánticamente equivale a "como si el revisor acabara de elegir
    # el contrato". El sv7 ya maneja todos los sub-casos:
    #   - workflow en AWAITING_CONTRACT_SELECTION → transición a VALUING
    #   - workflow en VALUATION_FAILED → reabrir
    #   - workflow en AWAITING_APPROVAL o terminal → spawn revaluation
    #
    # Best-effort: si sv7 está caído, el endpoint NO falla; loguea y
    # devuelve 200 con un mensaje informativo. El estado (contrato
    # seleccionado) ya está persistido en BBDD; cuando sv7 vuelva, el
    # revisor puede pulsar otra vez.
    # ------------------------------------------------------------------ #
    @app.post("/api/documents/{document_id}/valuate")
    def valuate_document_api(document_id: str, request: Request) -> dict:
        # 1) Verificar que el documento existe localmente.
        preview = review_service.get_document(document_id)
        if preview is None:
            raise HTTPException(
                status_code=404,
                detail="Documento no encontrado",
            )
        # F-053 R25: revalorar reemplaza la valoración; con alta bloqueante,
        # no se publica (design §11: se mira sin cerrojo). F-065 R4: tampoco
        # sobre un aprobado.
        review_service.comprobar_editable(document_id)

        # 2) Leer el contrato seleccionado directamente de BBDD (no del
        #    payload, para evitar que el front mande algo distinto).
        codigo_contrato: str | None = getattr(
            preview, "selected_contrato_codigo", None,
        )
        # (F-075 R10) Sin contrato, si el albarán trae importes se revalora
        # igual: sv3 reenriquece y, sin contrato, publica q-valoracion con
        # contrato nulo (valoración directa en sv6).
        sin_contrato_con_importes = not codigo_contrato and bool(
            getattr(preview, "importe_leido", None)
            and preview.importe_leido.trae_importes
        )
        if not codigo_contrato and not sin_contrato_con_importes:
            raise HTTPException(
                status_code=409,
                detail=(
                    "El documento no tiene contrato seleccionado. "
                    "Elige un contrato antes de valorar."
                ),
            )

        # 2b) (jul 2026) Guardia: sin líneas leídas del albarán no hay
        #     nada que valorar. Antes se encolaba igualmente, sv5
        #     respondía 400, el mensaje quedaba envenenado en la cola
        #     (reintento eterno cada 10 min) y el front mostraba
        #     "Valorando..." infinito. sv6 también cierra ya estos
        #     casos como 'failed' (defensa en profundidad); esta
        #     guardia evita directamente el viaje inútil.
        if not getattr(preview, "lines", None):
            return {
                "ok": False,
                "accepted": False,
                "document_id": document_id,
                "message": (
                    "El documento no tiene líneas leídas del albarán: "
                    "no hay nada que valorar. Revisa la extracción o "
                    "reprocesa el documento antes de valorar."
                ),
            }

        # 3) Componer el evento. El selected_at_utc es el INSTANTE del
        #    click, no la fecha del save anterior. Esto sirve como
        #    correlation_key del sv7: dos clicks separados → dos
        #    revaluations (legítimas); doble-click rápido (mismo
        #    timestamp ISO al segundo) → idempotente.
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        client: OrchestratorClient = app.state.orchestrator_client
        reviewer = _reviewer_from_request(request)
        outcome: dict | None = None
        try:
            outcome = client.notify_contract_selected(
                document_id=document_id,
                codigo_contrato=codigo_contrato,
                selected_by=reviewer,
                selected_at_utc=now_utc,
            )
        except Exception:
            # El cliente ya es best-effort; este try es por si en una
            # versión futura cambia el contrato. NO propagamos: el
            # usuario pulsó un botón y queremos darle feedback.
            logger.exception(
                "[valuate][api] error inesperado publicando valoración "
                "document_id=%s codigo=%s",
                document_id, codigo_contrato,
            )

        # ------------------------------------------------------------ #
        # FIX (jun 2026) — honestidad del "Valorar ahora".
        #
        # Antes este endpoint SIEMPRE respondía "Valoración encolada"
        # aunque sv7 estuviera caído o respondiera action='no_op'
        # (p.ej. documento sin workflow asociado). El front se quedaba
        # sondeando 2 minutos una valoración que nunca iba a llegar
        # (bug reportado: "dice que lanza valorar, pero no lo hace").
        # Ahora el resultado del orquestador viaja en la respuesta y el
        # front decide si sondear o avisar del problema.
        # ------------------------------------------------------------ #
        orchestrator_ok = outcome is not None
        action = (outcome or {}).get("action")
        detail = (outcome or {}).get("detail")
        if not orchestrator_ok:
            message = (
                "No se pudo encolar la valoración. La selección de "
                "contrato SÍ está guardada; reintenta en unos segundos."
            )
        elif action == "no_op":
            message = (
                "No se encontró nada que valorar: "
                f"{detail or 'sin detalle'}."
            )
        elif sin_contrato_con_importes:
            message = (
                "Valoración encolada sin contrato: se valora con los importes "
                "del albarán. Refresca la página en unos segundos."
            )
        else:
            message = (
                "Valoración encolada. Refresca la página en unos "
                "segundos para ver el resultado."
            )

        logger.info(
            "[valuate][api] document_id=%s codigo=%s reviewer=%s "
            "orchestrator_ok=%s action=%s",
            document_id, codigo_contrato, reviewer,
            orchestrator_ok, action,
        )
        return {
            "accepted": orchestrator_ok and action != "no_op",
            "orchestrator_ok": orchestrator_ok,
            "orchestrator_action": action,
            "orchestrator_detail": detail,
            "workflow_id": (outcome or {}).get("workflow_id"),
            "document_id": document_id,
            "codigo_contrato": codigo_contrato,
            "selected_at_utc": now_utc,
            "message": message,
        }

    @app.patch(
        "/api/documents/{document_id}/lines/{valuation_line_id}/conciliacion"
    )
    def set_line_conciliacion_api(
        document_id: str,
        valuation_line_id: int,
        payload: ConciliacionOverridePayload = Body(...),
    ) -> dict:
        ok = review_service.set_line_conciliacion(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
            mode=payload.mode,
            matched_contrato_line_id=payload.matched_contrato_line_id,
            descripcion=payload.descripcion,
            precio_unitario=payload.precio_unitario,
        )
        if not ok:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo aplicar la conciliacion (linea, contrato "
                    "o modo no validos)."
                ),
            )
        return {
            "ok": True,
            "document_id": document_id,
            "valuation_line_id": valuation_line_id,
            "mode": payload.mode,
        }

    # IMPORTANTE: path PROPIO (.../conciliacion/campos), distinto del PATCH
    # de arriba (set_line_conciliacion, que espera 'mode'). Antes ambos
    # compartían .../conciliacion como PATCH y FastAPI enrutaba los dos al
    # primero (el de 'mode'), de modo que el "Guardar" de la fila salmón
    # (sin 'mode') caía en el handler equivocado y daba 422 mode required.
    @app.patch(
        "/api/documents/{document_id}/lines/{valuation_line_id}/conciliacion/campos"
    )
    def update_line_conciliacion_api(
        document_id: str,
        valuation_line_id: int,
        payload: ConciliacionEditBody = Body(...),
        bloquear: bool = Query(default=False),
    ) -> dict:
        # F-065 R8: solo los campos que vinieron (ausente = no cambia; null =
        # vaciar). R13: «Guardar» de la fila manda ``?bloquear=1``.
        # F-106 R4, R7, R9: ``importe`` y ``cuadrar`` (solo si vino: sin él, la
        # llamada es la de siempre); sin precio que dé el importe (Q 0 o dto
        # 100 %), 422 con el texto para el revisor.
        extra = {} if payload.cuadrar is None else {"cuadrar": payload.cuadrar}
        try:
            ok = review_service.update_line_conciliacion(
                document_id=document_id,
                valuation_line_id=valuation_line_id,
                campos=payload.campos(),
                bloquear=bloquear,
                **extra,
            )
        except (NoDespejable, PrecioEImporte) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not ok:
            raise HTTPException(
                status_code=404,
                detail="Línea de valoración no encontrada",
            )
        return {
            "ok": True,
            "document_id": document_id,
            "valuation_line_id": valuation_line_id,
        }

    # F-106 R30: «Volver a lo calculado» de una fila editada a mano.
    @app.post("/api/documents/{document_id}/lines/{valuation_line_id}/volver-a-calculado")
    def volver_a_calculado_api(document_id: str, valuation_line_id: int) -> dict:
        if not review_service.volver_a_calculado(
            document_id=document_id, valuation_line_id=valuation_line_id,
        ):
            raise HTTPException(
                status_code=404,
                detail="Línea sin edición que deshacer",
            )
        return {
            "ok": True,
            "document_id": document_id,
            "valuation_line_id": valuation_line_id,
        }

    # F-065 R13, R15: bloquear (guardar sin cambios) y desbloquear una fila.
    @app.post("/api/documents/{document_id}/lines/{valuation_line_id}/bloquear")
    def bloquear_linea_api(document_id: str, valuation_line_id: int) -> dict:
        return _bloqueo(document_id, valuation_line_id, review_service.bloquear_linea)

    @app.post("/api/documents/{document_id}/lines/{valuation_line_id}/desbloquear")
    def desbloquear_linea_api(document_id: str, valuation_line_id: int) -> dict:
        return _bloqueo(document_id, valuation_line_id, review_service.desbloquear_linea)

    def _bloqueo(document_id: str, valuation_line_id: int, accion: Any) -> dict:
        if not accion(document_id=document_id, valuation_line_id=valuation_line_id):
            raise HTTPException(
                status_code=404, detail="Línea de valoración no encontrada en este albarán.",
            )
        return {"ok": True, "document_id": document_id, "valuation_line_id": valuation_line_id}

    @app.delete(
        "/api/documents/{document_id}/lines/{valuation_line_id}/conciliacion"
    )
    def remove_line_conciliacion_api(
        document_id: str,
        valuation_line_id: int,
    ) -> dict:
        ok = review_service.remove_line_conciliacion(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
        )
        if not ok:
            raise HTTPException(
                status_code=400,
                detail="No se pudo borrar la conciliacion (linea no valida).",
            )
        return {
            "ok": True,
            "document_id": document_id,
            "valuation_line_id": valuation_line_id,
        }

    @app.post(
        "/api/documents/{document_id}/lines/by-merge/{merge_line_id}/conciliacion"
    )
    def add_conciliacion_for_merge_line_api(
        document_id: str,
        merge_line_id: int,
        payload: ConciliacionOverridePayload,
    ) -> dict:
        # Trae una conciliacion a una linea NO casada. Admite:
        #  - mode=contract_line + matched_contrato_line_id (salmon Sigrid)
        #  - mode=nueva (salmon Nueva, copia la blanca del albaran)
        if payload.mode == "contract_line" and payload.matched_contrato_line_id is None:
            raise HTTPException(
                status_code=400,
                detail="Se requiere matched_contrato_line_id para mode=contract_line.",
            )
        if payload.mode not in ("contract_line", "nueva"):
            raise HTTPException(
                status_code=400,
                detail="mode no valido (contract_line | nueva).",
            )
        ok = review_service.add_conciliacion_for_merge_line(
            document_id=document_id,
            merge_line_id=merge_line_id,
            mode=payload.mode,
            matched_contrato_line_id=payload.matched_contrato_line_id,
            precio_unitario=payload.precio_unitario,
            descripcion=payload.descripcion,
        )
        if not ok:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo traer la linea de contrato (linea de albaran "
                    "o de contrato no validas)."
                ),
            )
        return {
            "ok": True,
            "document_id": document_id,
            "merge_line_id": merge_line_id,
            "matched_contrato_line_id": payload.matched_contrato_line_id,
        }

    # F-051 (R14-R16, R23): «Almacén (sin partida)» en una línea y
    # «Almacén a todas las líneas». 404 si no se toca nada (línea ajena
    # al documento o documento sin valoración).
    @app.post(
        "/api/documents/{document_id}/lines/{valuation_line_id}/almacen"
    )
    def asignar_almacen_linea_api(
        document_id: str,
        valuation_line_id: int,
    ) -> dict:
        ok = review_service.asignar_almacen_linea(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
        )
        if not ok:
            raise HTTPException(
                status_code=404,
                detail="Línea de valoración no encontrada en este albarán.",
            )
        return {
            "ok": True,
            "document_id": document_id,
            "valuation_line_id": valuation_line_id,
        }

    @app.post("/api/documents/{document_id}/almacen-todas")
    def asignar_almacen_todas_api(document_id: str) -> dict:
        # F-065 R14: las filas guardadas se saltan y se dice cuántas.
        resultado = review_service.asignar_almacen_todas_con_saltos(
            document_id=document_id,
        )
        if not resultado.tocadas and not resultado.saltadas:
            raise HTTPException(
                status_code=404,
                detail="El albarán no tiene líneas valoradas.",
            )
        return {
            "ok": True, "document_id": document_id,
            "lineas": resultado.tocadas, "saltadas": resultado.saltadas,
        }

    @app.post("/api/documents/{document_id}/lines/standalone")
    def add_standalone_line_api(document_id: str) -> dict:
        # Crea una linea salmon SUELTA (sin linea blanca): una valuation
        # line nueva con conciliacion "Nueva" en blanco. El usuario la
        # rellena o la engancha a una linea de contrato desde el combo de
        # descripcion de la salmon. NO toca ninguna linea blanca.
        new_id = review_service.add_standalone_valuation_line(
            document_id=document_id,
        )
        if new_id is None:
            raise HTTPException(
                status_code=400,
                detail="No se pudo crear la linea salmon (documento no valido).",
            )
        return {
            "ok": True,
            "document_id": document_id,
            "valuation_line_id": new_id,
        }

    # ------------------------------------------------------------------ #
    # DESHACER (jul 2026, mismo contrato de API que en partes-front):
    # historial persistente de las ediciones manuales y revertido del
    # más reciente. Alcance POR ALBARÁN (jul 2026): el widget vive
    # SOLO en el detalle (document_detail.html) y siempre manda el
    # ``document_id``; solo se lista/deshace lo hecho en ESE albarán.
    # Lo hecho en otro albarán se deshace entrando en el suyo.
    # ------------------------------------------------------------------ #
    @app.get("/api/undo/list", include_in_schema=False)
    def undo_list(
        document_id: str | None = Query(default=None),
    ) -> JSONResponse:
        if not (document_id or "").strip():
            # Sin albarán no hay historial que enseñar (el widget ya
            # no existe fuera del detalle; esto cubre llamadas viejas
            # o manuales sin romper nada).
            return JSONResponse({"items": []})
        try:
            items = review_service.list_undo(
                document_id=document_id.strip(), limit=15,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("[undo] list falló: %r", exc)
            items = []
        return JSONResponse({"items": items})

    @app.post("/api/undo", include_in_schema=False)
    def undo_apply(
        document_id: str | None = Query(default=None),
    ) -> JSONResponse:
        if not (document_id or "").strip():
            return JSONResponse({
                "ok": False,
                "error": (
                    "Falta document_id: el deshacer es por albarán "
                    "(abre el detalle del albarán a deshacer)."
                ),
            })
        try:
            res = review_service.undo_last(
                document_id=document_id.strip(),
            )
        except (AlbaranBloqueadoError, AlbaranAprobadoError) as exc:
            # F-053 R25 y F-065 R4: deshacer con alta bloqueante o en un
            # aprobado, no.
            return JSONResponse(
                status_code=409,
                content={"ok": False, "error": exc.aviso, "detail": exc.aviso},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[undo] fallo al deshacer")
            res = {"ok": False, "error": str(exc)}
        return JSONResponse(res)

    @app.post("/api/documents/{document_id}/lines/from-contrato")
    def add_lines_from_contrato_api(
        document_id: str,
        payload: TraerLineasBody = Body(...),
    ) -> dict:
        # (F-065 R23) Una fila Contrato por cada línea de contrato elegida,
        # con su cantidad (obligatoria y ≠ 0: si falta, 422 de la
        # validación), partida, descripción, unidad y precio del contrato.
        creadas = review_service.add_valuation_lines_from_contrato(
            document_id=document_id,
            lineas=[(linea.contrato_line_id, linea.cantidad) for linea in payload.lineas],
        )
        if creadas == 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Ninguna de las líneas seleccionadas pertenece a un "
                    "contrato de este albarán."
                ),
            )
        return {
            "ok": True,
            "document_id": document_id,
            "created": creadas,
        }

    @app.post("/api/documents/{document_id}/lines/{valuation_line_id}/dividir")
    def dividir_linea_api(
        document_id: str,
        valuation_line_id: int,
        payload: DivisionBody = Body(...),
    ) -> Any:
        # (F-065 R29, R30) De 2 a 20 partes (si no, 422 de la validación).
        # 404 si la fila no es del documento; 409 con alta bloqueante,
        # aprobado o fila guardada (manejador común); 422 con el motivo si
        # el reparto no vale (``RepartoInvalido``), sin cambios.
        try:
            hecha = review_service.dividir_linea(
                document_id=document_id,
                valuation_line_id=valuation_line_id,
                partes=payload.partes,
            )
        except RepartoInvalido as exc:
            return JSONResponse(status_code=422, content={"detail": str(exc)})
        if hecha is None:
            raise HTTPException(
                status_code=404, detail="Línea de valoración no encontrada en este albarán.",
            )
        return {
            "ok": True,
            "document_id": document_id,
            "valuation_line_id": valuation_line_id,
            "partes": hecha.partes,
        }

    # ------------------------------------------------------------------ #
    # F-053 · Alta en Sigrid desde la ficha y producto de las líneas.
    # ------------------------------------------------------------------ #
    @app.get("/api/documents/{document_id}/alta-sigrid/fase", include_in_schema=False)
    def fase_alta_sigrid_api(document_id: str) -> dict:
        """F-077 R18: fase del panel del alta, para el sondeo de la ficha
        (R19). Solo lectura: ni escribe el alta ni publica (R20)."""
        fase = review_service.fase_alta(document_id)
        if fase is None:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        return {"fase": fase}

    @app.post("/documents/{document_id}/alta-sigrid/solicitar", include_in_schema=False)
    def solicitar_alta_sigrid(document_id: str, request: Request) -> RedirectResponse:
        """R30: «Solicitar alta en Sigrid» (``accion="alta"``)."""
        resultado = review_service.solicitar_alta_sigrid(
            document_id=document_id, solicitado_por=_reviewer_from_request(request),
        )
        return _a_la_ficha(document_id, MENSAJES_ALTA["alta"][resultado])

    @app.post(
        "/documents/{document_id}/alta-sigrid/reintentar-adjunto",
        include_in_schema=False,
    )
    def reintentar_adjunto_sigrid(document_id: str, request: Request) -> RedirectResponse:
        """R30/R23 (v8, O1 = a): «Reintentar adjunto» (``accion="alta"``).
        Solo publica: R25 no la bloquea."""
        resultado = review_service.reintentar_adjunto_sigrid(
            document_id=document_id, solicitado_por=_reviewer_from_request(request),
        )
        return _a_la_ficha(document_id, MENSAJES_ALTA["reintentar_adjunto"][resultado])

    @app.post(
        "/documents/{document_id}/alta-sigrid/verificar-anulacion",
        include_in_schema=False,
    )
    def verificar_anulacion_sigrid(document_id: str, request: Request) -> RedirectResponse:
        """R28: «Ya lo he anulado en Sigrid» (``accion="verificar_anulacion"``)."""
        resultado = review_service.verificar_anulacion_sigrid(
            document_id=document_id, solicitado_por=_reviewer_from_request(request),
        )
        return _a_la_ficha(document_id, MENSAJES_ALTA["verificar_anulacion"][resultado])

    @app.post("/api/documents/{document_id}/lineas-valoradas/{valuation_line_id}/producto-sigrid")
    def elegir_producto_sigrid_api(
        document_id: str,
        valuation_line_id: int,
        payload: ProductoSigridBody = Body(...),
    ) -> dict:
        """R41: producto de una sin vincular (``null`` = por defecto); 400
        si la línea es ajena o vinculada, el código no es admitido o la
        feature está apagada; 409 con alta bloqueante (R25)."""
        resultado = review_service.elegir_producto_sigrid(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
            producto=payload.producto,
        )
        if resultado != "guardado":
            raise HTTPException(status_code=400, detail=MENSAJES_PRODUCTO[resultado])
        return {
            "ok": True,
            "document_id": document_id,
            "valuation_line_id": valuation_line_id,
            "producto": payload.producto,
        }

    @app.exception_handler(AlbaranBloqueadoError)
    @app.exception_handler(AlbaranSinValorarError)
    @app.exception_handler(AlbaranAprobadoError)
    @app.exception_handler(LineaBloqueadaError)
    @app.exception_handler(LineasIncompletasError)
    @app.exception_handler(ValoracionCambiadaError)
    @app.exception_handler(ValoracionDeOtroContratoError)
    @app.exception_handler(CabeceraIncompletaError)
    async def alta_sigrid_error_handler(
        request: Request,
        exc: (
            AlbaranBloqueadoError | AlbaranSinValorarError | AlbaranAprobadoError
            | LineaBloqueadaError | LineasIncompletasError | ValoracionCambiadaError
            | ValoracionDeOtroContratoError | CabeceraIncompletaError
        ),
    ) -> Response:
        """F-053 R25/R37, F-065 R4/R14/R20, F-106 R28, F-115 R13 y F-108 R11: nada cambió (el repositorio no
        confirmó). En la API, 409 con el aviso; en un formulario, de vuelta a
        la ficha con él."""
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=409, content={"detail": exc.aviso})
        return _a_la_ficha(exc.document_id, exc.aviso)

    @app.exception_handler(FechaAlbaranNoValidaError)
    @app.exception_handler(NumeroAlbaranNoValidoError)
    async def cabecera_no_valida_handler(
        _: Request, exc: FechaAlbaranNoValidaError | NumeroAlbaranNoValidoError,
    ) -> JSONResponse:
        """F-108 R7, R9: fecha no admitida o número demasiado largo; nada
        cambió. 422 con el aviso como TEXTO (las vías del PUT de la ficha
        enseñan ``detail`` tal cual; una lista saldría «[object Object]»)."""
        return JSONResponse(status_code=422, content={"detail": exc.aviso})

    @app.exception_handler(RequestValidationError)
    async def validacion_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        """El 422 de siempre, pero sin romperse con un ``NaN``/``Infinity`` en el
        cuerpo (F-065 CR1): el error lo devuelve en ``input`` y el JSON de la
        respuesta no admite números no finitos (sería un 500)."""
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(sin_no_finitos(exc.errors()))},
        )

    @app.exception_handler(KeyError)
    async def key_error_handler(_: Request, exc: KeyError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    return app


def sin_no_finitos(valor: Any) -> Any:
    """(F-065 CR1) ``valor`` con cada ``NaN``/``±inf`` (en listas, tuplas y
    diccionarios, a cualquier profundidad) cambiado por su texto, para poder
    devolverlo en JSON."""
    if isinstance(valor, float) and not math.isfinite(valor):
        return str(valor)
    if isinstance(valor, dict):
        return {clave: sin_no_finitos(v) for clave, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [sin_no_finitos(v) for v in valor]
    return valor


def _parse_optional_float(value: str | None, *, field_name: str) -> float | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "type": "float_parsing",
                    "loc": ["query", field_name],
                    "msg": "Input should be a valid number, unable to parse string as a number",
                    "input": value,
                }
            ],
        ) from exc


def _query_string(
    filters: DocumentListFilters,
    overrides: dict[str, Any] | None = None,
) -> str:
    payload = filters.model_dump()
    if overrides:
        payload.update(overrides)
    return urlencode(
        {
            key: value
            for key, value in payload.items()
            if value not in (None, "")
        }
    )


def _filters_from_query(
    request: Request,
    *,
    default_page_size: int,
) -> DocumentListFilters:
    """Reconstruye los filtros de la BANDEJA a partir de la query del
    detalle. Sirve para que los botones anterior/siguiente recorran el
    mismo conjunto ordenado que el revisor venia mirando en la lista.

    A diferencia de la ruta ``/documents`` (que usa ``Query(...)`` con
    validacion estricta y devuelve 422 si algo no parsea), aqui somos
    TOLERANTES: un parametro roto en la URL no debe tumbar la pagina de
    detalle. Los numeros que no parsean quedan en None y page/page_size
    se acotan al rango valido del modelo.
    """
    q = request.query_params

    def _f(name: str) -> float | None:
        raw = q.get(name)
        if raw is None or not raw.strip():
            return None
        try:
            return float(raw.strip())
        except ValueError:
            return None

    def _i(name: str, default: int) -> int:
        raw = q.get(name)
        if raw is None or not raw.strip():
            return default
        try:
            return int(raw.strip())
        except ValueError:
            return default

    page = max(1, _i("page", 1))
    page_size = min(100, max(1, _i("page_size", default_page_size)))

    return DocumentListFilters(
        search=q.get("search"),
        proveedor=q.get("proveedor"),
        fecha=q.get("fecha"),
        recepcion=q.get("recepcion"),
        obra=q.get("obra"),
        obra_codigo=q.get("obra_codigo"),
        proveedor_cif=q.get("proveedor_cif"),
        albaran=q.get("albaran"),
        contrato=q.get("contrato"),
        lineas=q.get("lineas"),
        min_importe=_f("min_importe"),
        max_importe=_f("max_importe"),
        approved=q.get("approved", "pending"),
        review_required=q.get("review_required", "all"),
        min_confidence=_f("min_confidence"),
        max_confidence=_f("max_confidence"),
        sort_by=q.get("sort_by", "confidence_pct_calc"),
        sort_dir=q.get("sort_dir", "asc"),
        vista=q.get("vista", "activos"),
        page=page,
        page_size=page_size,
    )


def _guess_media_type(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def _preview_error_response(
    *,
    title: str,
    message: str,
    external_url: str | None,
) -> HTMLResponse:
    safe_title = html.escape(title)
    safe_message = html.escape(message)
    safe_external = html.escape(external_url) if external_url else None
    open_link_html = (
        f'<p><a href="{safe_external}" target="_blank" rel="noreferrer">'
        "Abrir documento en SharePoint"
        "</a></p>"
        if safe_external
        else ""
    )
    payload = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>Vista previa no disponible</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f8fafc; color: #1f2937; margin: 0; padding: 24px; }}
            .card {{ max-width: 720px; margin: 0 auto; background: #ffffff; border: 1px solid #dbe4f0; border-radius: 12px; padding: 24px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
            h1 {{ margin-top: 0; font-size: 22px; }}
            p {{ line-height: 1.5; }}
            a {{ color: #2563eb; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>{safe_title}</h1>
            <p>{safe_message}</p>
            {open_link_html}
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=payload, status_code=200)