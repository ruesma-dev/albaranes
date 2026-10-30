# services/albaranes-front/tests/test_f106_t21_supervivientes.py
"""F-106 T21 · tests que cazan los supervivientes de sv4 de la campaña de
mutación del 2026-10-30 (``progress/mutacion_F-106.md``).

Cada test nombra el mutante que mata (fichero:línea). Repositorio real sobre
SQLite (``f065_bbdd``), como el resto de tests de F-106. Sin red ni BBDD real.
"""
from __future__ import annotations

import dataclasses

import pytest
from f065_bbdd import DOC, ejecutar, fila, repositorio
from test_f106_edicion import _edicion, _json
from test_f106_fila import FILA, _cliente, _patch, cecois

from ruesma_comun.edicion_manual import EdicionManual


def _concilia(motor, vid=FILA):
    detalle = repositorio(motor).get_document_detail(DOC)
    return next(d for d in detalle.display_lines if d.valuation_line_id == vid).concilia


def _origen(motor, vid=FILA):
    """Las columnas del origen de la fila (``COLUMNAS`` de ``f065_bbdd`` no
    trae la fuente ni el acuerdo del precio)."""
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    with Session(motor) as s:
        return dict(s.execute(text(
            "SELECT matched_contrato_line_id, derived_contrato_line_id, precio_unitario_source, "
            "precio_unitario_agreement FROM albaran_line_valuations WHERE id = :v"),
            {"v": vid}).mappings().one())


def _poner_edicion(motor, edicion: EdicionManual, vid=FILA):
    ejecutar(motor, "UPDATE albaran_line_valuations SET edicion_manual_json = :j WHERE id = :v",
             j=edicion.a_json(), v=vid)


# =================================================================== #
# review_models.py
# =================================================================== #
def test_f106_t21_texto_edicion_ignora_campos_sin_etiqueta_o_sin_valores():
    """review_models.py:881 (``and`` -> ``or``): un campo sin etiqueta, o una
    etiqueta sin su dict de columnas, no pinta línea (ni revienta)."""
    from domain.models.review_models import texto_edicion

    e = EdicionManual(
        campos={"sin_etiqueta": {"x": 1}, "cantidad": None, "bloqueada": {"bloqueada": True}},
        calculado={"cantidad_albaran": 10.0},
    )
    assert texto_edicion(e) == "Guardada"


def test_f106_t21_a_sigrid_es_inmutable():
    """review_models.py:898 (``frozen=True`` -> ``False``)."""
    from domain.models.review_models import ASigrid

    a = ASigrid(texto="A Sigrid: 1 × 2,00 €", difiere=False, factor=1.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.difiere = True  # type: ignore[misc]


def test_f106_t21_a_sigrid_difiere_solo_por_encima_de_la_tolerancia():
    """review_models.py:933 (``>`` -> ``>=``): una diferencia IGUAL a la
    tolerancia (1e-6) no es «difiere». 0,01 € / 10.000 = 0,000001 frente a un
    P de la ficha 0: la diferencia es exactamente la tolerancia."""
    from domain.models.review_models import TOLERANCIA_PRECIO_SIGRID, a_sigrid_de_fila

    a = a_sigrid_de_fila(vinculada=False, cantidad_albaran=10000.0, cantidad_convertida=None,
                         precio=0.0, importe=0.01)
    assert abs(1e-6 - 0.0) == TOLERANCIA_PRECIO_SIGRID
    assert a is not None and a.difiere is False


def test_f106_t21_cuadre_de_fila_usa_la_convertida_si_la_hay():
    """review_models.py:952 (``is not None`` -> ``is None``): Q de la ficha =
    la convertida (48 × 2,17 = 104,16 cuadra), no la del albarán (10)."""
    from domain.models.review_models import cuadre_de_fila

    assert cuadre_de_fila(cantidad_albaran=10.0, cantidad_convertida=48.0, precio=2.17,
                          descuento=None, importe=104.16) == (True, None)


def test_f106_t21_conciliacion_a_sigrid_difiere_es_false_por_defecto():
    """review_models.py:1663 (``a_sigrid_difiere = False`` -> ``True``)."""
    from domain.models.review_models import ConciliacionDisplay

    assert ConciliacionDisplay(kind="contract").a_sigrid_difiere is False


# =================================================================== #
# review_repository.py · «A Sigrid» en la ficha (vinculada o no)
# =================================================================== #
def _cantidades(motor, *, albaran: float, convertida: float):
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = :a, "
             "cantidad_convertida = :c WHERE id = :v", a=albaran, c=convertida, v=FILA)


def test_f106_t21_fila_vinculada_manda_la_convertida():
    """review_repository.py:1829 (``if not ids`` -> ``if ids``): casada con una
    línea de contrato con ``sigrid_ide`` del contrato de la valoración ⇒
    vinculada ⇒ a Sigrid va la convertida (48), no la del albarán (10)."""
    motor = cecois()
    _cantidades(motor, albaran=10.0, convertida=48.0)
    assert _concilia(motor).a_sigrid == "A Sigrid: 48 × 2,17 €"


def test_f106_t21_fila_sin_casar_manda_la_del_albaran():
    """review_repository.py:1757 (``get(vid, False)`` -> ``get(vid, True)``):
    una fila Nueva (con derivada, sin línea de contrato casada) no es vinculada
    ⇒ a Sigrid va la cantidad del albarán (10), no la convertida (48)."""
    motor = cecois()
    _patch(motor, {"precio_unitario": 12.0})  # Contrato -> Nueva
    assert fila(motor, FILA)["matched_contrato_line_id"] is None
    _cantidades(motor, albaran=10.0, convertida=48.0)
    assert _concilia(motor).a_sigrid.startswith("A Sigrid: 10 × ")


# =================================================================== #
# review_repository.py · PATCH
# =================================================================== #
def test_f106_t21_importe_tecleado_se_compara_redondeado_a_centimos():
    """review_repository.py:2290 (``round(…, 2)`` -> ``round(…, 3)``): 104,164
    sobre una fila de 104,16 es el mismo importe: no se escribe nada."""
    motor = cecois()
    antes = fila(motor, FILA)
    _patch(motor, {"importe": 104.164})
    assert fila(motor, FILA) == antes
    assert _json(motor) is None


def test_f106_t21_importe_de_r6_redondeado_a_centimos():
    """(R6) El importe tecleado que se queda porque cambia Q va a céntimos y de
    él sale P: 104,16 / (48 × 0,93) = 2,333333, no 104,164 / 44,64 = 2,333423.
    Fija el comportamiento de review_repository.py:2307; ese mutante
    (``round(…, 3)``) es EQUIVALENTE: ``recalcular_fila`` vuelve a redondear el
    importe a 2 decimales antes de despejar P y de escribir."""
    motor = cecois()
    _patch(motor, {"cantidad": 48.0, "importe": 104.164})
    f = fila(motor, FILA)
    assert (f["importe_calculado"], f["precio_unitario_final"]) == (104.16, 2.333333)


def test_f106_t21_cambiar_solo_el_dto_registra_solo_el_dto():
    """review_repository.py:2515 (``and`` -> ``or``): el dto mueve el importe
    (modo «importe») pero lo editado es el dto, no la cantidad."""
    motor = cecois()
    _patch(motor, {"descuento": 10.0})
    assert list(_edicion(motor).campos) == ["descuento"]


# =================================================================== #
# review_repository.py · «Volver a lo calculado»
# =================================================================== #
def test_f106_t21_volver_de_una_fila_inexistente_o_de_otro_documento_es_false():
    """review_repository.py:2594 (``or`` -> ``and``) y 2595 (``return False``
    -> ``True``): sin fila, o fila de otro documento, no se toca nada."""
    motor = cecois()
    _patch(motor, {"cantidad": 48.0})
    repo = repositorio(motor)
    antes = fila(motor, FILA)

    assert repo.volver_a_calculado(document_id=DOC, valuation_line_id=99999) is False
    assert repo.volver_a_calculado(document_id="OTRO-DOC", valuation_line_id=FILA) is False
    assert fila(motor, FILA) == antes


def test_f106_t21_volver_sin_calculado_es_false():
    """review_repository.py:2597 (``or not calculado`` -> ``and not
    calculado``): una edición sin ``calculado`` no tiene nada que restaurar."""
    motor = cecois()
    _poner_edicion(motor, EdicionManual(campos={"bloqueada": {"bloqueada": True}}, calculado={}))
    antes = fila(motor, FILA)

    assert repositorio(motor).volver_a_calculado(document_id=DOC, valuation_line_id=FILA) is False
    assert fila(motor, FILA) == antes


def test_f106_t21_volver_a_una_derivada_que_existe_restaura_el_origen():
    """review_repository.py:2605 (``is not None`` -> ``is None``): si la
    derivada calculada sigue existiendo, el origen vuelve a ella."""
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    motor = cecois()
    _patch(motor, {"precio_unitario": 12.0})  # Nueva: sv4 le crea su derivada
    derivada = fila(motor, FILA)["derived_contrato_line_id"]
    assert derivada is not None
    with Session(motor) as s:
        s.execute(text("UPDATE albaran_line_valuations SET derived_contrato_line_id = NULL, "
                       "precio_unitario_source = 'otra' WHERE id = :v"), {"v": FILA})
        s.commit()
    _poner_edicion(motor, EdicionManual(
        campos={"precio_unitario": {"precio_unitario_final": 12.0}},
        calculado={"precio_unitario_final": 11.2, "matched_contrato_line_id": None,
                   "derived_contrato_line_id": derivada, "precio_unitario_source": "derived"},
    ))

    assert repositorio(motor).volver_a_calculado(document_id=DOC, valuation_line_id=FILA) is True
    o = _origen(motor)
    assert (o["derived_contrato_line_id"], o["precio_unitario_source"]) == (derivada, "derived")


def test_f106_t21_volver_sin_linea_de_origen_restaura_la_fuente_del_precio():
    """review_repository.py:2611 (``existe = True`` -> ``False``): sin línea
    de contrato ni derivada calculadas, la fuente del precio calculada vuelve."""
    motor = cecois()
    ejecutar(motor, "UPDATE albaran_line_valuations SET matched_contrato_line_id = NULL, "
             "precio_unitario_source = 'manual', precio_unitario_agreement = 'manual' "
             "WHERE id = :v", v=FILA)
    _poner_edicion(motor, EdicionManual(
        campos={"precio_unitario": {"precio_unitario_final": 12.0}},
        calculado={"precio_unitario_final": 11.2, "matched_contrato_line_id": None,
                   "derived_contrato_line_id": None, "precio_unitario_source": "albaran",
                   "precio_unitario_agreement": None},
    ))

    assert repositorio(motor).volver_a_calculado(document_id=DOC, valuation_line_id=FILA) is True
    o = _origen(motor)
    assert (o["precio_unitario_source"], o["precio_unitario_agreement"]) == ("albaran", None)


# =================================================================== #
# review_repository.py · Dividir
# =================================================================== #
def test_f106_t21_dividir_con_la_misma_partida_solo_registra_la_cantidad():
    """review_repository.py:3593 (``!=`` -> ``==``): si la primera parte
    conserva la partida, la original registra solo su Q nueva."""
    from domain.models.review_models import ParteDivision

    motor = cecois()
    assert repositorio(motor).dividir_linea(
        document_id=DOC, valuation_line_id=FILA,
        partes=[ParteDivision(cantidad=6.0, codigo_partida="01.04"),
                ParteDivision(cantidad=4.0, codigo_partida="01.04")]) is not None
    assert list(_edicion(motor).campos) == ["cantidad"]


# =================================================================== #
# app.py
# =================================================================== #
def test_f106_t21_volver_a_calculado_responde_ok_true(monkeypatch):
    """app.py:1571 (``"ok": True`` -> ``False``)."""

    class _Volver:
        def initialize(self):
            return True

        def volver_a_calculado(self, **kwargs):
            return True

    r = _cliente(monkeypatch, _Volver()).post("/api/documents/DOC/lines/14/volver-a-calculado")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "document_id": "DOC", "valuation_line_id": 14}
