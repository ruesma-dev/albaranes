# tests/test_f069_script.py
"""F-069 · T4 · script de medición de solo lectura (R25–R27).

Sin red ni BBDD: sigrid-api con ``httpx.MockTransport`` y PostgreSQL con una
conexión de mentira que registra lo que se ejecuta.

- R25: misma consulta y misma clasificación que sv9 (las importa): ``unico``,
  ``ambiguo``, ``de_baja``, ``sin_empleado`` o ``sin_correo``.
- R26: las altas ya escritas con su ``dca.empide`` actual y el que les
  correspondería con R9–R12 (Lista primero, luego el correo, luego nulo).
- R27: CSV UTF-8 con BOM y ``;``; en la salida ningún correo completo (ni una
  @); solo ``SELECT`` y solo la ruta ``/api/sql/read``.
Los Logins, correos e ``ide`` son ficticios.
"""
from __future__ import annotations

import json
import re

import httpx
import pytest

from domain.services import usuario_sigrid
from infrastructure.sigrid import sigrid_api_alta_client as cliente
from scripts import medir_empleados_f069 as script
from scripts.medir_empleados_f069 import (
    AltaEscrita,
    LectorSigrid,
    Medida,
    clase_de,
    empide_que_corresponde,
    filas_csv,
    leer_postgres,
    medir,
    resumen,
)

BASE = "https://sigrid.invalid"


class SigridDeMentira:
    """``sql/read`` de mentira: responde por la SQL y el primer parámetro."""

    def __init__(self, *, correos=None, de_alta=(), dca=None, truncar=False, fallar=False):
        self.correos = correos or {}
        self.de_alta = set(de_alta)
        self.dca = dca or {}
        self.truncar = truncar
        self.fallar = fallar
        self.peticiones: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        if self.fallar:
            return httpx.Response(500, json={})
        cuerpo = json.loads(request.content)
        sql, parametros = cuerpo["sql"], cuerpo["parameters"]
        if sql == cliente.SQL_EMPLEADOS_POR_CORREO:
            columnas, filas = ["IDE", "FECBAJ"], [list(f) for f in self.correos.get(parametros[0], [])]
        elif sql == cliente.SQL_EMPLEADO_DE_ALTA:
            columnas, filas = ["ide"], [[parametros[0]]] if parametros[0] in self.de_alta else []
        else:
            columnas = ["ide", "empide"]
            filas = [[i, self.dca[i]] for i in parametros if i in self.dca]
        return httpx.Response(200, json={
            "ok": True, "columns": columnas, "rows": filas, "row_count": len(filas),
            "truncated": self.truncar,
        })

    def cuerpos(self) -> list[dict]:
        return [json.loads(p.content) for p in self.peticiones]


def _lector(servidor) -> LectorSigrid:
    return LectorSigrid(base_url=BASE + "/", clave="clave-de-mentira", database="ruesma",
                        transport=httpx.MockTransport(servidor), espera_base_s=0)


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


# ------------------------------------------------------------------ #
# R25 · clasificación (la de sv9)
# ------------------------------------------------------------------ #
def test_f069_script_r25_importa_lo_de_sv9():
    assert script.SQL_EMPLEADOS_POR_CORREO is cliente.SQL_EMPLEADOS_POR_CORREO
    assert script.clasificar_empleados_correo is usuario_sigrid.clasificar_empleados_correo
    assert script.correo_ruesma is usuario_sigrid.correo_ruesma
    assert script.empleados_de_filas is cliente.empleados_de_filas
    assert script.CLASES == ("unico", "ambiguo", "de_baja", "sin_empleado", "sin_correo")


@pytest.mark.parametrize("filas, esperado", [
    ([{"ide": 11, "fecbaj": 0}], ("unico", 11)),
    ([{"ide": 11, "fecbaj": None}, {"ide": 12, "fecbaj": 20240101}], ("unico", 11)),
    ([{"ide": 11, "fecbaj": 0}, {"ide": 12, "fecbaj": 0}], ("ambiguo", None)),
    ([{"ide": 11, "fecbaj": 20240101}], ("de_baja", None)),
    ([], ("sin_empleado", None)),
])
def test_f069_script_r25_clases_con_correo(filas, esperado):
    assert clase_de("login1@ruesma.es", filas) == esperado


def test_f069_script_r25_sin_correo():
    assert clase_de(None, []) == ("sin_correo", None)


# ------------------------------------------------------------------ #
# R26 · el empleado que les correspondería
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("medida, lista, esperado", [
    (Medida("login1", "unico", 11), None, 11),
    (Medida("login1", "unico", 11), 99, 99),          # la Lista va primero
    (Medida("login1", "ambiguo", None), None, None),
    (Medida("login1", "de_baja", None), 99, 99),
    (Medida(None, "sin_correo", None), None, None),
    (None, None, None),
])
def test_f069_script_r26_empide_que_corresponde(medida, lista, esperado):
    assert empide_que_corresponde(medida, lista) == esperado


@pytest.mark.parametrize("actual, corresponde, difiere", [
    (2425207, 11, True), (11, 11, False), (None, 11, True),
    # Con nulo sigrid-api pone su defecto: no hay nada que corregir.
    (2425207, None, False), (None, None, False),
])
def test_f069_script_r26_difiere(actual, corresponde, difiere):
    alta = AltaEscrita(con_ide=1, cod="AC26/1", login="login1", usu="login1",
                       empide_actual=actual, empide_que_corresponde=corresponde)
    assert alta.difiere is difiere


# ------------------------------------------------------------------ #
# medir: E/S con dobles
# ------------------------------------------------------------------ #
APROBADORES = ["Login1@ruesma.es", "login1@ruesma.es ", "login2@ruesma.es", "login3@ruesma.es",
               "login4@ruesma.es", "reviewer", None, "x_gmail.com#EXT#@otro.onmicrosoft.com"]
ALTAS_PG = [
    (9000001, "AC26/1", "login1@ruesma.es", "login1"),
    (9000002, "AC26/2", "login2@ruesma.es", "pgris"),
    (9000003, "AC26/3", "login5@ruesma.es", "login5"),
    (9000004, "AC26/4", "reviewer", "pgris"),
]


def _servidor(**extra):
    return SigridDeMentira(
        correos={
            "login1@ruesma.es": [(11, 0)],
            "login2@ruesma.es": [(21, 0), (22, 0)],
            "login3@ruesma.es": [(31, 20240101)],
            "login5@ruesma.es": [(51, 0)],
        },
        dca={9000001: 2425207, 9000002: 2425207, 9000003: 51, 9000004: 2425207},
        **extra,
    )


def test_f069_script_r25_medir_por_login_y_altas():
    servidor = _servidor()
    medidas, altas = medir(_lector(servidor), APROBADORES, ALTAS_PG, {})
    por_login = {m.login: m for m in medidas if m.login}
    assert {k: (m.clase, m.empide_correo) for k, m in por_login.items()} == {
        "login1": ("unico", 11), "login2": ("ambiguo", None), "login3": ("de_baja", None),
        "login4": ("sin_empleado", None), "login5": ("unico", 51),
    }
    assert sum(1 for m in medidas if m.clase == "sin_correo") == 3
    # Un correo con dos grafías es UN Quien aprobó: una sola lectura.
    correos = [c["parameters"][0] for c in servidor.cuerpos()
               if c["sql"] == cliente.SQL_EMPLEADOS_POR_CORREO]
    assert sorted(correos) == ["login1@ruesma.es", "login2@ruesma.es", "login3@ruesma.es",
                               "login4@ruesma.es", "login5@ruesma.es"]
    assert altas == [
        AltaEscrita(9000001, "AC26/1", "login1", "login1", 2425207, 11),
        AltaEscrita(9000002, "AC26/2", "login2", "pgris", 2425207, None),
        AltaEscrita(9000003, "AC26/3", "login5", "login5", 51, 51),
        AltaEscrita(9000004, "AC26/4", None, "pgris", 2425207, None),
    ]
    assert all(m.segundos is not None for m in medidas if m.clase != "sin_correo")


def test_f069_script_r26_la_lista_va_primero_si_es_de_alta():
    lista = usuario_sigrid.leer_equivalencias(
        '{"login1": {"empide": 77}, "login2": {"empide": 88}, "login5": {"usu": "l5"}}')
    servidor = _servidor(de_alta={77})
    _, altas = medir(_lector(servidor), APROBADORES, ALTAS_PG, lista)
    corresponde = {a.con_ide: a.empide_que_corresponde for a in altas}
    # login1: Entrada de alta (77) gana al correo; login2: Entrada de baja ⇒ correo
    # ambiguo ⇒ nulo; login5: Entrada sin empide ⇒ correo.
    assert corresponde == {9000001: 77, 9000002: None, 9000003: 51, 9000004: None}
    comprobados = [c["parameters"] for c in servidor.cuerpos()
                   if c["sql"] == cliente.SQL_EMPLEADO_DE_ALTA]
    assert sorted(comprobados) == [[77], [88]]


def test_f069_script_r27_solo_select_y_solo_sql_read():
    servidor = _servidor(de_alta={77})
    lista = usuario_sigrid.leer_equivalencias('{"login1": {"empide": 77}}')
    medir(_lector(servidor), APROBADORES, ALTAS_PG, lista)
    assert {p.url.path for p in servidor.peticiones} == {"/api/sql/read"}
    assert all(p.method == "POST" for p in servidor.peticiones)
    for cuerpo in servidor.cuerpos():
        assert cuerpo["sql"].startswith("SELECT ")
        assert cuerpo["database"] == "ruesma"


def test_f069_script_r26_dca_troceado_de_500_en_500():
    altas_pg = [(9100000 + i, f"AC26/{i}", "login1@ruesma.es", "login1") for i in range(1203)]
    servidor = _servidor()
    servidor.dca = {9100000 + i: 2425207 for i in range(1203)}
    _, altas = medir(_lector(servidor), ["login1@ruesma.es"], altas_pg, {})
    lotes = [c for c in servidor.cuerpos() if "dbo.dca" in c["sql"]]
    assert [len(c["parameters"]) for c in lotes] == [500, 500, 203]
    for c in lotes:
        assert c["sql"] == script.sql_empide_dca(len(c["parameters"]))
        assert c["max_rows"] == len(c["parameters"])
    assert len(altas) == 1203 and all(a.empide_actual == 2425207 for a in altas)


def test_f069_script_r26_sql_de_dca():
    assert script.sql_empide_dca(3) == (
        "SELECT d.ide, d.empide FROM dbo.dca d WHERE d.ide IN (?, ?, ?)"
    )


def test_f069_script_r26_alta_sin_fila_en_dca_es_none():
    servidor = _servidor()
    servidor.dca = {}
    _, altas = medir(_lector(servidor), [], ALTAS_PG[:1], {})
    assert altas[0].empide_actual is None


def test_f069_script_sin_altas_no_lee_dca():
    servidor = _servidor()
    _, altas = medir(_lector(servidor), ["login1@ruesma.es"], [], {})
    assert altas == []
    assert not [c for c in servidor.cuerpos() if "dbo.dca" in c["sql"]]


def test_f069_script_truncado_es_fallo():
    with pytest.raises(RuntimeError, match="truncad"):
        medir(_lector(_servidor(truncar=True)), ["login1@ruesma.es"], [], {})


def test_f069_script_lectura_caida_reintenta_y_falla():
    servidor = _servidor(fallar=True)
    with pytest.raises(RuntimeError, match="HTTP 500"):
        medir(_lector(servidor), ["login1@ruesma.es"], [], {})
    assert len(servidor.peticiones) == 3


@pytest.mark.parametrize("cuerpo", [{"ok": False}, ["x"], "no-json"])
def test_f069_script_respuesta_no_valida_es_fallo(cuerpo):
    def responder(request):
        if cuerpo == "no-json":
            return httpx.Response(200, content=b"<html>")
        return httpx.Response(200, json=cuerpo)

    with pytest.raises(RuntimeError, match="no válida"):
        _lector(responder).leer(cliente.SQL_EMPLEADO_DE_ALTA, [1], 2)


def test_f069_script_r27_el_lector_rechaza_lo_que_no_es_select():
    with pytest.raises(ValueError, match="SELECT"):
        _lector(_servidor()).leer("UPDATE dbo.dca SET empide = 1", [], 1)


def test_f069_script_r27_el_lector_no_guarda_la_clave_en_repr():
    assert "clave-de-mentira" not in repr(_lector(_servidor()))


# ------------------------------------------------------------------ #
# PostgreSQL: solo SELECT
# ------------------------------------------------------------------ #
def test_f069_script_r27_postgres_solo_select():
    conexion = ConexionDeMentira([("a@ruesma.es",), (None,)], [(1, "AC26/1", "a@ruesma.es", "a")])
    aprobadores, altas = leer_postgres(conexion)
    assert aprobadores == ["a@ruesma.es", None]
    assert altas == [(1, "AC26/1", "a@ruesma.es", "a")]
    assert conexion.sentencias == [script.SQL_PG_APROBADORES, script.SQL_PG_ALTAS]
    for sql in conexion.sentencias:
        assert sql.lstrip().startswith("SELECT ")
    assert "WHERE approved" in script.SQL_PG_APROBADORES
    assert "estado = 'registrado'" in script.SQL_PG_ALTAS
    assert "sigrid_con_ide IS NOT NULL" in script.SQL_PG_ALTAS


# ------------------------------------------------------------------ #
# R27 · salidas sin correos
# ------------------------------------------------------------------ #
def _medido():
    lista = usuario_sigrid.leer_equivalencias('{"login1": {"empide": 77}}')
    return medir(_lector(_servidor(de_alta={77})), APROBADORES, ALTAS_PG, lista)


def test_f069_script_r27_resumen_con_logins_e_ide_sin_correos():
    medidas, altas = _medido()
    texto = resumen(medidas, altas, entradas_lista=1)
    assert "@" not in texto and "gmail" not in texto.lower() and "reviewer" not in texto
    for login in ("login1", "login2", "login3", "login4", "login5"):
        assert login in texto
    for clase in script.CLASES:
        assert clase in texto
    assert "9000001" in texto and "AC26/1" in texto and "77" in texto
    assert re.search(r"difieren\D*1\b", texto)


def test_f069_script_r27_resumen_vacio():
    texto = resumen([], [], entradas_lista=0)
    assert "Quien aprobó distintos: 0" in texto


def test_f069_script_r27_filas_csv_sin_correos():
    medidas, altas = _medido()
    filas = filas_csv(medidas, altas)
    assert {f["tipo"] for f in filas} == {"aprobador", "alta"}
    assert len([f for f in filas if f["tipo"] == "alta"]) == 4
    assert all("@" not in str(v) for f in filas for v in f.values())
    assert list(filas[0]) == list(script.COLUMNAS_CSV)


def test_f069_script_r27_csv_utf8_bom_y_punto_y_coma(tmp_path):
    medidas, altas = _medido()
    ruta = tmp_path / "m.csv"
    script.escribir_csv(ruta, filas_csv(medidas, altas))
    bruto = ruta.read_bytes()
    assert bruto.startswith(b"\xef\xbb\xbf")
    cabecera = bruto.decode("utf-8-sig").splitlines()[0]
    assert cabecera == ";".join(script.COLUMNAS_CSV)


# ------------------------------------------------------------------ #
# main: de punta a punta con dobles
# ------------------------------------------------------------------ #
ENTORNO = {
    "SIGRID_API_BASE_URL": BASE, "SIGRID_API_FUNCTION_KEY": "clave-de-mentira",
    "PG_HOST": "pg.invalid", "PG_USER": "u", "PG_PASSWORD": "p",
}


def _entorno(monkeypatch, **extra):
    for nombre in (*ENTORNO, "PG_PORT", "PG_DB", "PG_SSLMODE", "SIGRID_API_DATABASE",
                   "ALTA_SIGRID_EQUIVALENCIAS_USUARIO"):
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in {**ENTORNO, **extra}.items():
        monkeypatch.setenv(nombre, valor)


def test_f069_script_main_de_punta_a_punta(monkeypatch, tmp_path, capsys):
    _entorno(monkeypatch, ALTA_SIGRID_EQUIVALENCIAS_USUARIO='{"login1": {"empide": 77}}')
    conexion = ConexionDeMentira([(a,) for a in APROBADORES], ALTAS_PG)
    parametros = {}

    def conectar(**kwargs):
        parametros.update(kwargs)
        return conexion

    servidor = _servidor(de_alta={77})
    codigo = script.main(["--salida", str(tmp_path)], conectar=conectar,
                         transport=httpx.MockTransport(servidor))
    assert codigo == 0
    assert conexion.read_only is True and conexion.cerrada is True
    assert parametros == {"host": "pg.invalid", "port": 5432, "dbname": "albaranes",
                          "user": "u", "password": "p", "sslmode": "prefer"}
    md = (tmp_path / "medicion_F-069.md").read_text(encoding="utf-8")
    csv_texto = (tmp_path / "medicion_F-069.csv").read_text(encoding="utf-8-sig")
    salida = capsys.readouterr().out
    for texto in (md, csv_texto, salida):
        assert "@" not in texto
        assert "clave-de-mentira" not in texto and "pg.invalid" not in texto
    assert "login1" in md and "Entradas en la Lista: 1" in md
    assert servidor.cuerpos()[0]["database"] == "ruesma"


def test_f069_script_main_parametros_de_postgres_del_entorno(monkeypatch, tmp_path):
    _entorno(monkeypatch, PG_PORT="6543", PG_DB="otra", PG_SSLMODE="require",
             SIGRID_API_DATABASE="pruebas")
    parametros = {}

    def conectar(**kwargs):
        parametros.update(kwargs)
        return ConexionDeMentira([], [])

    servidor = _servidor()
    assert script.main(["--salida", str(tmp_path)], conectar=conectar,
                       transport=httpx.MockTransport(servidor)) == 0
    assert parametros["port"] == 6543 and parametros["dbname"] == "otra"
    assert parametros["sslmode"] == "require"


@pytest.mark.parametrize("falta", ["SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY",
                                   "PG_HOST", "PG_USER", "PG_PASSWORD"])
def test_f069_script_main_sin_variable_no_conecta(monkeypatch, tmp_path, capsys, falta):
    _entorno(monkeypatch)
    monkeypatch.delenv(falta)
    llamado = []
    codigo = script.main(["--salida", str(tmp_path)], conectar=lambda **k: llamado.append(k))
    assert codigo == 2 and llamado == []
    assert falta in capsys.readouterr().err


def test_f069_script_main_lista_mal_escrita_no_mide(monkeypatch, tmp_path, capsys):
    _entorno(monkeypatch, ALTA_SIGRID_EQUIVALENCIAS_USUARIO="{roto")
    llamado = []
    assert script.main(["--salida", str(tmp_path)], conectar=lambda **k: llamado.append(k)) == 2
    assert llamado == []
    assert "ALTA_SIGRID_EQUIVALENCIAS_USUARIO" in capsys.readouterr().err


def test_f069_script_main_cierra_la_conexion_si_falla(monkeypatch, tmp_path):
    _entorno(monkeypatch)
    conexion = ConexionDeMentira([("login1@ruesma.es",)], [])
    with pytest.raises(RuntimeError):
        script.main(["--salida", str(tmp_path)], conectar=lambda **k: conexion,
                    transport=httpx.MockTransport(lambda r: httpx.Response(400, json={})))
    assert conexion.cerrada is True


def test_f069_script_main_por_defecto_usa_psycopg(monkeypatch):
    import psycopg

    assert script._conectar_por_defecto is psycopg.connect
