# tests/test_f019_r4_r7_importe_select.py
"""F-019 · R4-R7 (+ tramo sv5 de R16): el importe leido no se multiplica.

``_SQL_ALBARAN_LINES`` es SQL estandar (``COALESCE``, aritmetica,
``ORDER BY``): se ejecuta TAL CUAL contra SQLite en memoria con la tabla
``albaran_lines_merge`` creada al vuelo. Sin red, sin PostgreSQL, sin
contenedor. Lo que se prueba es la expresion real del servicio, no una
copia: el SQL se importa del modulo de produccion.

Semantica que fija F-019 (R1) y que este fichero vigila:

* ``precio``      = unitario BRUTO, antes de descuento.
* ``precio_neto`` = IMPORTE de la linea DESPUES de descuento (nombre
  historico y enga~noso; lo definen asi el prompt de IA1, el guard de
  consistencia de sv3, el front sv4 y los clientes de Document AI /
  Document Intelligence).
* Formula canonica:
  ``importe = cantidad x precio x (1 - descuento/100)``.

Antes de F-019 el SELECT hacia ``cantidad * COALESCE(precio_neto, ...)``,
es decir multiplicaba por la cantidad un valor que YA era el importe:
la linea 1 del albaran Feymaco 2.137.569 salia a 3.800,52 EUR donde el
documento dice 35,19 EUR.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from infrastructure.database.sqlalchemy_valuation_context_repository import (
    _SQL_ALBARAN_LINES,
)

_DOCUMENTO = "doc-f019"

# Solo las columnas que toca el SELECT. La tabla real (dueno: sv3) tiene
# muchas mas; anadir aqui las que no se leen no probaria nada.
_DDL_ALBARAN_LINES_MERGE = text(
    """
    CREATE TABLE albaran_lines_merge (
        id                  INTEGER PRIMARY KEY,
        document_id         TEXT,
        line_index          INTEGER,
        codigo              TEXT,
        concepto            TEXT,
        unidad_medida       TEXT,
        cantidad            REAL,
        precio              REAL,
        precio_neto         REAL,
        descuento           REAL,
        codigo_imputacion   TEXT,
        contexto_linea_json TEXT
    )
    """
)

_INSERT = text(
    """
    INSERT INTO albaran_lines_merge (
        id, document_id, line_index, codigo, concepto, unidad_medida,
        cantidad, precio, precio_neto, descuento, codigo_imputacion,
        contexto_linea_json
    ) VALUES (
        :id, :document_id, :line_index, :codigo, :concepto, :unidad_medida,
        :cantidad, :precio, :precio_neto, :descuento, :codigo_imputacion,
        :contexto_linea_json
    )
    """
)

# --------------------------------------------------------------------- #
# Albaran Feymaco 2.137.569 (ferreteria, contrato CTSU24/0454, 40 % de
# descuento en las cinco lineas). Numeros tomados del PDF y del informe
# progress/prueba_local_feymaco_20260818.md.
#
# COMENTARIO CRUZADO: esta misma fixture se repite, con los mismos
# numeros, en la suite de sv6
# (services/albaran-valoracion-persist/tests/test_f019_r16_r17_feymaco.py).
# Es deliberado: son los dos tramos de la MISMA cadena (sv5 fabrica el
# importe efectivo, sv6 decide precio e importe finales) y sv5 y sv6 no
# pueden importarse en la misma sesion de pytest (paquetes homonimos).
# Si estos numeros cambian, hay que cambiarlos en los dos sitios.
# --------------------------------------------------------------------- #
#: (line_index, concepto, cantidad, precio, descuento, precio_neto)
LINEAS_2137569: tuple[tuple[int, str, float, float, float, float], ...] = (
    (1, "PAPEL HIGIENICO (SACO 108)", 108.0, 0.543, 40.0, 35.19),
    (2, "LTS. JABON LIQUIDO PH NEUTRO", 10.0, 3.422, 40.0, 20.53),
    (3, "ROLLO PAPEL IND.", 12.0, 7.726, 40.0, 55.63),
    (4, "KGS ANIL ESPECIAL FEYMACO", 4.0, 5.497, 40.0, 13.19),
    (5, "BOLSA BASURA 52X58", 100.0, 0.252, 40.0, 15.12),
)

#: Total del albaran 2.137.569. Antes de F-019 salia 6.238,14 EUR.
TOTAL_2137569 = 139.66


@pytest.fixture
def motor():
    """SQLite en memoria con ``albaran_lines_merge`` creada al vuelo."""
    engine = create_engine("sqlite://")
    with engine.begin() as conexion:
        conexion.execute(_DDL_ALBARAN_LINES_MERGE)
    try:
        yield engine
    finally:
        engine.dispose()


def _insertar(motor, filas: list[dict]) -> None:
    completas = []
    for indice, fila in enumerate(filas, start=1):
        completa = {
            "id": indice,
            "document_id": _DOCUMENTO,
            "line_index": indice,
            "codigo": None,
            "concepto": None,
            "unidad_medida": None,
            "cantidad": None,
            "precio": None,
            "precio_neto": None,
            "descuento": None,
            "codigo_imputacion": None,
            "contexto_linea_json": None,
        }
        completa.update(fila)
        completas.append(completa)
    with motor.begin() as conexion:
        for fila in completas:
            conexion.execute(_INSERT, fila)


def _ejecutar_select(motor, filas: list[dict]) -> list[dict]:
    """Inserta las filas y ejecuta el SELECT REAL de sv5 sobre ellas."""
    _insertar(motor, filas)
    with motor.connect() as conexion:
        return [
            dict(fila)
            for fila in conexion.execute(
                _SQL_ALBARAN_LINES, {"document_id": _DOCUMENTO}
            ).mappings().all()
        ]


# --------------------------------------------------------------------- #
# R4 — el importe leido viaja tal cual
# --------------------------------------------------------------------- #
def test_f019_r4_importe_leido_no_se_multiplica_por_la_cantidad(motor):
    """Linea 1 del 2.137.569: 35,19 EUR, NUNCA 108 x 35,19 = 3.800,52."""
    filas = _ejecutar_select(
        motor,
        [{"cantidad": 108.0, "precio": 0.543, "descuento": 40.0,
          "precio_neto": 35.19}],
    )

    assert filas[0]["importe_albaran"] == pytest.approx(35.19)
    assert filas[0]["importe_albaran"] != pytest.approx(3800.52)


def test_f019_r4_el_resto_de_columnas_del_select_no_cambian(motor):
    """El fix mueve un parentesis: lo demas del contexto sigue igual."""
    filas = _ejecutar_select(
        motor,
        [{
            "codigo": "ART-1", "concepto": "PAPEL HIGIENICO (SACO 108)",
            "unidad_medida": "UD", "cantidad": 108.0, "precio": 0.543,
            "descuento": 40.0, "precio_neto": 35.19,
            "codigo_imputacion": "P4/P5.36.01",
            "contexto_linea_json": '{"familia": "otro"}',
        }],
    )

    fila = filas[0]
    assert fila["merge_line_id"] == 1
    assert fila["line_index"] == 1
    assert fila["codigo"] == "ART-1"
    assert fila["descripcion"] == "PAPEL HIGIENICO (SACO 108)"
    assert fila["unidad_medida"] == "UD"
    assert fila["cantidad"] == pytest.approx(108.0)
    assert fila["precio_unitario_albaran"] == pytest.approx(0.543)
    assert fila["codigo_partida_albaran"] == "P4/P5.36.01"
    assert fila["contexto_linea_json"] == '{"familia": "otro"}'
    assert fila["descuento_albaran"] == pytest.approx(40.0)
    assert fila["precio_neto_albaran"] == pytest.approx(35.19)


def test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco(motor):
    """Las 5 lineas del 2.137.569 y su total: 139,66 EUR (era 6.238,14)."""
    filas = _ejecutar_select(
        motor,
        [
            {"line_index": indice, "concepto": concepto, "cantidad": cantidad,
             "precio": precio, "descuento": descuento,
             "precio_neto": precio_neto}
            for indice, concepto, cantidad, precio, descuento, precio_neto
            in LINEAS_2137569
        ],
    )

    assert [f["descripcion"] for f in filas] == [
        linea[1] for linea in LINEAS_2137569
    ]
    for fila, linea in zip(filas, LINEAS_2137569, strict=True):
        assert fila["importe_albaran"] == pytest.approx(linea[5]), linea[1]

    total = sum(f["importe_albaran"] for f in filas)
    assert total == pytest.approx(TOTAL_2137569, abs=0.005)


# --------------------------------------------------------------------- #
# R5 — sin importe leido, se deriva de precio x cantidad x (1 - dto/100)
# --------------------------------------------------------------------- #
def test_f019_r5_sin_precio_neto_se_deriva_del_precio_con_descuento(motor):
    """Cascada del FIX 2 (jul 2026), intacta: 108 x 0,543 x 0,6."""
    filas = _ejecutar_select(
        motor,
        [{"cantidad": 108.0, "precio": 0.543, "descuento": 40.0,
          "precio_neto": None}],
    )

    assert filas[0]["importe_albaran"] == pytest.approx(108 * 0.543 * 0.6)


def test_f019_r5_sin_precio_neto_ni_descuento_usa_precio_por_cantidad(motor):
    """Sin descuento, ``COALESCE(descuento, 0)`` deja el bruto."""
    filas = _ejecutar_select(
        motor,
        [{"cantidad": 12.0, "precio": 7.726, "descuento": None,
          "precio_neto": None}],
    )

    assert filas[0]["importe_albaran"] == pytest.approx(12 * 7.726)


# --------------------------------------------------------------------- #
# R6 — sin ningun valor leido, NULL (el caso hormigon)
# --------------------------------------------------------------------- #
def test_f019_r6_sin_precio_ni_precio_neto_el_importe_es_nulo(motor):
    """Hormigon: el albaran no imprime precios; el importe lo pone sv6."""
    filas = _ejecutar_select(
        motor,
        [{"cantidad": 8.0, "precio": None, "descuento": None,
          "precio_neto": None}],
    )

    assert filas[0]["importe_albaran"] is None
    assert filas[0]["cantidad"] == pytest.approx(8.0)


# --------------------------------------------------------------------- #
# R7 — importe leido sin cantidad: el importe NO se pierde
# --------------------------------------------------------------------- #
def test_f019_r7_precio_neto_sin_cantidad_conserva_el_importe_leido(motor):
    """Antes salia NULL (el producto con NULL es NULL). Ahora 35,19."""
    filas = _ejecutar_select(
        motor,
        [{"cantidad": None, "precio": 0.543, "descuento": 40.0,
          "precio_neto": 35.19}],
    )

    assert filas[0]["importe_albaran"] == pytest.approx(35.19)


def test_f019_r7_precio_neto_sin_precio_unitario_tambien_manda(motor):
    """Fila 5 de la matriz del design: sin ``precio``, manda el neto."""
    filas = _ejecutar_select(
        motor,
        [{"cantidad": 108.0, "precio": None, "descuento": 40.0,
          "precio_neto": 35.19}],
    )

    assert filas[0]["importe_albaran"] == pytest.approx(35.19)


def test_f019_r5_sin_precio_neto_ni_precio_pero_con_cantidad_nula(motor):
    """Sin cantidad y sin neto no hay nada que derivar: NULL."""
    filas = _ejecutar_select(
        motor,
        [{"cantidad": None, "precio": 0.543, "descuento": 40.0,
          "precio_neto": None}],
    )

    assert filas[0]["importe_albaran"] is None
