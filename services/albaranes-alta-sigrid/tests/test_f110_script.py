# tests/test_f110_script.py
"""F-110 · T14 · el script de F-106 R18 entiende el ``dto`` (R19).

- Líneas pedidas con ``dto``: el precio enviado se compara con P (el bruto) y el
  ``dto`` enviado con d (``round(d, 2)``, 0,005 de margen); un precio distinto
  cuenta si mueve el importe más de ``TOLERANCIA_CUADRE_EUR``.
- Líneas pedidas sin ``dto``: como F-106 (precio enviado frente a P × (1 − d)).
- Sigue siendo solo ``SELECT`` (el test de F-106 lo cubre) y el CSV gana
  ``dto_enviado`` y ``dto_difiere`` al final.

Sin BBDD. Cifras de CECOIS (12 × 0,645 −7 % = 7,20).
"""
from __future__ import annotations

import pytest

from scripts import listar_altas_descuadradas_f106 as script
from scripts.listar_altas_descuadradas_f106 import comparar_alta, filas_csv


def _fila(**cambios):
    base = {"id": 7, "cantidad_albaran": 12.0, "cantidad_convertida": None,
            "precio_unitario_final": 0.645, "descuento_albaran_aplicado": 7.0,
            "importe_calculado": 7.20}
    base.update(cambios)
    return base


def _linea(precio=0.645, dto=7.0, cantidad=12.0):
    linea = {"referencia_linea": "7", "cantidad": cantidad, "precio": precio}
    if dto is not None:
        linea["dto"] = dto
    return linea


def test_f110_r19_con_dto_bruto_y_dto_correctos_no_sale():
    assert comparar_alta([_linea()], {"7": _fila()}) == []


def test_f110_r19_con_dto_el_despejado_no_es_diferencia():
    """10 × 26,796 −7 % con I 249,21: se mandó el despejado 26,796774."""
    fila = _fila(cantidad_albaran=10.0, precio_unitario_final=26.796, importe_calculado=249.21)
    assert comparar_alta([_linea(precio=26.796774, cantidad=10.0)], {"7": fila}) == []


def test_f110_r19_con_dto_precio_distinto_de_p_sale():
    (d,) = comparar_alta([_linea(precio=0.70)], {"7": _fila()})
    assert (d.precio_difiere, d.dto_difiere, d.dto_enviado) == (True, False, 7.0)
    assert d.precio_neto == pytest.approx(0.645)  # con dto, la referencia es P


def test_f110_r19_con_dto_distinto_de_d_sale():
    (d,) = comparar_alta([_linea(dto=10.0)], {"7": _fila()})
    assert (d.precio_difiere, d.dto_difiere, d.dto_enviado) == (False, True, 10.0)


@pytest.mark.parametrize("dto, difiere", [(7.005, False), (6.995, False), (7.006, True), (7.46, True)])
def test_f110_r19_borde_del_dto(dto, difiere):
    salida = comparar_alta([_linea(dto=dto)], {"7": _fila()})
    assert bool(salida) is difiere


def test_f110_r19_dto_redondeado_de_d():
    fila = _fila(cantidad_albaran=10.0, precio_unitario_final=10.0,
                 descuento_albaran_aplicado=7.456, importe_calculado=92.54)
    assert comparar_alta([_linea(precio=10.0, dto=7.46, cantidad=10.0)], {"7": fila}) == []


@pytest.mark.parametrize("descuento", [None, 0.0, 150.0])
def test_f110_r19_con_dto_pero_d_no_aplicable_sale(descuento):
    fila = _fila(descuento_albaran_aplicado=descuento, importe_calculado=7.74)
    (d,) = comparar_alta([_linea()], {"7": fila})
    assert d.dto_difiere is True


def test_f110_r19_sin_dto_como_f106():
    """Neto 0,60 enviado sin ``dto``: es lo de F-106 (P × (1 − d) = 0,59985)."""
    assert comparar_alta([_linea(precio=0.6, dto=None)], {"7": _fila()}) == []
    (d,) = comparar_alta([_linea(precio=0.645, dto=None)], {"7": _fila()})
    assert (d.precio_difiere, d.dto_difiere, d.dto_enviado) == (True, False, None)
    assert d.precio_neto == pytest.approx(0.59985)


@pytest.mark.parametrize("ilegible", ["7", True, float("nan")])
def test_f110_r19_dto_ilegible_cuenta_como_sin_dto(ilegible):
    (d,) = comparar_alta([_linea(precio=0.645, dto=ilegible)], {"7": _fila()})
    assert (d.precio_difiere, d.dto_enviado) == (True, None)


def test_f110_r19_csv_con_las_columnas_nuevas_al_final():
    assert script.COLUMNAS_CSV[-2:] == ("dto_enviado", "dto_difiere")
    assert script.COLUMNAS_CSV[:4] == ("document_id", "con_ide", "cod", "referencia_linea")
    (d,) = comparar_alta([_linea(dto=7.46)], {"7": _fila()})
    (fila,) = filas_csv([d])
    assert (fila["dto_enviado"], fila["dto_difiere"]) == ("7,46", "sí")
    (sin,) = filas_csv(comparar_alta([_linea(precio=0.645, dto=None)], {"7": _fila()}))
    assert (sin["dto_enviado"], sin["dto_difiere"]) == ("", "no")
    assert list(fila) == list(script.COLUMNAS_CSV)
