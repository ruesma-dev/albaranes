# tests/test_f098_ficha_partida.py
"""F-098 · la ficha pinta el código completo y guarda el cod (R23–R26, R28).

- ``presentar_partidas`` (dominio de sv4, puro): con la lista de la obra, el
  mapa cod → código completo de los cod de la ficha y el ✓ cuando la leída y la
  de su línea de contrato son la misma hoja (``CD.99.01.64`` frente a
  ``99.01.64`` de CD); sin lista, el mismo objeto (R28). Nunca convierte un ✓
  en ⚠ ni toca un ``None``.
- ``traducir_partida``: lo que se guarda es el cod de la lista si la partida
  casa ``exacta``, ``normalizada`` o ``completa``; si no, tal cual (R25).
  Nunca recorta texto: ``CD2.01`` de la 0692 se guarda ``CD2.01``.
- ``ReviewService`` (servicio): pinta con la lista y traduce antes del
  repositorio (R25, R26).
- La plantilla (render): ``value`` con el completo y ``data-partida-cod`` con
  el cod (R23).

Sin red ni BBDD: lista construida desde filas, repositorio y caché falsos.
"""
from __future__ import annotations

import pytest
from domain.models.review_models import (
    ConciliacionDisplay,
    ContratoLinePayload,
    DisplayLine,
    DocumentDetailPayload,
    LineValuationPayload,
    ValuationPayload,
)
from ruesma_comun.sigrid import ListaPartidasObra

_COLUMNAS = ["ide", "padide", "cod", "res"]
FILAS_0686 = [
    [1, 0, "ANT.", "AJUSTES ALMACÉN"],
    [2, 1, "98.01", "Anticipos"],
    [10, 0, "CD", "COSTES DIRECTOS"],
    [11, 10, "99", "VARIOS"],
    [12, 11, "99.01", "VARIOS OBRA"],
    [13, 12, "99.01.64", "Material de obra"],
    [14, 12, "99.01.65", "Otro material"],
    [20, 0, "CI", "COSTES INDIRECTOS"],
    [21, 20, "CI.4.18", "Costes indirectos de obra"],
]
FILAS_0692 = [
    [1, 0, "CD", "COSTES DIRECTOS"],
    [4, 1, "CD2", "FASE 2"],
    [5, 4, "CD2.01", "Fase 2 uno"],
    [9, 0, "CI.F2", "COSTES INDIRECTOS FASE 2"],
    [10, 9, "CI.01.01", "Personal fase 2"],
]
LISTA_0686 = ListaPartidasObra.desde_filas("0686", _COLUMNAS, FILAS_0686)
LISTA_0692 = ListaPartidasObra.desde_filas("0692", _COLUMNAS, FILAS_0692)


def _ficha():
    from domain.services import partidas_ficha

    return partidas_ficha


def _conc(final, casada, *, agree=None, kind="assigned", aviso=None, desde=None, almacen=False):
    return ConciliacionDisplay(
        kind=kind,
        codigo_partida=None if almacen else final,
        codigo_partida_casada=casada,
        estado_partida="almacen" if almacen else "partida",
        agree_partida=agree,
        aviso_partida=aviso,
        partida_normalizada_desde=desde,
    )


def _detalle(*lineas: DisplayLine, contrato=(), valoracion=None, obra="0686") -> DocumentDetailPayload:
    return DocumentDetailPayload(
        id="doc-f098", source_filename="a.pdf", provider_origin="merge", model_name="m",
        created_at_utc="2026-10-24T00:00:00Z", obra_codigo=obra, display_lines=list(lineas),
        contrato_lines=list(contrato), valuation=valoracion,
    )


def _blanca(leida, conc, mid=1):
    return DisplayLine(line_kind="from_albaran", merge_line_id=mid, valuation_line_id=100 + mid,
                       codigo_imputacion=leida, concilia=conc)


def _sintetica(conc, vid=900):
    return DisplayLine(line_kind="synthetic_modifier", valuation_line_id=vid, concilia=conc)


# ------------------------------------------------------------------ #
# presentar_partidas (R23, R24, R28)
# ------------------------------------------------------------------ #
def test_f098_presentar_sin_lista_es_el_mismo_objeto():
    detalle = _detalle(_blanca("CD.99.01.64", _conc("99.01.64", "99.01.64", agree=False, aviso="⚠")))
    assert _ficha().presentar_partidas(detalle, None) is detalle


def test_f098_presentar_mapa_de_los_cod_de_la_ficha():
    detalle = _detalle(
        _blanca("CD.99.01.64", _conc("99.01.64", "99.01.65", agree=False)),
        _sintetica(_conc("98.01", None)),
        _blanca(None, _conc("CI.4.18", "CI.4.18", agree=None), mid=2),
        contrato=[ContratoLinePayload(id=1, codigo_contrato="C", codigo_partida=" 99.01.64 "),
                  ContratoLinePayload(id=2, codigo_contrato="C", codigo_partida=None)],
        valoracion=ValuationPayload(
            valuation_id="v", status="ok",
            lines_by_merge_line_id={1: LineValuationPayload(valuation_line_id=101, merge_line_id=1,
                                                            codigo_partida_final="99.01.64")},
            synthetic_lines=[LineValuationPayload(valuation_line_id=900, codigo_partida_final="98.01")],
        ),
    )
    nuevo = _ficha().presentar_partidas(detalle, LISTA_0686)
    assert nuevo.partidas_mostradas == {
        "99.01.64": "CD.99.01.64", "99.01.65": "CD.99.01.65", "98.01": "ANT.98.01",
    }
    assert detalle.partidas_mostradas == {}  # no muta


@pytest.mark.parametrize("fuente", ["final", "casada", "contrato", "valoracion", "sintetica_valoracion"])
def test_f098_presentar_cada_fuente_de_cods(fuente):
    conc = _conc("99.01.64" if fuente == "final" else None, "99.01.64" if fuente == "casada" else None)
    contrato = [ContratoLinePayload(id=1, codigo_contrato="C", codigo_partida="99.01.64")] if fuente == "contrato" else []
    valoracion = None
    if fuente == "valoracion":
        valoracion = ValuationPayload(valuation_id="v", status="ok", lines_by_merge_line_id={
            7: LineValuationPayload(merge_line_id=7, codigo_partida_final="99.01.64")})
    if fuente == "sintetica_valoracion":
        valoracion = ValuationPayload(valuation_id="v", status="ok", synthetic_lines=[
            LineValuationPayload(codigo_partida_final="99.01.64")])
    detalle = _detalle(_blanca(None, conc), contrato=contrato, valoracion=valoracion)
    assert _ficha().presentar_partidas(detalle, LISTA_0686).partidas_mostradas == {"99.01.64": "CD.99.01.64"}


def test_f098_presentar_cods_que_no_cambian_no_entran():
    detalle = _detalle(_blanca(None, _conc("CI.4.18", "X.NO.ESTA")),
                       contrato=[ContratoLinePayload(id=1, codigo_contrato="C", codigo_partida="   ")])
    assert _ficha().presentar_partidas(detalle, LISTA_0686).partidas_mostradas == {}


def test_f098_presentar_aviso_pasa_a_ok_si_es_la_misma_hoja():
    conc = _conc("99.01.64", "99.01.64", agree=False, aviso="No coincide con la partida leída en el albarán (CD.99.01.64)")
    nuevo = _ficha().presentar_partidas(_detalle(_blanca("CD.99.01.64", conc)), LISTA_0686)
    c = nuevo.display_lines[0].concilia
    assert (c.agree_partida, c.aviso_partida, c.partida_normalizada_desde) == (True, None, None)
    # «CD.99.01.64» es lo pintado (el completo de 99.01.64): sin nota.
    assert conc.agree_partida is False  # no muta


def test_f098_presentar_nota_si_la_leida_difiere_de_lo_pintado():
    conc = _conc("99.01.64", "99.01.64", agree=False, aviso="⚠")
    nuevo = _ficha().presentar_partidas(_detalle(_blanca(" cd 99.1.64 ", conc)), LISTA_0686)
    c = nuevo.display_lines[0].concilia
    assert (c.agree_partida, c.aviso_partida, c.partida_normalizada_desde) == (True, None, "cd 99.1.64")


def test_f098_presentar_sintetica_compara_la_final():
    """Sin blanca, la leída es la final (como el repositorio, F-076)."""
    conc = _conc("CD.99.01.64", "99.01.64", agree=False, kind="derived")
    nuevo = _ficha().presentar_partidas(_detalle(_sintetica(conc)), LISTA_0686)
    c = nuevo.display_lines[0].concilia
    assert (c.agree_partida, c.partida_normalizada_desde) == (True, None)


def test_f098_presentar_sintetica_con_final_que_no_es_cod_sin_nota():
    """Una final que no es cod se pinta tal cual: la leída (la final) es lo
    pintado y no lleva nota, aunque sea la misma hoja que la casada."""
    conc = _conc("cd.99.01.64", "99.01.64", agree=False, kind="derived")
    nuevo = _ficha().presentar_partidas(_detalle(_sintetica(conc)), LISTA_0686)
    c = nuevo.display_lines[0].concilia
    assert (c.agree_partida, c.partida_normalizada_desde) == (True, None)


def test_f098_presentar_no_misma_hoja_sigue_aviso():
    conc = _conc("99.01.64", "99.01.65", agree=False, aviso="⚠")
    nuevo = _ficha().presentar_partidas(_detalle(_blanca("CD.99.01.64", conc)), LISTA_0686)
    c = nuevo.display_lines[0].concilia
    assert (c.agree_partida, c.aviso_partida) == (False, "⚠")


@pytest.mark.parametrize("agree", [True, None])
def test_f098_presentar_nunca_toca_un_true_ni_un_none(agree):
    conc = _conc("99.01.64", "99.01.65", agree=agree, desde="X")
    nuevo = _ficha().presentar_partidas(_detalle(_blanca("CD.99.01.65", conc)), LISTA_0686)
    c = nuevo.display_lines[0].concilia
    assert (c.agree_partida, c.partida_normalizada_desde) == (agree, "X")


def test_f098_presentar_almacen_no_compara():
    conc = _conc(None, "99.01.64", agree=False, almacen=True)
    nuevo = _ficha().presentar_partidas(_detalle(_blanca("CD.99.01.64", conc)), LISTA_0686)
    assert nuevo.display_lines[0].concilia.agree_partida is False


def test_f098_presentar_linea_sin_conciliacion():
    detalle = _detalle(DisplayLine(line_kind="from_albaran", merge_line_id=3, codigo_imputacion="99.01.64"))
    nuevo = _ficha().presentar_partidas(detalle, LISTA_0686)
    assert nuevo.display_lines[0].concilia is None


def test_f098_presentar_sin_lineas_ni_cods():
    detalle = _detalle()
    nuevo = _ficha().presentar_partidas(detalle, LISTA_0686)
    assert nuevo.partidas_mostradas == {} and nuevo.display_lines == []


# ------------------------------------------------------------------ #
# traducir_partida (R25)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("lista", "valor", "guardado"),
    [
        (LISTA_0686, "CD.99.01.64", "99.01.64"),  # completa
        (LISTA_0686, "cd 99.1.64", "99.01.64"),
        (LISTA_0686, "99.01.64", "99.01.64"),  # exacta
        (LISTA_0686, "99.1.64", "99.01.64"),  # normalizada
        (LISTA_0686, "ANT.98.01", "98.01"),
        (LISTA_0692, "CD2.01", "CD2.01"),  # nunca 2.01
        (LISTA_0692, "CI.01.01", "CI.01.01"),
        (LISTA_0686, "CD.99.01", "CD.99.01"),  # subcapítulo: tal cual
        (LISTA_0686, "X.NO.ESTA", "X.NO.ESTA"),  # no casa: tal cual (no se rechaza)
        (LISTA_0686, "CD.99.01.64/CI.4.18", "CD.99.01.64/CI.4.18"),  # compuesta: tal cual
        (LISTA_0686, None, None),
        (LISTA_0686, "", ""),
        (LISTA_0686, "   ", "   "),
        (None, "CD.99.01.64", "CD.99.01.64"),  # sin lista: tal cual
    ],
)
def test_f098_traducir_partida(lista, valor, guardado):
    assert _ficha().traducir_partida(lista, valor) == guardado


def test_f098_traducir_partida_ambigua_tal_cual():
    filas = [[1, 0, "CI", "CI"], [2, 1, "CI.1.1", "a"], [3, 0, "CI.F2", "F2"], [4, 3, "CI.01.01", "b"]]
    lista = ListaPartidasObra.desde_filas("0692", _COLUMNAS, filas)
    assert _ficha().traducir_partida(lista, "CI.1.01") == "CI.1.01"


def test_f098_traducir_partida_alm_no_es_literal_especial():
    assert _ficha().traducir_partida(LISTA_0686, "ALM") == "ALM"
