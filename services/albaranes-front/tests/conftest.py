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
