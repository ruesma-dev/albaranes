# tests/test_f106_script.py
"""F-106 · T19 · script de solo lectura de R18: altas reales ``registrado`` con
una línea que no cuadra o con precio enviado ≠ P × (1 − d).

Sin BBDD: PostgreSQL con una conexión de mentira que registra lo que se
ejecuta. Las cifras son las del caso CECOIS (10 × 11,20 −7 % = 104,16).

- Comparación pura (``comparar_alta``): cuadre con ``cuadra_linea`` de comun y
  precio enviado contra P × (1 − d), con la misma tolerancia en euros.
- CSV UTF-8 con BOM, ``;`` y coma decimal.
- Solo ``SELECT``, en una conexión de solo lectura que se cierra siempre.
"""
from __future__ import annotations

import json

import pytest

from scripts import listar_altas_descuadradas_f106 as script
from scripts.listar_altas_descuadradas_f106 import (
    Descuadre,
    comparar_alta,
    filas_csv,
    leer_postgres,
    listar,
)


def _fila(**cambios):
    base = {"id": 14, "cantidad_albaran": 10.0, "cantidad_convertida": 10.0,
            "precio_unitario_final": 11.2, "descuento_albaran_aplicado": 7.0,
            "importe_calculado": 104.16}
    base.update(cambios)
    return base


def _linea(referencia="14", cantidad=10.0, precio=10.416):
    return {"referencia_linea": referencia, "cantidad": cantidad, "precio": precio}


# =================================================================== #
# Comparación pura
# =================================================================== #
def test_f106_r18_la_que_cuadra_y_con_su_precio_no_sale():
    assert comparar_alta([_linea()], {"14": _fila()}) == []


def test_f106_r18_la_q_cambiada_con_el_importe_de_antes_sale_por_las_dos():
    fila = _fila(cantidad_albaran=48.0, cantidad_convertida=48.0)
    (d,) = comparar_alta([_linea(cantidad=48.0, precio=2.17)], {"14": fila})
    assert (d.referencia_linea, d.no_cuadra, d.precio_difiere) == ("14", True, True)
    assert d.precio_neto == pytest.approx(10.416)


def test_f106_r18_cuadra_pero_el_precio_enviado_no_es_el_neto():
    # Sin vincular con conversión: va la cantidad del albarán (5) y no la Q (10).
    (d,) = comparar_alta([_linea(cantidad=5.0, precio=20.832)], {"14": _fila()})
    assert (d.no_cuadra, d.precio_difiere) == (False, True)


def test_f106_r18_no_cuadra_aunque_el_precio_enviado_sea_el_neto():
    fila = _fila(importe_calculado=120.0)
    (d,) = comparar_alta([_linea(precio=10.416)], {"14": fila})
    assert (d.no_cuadra, d.precio_difiere) == (True, False)


def test_f106_r18_el_redondeo_a_centimos_no_es_descuadre():
    # 3 × 1,10 −7 % = 3,069 ⇒ 3,07; enviado 3,07 / 3 = 1,023333 ≠ 1,023 por redondeo.
    fila = _fila(cantidad_albaran=3.0, cantidad_convertida=3.0, precio_unitario_final=1.1,
                 importe_calculado=3.07)
    assert comparar_alta([_linea(cantidad=3.0, precio=1.023333)], {"14": fila}) == []


def test_f106_r18_sin_descuento_el_neto_es_p():
    fila = _fila(descuento_albaran_aplicado=None, importe_calculado=112.0)
    assert comparar_alta([_linea(precio=11.2)], {"14": fila}) == []
    (d,) = comparar_alta([_linea(precio=10.416)], {"14": fila})
    assert d.precio_difiere is True and d.precio_neto == pytest.approx(11.2)


def test_f106_r18_abono_compara_en_valor_absoluto():
    fila = _fila(cantidad_albaran=-10.0, cantidad_convertida=-10.0, importe_calculado=-104.16)
    assert comparar_alta([_linea(cantidad=-10.0, precio=10.416)], {"14": fila}) == []


def test_f106_r18_linea_sin_fila_o_ilegible_no_se_compara():
    lineas = [_linea(referencia="99"), {"referencia_linea": "14"}, "basura"]
    assert comparar_alta(lineas, {"14": _fila()}) == []


def test_f106_r18_no_comparable_no_cuenta_como_descuadre():
    fila = _fila(precio_unitario_final=None)
    assert comparar_alta([_linea()], {"14": fila}) == []


def test_f106_r18_linea_a_la_que_falta_cantidad_o_precio_no_se_compara():
    fila = _fila(importe_calculado=120.0)  # no cuadra: saldría si se comparase
    lineas = [{"referencia_linea": "14", "cantidad": 10.0},
              {"referencia_linea": "14", "precio": 10.416}]
    assert comparar_alta(lineas, {"14": fila}) == []


def test_f106_r18_un_booleano_no_es_una_cantidad():
    fila = _fila(importe_calculado=120.0)
    assert comparar_alta([_linea(cantidad=True)], {"14": fila}) == []


def test_f106_r18_sin_q_convertida_vale_la_cantidad_del_albaran():
    # Q = convertida ?? albarán: 48 × 11,20 −7 % ≠ 104,16 ⇒ no cuadra.
    fila = _fila(cantidad_albaran=48.0, cantidad_convertida=None)
    (d,) = comparar_alta([_linea(cantidad=48.0)], {"14": fila})
    assert (d.no_cuadra, d.precio_difiere, d.cantidad) == (True, False, 48.0)


def test_f106_r18_justo_en_la_tolerancia_no_es_descuadre():
    # Misma tolerancia que el cuadre (≤ 0,02 €): línea a 0 € enviada a 0,02 €.
    fila = _fila(cantidad_albaran=1.0, cantidad_convertida=1.0, precio_unitario_final=0.0,
                 descuento_albaran_aplicado=None, importe_calculado=0.0)
    assert comparar_alta([_linea(cantidad=1.0, precio=0.02)], {"14": fila}) == []
    (d,) = comparar_alta([_linea(cantidad=1.0, precio=0.03)], {"14": fila})
    assert d.precio_difiere is True


@pytest.mark.parametrize("descuento", [150.0, -5.0, "7 %"])
def test_f106_r18_descuento_no_aplicable_el_neto_es_p(descuento):
    assert script.precio_neto(11.2, descuento) == 11.2


# =================================================================== #
# Lectura (solo SELECT) y listado
# =================================================================== #
class CursorDeMentira:
    def __init__(self, conexion):
        self.conexion = conexion
        self._filas = []

    def execute(self, sql, parametros=None):
        self.conexion.sentencias.append(sql)
        self._filas = self.conexion.respuestas[len(self.conexion.sentencias) - 1]

    def fetchall(self):
        return list(self._filas)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ConexionDeMentira:
    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.sentencias: list[str] = []
        self.read_only = False
        self.cerrada = False

    def cursor(self):
        return CursorDeMentira(self)

    def close(self):
        self.cerrada = True


def _peticion(*lineas):
    return json.dumps({"cod_obra": "O1", "lineas": list(lineas)})


ALTAS = [("DOC1", 9100001, "AC26/1", _peticion(_linea(cantidad=48.0, precio=2.17))),
         ("DOC2", 9100002, "AC26/2", _peticion(_linea(referencia="20")))]
FILAS = [("DOC1", 14, 48.0, 48.0, 11.2, 7.0, 104.16),
         ("DOC2", 20, 10.0, 10.0, 11.2, 7.0, 104.16)]


def test_f106_r18_solo_select_de_altas_reales_registradas():
    conexion = ConexionDeMentira(ALTAS, FILAS)
    altas, filas = leer_postgres(conexion)
    assert len(altas) == 2 and len(filas) == 2
    assert len(conexion.sentencias) == 2
    for sql in conexion.sentencias:
        assert sql.lstrip().upper().startswith("SELECT ")
        assert "estado = 'registrado'" in sql and "modo = 'real'" in sql
        for prohibida in ("INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "CREATE", "TRUNCATE"):
            assert prohibida not in sql.upper()


def test_f106_r18_listar_por_documento():
    descuadres = listar(ALTAS, FILAS)
    assert [(d.document_id, d.con_ide, d.cod, d.referencia_linea) for d in descuadres] == [
        ("DOC1", 9100001, "AC26/1", "14")]


def test_f106_r18_fila_con_columnas_de_menos_falla_en_vez_de_leer_mal():
    with pytest.raises(ValueError):
        listar(ALTAS, [("DOC1", 14, 48.0, 48.0, 11.2, 7.0)])


def test_f106_r18_peticion_ilegible_no_tumba_el_listado():
    altas = [("DOC1", 9100001, "AC26/1", "{roto"), ("DOC3", 9100003, "AC26/3", None), *ALTAS]
    assert len(listar(altas, FILAS)) == 1


def test_f106_r18_csv_con_coma_decimal():
    (fila,) = filas_csv(listar(ALTAS, FILAS))
    assert fila["precio_enviado"] == "2,17" and fila["precio_neto"] == "10,416"
    assert fila["importe"] == "104,16" and fila["no_cuadra"] == "sí"
    assert fila["precio_difiere"] == "sí"


def _entorno(monkeypatch):
    for nombre, valor in {"PG_HOST": "pg.invalid", "PG_USER": "u", "PG_PASSWORD": "p"}.items():
        monkeypatch.setenv(nombre, valor)
    for nombre in ("PG_PORT", "PG_DB", "PG_SSLMODE"):
        monkeypatch.delenv(nombre, raising=False)


def test_f106_r18_main_de_punta_a_punta(monkeypatch, tmp_path, capsys):
    _entorno(monkeypatch)
    conexion = ConexionDeMentira(ALTAS, FILAS)
    parametros = {}

    def conectar(**kwargs):
        parametros.update(kwargs)
        return conexion

    salida = tmp_path / "altas_f106.csv"
    assert script.main(["--salida", str(salida)], conectar=conectar) == 0
    assert conexion.read_only is True and conexion.cerrada is True
    assert parametros == {"host": "pg.invalid", "port": 5432, "dbname": "albaranes",
                          "user": "u", "password": "p", "sslmode": "prefer"}
    crudo = salida.read_bytes()
    assert crudo.startswith(b"\xef\xbb\xbf")
    texto = crudo.decode("utf-8-sig")
    cabecera, linea = texto.splitlines()
    assert cabecera.split(";")[:4] == ["document_id", "con_ide", "cod", "referencia_linea"]
    assert linea.startswith("DOC1;9100001;AC26/1;14;")
    impreso = capsys.readouterr().out
    assert impreso.splitlines()[0].endswith("1 línea descuadrada en 1 alta") and "pg.invalid" not in impreso


def test_f106_r18_main_en_plural_y_en_una_carpeta_nueva(monkeypatch, tmp_path, capsys):
    _entorno(monkeypatch)
    filas = [FILAS[0], ("DOC2", 20, 10.0, 10.0, 11.2, 7.0, 120.0)]
    salida = tmp_path / "nueva" / "dentro" / "altas_f106.csv"
    assert script.main(["--salida", str(salida)],
                       conectar=lambda **_k: ConexionDeMentira(ALTAS, filas)) == 0
    assert salida.exists()
    assert capsys.readouterr().out.splitlines()[0] == "Altas reales registradas: 2 · 2 líneas descuadradas en 2 altas"


def test_f106_r18_ayuda_con_la_primera_linea_del_modulo(capsys):
    with pytest.raises(SystemExit):
        script.main(["--help"])
    assert script.__doc__.splitlines()[0] in capsys.readouterr().out


@pytest.mark.parametrize("falta", ["PG_HOST", "PG_USER", "PG_PASSWORD"])
def test_f106_r18_main_sin_variable_no_conecta(monkeypatch, tmp_path, capsys, falta):
    _entorno(monkeypatch)
    monkeypatch.delenv(falta)
    llamado = []
    codigo = script.main(["--salida", str(tmp_path / "x.csv")], conectar=lambda **k: llamado.append(k))
    assert codigo == 2 and llamado == []
    assert falta in capsys.readouterr().err


def test_f106_r18_main_cierra_la_conexion_si_falla(monkeypatch, tmp_path):
    _entorno(monkeypatch)
    conexion = ConexionDeMentira()
    with pytest.raises(IndexError):
        script.main(["--salida", str(tmp_path / "x.csv")], conectar=lambda **k: conexion)
    assert conexion.cerrada is True


def test_f106_r18_descuadre_es_inmutable():
    d = listar(ALTAS, FILAS)[0]
    assert isinstance(d, Descuadre)
    with pytest.raises(AttributeError):
        d.no_cuadra = False  # type: ignore[misc]
