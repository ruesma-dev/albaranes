# tests/test_f052_rastro_detalle.py
"""F-052 T11 · sv4 lee el rastro de la búsqueda de contratos y lo pone en el detalle.

sv3 (dueño del schema) sella cuatro columnas en ``albaran_documents_merge``
(R20, R21). sv4 las declara en su ORM con las mismas longitudes, el
payload del detalle gana ``busqueda_contratos`` (``BusquedaContratosVista``)
y el repositorio lo rellena con ``estado_busqueda`` (R27) al montar el
detalle del merge.

Sin red ni BBDD real: SQLite en memoria con las tablas del ORM de sv4.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from domain.models.review_models import (
    BUSQUEDA_NINGUNO,
    ESTADO_BUSQUEDA_DESFASADA,
    ESTADO_BUSQUEDA_SIN_RASTRO,
    ESTADO_BUSQUEDA_VIGENTE,
    BusquedaContratosVista,
    DocumentDetailPayload,
)

DOC_ID = "f052-doc-0000-0000-0000-000026122"
COLUMNAS_RASTRO = (
    "contratos_busqueda_cif",
    "contratos_busqueda_obra",
    "contratos_busqueda_resultado",
    "contratos_busqueda_at_utc",
)
FECHA = "2026-09-30T10:15:00+00:00"


@pytest.fixture
def sesion_merge():
    """SQLite en memoria con las tablas del ORM de sv4 (merge y líneas)."""
    from infrastructure.database.orm_models import Base

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    with Session(motor) as sesion:
        yield sesion
    motor.dispose()


def _sembrar(sesion, *, cif="B82899550", obra="0691", rastro=None):
    """Inserta el merge con SQL crudo y los nombres de columna de sv3."""
    valores = {
        "id": DOC_ID,
        "provider_origin": "merge",
        "source_filename": "SS-0026122.pdf",
        "source_mime_type": "application/pdf",
        "source_sha256": "0" * 64,
        "prompt_key": "p",
        "schema_name": "s",
        "model_name": "m",
        "raw_extraction_json": "{}",
        "created_at_utc": "2026-09-29T08:00:00+00:00",
        "is_active": True,
        "approved": False,
        "proveedor_cif": cif,
        "obra_codigo": obra,
    }
    valores.update(rastro or {})
    columnas = ", ".join(valores)
    marcas = ", ".join(f":{c}" for c in valores)
    sesion.execute(
        text(f"INSERT INTO albaran_documents_merge ({columnas}) VALUES ({marcas})"),
        valores,
    )
    sesion.commit()


def _detalle(repositorio, sesion):
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    doc = sesion.get(AlbaranDocumentMergeOrm, DOC_ID)
    return repositorio._build_merge_detail(
        merge_doc=doc,
        available_views=[],
        provider_snapshots=[],
        contratos=[],
        selected_contrato_codigo=None,
    )


def test_f052_t11_el_orm_declara_las_cuatro_columnas_con_las_longitudes_de_sv3():
    """Mismas longitudes que el ``ALTER`` de sv3 (``phase2_ddl.py``)."""
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    tabla = AlbaranDocumentMergeOrm.__table__
    ddl_sv3 = (
        Path(__file__).resolve().parents[2]
        / "albaranes-persistencia" / "infrastructure" / "database"
        / "phase2_ddl.py"
    ).read_text(encoding="utf-8")
    for columna in COLUMNAS_RASTRO:
        assert columna in tabla.columns, f"el ORM de sv4 no declara {columna}"
        m = re.search(rf"{columna} VARCHAR\((\d+)\)", ddl_sv3)
        assert m, f"sv3 ya no declara {columna} como VARCHAR"
        assert tabla.columns[columna].type.length == int(m.group(1)), columna
        assert tabla.columns[columna].nullable


def test_f052_t11_el_payload_expone_busqueda_contratos_opcional():
    campo = DocumentDetailPayload.model_fields["busqueda_contratos"]
    assert campo.default is None


def test_f052_t11_el_detalle_lleva_el_rastro_vigente(repositorio, sesion_merge):
    _sembrar(
        sesion_merge,
        cif="B 82899550",
        obra="691",
        rastro={
            "contratos_busqueda_cif": "B82899550",
            "contratos_busqueda_obra": "0691",
            "contratos_busqueda_resultado": BUSQUEDA_NINGUNO,
            "contratos_busqueda_at_utc": FECHA,
        },
    )
    detalle = _detalle(repositorio, sesion_merge)
    assert detalle.busqueda_contratos == BusquedaContratosVista(
        estado=ESTADO_BUSQUEDA_VIGENTE,
        cif="B82899550",
        obra="0691",
        fecha=FECHA,
        resultado=BUSQUEDA_NINGUNO,
    )


def test_f052_t11_el_detalle_compara_con_el_cif_actual(repositorio, sesion_merge):
    """SS-0026122: el revisor corrigió el CIF y guardó; el rastro es el viejo."""
    _sembrar(
        sesion_merge,
        cif="B82899550",
        rastro={
            "contratos_busqueda_cif": "B82890580",
            "contratos_busqueda_obra": "0691",
            "contratos_busqueda_resultado": BUSQUEDA_NINGUNO,
            "contratos_busqueda_at_utc": FECHA,
        },
    )
    vista = _detalle(repositorio, sesion_merge).busqueda_contratos
    assert vista.estado == ESTADO_BUSQUEDA_DESFASADA
    assert vista.cif == "B82890580"


def test_f052_t11_documento_anterior_a_f052_sin_rastro(repositorio, sesion_merge):
    _sembrar(sesion_merge)
    vista = _detalle(repositorio, sesion_merge).busqueda_contratos
    assert vista == BusquedaContratosVista(estado=ESTADO_BUSQUEDA_SIN_RASTRO)


def test_f052_t11_la_serializacion_del_detalle_incluye_el_estado(
    repositorio, sesion_merge,
):
    """El JS sondea ``GET /api/documents/{id}`` y mira este campo (T13 bis)."""
    _sembrar(sesion_merge)
    volcado = _detalle(repositorio, sesion_merge).model_dump()
    assert volcado["busqueda_contratos"]["estado"] == ESTADO_BUSQUEDA_SIN_RASTRO
