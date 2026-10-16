# tests/test_f078_escrituras.py
"""F-078 · R9–R16 · sv4 guarda en la fila lo que se va a ver.

- R9: el PATCH de fila toma el estado actual SOLO de la fila; lo que no tiene
  no lo completa con su línea.
- R10: cambiar la descripción la guarda en ``descripcion_linea`` en toda fila
  (Contrato o Nueva, con o sin blanca); vaciarla la deja vacía. Sustituye a
  F-065 CR1/H1 y al override de las Contrato «solo si difiere».
- R11: cambiar la unidad la guarda en ``unidad_contrato`` y, sin conversión,
  también en ``unidad_albaran`` (y en la derivada si es Nueva).
- R12–R16: «Origen ✎», «+ a Sigrid», «Traer líneas contrato» y «Dividir» dejan
  la fila con ``fila_a_guardar`` aplicada, en la misma transacción.

Repositorio real sobre SQLite (``f065_bbdd``: METALFIRE). Sin red.
"""
from __future__ import annotations

import pytest
from f065_bbdd import DOC, construir, ejecutar, fila, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session


def _editar(motor, vid, **campos):
    return repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, campos=campos,
    )


def _columnas(motor, vid, *columnas):
    with Session(motor) as s:
        return tuple(s.execute(
            text(f"SELECT {', '.join(columnas)} FROM albaran_line_valuations "  # noqa: S608
                 "WHERE id = :id"), {"id": vid},
        ).one())


def _derivada(motor, did):
    with Session(motor) as s:
        return dict(s.execute(
            text("SELECT descripcion_linea, unidad_medida, precio_unitario, codigo_partida, "
                 "origen FROM contrato_lines_derived WHERE id = :id"), {"id": did},
        ).mappings().one())


# =================================================================== #
# R9 · el estado actual sale solo de la fila
# =================================================================== #
def test_f078_r9_editar_la_cantidad_no_completa_la_unidad_con_la_de_su_linea():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_contrato = NULL WHERE id = 11")

    _editar(motor, 11, cantidad=6.0)

    assert fila(motor, 11)["unidad_contrato"] is None
    assert fila(motor, 11)["matched_contrato_line_id"] == 501


def test_f078_r9_editar_la_descripcion_no_completa_el_precio_con_el_de_su_linea():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = NULL "
             "WHERE id = 11")

    _editar(motor, 11, descripcion="PUERTA EI2-60 IZQUIERDA")

    f = fila(motor, 11)
    assert f["precio_unitario_final"] is None
    assert f["matched_contrato_line_id"] == 501      # sin cambio de origen


def test_f078_r9_la_descripcion_de_su_linea_cuenta_como_cambio_si_la_fila_no_la_tiene():
    """Antes, «PUERTA CORTAFUEGOS EI2-60» era «lo que ya hay» (la de su línea) y no se
    escribía nada; ahora la fila no la tiene: se guarda."""
    motor = construir()

    _editar(motor, 11, descripcion="PUERTA CORTAFUEGOS EI2-60")

    assert fila(motor, 11)["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-60"


def test_f078_r9_la_derivada_editada_in_situ_recibe_lo_de_la_fila():
    """Nueva 13: la fila dice 55 € y su derivada 50 €; editar la cantidad deja la
    derivada con lo de la fila (el estado actual es el de la fila)."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = 55, "
             "descripcion_linea = 'PORTES A OBRA' WHERE id = 13")

    _editar(motor, 13, cantidad=2.0)

    d = _derivada(motor, 601)
    assert (d["precio_unitario"], d["descripcion_linea"]) == (55.0, "PORTES A OBRA")
    assert fila(motor, 13)["importe_calculado"] == pytest.approx(110.0)


# =================================================================== #
# R10 · la descripción, en descripcion_linea en toda fila
# =================================================================== #
def test_f078_r10_contrato_igual_que_la_de_su_linea_se_guarda():
    """Sustituye al override «solo si difiere» de F-065 R8."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'OTRA' "
             "WHERE id = 11")

    _editar(motor, 11, descripcion="PUERTA CORTAFUEGOS EI2-60")

    f = fila(motor, 11)
    assert f["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-60"
    assert f["matched_contrato_line_id"] == 501


def test_f078_r10_nueva_con_blanca_se_guarda_en_la_fila_y_en_su_derivada():
    motor = construir()

    _editar(motor, 13, descripcion="  PORTES URGENTES  ")

    assert fila(motor, 13)["descripcion_linea"] == "PORTES URGENTES"
    assert _derivada(motor, 601)["descripcion_linea"] == "PORTES URGENTES"


def test_f078_r10_contrato_a_nueva_con_descripcion_nueva_va_a_la_fila_y_a_la_derivada():
    motor = construir()

    _editar(motor, 11, descripcion="PUERTA ESPECIAL", precio_unitario=120.0)

    f = fila(motor, 11)
    assert f["matched_contrato_line_id"] is None
    assert f["descripcion_linea"] == "PUERTA ESPECIAL"
    assert _derivada(motor, f["derived_contrato_line_id"])["descripcion_linea"] == (
        "PUERTA ESPECIAL"
    )


def test_f078_r10_contrato_a_nueva_sin_tocar_la_descripcion_conserva_la_de_la_fila():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = "
             "'PUERTA EI2-60 IZQUIERDA' WHERE id = 11")

    _editar(motor, 11, codigo_partida="09.09")

    f = fila(motor, 11)
    assert f["descripcion_linea"] == "PUERTA EI2-60 IZQUIERDA"
    assert _derivada(motor, f["derived_contrato_line_id"])["descripcion_linea"] == (
        "PUERTA EI2-60 IZQUIERDA"
    )


@pytest.mark.parametrize("vid", [11, 13])
def test_f078_r10_vaciarla_la_deja_vacia(vid):
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'ALGO' "
             "WHERE id = :id", id=vid)

    _editar(motor, vid, descripcion=None)

    assert fila(motor, vid)["descripcion_linea"] is None


def test_f078_r10_sin_blanca_se_guarda_como_siempre():
    motor = construir()
    vid = repositorio(motor).add_standalone_valuation_line(document_id=DOC)

    _editar(motor, vid, descripcion="CARGA INCOMPLETA", cantidad=1.0, precio_unitario=12.5)

    assert fila(motor, vid)["descripcion_linea"] == "CARGA INCOMPLETA"


# =================================================================== #
# R11 · la unidad, también en unidad_albaran sin conversión
# =================================================================== #
def test_f078_r11_nueva_sin_conversion_guarda_la_unidad_en_las_dos_y_en_la_derivada():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET factor_conversion = 1.0 WHERE id = 13")

    _editar(motor, 13, unidad="VIAJE")

    assert _columnas(motor, 13, "unidad_contrato", "unidad_albaran") == ("VIAJE", "VIAJE")
    assert _derivada(motor, 601)["unidad_medida"] == "VIAJE"


def test_f078_r11_con_conversion_no_toca_unidad_albaran():
    """Fila 13: ``factor_conversion`` nulo (conversión desconocida)."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_albaran = 'M3' WHERE id = 13")

    _editar(motor, 13, unidad="VIAJE")

    assert _columnas(motor, 13, "unidad_contrato", "unidad_albaran") == ("VIAJE", "M3")


def test_f078_r11_contrato_que_pasa_a_nueva_por_la_unidad_la_guarda_en_las_dos():
    motor = construir()

    _editar(motor, 11, unidad="PAR")

    f = fila(motor, 11)
    assert f["matched_contrato_line_id"] is None
    assert _columnas(motor, 11, "unidad_contrato", "unidad_albaran") == ("PAR", "PAR")


def test_f078_r11_sin_cambiar_la_unidad_no_se_toca_unidad_albaran():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_albaran = 'UDS' WHERE id = 11")

    _editar(motor, 11, cantidad=7.0)

    assert _columnas(motor, 11, "unidad_contrato", "unidad_albaran") == ("UD", "UDS")
