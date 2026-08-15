# tests/test_f003_mapeo_campos_leidos.py
"""F-003 · Los campos leidos llegan de sv2 a las tablas de sv3 (R3).

El importe de linea impreso y el total del albaran no existian en el
pipeline. Aqui se comprueba la cadena completa DENTRO de sv3:

  envelope de sv2 -> modelos de extraccion -> merge -> filas ORM
  (raw y merge) + las columnas nuevas en el DDL idempotente.

Sin red ni BBDD: se construyen objetos ORM en memoria (sin sesion) y se
inspecciona la lista de sentencias DDL como texto.
"""
from __future__ import annotations

import json

import pytest

from application.services.albaran_confidence_service import (
    AlbaranConfidenceService,
)
from domain.models.extraction_models import (
    CabeceraAlbaran,
    DocumentoAlbaran,
    LineaAlbaran,
)
from infrastructure.database import schema_contribution
from infrastructure.database.orm_models import (
    AlbaranLineMergeOrm,
    AlbaranLineOrm,
)
from infrastructure.database.sqlalchemy_albaran_repository import (
    SqlAlchemyAlbaranRepository,
)


# ---------------------------------------------------------------------
# R3 · El envelope de sv2 valida en sv3 (extra='forbid' en los dos lados)
# ---------------------------------------------------------------------


def test_f003_r3_el_envelope_con_campos_nuevos_valida_en_sv3() -> None:
    """Si sv3 no declara los campos, el envelope de sv2 REBOTA entero:
    StrictSchemaModel prohibe los extras."""
    documento = DocumentoAlbaran.model_validate(
        {
            "cabecera": {
                "numero_albaran": "A-1",
                "importe_total": 191.40,
                "importe_total_incluye_iva": False,
            },
            "lineas": [
                {
                    "concepto": "GASOLEO B",
                    "cantidad": 120.55,
                    "precio": 1.5877,
                    "descuentos": [5.0, 2.0],
                    "importe": 191.40,
                }
            ],
        }
    )

    assert documento.cabecera.importe_total == pytest.approx(191.40)
    assert documento.cabecera.importe_total_incluye_iva is False
    assert documento.lineas[0].importe == pytest.approx(191.40)
    assert documento.lineas[0].descuentos == [5.0, 2.0]


def test_f003_r3_el_envelope_antiguo_sigue_validando_en_sv3() -> None:
    documento = DocumentoAlbaran.model_validate(
        {
            "cabecera": {"numero_albaran": "A-1"},
            "lineas": [{"concepto": "ARENA", "cantidad": 1.0}],
        }
    )

    assert documento.cabecera.importe_total is None
    assert documento.lineas[0].importe is None
    assert documento.lineas[0].descuentos is None


# ---------------------------------------------------------------------
# R3 · Las columnas nuevas estan en el DDL idempotente (raw y merge)
# ---------------------------------------------------------------------


@pytest.fixture(scope="module")
def ddl() -> str:
    return "\n".join(sql for _, sql in schema_contribution.get_ddl_statements())


@pytest.mark.parametrize(
    "tabla,columna,tipo",
    [
        ("albaran_lines", "importe", "DOUBLE PRECISION"),
        ("albaran_lines_merge", "importe", "DOUBLE PRECISION"),
        ("albaran_lines", "descuentos_json", "TEXT"),
        ("albaran_lines_merge", "descuentos_json", "TEXT"),
        ("albaran_documents", "importe_total", "DOUBLE PRECISION"),
        ("albaran_documents_merge", "importe_total", "DOUBLE PRECISION"),
        ("albaran_documents", "importe_total_incluye_iva", "BOOLEAN"),
        ("albaran_documents_merge", "importe_total_incluye_iva", "BOOLEAN"),
    ],
)
def test_f003_r3_el_ddl_anade_la_columna(
    ddl: str, tabla: str, columna: str, tipo: str,
) -> None:
    esperado = (
        f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS {columna} {tipo}"
    )
    assert esperado in " ".join(ddl.split())


def test_f003_r3_el_ddl_de_las_columnas_nuevas_es_idempotente(ddl: str) -> None:
    """Ningun ALTER de esta feature puede reventar en el segundo arranque."""
    alters = [
        linea
        for linea in ddl.splitlines()
        if linea.startswith("ALTER TABLE")
        and any(
            columna in linea
            for columna in ("importe", "descuentos_json")
        )
    ]

    assert alters, "no hay ALTERs de las columnas nuevas"
    for linea in alters:
        assert "ADD COLUMN IF NOT EXISTS" in linea


# ---------------------------------------------------------------------
# R3 · El merge de 3 proveedores no se come los campos nuevos
# ---------------------------------------------------------------------


def _linea(**kwargs) -> LineaAlbaran:
    base = {"concepto": "GASOLEO B", "cantidad": 120.55, "precio": 1.5877}
    base.update(kwargs)
    return LineaAlbaran(**base)


def test_f003_r3_el_merge_conserva_el_importe_leido() -> None:
    servicio = AlbaranConfidenceService()

    resultado = servicio._build_line_from_triple(
        gemini_line=_linea(importe=191.40),
        openai_line=_linea(importe=191.40),
        claude_line=None,
        gemini_index=1,
        openai_index=1,
        claude_index=None,
        line_match_score=1.0,
        primary_provider="gemini",
    )

    assert resultado.merged_line.importe == pytest.approx(191.40)


def test_f003_r3_el_merge_conserva_la_lista_de_descuentos() -> None:
    servicio = AlbaranConfidenceService()

    resultado = servicio._build_line_from_triple(
        gemini_line=_linea(descuentos=[5.0, 2.0]),
        openai_line=_linea(descuentos=None),
        claude_line=None,
        gemini_index=1,
        openai_index=1,
        claude_index=None,
        line_match_score=1.0,
        primary_provider="gemini",
    )

    assert resultado.merged_line.descuentos == [5.0, 2.0]


def test_f003_r3_el_merge_rellena_el_importe_desde_el_secundario() -> None:
    """Si el primario no lo leyo y el secundario si, no se pierde."""
    servicio = AlbaranConfidenceService()

    resultado = servicio._build_line_from_triple(
        gemini_line=_linea(importe=None),
        openai_line=_linea(importe=191.40),
        claude_line=None,
        gemini_index=1,
        openai_index=1,
        claude_index=None,
        line_match_score=1.0,
        primary_provider="gemini",
    )

    assert resultado.merged_line.importe == pytest.approx(191.40)


def test_f003_r3_el_merge_de_cabecera_conserva_el_total_y_su_marca() -> None:
    servicio = AlbaranConfidenceService()

    cabecera = servicio._merge_header_triple(
        primary=CabeceraAlbaran(numero_albaran="A-1"),
        secondary=CabeceraAlbaran(
            numero_albaran="A-1",
            importe_total=191.40,
            importe_total_incluye_iva=False,
        ),
        tertiary=None,
    )

    assert cabecera.importe_total == pytest.approx(191.40)
    assert cabecera.importe_total_incluye_iva is False


def test_f003_r3_el_merge_de_cabecera_conserva_el_false_del_iva() -> None:
    """`False` no es 'vacio': un total marcado como base imponible no
    puede degradarse a null por el coalesce."""
    servicio = AlbaranConfidenceService()

    cabecera = servicio._merge_header_triple(
        primary=CabeceraAlbaran(
            importe_total=191.40, importe_total_incluye_iva=False,
        ),
        secondary=CabeceraAlbaran(
            importe_total=231.59, importe_total_incluye_iva=True,
        ),
        tertiary=None,
    )

    assert cabecera.importe_total == pytest.approx(191.40)
    assert cabecera.importe_total_incluye_iva is False


# ---------------------------------------------------------------------
# R3 · Mapeo linea -> fila ORM (raw y merge), con la derivacion en cascada
# ---------------------------------------------------------------------


@pytest.mark.parametrize("orm_cls", [AlbaranLineOrm, AlbaranLineMergeOrm])
def test_f003_r3_la_fila_guarda_el_importe_transcrito(orm_cls) -> None:
    filas = SqlAlchemyAlbaranRepository._build_lines(
        orm_line_cls=orm_cls,
        document_id="doc-1",
        provider_origin="openai",
        source_lines=[_linea(importe=191.40)],
        line_results=None,
    )

    assert filas[0].importe == pytest.approx(191.40)


@pytest.mark.parametrize("orm_cls", [AlbaranLineOrm, AlbaranLineMergeOrm])
def test_f003_r3_la_fila_guarda_los_descuentos_como_json(orm_cls) -> None:
    filas = SqlAlchemyAlbaranRepository._build_lines(
        orm_line_cls=orm_cls,
        document_id="doc-1",
        provider_origin="openai",
        source_lines=[_linea(descuentos=[5.0, 2.0])],
        line_results=None,
    )

    assert json.loads(filas[0].descuentos_json) == [5.0, 2.0]


def test_f003_r3_la_fila_deriva_el_descuento_efectivo_en_cascada() -> None:
    filas = SqlAlchemyAlbaranRepository._build_lines(
        orm_line_cls=AlbaranLineMergeOrm,
        document_id="doc-1",
        provider_origin="gemini_filled",
        source_lines=[_linea(descuento=None, descuentos=[5.0, 2.0])],
        line_results=None,
    )

    assert filas[0].descuento == pytest.approx(6.9)
    # Y la transcripcion fiel sigue ahi, sin machacar.
    assert json.loads(filas[0].descuentos_json) == [5.0, 2.0]


def test_f003_r3_la_fila_respeta_el_descuento_unico_transcrito() -> None:
    filas = SqlAlchemyAlbaranRepository._build_lines(
        orm_line_cls=AlbaranLineMergeOrm,
        document_id="doc-1",
        provider_origin="gemini_filled",
        source_lines=[_linea(descuento=7.0, descuentos=[5.0, 2.0])],
        line_results=None,
    )

    assert filas[0].descuento == pytest.approx(7.0)


def test_f003_r3_la_fila_de_una_linea_antigua_deja_los_campos_a_null() -> None:
    filas = SqlAlchemyAlbaranRepository._build_lines(
        orm_line_cls=AlbaranLineOrm,
        document_id="doc-1",
        provider_origin="openai",
        source_lines=[_linea()],
        line_results=None,
    )

    assert filas[0].importe is None
    assert filas[0].descuentos_json is None
    assert filas[0].descuento is None


# ---------------------------------------------------------------------
# R3 · Coherencia de linea: precio_neto es UNITARIO (efecto de R1)
# ---------------------------------------------------------------------


def test_f003_r3_precio_neto_unitario_impreso_es_coherente() -> None:
    """Con el prompt de R1, precio_neto solo aparece si esta IMPRESO como
    precio unitario neto. La coherencia se mide contra el precio, no
    contra el importe total de la linea."""
    servicio = AlbaranConfidenceService()

    coherente = servicio._is_line_net_consistent(
        _linea(cantidad=10.0, precio=100.0, descuento=10.0, precio_neto=90.0)
    )

    assert coherente is True


def test_f003_r3_el_importe_leido_manda_en_la_coherencia() -> None:
    servicio = AlbaranConfidenceService()

    assert servicio._is_line_net_consistent(
        _linea(cantidad=120.55, precio=1.5877, importe=191.40)
    ) is True
    # El caso x120 con el importe que NO cuadra: incoherente.
    assert servicio._is_line_net_consistent(
        _linea(cantidad=120.55, precio=1.5877, importe=23073.60)
    ) is False


def test_f003_r3_sin_datos_suficientes_la_linea_no_se_penaliza() -> None:
    servicio = AlbaranConfidenceService()

    assert servicio._is_line_net_consistent(_linea(precio=None)) is True
    assert servicio._is_line_net_consistent(LineaAlbaran()) is True


def test_f003_r3_sin_importe_ni_precio_neto_no_hay_nada_que_medir() -> None:
    """La linea trae precio y cantidad pero el albaran no viene valorado:
    no hay contra que contrastar, y eso no es una incoherencia."""
    servicio = AlbaranConfidenceService()

    coherente = servicio._is_line_net_consistent(
        _linea(cantidad=10.0, precio=5.0, importe=None, precio_neto=None)
    )

    assert coherente is True


def test_f003_r3_un_descuadre_moderado_del_importe_se_detecta() -> None:
    """El doble de lo que sale de la aritmetica es incoherente, no solo
    los descuadres astronomicos."""
    servicio = AlbaranConfidenceService()

    assert servicio._is_line_net_consistent(
        _linea(cantidad=10.0, precio=10.0, importe=200.0)
    ) is False


def test_f003_r3_la_tolerancia_del_importe_es_inclusiva() -> None:
    """2 % de 100 = 2: 102 entra justo, 103 ya no."""
    servicio = AlbaranConfidenceService()

    assert servicio._is_line_net_consistent(
        _linea(cantidad=10.0, precio=10.0, importe=102.0)
    ) is True
    assert servicio._is_line_net_consistent(
        _linea(cantidad=10.0, precio=10.0, importe=103.0)
    ) is False


def test_f003_r3_un_precio_neto_moderadamente_falso_se_detecta() -> None:
    servicio = AlbaranConfidenceService()

    assert servicio._is_line_net_consistent(
        _linea(cantidad=10.0, precio=100.0, descuento=10.0, precio_neto=50.0)
    ) is False


def test_f003_r3_la_tolerancia_del_precio_neto_es_inclusiva() -> None:
    """2 % de 100 = 2: un neto de 102 pasa, uno de 103 no."""
    servicio = AlbaranConfidenceService()

    assert servicio._is_line_net_consistent(
        _linea(cantidad=10.0, precio=100.0, precio_neto=102.0)
    ) is True
    assert servicio._is_line_net_consistent(
        _linea(cantidad=10.0, precio=100.0, precio_neto=103.0)
    ) is False
