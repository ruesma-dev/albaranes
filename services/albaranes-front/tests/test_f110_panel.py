# tests/test_f110_panel.py
"""F-110 · T12 · el panel del alta enseña el ``dto`` (R17, R18).

- R17: la tabla de líneas del panel (``_alta_sigrid.html``) añade «Dto %» con el
  ``dto`` pedido («—» si no se pidió) y, si la previa devolvió otro,
  «(Sigrid: x)». «Precio» es el pedido (el bruto, con ``dto``).
- R18: ``TEXTOS_MOTIVO_ALTA["dto_distinto"]`` = «Sigrid no aplica el descuento
  pedido» (el test de F-077 que lo contrasta con las fuentes de sv9 lo cubre).

Modelo de vista y la plantilla real con Jinja2. Sin red ni BBDD.
"""
from __future__ import annotations

import re

import pytest
from test_f053_t21_panel import _alta, _con_alta, _panel

from domain.models.alta_sigrid_models import TEXTOS_MOTIVO_ALTA, texto_motivo_alta

PETICION = {"lineas": [
    {"referencia_linea": "7", "producto": "MA9999", "descripcion": "CECOIS",
     "cantidad": 12.0, "precio": 0.645, "dto": 7.0},
    {"referencia_linea": "8", "producto": "MA9999", "descripcion": "SIN DTO",
     "cantidad": 10.0, "precio": 4.4},
    {"referencia_linea": "9", "ctrpro_ide": 700101, "cantidad": 108.0, "precio": 0.543,
     "dto": 7.46},
]}


def _respuesta(*lineas):
    return {"estado": "previsto", "totales": {"totbas": 1.0}, "lineas": list(lineas)}


# ------------------------------------------------------------------ R17 · modelo
def test_f110_r17_lineas_con_dto_pedido_y_de_sigrid():
    alta = _alta(peticion=PETICION, respuesta=_respuesta(
        {"referencia_linea": "7", "total": 7.2, "dto": 7, "precio_bruto": 0.645},
        {"referencia_linea": "8", "total": 44.0, "dto": 10},
        {"referencia_linea": "9", "total": 54.27},
    ))
    filas = {f["referencia_linea"]: f for f in alta.lineas}
    assert (filas["7"]["dto"], filas["7"]["dto_sigrid"]) == (7.0, 7)
    assert (filas["7"]["dto_texto"], filas["7"]["dto_sigrid_texto"]) == ("7", None)
    assert (filas["8"]["dto"], filas["8"]["dto_texto"], filas["8"]["dto_sigrid_texto"]) == (
        None, "—", "10")
    assert (filas["9"]["dto_texto"], filas["9"]["dto_sigrid_texto"]) == ("7,46", None)
    assert filas["7"]["precio"] == 0.645


@pytest.mark.parametrize("dto_sigrid, texto", [
    (7.005, None), (7.006, "7,006"), (6.5, "6,5"), (0, "0"), (None, None), ("7", None), (True, None),
])
def test_f110_r17_sigrid_solo_si_devolvio_otro(dto_sigrid, texto):
    alta = _alta(peticion={"lineas": [PETICION["lineas"][0]]}, respuesta=_respuesta(
        {"referencia_linea": "7", "total": 7.2, "dto": dto_sigrid}))
    (fila,) = alta.lineas
    assert fila["dto_sigrid_texto"] == texto


def test_f110_r17_sin_respuesta():
    alta = _alta(peticion=PETICION, respuesta=None)
    assert [(f["dto_texto"], f["dto_sigrid"], f["dto_sigrid_texto"]) for f in alta.lineas] == [
        ("7", None, None), ("—", None, None), ("7,46", None, None),
    ]


# --------------------------------------------------------------- R17 · plantilla
def _celdas(panel):
    cabecera = re.findall(r"<th>([^<]*)</th>", re.search(
        r'<table class="table alta-sigrid-lineas">.*?</thead>', panel, re.DOTALL).group(0))
    cuerpo = re.search(r"<tbody>(.*?)</tbody>", panel.split('alta-sigrid-lineas', 1)[1],
                       re.DOTALL).group(1)
    filas = [re.findall(r"<td>(.*?)</td>", f, re.DOTALL) for f in
             re.findall(r"<tr>(.*?)</tr>", cuerpo, re.DOTALL)]
    return cabecera, [[" ".join(c.split()) for c in fila] for fila in filas]


def test_f110_r17_panel_columna_dto(render_detalle, documento_detalle):
    alta = _alta("revisar", peticion=PETICION, respuesta=_respuesta(
        {"referencia_linea": "7", "total": 7.2},
        {"referencia_linea": "8", "total": 44.0, "dto": 10},
        {"referencia_linea": "9", "total": 54.27, "dto": 7.46},
    ))
    cabecera, filas = _celdas(_panel(render_detalle(_con_alta(documento_detalle(), alta))))
    assert cabecera == ["Línea", "Producto", "Descripción", "Partida", "Cantidad", "Precio",
                        "Dto %", "Total previa", "Motivos"]
    precio, dto = cabecera.index("Precio"), cabecera.index("Dto %")
    assert [(f[precio], f[dto]) for f in filas] == [
        ("0.645", "7"), ("4.4", "— (Sigrid: 10)"), ("0.543", "7,46"),
    ]


def test_f110_r17_panel_dto_distinto_de_sigrid(render_detalle, documento_detalle):
    alta = _alta("revisar", peticion={"lineas": [PETICION["lineas"][0]]}, respuesta=_respuesta(
        {"referencia_linea": "7", "total": 7.74, "dto": 0}))
    cabecera, filas = _celdas(_panel(render_detalle(_con_alta(documento_detalle(), alta))))
    assert filas[0][cabecera.index("Dto %")] == "7 (Sigrid: 0)"


# -------------------------------------------------------------------- R18
def test_f110_r18_texto_de_dto_distinto():
    assert TEXTOS_MOTIVO_ALTA["dto_distinto"] == "Sigrid no aplica el descuento pedido"
    assert texto_motivo_alta("dto_distinto") == "Sigrid no aplica el descuento pedido"
