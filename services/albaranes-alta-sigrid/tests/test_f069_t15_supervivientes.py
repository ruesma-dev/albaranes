# tests/test_f069_t15_supervivientes.py
"""F-069 · T15 · tests que matan supervivientes de la campaña de mutación
(``progress/mutacion_F-069.md``). Sin red ni BBDD: el script se ejecuta con
``--help`` (sale antes de leer el entorno) y el resto con dobles.
"""
from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from domain.services.usuario_sigrid import leer_equivalencias
from scripts.medir_empleados_f069 import AltaEscrita, Medida, medir, resumen
from tests.test_f069_script import ConexionDeMentira, SigridDeMentira, _lector

from scripts import medir_empleados_f069 as script

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "scripts" / "medir_empleados_f069.py"


# ------------------------------------------------------------------ #
# usuario_sigrid.py:130 · dentro de una Entrada, las claves distinguen
# mayúsculas: «USU» no es «usu» repetida, es una clave no admitida.
# ------------------------------------------------------------------ #
def test_f069_t15_clave_interna_en_mayusculas_es_no_admitida_no_repetida():
    with pytest.raises(ValueError) as error:
        leer_equivalencias('{"login1": {"usu": "a", "USU": "b"}}')
    assert "no admitidas" in str(error.value) and "'USU'" in str(error.value)
    assert "repetida" not in str(error.value)


# ------------------------------------------------------------------ #
# medir_empleados_f069.py:44 y :382 · el script se lanza tal cual desde la
# raíz del repositorio (fuera de sv9) y su ayuda dice qué es.
# ------------------------------------------------------------------ #
def test_f069_t15_script_arranca_fuera_de_sv9_y_su_ayuda_es_la_primera_linea(tmp_path):
    assert script.RAIZ_SV9 == RAIZ
    entorno = {"PATH": "", "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
    salida = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"], cwd=tmp_path, env=entorno,
        capture_output=True, text=True, encoding="utf-8", timeout=60, check=False,
    )
    assert salida.returncode == 0, salida.stderr
    ayuda = " ".join(salida.stdout.split())
    primera = " ".join(script.__doc__.splitlines()[0].split())
    assert primera in ayuda
    assert " ".join(script.__doc__.splitlines()[1].split()) not in ayuda


# ------------------------------------------------------------------ #
# :110 y :121 · Medida y AltaEscrita son inmutables.
# ------------------------------------------------------------------ #
def test_f069_t15_medida_y_alta_escrita_son_inmutables():
    medida = Medida("login1", "unico", 11)
    alta = AltaEscrita(9000001, "AC26/1", "login1", "login1", 2425207, 11)
    with pytest.raises(dataclasses.FrozenInstanceError):
        medida.clase = "ambiguo"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        alta.empide_actual = 11  # type: ignore[misc]


# ------------------------------------------------------------------ #
# :193 · el porcentaje es n / total, también con n > 1.
# ------------------------------------------------------------------ #
def test_f069_t15_porcentaje_con_varios_de_una_clase():
    medidas = [Medida("login1", "unico", 11), Medida("login2", "unico", 22),
               Medida("login3", "ambiguo", None), Medida(None, "sin_correo", None)]
    texto = resumen(medidas, [], entradas_lista=0)
    assert "| unico | 2 | 50,0 |" in texto
    assert "| ambiguo | 1 | 25,0 |" in texto
    assert "| de_baja | 0 | 0,0 |" in texto


# ------------------------------------------------------------------ #
# :343 · lo que tardó la consulta es la diferencia de dos instantes.
# ------------------------------------------------------------------ #
def test_f069_t15_segundos_es_lo_que_tardo_la_consulta(monkeypatch):
    # Un reloj que avanza 0,25 s por lectura y parte de 1000 s (httpx también
    # lo lee): la diferencia es pequeña y positiva; una suma daría ~2000 s.
    reloj = iter(1000.0 + 0.25 * n for n in range(1000))
    monkeypatch.setattr(script.time, "perf_counter", lambda: next(reloj))
    servidor = SigridDeMentira(correos={"login1@ruesma.es": [(11, 0)]})
    medidas, _ = medir(_lector(servidor), ["login1@ruesma.es"], [], {})
    (segundos,) = [m.segundos for m in medidas]
    assert 0 < segundos < 10


# ------------------------------------------------------------------ #
# :414 · --salida puede ser una carpeta que aún no existe, anidada.
# ------------------------------------------------------------------ #
def test_f069_t15_salida_anidada_que_no_existe(monkeypatch, tmp_path):
    for nombre, valor in {"SIGRID_API_BASE_URL": "https://sigrid.invalid/",
                          "SIGRID_API_FUNCTION_KEY": "clave-de-mentira",
                          "PG_HOST": "pg.invalid", "PG_USER": "u", "PG_PASSWORD": "p"}.items():
        monkeypatch.setenv(nombre, valor)
    monkeypatch.delenv("ALTA_SIGRID_EQUIVALENCIAS_USUARIO", raising=False)
    salida = tmp_path / "a" / "b"
    conexion = ConexionDeMentira([], [])
    codigo = script.main(["--salida", str(salida)], conectar=lambda **k: conexion,
                         transport=httpx.MockTransport(SigridDeMentira()))
    assert codigo == 0
    assert (salida / "medicion_F-069.md").is_file()
    assert (salida / "medicion_F-069.csv").is_file()


# ------------------------------------------------------------------ #
# :286 · la espera entre reintentos tiene tope de 30 s, por grande que sea
# la espera base.
# ------------------------------------------------------------------ #
def test_f069_t15_espera_entre_reintentos_con_tope_de_30_s(monkeypatch):
    esperas: list[float] = []
    monkeypatch.setattr("tenacity.nap.time.sleep", esperas.append)
    lector = script.LectorSigrid(
        base_url="https://sigrid.invalid/", clave="clave-de-mentira", database="ruesma",
        transport=httpx.MockTransport(SigridDeMentira(fallar=True)), espera_base_s=100,
    )
    with pytest.raises(RuntimeError, match="sin respuesta"):
        lector.leer("SELECT 1", [], 1)
    assert esperas == [30, 30]
