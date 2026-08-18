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


#: Subconjunto de ``albaran_valuations`` y ``albaran_line_valuations``
#: que toca el recalculo de importes. Los tipos son los de
#: ``services/albaran-valoracion-persist/infrastructure/database/
#: schema_contribution.py`` (sv6 es el dueno del schema); en SQLite
#: DOUBLE PRECISION se acepta tal cual.
_DDL = (
    """
    CREATE TABLE albaran_valuations (
        id              VARCHAR(64) PRIMARY KEY,
        document_id     VARCHAR(64) NOT NULL,
        total_valorado  DOUBLE PRECISION,
        updated_at_utc  VARCHAR(40)
    )
    """,
    """
    CREATE TABLE albaran_line_valuations (
        id                          INTEGER PRIMARY KEY,
        valuation_id                VARCHAR(64) NOT NULL,
        merge_line_id               INTEGER,
        precio_unitario_final       DOUBLE PRECISION,
        factor_conversion           DOUBLE PRECISION,
        cantidad_albaran            DOUBLE PRECISION,
        cantidad_convertida         DOUBLE PRECISION,
        importe_calculado           DOUBLE PRECISION,
        importe_albaran_declarado   DOUBLE PRECISION,
        importe_source              VARCHAR(32) NOT NULL,
        descuento_albaran_aplicado  DOUBLE PRECISION
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
