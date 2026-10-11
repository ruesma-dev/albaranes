# tests/test_f065_f2_pasada2.py
"""F-065 · fase 2 · pasada 2 (review `progress/review_F-065_fase2.md`).

- CR1: una fila que pasa a Nueva (o una Nueva que se edita) sin blanca no puede
  quedarse sin descripción en la valoración: sv9 solo lee
  ``descripcion_linea`` o el concepto de la blanca y, sin ninguna, el albarán
  entero sale ``no_admitido`` (``falta_descripcion``). Caso METALFIRE: traer 5
  del contrato y cambiarles la partida.
- H1 (líder, modelo del humano): la descripción que el administrativo EDITA en
  sv4 es la que llega a Sigrid, también con blanca. sv9 ya prefiere
  ``descripcion_linea`` al concepto leído; lo que faltaba es que sv4 no la
  borre al pasar a Nueva y la escriba al editarla.
- H2: «Origen ✎» hacia una línea de contrato de OTRA unidad no deja la fila
  silenciosamente falsa: si la nueva unidad es la del albarán, la cantidad
  pasa a ser la del albarán; si no, se deja la cantidad, la fila NO se bloquea
  y lleva el aviso visible «revisa la cantidad: cambió la unidad».
- H4: la caché de partidas del combo es por obra.

Repositorio real sobre SQLite (``f065_bbdd``), plantilla real y JS con node.
"""
from __future__ import annotations

import json
import re

import pytest
from f065_bbdd import DOC, construir, ejecutar, fila, repositorio
from test_f065_f1_js import _ejecutar, con_node

AVISO_UNIDAD = "front_unidad_cambiada_revisa_cantidad"


def _editar(motor, vid, bloquear=False, **campos):
    return repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, campos=campos, bloquear=bloquear,
    )


def _traida(motor):
    (vid,) = repositorio(motor).add_valuation_lines_from_contrato(
        document_id=DOC, lineas=[(503, 5.0)])
    return vid


# =================================================================== #
# CR1 · la fila sin blanca conserva su descripción al pasar a Nueva
# =================================================================== #
def test_f065_cr1_traida_con_otra_partida_conserva_su_descripcion():
    motor = construir()
    vid = _traida(motor)

    _editar(motor, vid, codigo_partida="09.09")

    f = fila(motor, vid)
    assert f["matched_contrato_line_id"] is None and f["derived_contrato_line_id"]
    assert f["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-120"


def test_f065_cr1_traida_pasada_a_nueva_por_origen_conserva_su_descripcion():
    motor = construir()
    vid = _traida(motor)

    repositorio(motor).set_line_conciliacion(document_id=DOC, valuation_line_id=vid, mode="nueva")

    assert fila(motor, vid)["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-120"


def test_f065_cr1_la_nueva_traida_editada_despues_sigue_con_descripcion():
    motor = construir()
    vid = _traida(motor)
    _editar(motor, vid, codigo_partida="09.09")

    _editar(motor, vid, cantidad=4.0)

    assert fila(motor, vid)["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-120"


def test_f065_cr1_anadir_linea_y_rellenarla_deja_la_descripcion_en_la_valoracion():
    motor = construir()
    vid = repositorio(motor).add_standalone_valuation_line(document_id=DOC)

    _editar(motor, vid, descripcion="TORNILLERIA M8", cantidad=10.0, precio_unitario=2.0)

    f = fila(motor, vid)
    assert f["descripcion_linea"] == "TORNILLERIA M8"
    assert f["importe_calculado"] == pytest.approx(20.0)


# =================================================================== #
# H1 · con blanca, solo la descripción EDITADA va a la valoración
# =================================================================== #
def test_f065_h1_con_blanca_sin_editarla_sigue_mandando_el_concepto_leido():
    """Contrato → Nueva solo por la partida: la valoración no fija descripción y
    sv9 manda el concepto leído del albarán (diseño de F-053)."""
    motor = construir()

    _editar(motor, 11, codigo_partida="09.09")

    assert fila(motor, 11)["descripcion_linea"] is None


def test_f065_h1_con_blanca_la_descripcion_editada_de_una_nueva_se_guarda():
    motor = construir()

    _editar(motor, 13, descripcion="PORTES URGENTES")

    assert fila(motor, 13)["descripcion_linea"] == "PORTES URGENTES"


def test_f065_h1_editar_otra_cosa_no_borra_la_descripcion_editada():
    motor = construir()
    _editar(motor, 13, descripcion="PORTES URGENTES")

    _editar(motor, 13, cantidad=2.0)

    assert fila(motor, 13)["descripcion_linea"] == "PORTES URGENTES"


def test_f065_h1_la_descripcion_editada_de_una_contrato_viaja_al_pasar_a_nueva():
    motor = construir()
    _editar(motor, 11, descripcion="PUERTA EI2-60 IZQUIERDA")

    _editar(motor, 11, precio_unitario=120.0)

    f = fila(motor, 11)
    assert f["derived_contrato_line_id"] is not None
    assert f["descripcion_linea"] == "PUERTA EI2-60 IZQUIERDA"


def test_f065_h1_origen_nueva_con_blanca_sin_editar_no_fija_descripcion():
    motor = construir()

    repositorio(motor).set_line_conciliacion(document_id=DOC, valuation_line_id=11, mode="nueva")

    assert fila(motor, 11)["descripcion_linea"] is None


def test_f065_h1_origen_nueva_con_descripcion_dada_la_fija():
    motor = construir()

    repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=11, mode="nueva", descripcion="PUERTA ESPECIAL")

    assert fila(motor, 11)["descripcion_linea"] == "PUERTA ESPECIAL"


# =================================================================== #
# H2 · «Origen ✎» a una línea de otra unidad
# =================================================================== #
def _reapuntar(motor, vid, linea):
    return repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, mode="contract_line",
        matched_contrato_line_id=linea)


def _razones(f):
    return json.loads(f["review_reasons_json"] or "[]")


def test_f065_h2_otra_unidad_desconocida_deja_la_cantidad_y_avisa():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET unidad_medida = 'M2', "
             "precio_unitario = 30 WHERE id = 503")

    _reapuntar(motor, 11, 503)

    f = fila(motor, 11)
    assert (f["cantidad_albaran"], f["cantidad_convertida"]) == (8.0, 8.0)
    assert f["unidad_contrato"] == "M2"
    assert f["review_required"] in (1, True)
    assert f["bloqueada"] in (0, False)
    assert AVISO_UNIDAD in _razones(f)
    assert "ia_match_trusted" in _razones(f)  # las de sv6 no se pierden


def test_f065_h2_la_unidad_del_albaran_convierte_a_su_cantidad():
    """Fila en t (1 t = 1000 kg leídos, factor 0,001, reproducible) reapuntada a
    una línea en kg a 0,12 €: Q pasa a 1000 kg y el importe a 120 €."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_albaran = 'kg', "
             "unidad_contrato = 'T', factor_conversion = 0.001, cantidad_albaran = 1000, "
             "cantidad_convertida = 1, precio_unitario_final = 120, importe_calculado = 120 "
             "WHERE id = 11")
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET unidad_medida = 'KG', "
             "precio_unitario = 0.12 WHERE id = 503")

    _reapuntar(motor, 11, 503)

    f = fila(motor, 11)
    assert (f["cantidad_albaran"], f["cantidad_convertida"], f["factor_conversion"]) == (
        1000.0, 1000.0, 1.0)
    assert f["importe_calculado"] == pytest.approx(120.0)
    assert AVISO_UNIDAD not in _razones(f)


@pytest.mark.parametrize("unidad", ["UD", " ud ", None])
def test_f065_h2_la_misma_unidad_o_sin_unidad_no_avisa(unidad):
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET unidad_medida = :u WHERE id = 503",
             u=unidad)

    _reapuntar(motor, 11, 503)

    f = fila(motor, 11)
    assert AVISO_UNIDAD not in _razones(f)
    assert f["cantidad_convertida"] == 8.0


@pytest.mark.parametrize("como", ["cantidad", "guardar"])
def test_f065_h2_el_aviso_se_va_al_revisar_la_cantidad(como):
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET unidad_medida = 'M2' WHERE id = 503")
    _reapuntar(motor, 11, 503)

    if como == "cantidad":
        _editar(motor, 11, cantidad=20.0)
    else:
        _editar(motor, 11, bloquear=True)

    f = fila(motor, 11)
    assert AVISO_UNIDAD not in _razones(f)
    assert "ia_match_trusted" in _razones(f)


def test_f065_h2_editar_otra_cosa_no_quita_el_aviso():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET unidad_medida = 'M2' WHERE id = 503")
    _reapuntar(motor, 11, 503)

    _editar(motor, 11, codigo_externo="E-1")

    assert AVISO_UNIDAD in _razones(fila(motor, 11))


def test_f065_h2_plantilla_aviso_visible_en_la_cantidad(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(review_reasons=[AVISO_UNIDAD])],
        display=[fila_detalle()]))
    celda = re.search(r'<td[^>]*data-col="cantidad"[^>]*>.*?</td>', html, re.DOTALL).group(0)

    assert "revisa la cantidad: cambió la unidad" in celda


def test_f065_h2_plantilla_sin_aviso_no_lo_pinta(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()], display=[fila_detalle()]))

    assert "revisa la cantidad" not in html


# =================================================================== #
# H4 · la caché de partidas es por obra
# =================================================================== #
@con_node
def test_f065_h4_js_la_cache_de_partidas_es_por_obra(tmp_path):
    casos = _ejecutar(tmp_path, ["_normLine", "partidasDeRespuesta", "cargarPartidasObra"], """
        var _partidasObra = null, _partidasObraCodigo = null;
        var obra = "", pedidas = [];
        var document = {getElementById: function () { return {value: obra}; }};
        function fetch(url) {
            pedidas.push(url);
            return Promise.resolve({json: function () {
                return {ok: true, items: [{codigo: "01.01", descripcion: "X"}]};
            }});
        }
        (async function () {
            const sin = await cargarPartidasObra();
            obra = "0404";
            const con = await cargarPartidasObra();
            await cargarPartidasObra();
            obra = "0505";
            await cargarPartidasObra();
            console.log(JSON.stringify({sin: sin.items.length, con: con.items.length,
                                        pedidas: pedidas}));
        })();
    """)

    assert casos == {"sin": 0, "con": 1, "pedidas": [
        "/api/sigrid/partidas?obra=0404", "/api/sigrid/partidas?obra=0505"]}


# --- mutación (pasada 2, campaña 1) ------------------------------------ #
@pytest.mark.parametrize(("actual", "nueva", "albaran", "esperado"), [
    (None, "M2", "M2", (6.0, 1.0, None, False)),   # unidad actual desconocida: nada
    ("T", None, "KG", (6.0, 1.0, None, False)),    # unidad nueva desconocida: nada
    ("T", "M2", "KG", (6.0, 1.0, None, True)),     # otra: se deja y se avisa
    ("T", " kg ", "KG", (6.0, 6.0, 1.0, False)),   # la del albarán: su cantidad
    ("T", "t", "KG", (6.0, 1.0, None, False)),     # la misma
])
def test_f065_h2_dominio_cantidades_tras_reapuntar(actual, nueva, albaran, esperado):
    from domain.models.review_models import cantidades_tras_reapuntar

    assert cantidades_tras_reapuntar(
        unidad_actual=actual, unidad_nueva=nueva, unidad_albaran=albaran,
        cantidad_albaran=6.0, cantidad_convertida=1.0, factor=None,
    ) == esperado


def test_f065_h2_dominio_motivos_con_no_escapa_ni_pierde_los_demas():
    from domain.models.review_models import MOTIVO_UNIDAD_CAMBIADA, motivos_con

    assert motivos_con('["camión"]', MOTIVO_UNIDAD_CAMBIADA, True) == (
        '["camión", "front_unidad_cambiada_revisa_cantidad"]')
    assert motivos_con(
        '["camión", "front_unidad_cambiada_revisa_cantidad"]', MOTIVO_UNIDAD_CAMBIADA, False,
    ) == '["camión"]'


@pytest.mark.parametrize(("unidad_fila", "esperado"), [("M2", True), (None, True)])
def test_f065_h2_la_unidad_actual_es_la_de_la_fila_o_la_de_su_linea(unidad_fila, esperado):
    """La fila guarda «M2» (o nada, y entonces vale la de su línea, «UD») y se
    reapunta a una línea en «UD» (sin nada) o «M2» respectivamente."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_contrato = :u WHERE id = 11",
             u=unidad_fila)
    nueva = "UD" if unidad_fila else "M2"
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET unidad_medida = :u WHERE id = 503",
             u=nueva)

    _reapuntar(motor, 11, 503)

    assert (AVISO_UNIDAD in _razones(fila(motor, 11))) is esperado


def test_f065_h2_sin_convertida_el_importe_sale_de_la_cantidad_del_albaran():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_convertida = NULL WHERE id = 11")

    _reapuntar(motor, 11, 503)

    assert fila(motor, 11)["importe_calculado"] == pytest.approx(8 * 115.0)
