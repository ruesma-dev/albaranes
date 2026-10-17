# tests/test_f076_medicion.py
"""F-076 T15 · el script de medición (R22), con conexión y lector falsos.

``scripts/medir_f076_partidas.py`` abre PostgreSQL en solo lectura y aborta si
``SHOW transaction_read_only`` no da ``on``; lee sigrid-api con ``NO_TOLERA``;
toma las credenciales solo del entorno; e imprime solo recuentos (clase de R5 ×
aprobado/pendiente), nunca precios, textos de proveedor ni secretos. La
ejecución real es la MANUAL T19 del humano.
"""
from __future__ import annotations

import json
import re

import pytest
from ruesma_comun.sigrid import PoliticaTruncado, SigridRespuestaTruncada

from scripts import medir_f076_partidas as medir

_COLUMNAS = ["ide", "padide", "cod", "res"]
_FILAS_0678 = [[1, None, "CI", "Costes indirectos"], [2, 1, "CI.4.18", "Medios auxiliares"],
               [3, 1, "CI.03A.2", "Otra"], [4, None, "03.02", "Capítulo"], [5, 4, "03.02.01", "Hoja"]]


class _Resultado:
    def __init__(self, valor=None, filas=None):
        self._valor, self._filas = valor, filas or []

    def scalar(self):
        return self._valor

    def mappings(self):
        return self

    def all(self):
        return self._filas


class _Conexion:
    """Conexión falsa: responde a ``SHOW transaction_read_only`` y al SELECT."""

    def __init__(self, *, solo_lectura="on", filas=()):
        self.solo_lectura = solo_lectura
        self.filas = list(filas)
        self.sentencias: list[str] = []

    def execute(self, sentencia, parametros=None):
        sql = str(sentencia)
        self.sentencias.append(sql)
        if "SHOW transaction_read_only" in sql:
            return _Resultado(self.solo_lectura)
        return _Resultado(filas=self.filas)


class _Lector:
    def __init__(self, *, truncado_en=()):
        self.llamadas: list[tuple] = []
        self.truncado_en = set(truncado_en)

    def __call__(self, sql, parametros, etiqueta, politica, max_rows):
        self.llamadas.append((parametros[0], politica, max_rows))
        if parametros[0] in self.truncado_en:
            raise SigridRespuestaTruncada(etiqueta, 3)
        return list(_COLUMNAS), [list(f) for f in _FILAS_0678]


def _fila(final, *, leida=None, obra="0678", aprobado=False, motivos=()):
    return {"codigo_partida_albaran": leida, "codigo_partida_final": final, "obra_codigo": obra,
            "approved": aprobado, "review_reasons_json": json.dumps(list(motivos)) if motivos else None}


def test_f076_r22_aborta_si_la_sesion_no_es_de_solo_lectura():
    with pytest.raises(medir.SesionNoSoloLectura):
        medir.comprobar_solo_lectura(_Conexion(solo_lectura="off"))
    medir.comprobar_solo_lectura(_Conexion(solo_lectura="on"))


def test_f076_r22_la_conexion_se_abre_en_solo_lectura():
    assert medir.OPCIONES_SOLO_LECTURA == {"options": "-c default_transaction_read_only=on"}


def test_f076_r22_la_consulta_solo_lee():
    sql = " ".join(medir.SQL_LINEAS.split()).upper()
    assert sql.startswith("SELECT ")
    for verbo in ("INSERT", "UPDATE", "DELETE", "ALTER", "DROP", "CREATE"):
        assert verbo not in sql
    assert "PRECIO" not in sql and "IMPORTE" not in sql and "DESCRIPCION" not in sql


def test_f076_r22_cuenta_por_clase_y_estado():
    filas = [
        _fila("CI.4.18", leida="CI.04.18", motivos=["partida_normalizada:CI.04.18>CI.4.18"]),
        _fila("CI.04.18", leida="CI.04.18"),  # normalizable sin normalizar
        _fila("CI.04.18", aprobado=True),
        _fila("CI.14.18", motivos=["partida_fuera_de_lista"]),
        _fila("03.2"),  # clave del capítulo 03.02: fuera de lista
        _fila(None),
        _fila("CI.4.18", obra="0999"),  # obra truncada: sin lista
        _fila("CI.4.18", obra=None),
    ]
    lector = _Lector(truncado_en={"0999"})
    resultado = medir.medir(_Conexion(filas=filas), lector, alm="ALM")
    assert resultado.clases == {
        ("exacta", "pendiente"): 1,
        ("normalizada", "pendiente"): 1,
        ("normalizada", "aprobado"): 1,
        ("fuera_de_lista", "pendiente"): 2,
        ("no_aplica", "pendiente"): 1,
        ("sin_lista", "pendiente"): 2,
    }
    assert resultado.motivos == {
        ("partida_normalizada", "pendiente"): 1,
        ("partida_fuera_de_lista", "pendiente"): 1,
    }
    # UNA consulta por obra, NO_TOLERA y 500.000 filas
    assert sorted(lector.llamadas) == [("0678", PoliticaTruncado.NO_TOLERA, 500_000),
                                       ("0999", PoliticaTruncado.NO_TOLERA, 500_000)]
    assert resultado.obras_sin_lista == 2


def test_f076_r22_el_informe_solo_lleva_recuentos():
    filas = [_fila("CI.04.18", leida="CI.04.18"), _fila("CI.14.18", motivos=["partida_fuera_de_lista"])]
    informe = medir.formatear(medir.medir(_Conexion(filas=filas), _Lector(), alm="ALM"))
    assert "normalizable sin normalizar" in informe
    assert "pendiente" in informe and "aprobado" in informe
    for prohibido in ("CI.04.18", "CI.14.18", "Costes", "Medios", "0678"):
        assert prohibido not in informe


def test_f076_r22_main_sin_configuracion_de_sigrid_falla_sin_secretos(monkeypatch, capsys):
    for nombre in ("SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE"):
        monkeypatch.delenv(nombre, raising=False)
    monkeypatch.setenv("PG_USER", "u")
    monkeypatch.setenv("PG_PASSWORD", "secreto-pg-de-test")
    monkeypatch.setattr(medir, "_ajustes", lambda: __import__("config.settings", fromlist=["Settings"]).Settings(
        _env_file=None))
    assert medir.main([]) == 1
    salida = capsys.readouterr()
    assert "SIGRID_API" in salida.err
    assert "secreto-pg-de-test" not in salida.out + salida.err


def test_f076_r22_main_un_error_no_imprime_su_detalle(monkeypatch, capsys):
    def _roto():
        raise RuntimeError("postgresql://u:secreto-pg-de-test@host/db")

    monkeypatch.setattr(medir, "_ajustes", _roto)
    assert medir.main([]) == 1
    salida = capsys.readouterr()
    assert "secreto-pg-de-test" not in salida.out + salida.err
    assert "RuntimeError" in salida.err


def test_f076_r22_main_completo_con_dobles(monkeypatch, capsys):
    from config.settings import Settings

    ajustes = Settings(_env_file=None, PG_USER="u", PG_PASSWORD="secreto-pg-de-test",
                       SIGRID_API_BASE_URL="https://sigrid.invalid", SIGRID_API_FUNCTION_KEY="clave-de-test",
                       SIGRID_API_DATABASE="db")
    conexion = _Conexion(filas=[_fila("CI.4.18")])
    monkeypatch.setattr(medir, "_ajustes", lambda: ajustes)
    monkeypatch.setattr(medir, "_conectar", lambda a: _Contexto(conexion))
    monkeypatch.setattr(medir, "_lector", lambda a: _Lector())
    assert medir.main([]) == 0
    salida = capsys.readouterr().out
    assert re.search(r"existe tal cual +1 / +0", salida)
    assert "clave-de-test" not in salida and "secreto-pg-de-test" not in salida
    assert any("SHOW transaction_read_only" in s for s in conexion.sentencias)


class _Contexto:
    def __init__(self, conexion):
        self.conexion = conexion

    def __enter__(self):
        return self.conexion

    def __exit__(self, *exc):
        return False
