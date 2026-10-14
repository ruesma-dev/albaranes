# tests/test_f053_r14_normalizada.py
"""F-053 v8 · T45 (U6, R14) · altas a mano con el número del proveedor normalizado.

T0b: en Sigrid, ``dca.entref`` lleva el número del proveedor tecleado a mano en
formato libre (``2.172.946`` frente a ``2172946``, ``26/28193``...). La búsqueda
de R14 compara los dos lados normalizados IGUAL: mayúsculas y sin espacio, ``.``,
``-`` ni ``/`` (en T-SQL con ``UPPER`` y ``REPLACE`` anidados; en Python,
``normalizar_referencia``). ``httpx.MockTransport``: sin red.
"""
from __future__ import annotations

import re

import pytest

from domain.services.validador_alta import SEPARADORES_REFERENCIA, normalizar_referencia
from infrastructure.sigrid.sigrid_api_alta_client import SQL_BUSCAR_ALBARANES
from tests.test_f053_cliente_sigrid import Servidor, _cliente, _lectura

SQL_ESPERADO = (
    "SELECT c.ide, c.cod, c.fec FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
    "WHERE c.tip = 14 AND d.entcif = ? AND "
    "UPPER(REPLACE(REPLACE(REPLACE(REPLACE(d.entref, ' ', ''), '.', ''), '-', ''), '/', '')) = ? "
    "AND ISNULL(d.synckey, '') <> ?"
)


@pytest.mark.parametrize("a, b", [
    ("2.172.946", "2172946"),
    ("26/28193", "26-28193"),
    ("26/28193", "2628193"),
    ("7 00004", "700004"),
    ("2026/40/011764", "20264001 1764"),
    ("ab-12.c", "AB12C"),
])
def test_f053_r14_casan_los_que_solo_difieren_en_formato(a, b):
    assert normalizar_referencia(a) == normalizar_referencia(b)


@pytest.mark.parametrize("a, b", [
    ("101535", "101533"),
    ("2.2168.320", "2.168.320"),   # una errata no es formato
    ("A1_2", "A12"),               # el guion bajo no se quita
])
def test_f053_r14_no_casan_los_distintos(a, b):
    assert normalizar_referencia(a) != normalizar_referencia(b)


def test_f053_r14_normalizada_exacta():
    assert normalizar_referencia(" 2.172-946/ab ") == "2172946AB"
    assert normalizar_referencia(None) == ""
    assert SEPARADORES_REFERENCIA == (" ", ".", "-", "/")


def test_f053_r14_sql_normaliza_los_mismos_separadores_que_python():
    assert SQL_BUSCAR_ALBARANES == SQL_ESPERADO
    quitados = tuple(re.findall(r"'(.)', ''\)", SQL_BUSCAR_ALBARANES))
    assert quitados == SEPARADORES_REFERENCIA
    assert "UPPER(" in SQL_BUSCAR_ALBARANES


def test_f053_r14_el_cliente_manda_el_numero_normalizado():
    servidor = Servidor(_lectura([]))
    _cliente(servidor).buscar_albaranes("B00000000", "2.172.946/a", "ALB-d1")
    (cuerpo,) = servidor.cuerpos()
    assert cuerpo["sql"] == SQL_ESPERADO
    assert cuerpo["parameters"] == ["B00000000", "2172946A", "ALB-d1"]


@pytest.mark.parametrize("numero", ["", "...", " - / "])
def test_f053_r14_numero_que_se_queda_vacio_no_busca(numero):
    """Un número solo de separadores casaría con los ``entref`` vacíos: no se busca."""
    servidor = Servidor()
    assert _cliente(servidor).buscar_albaranes("B1", numero, "ALB-d") == []
    assert servidor.peticiones == []
