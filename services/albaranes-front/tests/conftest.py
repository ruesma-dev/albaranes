# tests/conftest.py
"""Ancla la raiz de sv4 en ``sys.path`` y da una BBDD SQLite en memoria.

sv4 no tenia directorio de tests: ``bash harness/init.sh`` lo avisaba en
cada pasada («NADIE esta comprobando los tests de sv4-front»). El aviso
tenia razon — el fallo del round trip 2 de F-019 vivia justo aqui.

Los tests importan ``domain`` e ``infrastructure`` como paquetes de
primer nivel (igual que hace el servicio al arrancar). Cuando la suite
se lanza desde la raiz del monorepo esos imports fallarian; este
conftest mete la raiz del servicio en ``sys.path`` en vez de depender
del cwd. Mismo patron que los conftest de sv2, sv5 y sv6.

NINGUN test de este directorio toca red, la BBDD real ni un LLM: el
repositorio recibe una sesion de SQLAlchemy sobre **SQLite en memoria**
con las dos tablas de valoracion creadas al vuelo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))


#: Subconjunto de ``albaran_valuations``, ``albaran_line_valuations`` y
#: ``albaran_documents_merge`` que tocan el recalculo de importes y la
#: trazabilidad de motivos. Los tipos son los de
#: ``services/albaran-valoracion-persist/infrastructure/database/
#: schema_contribution.py`` (sv6 es el dueno del schema de valoracion) y
#: los de ``infrastructure/database/orm_models.py`` para el merge; en
#: SQLite DOUBLE PRECISION se acepta tal cual.
#:
#: Es un SUBCONJUNTO a proposito: replicar el schema entero aqui seria
#: una segunda copia que divergiria del dueno a la primera migracion.
#: Se anaden columnas cuando un test las necesita.
#:
#: Las columnas que en el schema real son NOT NULL aqui van NULABLES
#: salvo ``importe_source``: un test siembra la fila minima que su caso
#: necesita, no una fila valida de produccion. Lo que se prueba es el
#: comportamiento del repositorio, no las restricciones de sv6.
_DDL = (
    """
    CREATE TABLE albaran_valuations (
        id                        VARCHAR(64) PRIMARY KEY,
        document_id               VARCHAR(64) NOT NULL,
        contrato_codigo           VARCHAR(64),
        status                    VARCHAR(32),
        provider_ia               VARCHAR(32),
        model_name                VARCHAR(100),
        total_valorado            DOUBLE PRECISION,
        total_lines               INTEGER,
        lines_matched_exact       INTEGER,
        lines_matched_semantic    INTEGER,
        lines_matched_price_only  INTEGER,
        lines_unmatched           INTEGER,
        review_required           BOOLEAN NOT NULL DEFAULT 0,
        review_reasons_json       TEXT,
        created_at_utc            VARCHAR(64),
        updated_at_utc            VARCHAR(40)
    )
    """,
    """
    CREATE TABLE albaran_line_valuations (
        id                            INTEGER PRIMARY KEY,
        valuation_id                  VARCHAR(64) NOT NULL,
        merge_line_id                 INTEGER,
        matched_contrato_line_id      INTEGER,
        derived_contrato_line_id      INTEGER,
        precio_unitario_contrato_db   DOUBLE PRECISION,
        precio_unitario_pdf_inferido  DOUBLE PRECISION,
        precio_unitario_final         DOUBLE PRECISION,
        precio_unitario_source        VARCHAR(32),
        precio_unitario_agreement     VARCHAR(32),
        unidad_albaran                VARCHAR(32),
        unidad_contrato               VARCHAR(32),
        unidad_categoria              VARCHAR(32),
        unidad_category_match         BOOLEAN,
        factor_conversion             DOUBLE PRECISION,
        cantidad_albaran              DOUBLE PRECISION,
        cantidad_convertida           DOUBLE PRECISION,
        importe_calculado             DOUBLE PRECISION,
        importe_albaran_declarado     DOUBLE PRECISION,
        importe_source                VARCHAR(32) NOT NULL,
        codigo_partida_albaran        VARCHAR(64),
        codigo_partida_final          VARCHAR(64),
        partida_action                VARCHAR(32),
        match_confidence_pct          DOUBLE PRECISION,
        match_method                  VARCHAR(32),
        descuento_albaran_aplicado    DOUBLE PRECISION,
        codigo_externo                VARCHAR(64),
        line_kind                     VARCHAR(32),
        parent_merge_line_id          INTEGER,
        modifier_source               VARCHAR(32),
        modifier_reason               TEXT,
        descripcion_linea             TEXT,
        review_required               BOOLEAN NOT NULL DEFAULT 0,
        review_reasons_json           TEXT
    )
    """,
    # F-036: la trazabilidad (R23, R24) toca tambien la cabecera del
    # merge. Solo las tres columnas que interviene la purga de motivos
    # (`_depurar_motivos_documento_in_session`): la tabla real la
    # gobierna sv3 y tiene cuarenta y pico.
    """
    CREATE TABLE albaran_documents_merge (
        id                   VARCHAR(64) PRIMARY KEY,
        proveedor_cif        VARCHAR(64),
        review_reasons_json  TEXT
    )
    """,
)


@pytest.fixture
def sesion():
    """Sesion de SQLAlchemy sobre SQLite en memoria con el schema puesto."""
    motor = create_engine("sqlite://")
    with motor.begin() as conexion:
        for sentencia in _DDL:
            conexion.execute(text(sentencia))
    with Session(motor) as sesion_abierta:
        yield sesion_abierta
    motor.dispose()


class _PeticionFalsa:
    """Lo unico que la plantilla base pide de ``request``: ``url_for``."""

    @staticmethod
    def url_for(nombre: str, path: str = "") -> str:
        return f"/{nombre}/{path}"


def _importe_eur(valor):
    """Stand-in del filtro ``importe_eur`` de ``interface_adapters.web.app``.

    NO se importa el de produccion a proposito: ese modulo arrastra
    FastAPI y la suite de sv4 se ejecuta con el interprete del arnes, que
    no lo tiene. Lo que los tests de render comprueban es QUE VALOR llega
    al filtro (el importe persistido o el producto recalculado en Jinja),
    no como se formatea; el formato va en formato espanol solo para que
    las aserciones se lean como lo que ve el revisor.
    """
    if valor is None:
        return "—"
    entero, _, decimal = f"{float(valor):,.2f}".partition(".")
    return f"{entero.replace(',', '.')},{decimal} €"


@pytest.fixture
def render_detalle():
    """Renderiza ``templates/document_detail.html`` y devuelve el HTML.

    Sin FastAPI ni servidor: Jinja2 a pelo sobre el directorio real de
    plantillas del servicio, con un ``request`` falso y los filtros
    minimos que la plantilla usa.
    """
    pytest.importorskip(
        "jinja2",
        reason=(
            "jinja2 es dependencia declarada de sv4 (requirements.txt); "
            "sin ella no se puede comprobar lo que pinta la plantilla"
        ),
    )
    import json

    from jinja2 import Environment, FileSystemLoader, select_autoescape

    entorno = Environment(
        loader=FileSystemLoader(str(RAIZ_SERVICIO / "templates")),
        autoescape=select_autoescape(["html"]),
    )
    entorno.filters["importe_eur"] = _importe_eur
    entorno.filters["fecha_int_iso"] = lambda valor: str(valor or "—")
    entorno.filters["tojson_pretty"] = lambda valor: json.dumps(
        valor, ensure_ascii=False, indent=2
    )
    entorno.filters["fecha_hora_local"] = lambda valor: str(valor or "—")
    entorno.filters["fecha_local"] = lambda valor: str(valor or "—")
    entorno.filters["hora_local"] = lambda valor: str(valor or "—")
    entorno.globals["view_label"] = str
    entorno.globals["asset_version"] = "test"

    def _render(document, **extra):
        contexto = {
            "request": _PeticionFalsa(),
            "title": "Albaranes · test",
            "document": document,
            "document_json": "{}",
            "message": None,
            "preview_enabled": False,
            "document_preview_url": f"/documents/{document.id}/preview",
            "current_view": document.view_mode,
            "available_views": document.available_views,
            "view_label": str,
            "back_to_list_url": "/documents",
            "nav_prev_url": None,
            "nav_next_url": None,
        }
        contexto.update(extra)
        return entorno.get_template("document_detail.html").render(**contexto)

    return _render


#: Documento y valoracion de referencia de los tests de render: la
#: linea de residuos de SALMEDINA SS-0000589 tal cual la dejo sv6.
DOCUMENT_ID_RENDER = "f036-doc-0000-0000-000000000589"
VALUATION_ID_RENDER = "f036-val-0000-0000-000000000589"


@pytest.fixture
def linea_valorada():
    """Factoria de ``LineValuationPayload`` (la linea de SS-0000589)."""
    from domain.models.review_models import LineValuationPayload

    def _linea(**campos):
        base = {
            "valuation_line_id": 900,
            "merge_line_id": 500,
            "precio_unitario_final": 120.0,
            "cantidad_albaran": 6.0,
            "cantidad_convertida": 1.0,
            "factor_conversion": None,
            "importe_calculado": 120.0,
            "importe_source": "declared_albaran",
            "review_reasons": ["residuos_contenedores"],
            "review_required": True,
        }
        base.update(campos)
        return LineValuationPayload(**base)

    return _linea


@pytest.fixture
def fila_detalle():
    """Factoria de ``DisplayLine`` con su bloque de conciliacion."""
    from domain.models.review_models import ConciliacionDisplay, DisplayLine

    def _fila(conciliacion=None, **campos):
        conc = ConciliacionDisplay(
            **{
                "kind": "assigned",
                "codigo_partida": "01.01",
                "descripcion": "RETIRADA CONTENEDOR RCD",
                "unidad": "UD",
                "unitario": 120.0,
                "descuento": None,
                **(conciliacion or {}),
            }
        )
        base = {
            "line_kind": "from_albaran",
            "merge_line_id": 500,
            "valuation_line_id": 900,
            "line_index": 1,
            "concepto": "RETIRADA CONTENEDOR RCD",
            "cantidad": 6.0,
            "unidad": "M3",
            "precio_unitario": 120.0,
            "importe": 120.0,
            "is_valued": True,
            "concilia": conc,
        }
        base.update(campos)
        return DisplayLine(**base)

    return _fila


@pytest.fixture
def documento_detalle():
    """Factoria de ``DocumentDetailPayload`` listo para renderizar."""
    import json as _json

    from domain.models.review_models import (
        DocumentDetailPayload,
        ValuationPayload,
    )

    def _documento(
        lineas_valoracion=(),
        motivos_documento=None,
        display=(),
        is_editable=True,
    ):
        valoracion = None
        if lineas_valoracion:
            valoracion = ValuationPayload(
                valuation_id=VALUATION_ID_RENDER,
                contrato_codigo="C-001",
                status="completed",
                total_valorado=120.0,
                total_lines=len(lineas_valoracion),
                review_required=True,
                lines_by_merge_line_id={
                    linea.merge_line_id: linea
                    for linea in lineas_valoracion
                    if linea.merge_line_id is not None
                },
                synthetic_lines=[
                    linea
                    for linea in lineas_valoracion
                    if linea.merge_line_id is None
                ],
            )
        return DocumentDetailPayload(
            id=DOCUMENT_ID_RENDER,
            is_editable=is_editable,
            source_filename="SS-0000589.pdf",
            provider_origin="merge",
            model_name="—",
            created_at_utc="2026-08-19T10:00:00Z",
            proveedor_cif="B87654321",
            review_reasons_json=(
                _json.dumps(motivos_documento) if motivos_documento else None
            ),
            review_required=bool(motivos_documento),
            display_lines=list(display),
            valuation=valoracion,
        )

    return _documento


@pytest.fixture
def repositorio():
    """``AlbaranReviewRepository`` sin factoria de sesiones.

    Los metodos bajo prueba reciben la sesion por parametro y no tocan
    ``self._session_factory``, asi que no hace falta motor real.
    """
    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    return AlbaranReviewRepository(None)  # type: ignore[arg-type]
