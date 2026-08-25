# tests/test_f036_r23_r24_trazabilidad.py
"""F-036 · R23-R24: lo que el sistema sabe, el revisor lo ve.

R23 — sv6 sella en cada linea de valoracion POR QUE tomo la decision que
tomo (``residuos_contenedores``, ``residuos_sin_volumen_m3``,
``declared_vs_calculated_mismatch``...) en
``albaran_line_valuations.review_reasons_json``. Hasta F-036 sv4 ni
siquiera leia esa columna: el revisor veia el numero y no el porque, y
la unica salida era abrir la BBDD.

R24 — sv3 sella en el documento motivos con el dato SELLADO dentro:
``proveedor_cif_no_casa:B12345678``. Cuando el revisor corrige el CIF en
la ficha, el motivo se queda ahi con el CIF viejo para siempre. En
SS-0801977 seguia colgado meses despues de haberse corregido.

Sin red, sin BBDD real: SQLite en memoria del ``conftest.py`` de sv4.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

VALUATION_ID = "f036-val-0000-0000-000000000801"
DOCUMENT_ID = "f036-doc-0000-0000-000000000801"


def _sembrar_valoracion(sesion, lineas):
    """Cabecera + lineas de valoracion. ``lineas`` son dicts sueltos."""
    sesion.execute(
        text(
            "INSERT INTO albaran_valuations ("
            "  id, document_id, contrato_codigo, status, total_valorado, "
            "  total_lines, review_required, created_at_utc, updated_at_utc) "
            "VALUES (:id, :doc, 'C-001', 'completed', 120.0, "
            "        :n, 1, '2026-08-19T10:00:00Z', '2026-08-19T10:00:00Z')"
        ),
        {"id": VALUATION_ID, "doc": DOCUMENT_ID, "n": len(lineas)},
    )
    for linea in lineas:
        campos = {
            "id": None,
            "merge_line_id": None,
            "line_kind": "from_albaran",
            "importe_source": "declared_albaran",
            "review_reasons_json": None,
            "review_required": 0,
            "descripcion_linea": None,
        }
        campos.update(linea)
        sesion.execute(
            text(
                "INSERT INTO albaran_line_valuations ("
                "  id, valuation_id, merge_line_id, line_kind, "
                "  importe_source, review_reasons_json, review_required, "
                "  descripcion_linea) "
                "VALUES (:id, :vid, :merge_line_id, :line_kind, "
                "        :importe_source, :review_reasons_json, "
                "        :review_required, :descripcion_linea)"
            ),
            {"vid": VALUATION_ID, **campos},
        )
    sesion.flush()


# ------------------------------------------------------------------ #
# R23 · las razones de la LINEA llegan al payload
# ------------------------------------------------------------------ #
def test_f036_r23_la_linea_valorada_trae_sus_razones(repositorio, sesion):
    """El caso de SALMEDINA: la linea dice que valoro por contenedores."""
    _sembrar_valoracion(
        sesion,
        [
            {
                "id": 900,
                "merge_line_id": 500,
                "review_reasons_json": json.dumps(
                    ["residuos_contenedores", "residuos_sin_volumen_m3"]
                ),
                "review_required": 1,
            }
        ],
    )

    valoracion = repositorio._load_valuation_in_session(
        session=sesion, document_id=DOCUMENT_ID
    )

    linea = valoracion.lines_by_merge_line_id[500]
    assert linea.review_reasons == [
        "residuos_contenedores",
        "residuos_sin_volumen_m3",
    ]


def test_f036_r23_sin_razones_la_lista_va_vacia(repositorio, sesion):
    """NULL en la columna no es ``None`` en el payload: es lista vacia.

    La plantilla itera sin preguntar; un ``None`` ahi obligaria a un
    guard en cada uso.
    """
    _sembrar_valoracion(sesion, [{"id": 901, "merge_line_id": 501}])

    valoracion = repositorio._load_valuation_in_session(
        session=sesion, document_id=DOCUMENT_ID
    )

    assert valoracion.lines_by_merge_line_id[501].review_reasons == []


def test_f036_r23_un_json_ilegible_no_rompe_la_ficha(repositorio, sesion):
    """Basura en la columna: la ficha se abre igual, sin razones.

    sv4 no es dueno de esa columna. Que un dia llegue algo que no es una
    lista JSON no puede dejar al revisor sin poder abrir el documento.
    """
    _sembrar_valoracion(
        sesion,
        [
            {"id": 902, "merge_line_id": 502, "review_reasons_json": "{no json"},
            {"id": 903, "merge_line_id": 503, "review_reasons_json": '"texto"'},
        ],
    )

    valoracion = repositorio._load_valuation_in_session(
        session=sesion, document_id=DOCUMENT_ID
    )

    assert valoracion.lines_by_merge_line_id[502].review_reasons == []
    assert valoracion.lines_by_merge_line_id[503].review_reasons == []


def test_f036_r23_las_sinteticas_tambien_traen_sus_razones(
    repositorio, sesion,
):
    """La sintetica sin tarifa de R17 vive de su razon: hay que verla."""
    _sembrar_valoracion(
        sesion,
        [
            {
                "id": 904,
                "merge_line_id": None,
                "line_kind": "synthetic_modifier",
                "descripcion_linea": "INCREMENTO LER 170504",
                "review_reasons_json": json.dumps(
                    ["residuos_ler_sin_tarifa_en_contrato"]
                ),
                "review_required": 1,
            }
        ],
    )

    valoracion = repositorio._load_valuation_in_session(
        session=sesion, document_id=DOCUMENT_ID
    )

    assert len(valoracion.synthetic_lines) == 1
    assert valoracion.synthetic_lines[0].review_reasons == [
        "residuos_ler_sin_tarifa_en_contrato"
    ]


# ------------------------------------------------------------------ #
# R23 · los motivos del DOCUMENTO, parseados para la plantilla
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("guardado", "esperado"),
    [
        (json.dumps(["proveedor_cif_no_casa:B12345678"]),
         ["proveedor_cif_no_casa:B12345678"]),
        (json.dumps([]), []),
        (None, []),
        ("", []),
        ("{no es json", []),
        (json.dumps({"motivo": "x"}), []),
        # Un motivo que no es texto no se pinta, pero no tira el resto.
        (json.dumps(["ok", 7, None]), ["ok"]),
    ],
)
def test_f036_r23_los_motivos_del_documento_se_exponen_como_lista(
    guardado, esperado,
):
    """``DocumentDetailPayload.review_reasons`` para la plantilla.

    El JSON crudo ya viajaba al payload; nadie lo parseaba, asi que la
    plantilla no podia pintarlo sin meter logica de parseo en Jinja.
    """
    from domain.models.review_models import DocumentDetailPayload

    payload = DocumentDetailPayload(
        id=DOCUMENT_ID,
        source_filename="SS-0801977.pdf",
        provider_origin="merge",
        model_name="—",
        created_at_utc="2026-08-19T10:00:00Z",
        review_reasons_json=guardado,
    )

    assert payload.review_reasons == esperado
