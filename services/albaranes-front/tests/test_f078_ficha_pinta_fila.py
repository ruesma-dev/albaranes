# tests/test_f078_ficha_pinta_fila.py
"""F-078 · R6–R8 · la tabla «Líneas a Sigrid» pinta la fila, y solo la fila.

- R6: concepto, unidad y precio salen de las columnas de la fila
  (``descripcion_linea``, ``unidad_contrato``, ``precio_unitario_final``), sin
  completarlos con su línea de contrato, su derivada ni su blanca.
- R7: una columna vacía se pinta vacía; el importe nulo, también (la plantilla
  ya no lo calcula).
- R8: su línea se usa para lo que no es de la fila: el precio del contrato del
  ``title``, la medición, la descripción de la partida, los avisos ✓/⚠ y el
  origen de la derivada.

BBDD SQLite en memoria (``f065_bbdd``: METALFIRE) y la plantilla real con
Jinja2 (``render_detalle``). Sin red.
"""
from __future__ import annotations

import re

import pytest
from f065_bbdd import DOC, construir, ejecutar, repositorio
from sqlalchemy.orm import Session


def _mapa(motor):
    repo = repositorio(motor)
    with Session(motor) as s:
        valoracion = repo._load_valuation_in_session(session=s, document_id=DOC)
        return repo._load_conciliation_map_in_session(session=s, valuation=valoracion)


# =================================================================== #
# R6 · Contrato (filas 11 y 12 casan con 501 y 502)
# =================================================================== #
def test_f078_r6_contrato_pinta_la_descripcion_de_la_fila():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'PUERTA "
             "EI2-60 HOJA DOBLE' WHERE id = 11")

    assert _mapa(motor)[11].descripcion == "PUERTA EI2-60 HOJA DOBLE"


def test_f078_r6_contrato_sin_descripcion_en_la_fila_se_pinta_vacia():
    """Antes la ficha la completaba con «PUERTA CORTAFUEGOS EI2-60» (su línea)."""
    conc = _mapa(construir())[11]

    assert conc.descripcion is None


def test_f078_r6_contrato_pinta_la_unidad_y_el_precio_de_la_fila():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_contrato = 'M2', "
             "precio_unitario_final = 99.5 WHERE id = 11")

    conc = _mapa(motor)[11]

    assert (conc.unidad, conc.unitario) == ("M2", 99.5)


def test_f078_r7_contrato_sin_unidad_ni_precio_en_la_fila_se_pintan_vacios():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_contrato = NULL, "
             "precio_unitario_final = NULL WHERE id = 11")

    conc = _mapa(motor)[11]

    assert (conc.unidad, conc.unitario) == (None, None)


# =================================================================== #
# R6 · Nueva (fila 13, derivada 601 «PORTES», UD, 50 €)
# =================================================================== #
def test_f078_r6_nueva_pinta_la_fila_y_no_la_derivada():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'Portes "
             "a obra', unidad_contrato = 'VIAJE', precio_unitario_final = 55 WHERE id = 13")

    conc = _mapa(motor)[13]

    assert (conc.descripcion, conc.unidad, conc.unitario) == ("Portes a obra", "VIAJE", 55)


def test_f078_r7_nueva_sin_descripcion_ni_unidad_en_la_fila_se_pintan_vacias():
    """Antes: «PORTES» y «UD» de la derivada 601 (el caso de la 386)."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_contrato = NULL, "
             "descripcion_linea = NULL WHERE id = 13")

    conc = _mapa(motor)[13]

    assert (conc.descripcion, conc.unidad) == (None, None)


def test_f078_r6_nueva_el_precio_es_el_de_la_fila_aunque_la_derivada_diga_otro():
    motor = construir()
    ejecutar(motor, "UPDATE contrato_lines_derived SET precio_unitario = 60 WHERE id = 601")

    conc = _mapa(motor)[13]

    assert conc.unitario == 50.0
    # R8: la derivada sigue siendo la referencia de los avisos.
    assert conc.unitario_contrato == 60.0
    assert conc.price_agreement == "disagree"


# =================================================================== #
# R8 · su línea, solo para lo que no es de la fila
# =================================================================== #
def test_f078_r8_contrato_conserva_title_medicion_partida_y_avisos_de_su_linea():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET uds = 40, "
             "pendiente_servir = 12, descripcion_partida = 'Carpinteria' WHERE id = 501")
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = 120 "
             "WHERE id = 11")

    conc = _mapa(motor)[11]

    assert conc.kind == "assigned"
    assert conc.unitario_contrato == 115.0
    assert (conc.medicion_total, conc.medicion_pendiente) == (40, 12)
    assert conc.descripcion_partida == "Carpinteria"
    assert conc.codigo_partida_casada == "01.01"
    assert conc.price_agreement == "disagree"


def test_f078_r8_nueva_conserva_el_origen_de_su_derivada():
    conc = _mapa(construir())[13]

    assert (conc.kind, conc.derived_origen) == ("derived", "nueva_no_match")


# =================================================================== #
# R7 · plantilla: importe nulo = vacío; las celdas pintan lo que llega
# =================================================================== #
def _celda(html, columna):
    patron = re.compile(
        rf'<td class="concilia-td[^"]*" data-col="{columna}"[^>]*>(.*?)</td>', re.S,
    )
    encontrada = patron.search(html)
    assert encontrada is not None, columna
    return encontrada.group(1)


def _aprobado(documento):
    """Aprobado = la tabla en solo lectura (F-065 R4)."""
    return documento.model_copy(update={"approved": True})


def test_f078_r7_importe_nulo_se_pinta_vacio_aunque_haya_cantidad_y_precio(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(importe_calculado=None)],
        display=[fila_detalle(cantidad=6.0, conciliacion={"unitario": 120.0})],
    ))

    celda = _celda(html, "importe")
    assert 'value=""' in celda
    assert "720" not in celda


def test_f078_r7_importe_nulo_en_solo_lectura_es_un_guion(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(_aprobado(documento_detalle(
        lineas_valoracion=[linea_valorada(importe_calculado=None)],
        display=[fila_detalle(cantidad=6.0)],
    )))

    celda = _celda(html, "importe")
    assert "—" in celda
    assert "720" not in celda


@pytest.mark.parametrize("editable", [True, False])
def test_f078_r7_concepto_y_unidad_vacios_se_pintan_vacios(
    render_detalle, documento_detalle, linea_valorada, fila_detalle, editable,
):
    documento = documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"descripcion": None, "unidad": None},
                              concepto="RETIRADA CONTENEDOR RCD")],
    )
    html = render_detalle(documento if editable else _aprobado(documento))

    concepto = _celda(html, "concepto")
    unidad = _celda(html, "unidad")
    assert "RETIRADA CONTENEDOR RCD" not in concepto
    if editable:
        assert 'value=""' in concepto
        assert 'value=""' in unidad
    else:
        assert "—" in concepto and "—" in unidad
