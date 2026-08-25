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
            {"id": 902, "merge_line_id": 502,
             "review_reasons_json": "{no json"},
            {"id": 903, "merge_line_id": 503,
             "review_reasons_json": '"texto"'},
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
#
# Las factorias de payload (`documento_detalle`, `linea_valorada`,
# `fila_detalle`) y el renderizador viven en el conftest: los comparten
# estos tests y los de R8.
# ------------------------------------------------------------------ #
def test_f036_r23_la_ficha_pinta_las_razones_de_la_linea(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """La razon de sv6 llega hasta el HTML que ve el revisor."""
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[
                linea_valorada(
                    review_reasons=[
                        "residuos_contenedores",
                        "residuos_sin_volumen_m3",
                    ]
                )
            ],
            display=[fila_detalle()],
        )
    )

    assert "residuos_contenedores" in html
    assert "residuos_sin_volumen_m3" in html


def test_f036_r23_una_linea_sin_razones_no_pinta_el_hueco(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Sin razones no hay marca: la tabla no se llena de adornos vacios."""
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[linea_valorada(review_reasons=[])],
            display=[fila_detalle()],
        )
    )

    assert "js-linea-razones" not in html


def test_f036_r23_las_razones_de_la_sintetica_tambien_se_pintan(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """La sintetica sin tarifa (R17) existe para que el revisor actue.

    Si su razon no se pinta, la linea sin precio parece un error del
    sistema en vez de un encargo.
    """
    sintetica = linea_valorada(
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
        documento_detalle(
            lineas_valoracion=[linea_valorada(), sintetica],
            display=[
                fila_detalle(),
                fila_detalle(
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


def test_f036_r23_el_banner_pinta_los_motivos_del_documento(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Los motivos que sella sv3 tampoco se veian en ninguna parte."""
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[linea_valorada()],
            motivos_documento=[
                "proveedor_cif_no_casa:B12345678",
                "obra_no_resuelta",
            ],
            display=[fila_detalle()],
        )
    )

    assert "proveedor_cif_no_casa:B12345678" in html
    assert "obra_no_resuelta" in html


def test_f036_r23_sin_motivos_el_banner_no_inventa_nada(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Un documento limpio no gana una lista de motivos vacia."""
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[linea_valorada()],
            display=[fila_detalle()],
        )
    )

    assert "Motivos de revisión" not in html


# ------------------------------------------------------------------ #
# R24 · el motivo que sella un CIF caduca cuando el CIF cambia
# ------------------------------------------------------------------ #
def _sembrar_documento(sesion, cif, motivos):
    sesion.execute(
        text(
            "INSERT INTO albaran_documents_merge "
            "(id, proveedor_cif, review_reasons_json) "
            "VALUES (:id, :cif, :motivos)"
        ),
        {
            "id": DOCUMENT_ID,
            "cif": cif,
            "motivos": json.dumps(motivos) if motivos is not None else None,
        },
    )
    sesion.flush()


def _leer_motivos(sesion):
    """Los motivos del documento, leidos como los lee sv4."""
    from domain.models.review_models import motivos_de_json

    return motivos_de_json(
        sesion.execute(
            text(
                "SELECT review_reasons_json FROM albaran_documents_merge "
                "WHERE id = :id"
            ),
            {"id": DOCUMENT_ID},
        ).scalar_one()
    )


def test_f036_r24_el_motivo_con_el_cif_viejo_se_retira(repositorio, sesion):
    """El caso de SS-0801977, medido en la BBDD real.

    sv3 sello ``proveedor_cif_no_casa:B12345678``; el revisor corrigio el
    CIF a B87654321 y el motivo se quedo colgado meses.
    """
    _sembrar_documento(
        sesion,
        cif="B87654321",
        motivos=["proveedor_cif_no_casa:B12345678", "obra_no_resuelta"],
    )

    repositorio._depurar_motivos_documento_in_session(
        session=sesion, document_id=DOCUMENT_ID, cif_actual="B87654321"
    )

    assert _leer_motivos(sesion) == ["obra_no_resuelta"]


def test_f036_r24_el_motivo_vigente_no_se_toca(repositorio, sesion):
    """Si el CIF sigue siendo el sellado, el aviso sigue siendo verdad.

    Es la mitad que importa: R24 retira motivos CADUCOS, no motivos
    incomodos. Barrerlos todos dejaria al revisor sin el aviso.
    """
    _sembrar_documento(
        sesion,
        cif="B12345678",
        motivos=["proveedor_cif_no_casa:B12345678"],
    )

    repositorio._depurar_motivos_documento_in_session(
        session=sesion, document_id=DOCUMENT_ID, cif_actual="B12345678"
    )

    assert _leer_motivos(sesion) == ["proveedor_cif_no_casa:B12345678"]


@pytest.mark.parametrize(
    ("sellado", "actual"),
    [
        ("b12345678", "B12345678"),
        ("B12345678", " b12345678 "),
        ("B-12345678", "B12345678"),
    ],
)
def test_f036_r24_el_cif_se_compara_normalizado(
    repositorio, sesion, sellado, actual,
):
    """Mayusculas, espacios y guiones no hacen caducar un motivo vigente.

    El CIF llega tecleado por un humano en un formulario libre.
    """
    _sembrar_documento(
        sesion, cif=actual, motivos=[f"proveedor_cif_no_casa:{sellado}"]
    )

    repositorio._depurar_motivos_documento_in_session(
        session=sesion, document_id=DOCUMENT_ID, cif_actual=actual
    )

    assert _leer_motivos(sesion) == [f"proveedor_cif_no_casa:{sellado}"]


def test_f036_r24_sin_cif_en_el_merge_el_motivo_caduca(repositorio, sesion):
    """Si el revisor borra el CIF, el motivo ya no describe nada."""
    _sembrar_documento(
        sesion, cif=None, motivos=["proveedor_cif_no_casa:B12345678"]
    )

    repositorio._depurar_motivos_documento_in_session(
        session=sesion, document_id=DOCUMENT_ID, cif_actual=None
    )

    assert _leer_motivos(sesion) == []


def test_f036_r24_un_motivo_sin_cif_sellado_se_respeta(repositorio, sesion):
    """``proveedor_cif_no_casa`` a secas: no hay con que compararlo.

    Retirarlo seria inventarse que ha caducado. Se deja para que lo
    resuelva quien lo puso.
    """
    _sembrar_documento(
        sesion, cif="B87654321", motivos=["proveedor_cif_no_casa"]
    )

    repositorio._depurar_motivos_documento_in_session(
        session=sesion, document_id=DOCUMENT_ID, cif_actual="B87654321"
    )

    assert _leer_motivos(sesion) == ["proveedor_cif_no_casa"]


def test_f036_r24_los_demas_motivos_no_se_tocan(repositorio, sesion):
    """R24 esta ACOTADO a ``proveedor_cif_no_casa`` (decision 2026-08-22).

    El resto de motivos sellados por sv3 van en ficha aparte; aqui no se
    barre nada mas.
    """
    otros = [
        "obra_no_resuelta",
        "contrato_no_encontrado",
        "confianza_baja",
    ]
    _sembrar_documento(sesion, cif="B87654321", motivos=list(otros))

    repositorio._depurar_motivos_documento_in_session(
        session=sesion, document_id=DOCUMENT_ID, cif_actual="B87654321"
    )

    assert _leer_motivos(sesion) == otros


@pytest.mark.parametrize("guardado", [None, "", "{no es json"])
def test_f036_r24_una_columna_ilegible_no_rompe_el_guardado(
    repositorio, sesion, guardado,
):
    """Sin motivos que depurar, el guardado del revisor sigue su curso."""
    sesion.execute(
        text(
            "INSERT INTO albaran_documents_merge "
            "(id, proveedor_cif, review_reasons_json) "
            "VALUES (:id, 'B87654321', :motivos)"
        ),
        {"id": DOCUMENT_ID, "motivos": guardado},
    )
    sesion.flush()

    repositorio._depurar_motivos_documento_in_session(
        session=sesion, document_id=DOCUMENT_ID, cif_actual="B87654321"
    )

    assert _leer_motivos(sesion) == []


def test_f036_r24_la_depuracion_esta_cableada_en_update_document():
    """El cableado, fijado por test (leccion del round trip 3 de F-019).

    La depuracion puede estar perfecta y no servir de nada si nadie la
    llama desde el guardado del revisor, que es el unico momento en que
    el CIF puede haber cambiado.
    """
    import inspect

    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    fuente = inspect.getsource(AlbaranReviewRepository.update_document)
    assert "_depurar_motivos_documento_in_session" in fuente


def test_f036_r24_un_documento_que_no_existe_no_rompe_nada(
    repositorio, sesion,
):
    """Depurar un documento borrado entre medias no crea filas."""
    repositorio._depurar_motivos_documento_in_session(
        session=sesion, document_id="no-existe", cif_actual="B87654321"
    )

    assert sesion.execute(
        text("SELECT COUNT(*) FROM albaran_documents_merge")
    ).scalar_one() == 0
