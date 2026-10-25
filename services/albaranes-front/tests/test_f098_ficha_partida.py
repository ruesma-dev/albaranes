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


# ------------------------------------------------------------------ #
# ReviewService (servicio): pinta con la lista y traduce lo que guarda
# ------------------------------------------------------------------ #
#: La obra 0404 del albarán de METALFIRE (``tests/f065_bbdd.py``), con su CD:
#: las partidas 01.01–01.03 y 03.01–03.02 son hojas de CD (completo CD.01.01…).
FILAS_0404 = [
    [1, 0, "CD", "COSTES DIRECTOS"],
    [2, 1, "01", "CARPINTERÍA"],
    [3, 2, "01.01", "Puerta EI2-60"],
    [4, 2, "01.02", "Puerta EI2-90"],
    [5, 2, "01.03", "Puerta EI2-120"],
    [6, 1, "03", "VARIOS"],
    [7, 6, "03.01", "Portes"],
    [8, 6, "03.02", "Otros portes"],
]
LISTA_0404 = ListaPartidasObra.desde_filas("0404", _COLUMNAS, FILAS_0404)


class _Partidas:
    """``PartidasObraPort`` falso: una lista por obra y las obras pedidas."""

    def __init__(self, listas=None) -> None:
        self.listas = {"0404": LISTA_0404} if listas is None else listas
        self.pedidas: list[str | None] = []

    def lista(self, obra):
        self.pedidas.append(obra)
        return self.listas.get(obra)

    def consultar(self, obra):
        lista = self.lista(obra)
        return lista, lista is not None


def _servicio(motor, partidas):
    from application.services.review_service import ReviewService
    from f065_bbdd import repositorio

    return ReviewService(repositorio(motor), "ana", None, None, partidas)


def test_f098_servicio_port_es_el_de_comun():
    from domain.ports.partidas_obra_port import PartidasObraPort
    from ruesma_comun.sigrid import CachePartidasObra

    cache = CachePartidasObra(lambda *a: ([], []), ttl_s=1, max_obras=1, ttl_fallo_s=1)
    assert isinstance(cache, PartidasObraPort)
    assert isinstance(_Partidas(), PartidasObraPort)


def test_f098_servicio_guarda_el_cod_y_la_fila_contrato_sigue_contrato():
    from f065_bbdd import DOC, construir, fila

    motor = construir()
    partidas = _Partidas()
    assert _servicio(motor, partidas).update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"codigo_partida": "CD.01.01"})
    f = fila(motor, 11)
    assert f["codigo_partida_final"] == "01.01"
    assert (f["matched_contrato_line_id"], f["derived_contrato_line_id"]) == (501, None)
    assert partidas.pedidas == ["0404"]


def test_f098_servicio_sin_f098_la_misma_edicion_pasaba_a_nueva():
    """La regresión que arregla R26: sin traducir, ``CD.01.01`` ≠ ``01.01``."""
    from f065_bbdd import DOC, construir, fila

    motor = construir()
    _servicio(motor, None).update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"codigo_partida": "CD.01.01"})
    f = fila(motor, 11)
    assert f["codigo_partida_final"] == "CD.01.01"
    assert f["derived_contrato_line_id"] is not None


def test_f098_servicio_obra_sin_lista_guarda_tal_cual():
    from f065_bbdd import DOC, construir, fila

    motor = construir()
    partidas = _Partidas(listas={})
    _servicio(motor, partidas).update_line_conciliacion(
        document_id=DOC, valuation_line_id=13, campos={"codigo_partida": "CD.03.02"})
    assert fila(motor, 13)["codigo_partida_final"] == "CD.03.02"
    assert partidas.pedidas == ["0404"]


@pytest.mark.parametrize("campos", [{"cantidad": 6.0}, {"codigo_partida": ""}, {"codigo_partida": None},
                                     {"codigo_partida": "   "}, None])
def test_f098_servicio_sin_partida_no_pide_la_lista(campos):
    from f065_bbdd import DOC, construir

    motor = construir()
    partidas = _Partidas()
    _servicio(motor, partidas).update_line_conciliacion(document_id=DOC, valuation_line_id=13, campos=campos)
    assert partidas.pedidas == []


def test_f098_servicio_traduce_sin_mutar_los_campos():
    from f065_bbdd import DOC, construir

    motor = construir()
    campos = {"codigo_partida": "CD.01.01", "cantidad": 6.0}
    _servicio(motor, _Partidas()).update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos=campos)
    assert campos == {"codigo_partida": "CD.01.01", "cantidad": 6.0}


def test_f098_servicio_dividir_manda_el_cod_de_cada_parte():
    from domain.models.review_models import ParteDivision
    from f065_bbdd import DOC, construir, fila

    motor = construir()
    partes = [ParteDivision(cantidad=4, codigo_partida="CD.01.02"),
              ParteDivision(cantidad=3, codigo_partida="cd 01 03"),
              ParteDivision(cantidad=3, codigo_partida=None)]
    hecha = _servicio(motor, _Partidas()).dividir_linea(document_id=DOC, valuation_line_id=12, partes=partes)
    assert hecha is not None
    # La original (12) es la parte 1; ``hecha.partes`` son las 2..N.
    finales = [fila(motor, vid)["codigo_partida_final"] for vid in [12, *hecha.partes]]
    assert finales == ["01.02", "01.03", None]
    assert [p.codigo_partida for p in partes] == ["CD.01.02", "cd 01 03", None]  # no muta


def test_f098_servicio_dividir_sin_partidas_no_pide_la_lista():
    from domain.models.review_models import ParteDivision
    from f065_bbdd import DOC, construir

    motor = construir()
    partidas = _Partidas()
    _servicio(motor, partidas).dividir_linea(
        document_id=DOC, valuation_line_id=12,
        partes=[ParteDivision(cantidad=4, codigo_partida=None), ParteDivision(cantidad=6, codigo_partida=None)])
    assert partidas.pedidas == []


def test_f098_servicio_dividir_sin_lista_tal_cual():
    from domain.models.review_models import ParteDivision
    from f065_bbdd import DOC, construir, fila

    motor = construir()
    hecha = _servicio(motor, _Partidas(listas={})).dividir_linea(
        document_id=DOC, valuation_line_id=12,
        partes=[ParteDivision(cantidad=4, codigo_partida="CD.01.02"), ParteDivision(cantidad=6, codigo_partida="01.02")])
    assert [fila(motor, vid)["codigo_partida_final"] for vid in [12, *hecha.partes]] == ["CD.01.02", "01.02"]


class _RepoFicha:
    def __init__(self, detalle) -> None:
        self.detalle = detalle

    def get_document_detail(self, document_id, *, view_mode):
        return self.detalle


def test_f098_servicio_get_document_presenta_con_la_lista():
    from application.services.review_service import ReviewService

    detalle = _detalle(_blanca("CD.99.01.64", _conc("99.01.64", "99.01.64", agree=False, aviso="⚠")))
    partidas = _Partidas(listas={"0686": LISTA_0686})
    nuevo = ReviewService(_RepoFicha(detalle), "r", None, None, partidas).get_document("doc-f098")
    assert nuevo.partidas_mostradas == {"99.01.64": "CD.99.01.64"}
    assert nuevo.display_lines[0].concilia.agree_partida is True
    assert partidas.pedidas == ["0686"]


def test_f098_servicio_get_document_sin_puerto_o_sin_obra_igual():
    from application.services.review_service import ReviewService

    detalle = _detalle(_blanca("CD.99.01.64", _conc("99.01.64", "99.01.64", agree=False)))
    assert ReviewService(_RepoFicha(detalle), "r").get_document("d") is detalle
    sin_obra = _detalle(obra=None)
    partidas = _Partidas(listas={"0686": LISTA_0686})
    assert ReviewService(_RepoFicha(sin_obra), "r", None, None, partidas).get_document("d") is sin_obra
    assert partidas.pedidas == []
    assert ReviewService(_RepoFicha(None), "r", None, None, partidas).get_document("d") is None


def test_f098_servicio_get_document_obra_sin_lista_igual():
    from application.services.review_service import ReviewService

    detalle = _detalle()
    partidas = _Partidas(listas={})
    assert ReviewService(_RepoFicha(detalle), "r", None, None, partidas).get_document("d") is detalle
    assert partidas.pedidas == ["0686"]


# ------------------------------------------------------------------ #
# Plantilla (R23, R25): pinta el completo, guarda el cod
# ------------------------------------------------------------------ #
def _celda_partida(html):
    import re

    celda = re.search(r'<td[^>]*data-col="partida"[^>]*>.*?</td>', html, re.DOTALL)
    assert celda is not None, "no se encontro la celda de partida"
    return celda.group(0)


def _valor_del_input(celda):
    """El atributo ``value`` del ``<input>`` de la celda (no el de ``data-sort-value``)."""
    import re

    entrada = re.search(r"<input\b[^>]*>", celda)
    assert entrada is not None, "la celda no tiene <input>"
    valor = re.search(r'\svalue="([^"]*)"', entrada.group(0))
    assert valor is not None, "el <input> no tiene value"
    return valor.group(1)


def _render_partida(render_detalle, documento_detalle, linea_valorada, fila_detalle, mostradas, **conc):
    doc = documento_detalle(lineas_valoracion=[linea_valorada(codigo_partida_final="99.01.64")],
                            display=[fila_detalle({"codigo_partida": "99.01.64", **conc})])
    return render_detalle(doc.model_copy(update={"partidas_mostradas": mostradas}))


def test_f098_render_pinta_el_completo_y_guarda_el_cod(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = _render_partida(render_detalle, documento_detalle, linea_valorada, fila_detalle,
                           {"99.01.64": "CD.99.01.64"})
    celda = _celda_partida(html)
    assert _valor_del_input(celda) == "CD.99.01.64"
    assert 'data-partida-cod="99.01.64"' in celda
    assert 'data-sort-value="CD.99.01.64"' in celda


def test_f098_render_sin_lista_pinta_el_cod(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    celda = _celda_partida(_render_partida(render_detalle, documento_detalle, linea_valorada, fila_detalle, {}))
    assert _valor_del_input(celda) == "99.01.64"
    assert 'data-partida-cod="99.01.64"' in celda
    assert "CD.99.01.64" not in celda


def test_f098_render_nota_normalizada_con_el_completo(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = _render_partida(render_detalle, documento_detalle, linea_valorada, fila_detalle,
                           {"99.01.64": "CD.99.01.64"}, partida_normalizada_desde="99-01-64")
    assert "Normalizada: 99-01-64 → CD.99.01.64" in _celda_partida(html)


def test_f098_render_dividir_lleva_el_completo(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = _render_partida(render_detalle, documento_detalle, linea_valorada, fila_detalle,
                           {"99.01.64": "CD.99.01.64"})
    assert "js-dividir" in html
    assert 'data-partida="CD.99.01.64"' in html


def test_f098_render_contrato_json_part_cod_y_mostrada(render_detalle, documento_detalle):
    import json
    import re

    doc = documento_detalle().model_copy(update={
        "partidas_mostradas": {"99.01.64": "CD.99.01.64"},
        "contrato_lines": [ContratoLinePayload(id=7, codigo_contrato="C-001", codigo_partida="99.01.64", descripcion="Material",
                                               precio_unitario=2.5)],
    })
    html = render_detalle(doc)
    bloque = re.search(r'<script type="application/json" id="contrato-lines-json">(.*?)</script>', html, re.DOTALL)
    assert bloque is not None
    datos = json.loads(bloque.group(1))
    assert datos[0]["part"] == "99.01.64"
    assert datos[0]["partMostrada"] == "CD.99.01.64"
    assert datos[0]["label"].startswith("CD.99.01.64 · Material")


def test_f098_render_modelo_partida_mostrada():
    doc = _detalle().model_copy(update={"partidas_mostradas": {"99.01.64": "CD.99.01.64"}})
    assert doc.partida_mostrada("99.01.64") == "CD.99.01.64"
    assert doc.partida_mostrada(" 99.01.64 ") == "CD.99.01.64"
    assert doc.partida_mostrada("01.01") == "01.01"
    assert doc.partida_mostrada(None) is None
    assert doc.partida_mostrada("") == ""


def test_f098_render_solo_lectura_pinta_el_completo(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Fila guardada (bloqueada): sale en solo lectura y pinta el completo."""
    doc = documento_detalle(lineas_valoracion=[linea_valorada(codigo_partida_final="99.01.64", bloqueada=True)],
                            display=[fila_detalle({"codigo_partida": "99.01.64"})])
    html = render_detalle(doc.model_copy(update={"partidas_mostradas": {"99.01.64": "CD.99.01.64"}}))
    import re

    celda = _celda_partida(html)
    assert "<input" not in celda
    texto = re.search(r'<span class="concilia-val"[^>]*>(.*?)</span>', celda, re.DOTALL)
    assert texto is not None and texto.group(1).strip() == "CD.99.01.64"


def test_f098_render_solo_lectura_con_aviso_pinta_el_completo(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Fila guardada con aviso de partida (F-077 R21): el ⚠ va con el completo."""
    doc = documento_detalle(lineas_valoracion=[linea_valorada(codigo_partida_final="99.01.64", bloqueada=True)],
                            display=[fila_detalle({"codigo_partida": "99.01.64",
                                                   "aviso_partida": "Leída 99.02.10 en el albarán"})])
    celda = _celda_partida(render_detalle(doc.model_copy(update={"partidas_mostradas": {"99.01.64": "CD.99.01.64"}})))
    assert "<input" not in celda
    assert "⚠</span> CD.99.01.64</span>" in celda
