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


# ------------------------------------------------------------------ #
# R23 · lo que el revisor VE en la ficha
# ------------------------------------------------------------------ #
def _documento(lineas_valoracion=(), motivos_documento=None, display=()):
    """``DocumentDetailPayload`` minimo para renderizar el detalle."""
    from domain.models.review_models import (
        DocumentDetailPayload,
        ValuationPayload,
    )

    valoracion = None
    if lineas_valoracion:
        valoracion = ValuationPayload(
            valuation_id=VALUATION_ID,
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
        id=DOCUMENT_ID,
        source_filename="SS-0801977.pdf",
        provider_origin="merge",
        model_name="—",
        created_at_utc="2026-08-19T10:00:00Z",
        proveedor_cif="B87654321",
        review_reasons_json=(
            json.dumps(motivos_documento) if motivos_documento else None
        ),
        review_required=bool(motivos_documento),
        display_lines=list(display),
        valuation=valoracion,
    )


def _linea_valorada(**campos):
    from domain.models.review_models import LineValuationPayload

    base = {
        "valuation_line_id": 900,
        "merge_line_id": 500,
        "precio_unitario_final": 120.0,
        "cantidad_albaran": 6.0,
        "cantidad_convertida": 1.0,
        "importe_calculado": 120.0,
        "importe_source": "declared_albaran",
        "review_reasons": ["residuos_contenedores"],
        "review_required": True,
    }
    base.update(campos)
    return LineValuationPayload(**base)


def _display(**campos):
    from domain.models.review_models import ConciliacionDisplay, DisplayLine

    conciliacion = ConciliacionDisplay(
        kind="assigned",
        codigo_partida="01.01",
        descripcion="RETIRADA CONTENEDOR RCD",
        unidad="UD",
        unitario=120.0,
        descuento=None,
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
        "concilia": conciliacion,
    }
    base.update(campos)
    return DisplayLine(**base)


def test_f036_r23_la_ficha_pinta_las_razones_de_la_linea(render_detalle):
    """La razon de sv6 llega hasta el HTML que ve el revisor."""
    html = render_detalle(
        _documento(
            lineas_valoracion=[
                _linea_valorada(
                    review_reasons=[
                        "residuos_contenedores",
                        "residuos_sin_volumen_m3",
                    ]
                )
            ],
            display=[_display()],
        )
    )

    assert "residuos_contenedores" in html
    assert "residuos_sin_volumen_m3" in html


def test_f036_r23_una_linea_sin_razones_no_pinta_el_hueco(render_detalle):
    """Sin razones no hay marca: la tabla no se llena de adornos vacios."""
    html = render_detalle(
        _documento(
            lineas_valoracion=[_linea_valorada(review_reasons=[])],
            display=[_display()],
        )
    )

    assert "js-linea-razones" not in html


def test_f036_r23_las_razones_de_la_sintetica_tambien_se_pintan(
    render_detalle,
):
    """La sintetica sin tarifa (R17) existe para que el revisor actue.

    Si su razon no se pinta, la linea sin precio parece un error del
    sistema en vez de un encargo.
    """
    sintetica = _linea_valorada(
        valuation_line_id=904,
        merge_line_id=None,
        precio_unitario_final=None,
        importe_calculado=None,
        descripcion_linea="INCREMENTO LER 170504",
        line_kind="synthetic_modifier",
        parent_merge_line_id=500,
        review_reasons=["residuos_ler_sin_tarifa_en_contrato"],
    )
    html = render_detalle(
        _documento(
            lineas_valoracion=[_linea_valorada(), sintetica],
            display=[
                _display(),
                _display(
                    line_kind="synthetic_modifier",
                    merge_line_id=None,
                    valuation_line_id=904,
                    concepto="INCREMENTO LER 170504",
                    cantidad=1.0,
                    precio_unitario=None,
                    importe=None,
                ),
            ],
        )
    )

    assert "residuos_ler_sin_tarifa_en_contrato" in html


def test_f036_r23_el_banner_pinta_los_motivos_del_documento(render_detalle):
    """Los motivos que sella sv3 tampoco se veian en ninguna parte."""
    html = render_detalle(
        _documento(
            lineas_valoracion=[_linea_valorada()],
            motivos_documento=[
                "proveedor_cif_no_casa:B12345678",
                "obra_no_resuelta",
            ],
            display=[_display()],
        )
    )

    assert "proveedor_cif_no_casa:B12345678" in html
    assert "obra_no_resuelta" in html


def test_f036_r23_sin_motivos_el_banner_no_inventa_nada(render_detalle):
    """Un documento limpio no gana una lista de motivos vacia."""
    html = render_detalle(
        _documento(
            lineas_valoracion=[_linea_valorada()],
            display=[_display()],
        )
    )

    assert "Motivos de revisión" not in html
