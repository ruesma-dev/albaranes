# tests/test_f078_relleno.py
"""F-078 · R21–R25 · ``scripts/rellenar_filas_f078.py``: el relleno de lo existente.

- R21: por defecto solo lee (``READ ONLY``) e informa, por columna,
  ``line_kind`` y aprobado / pendiente, cuántas filas cambiarían y sus ``id``.
- R22: con ``--aplicar`` escribe en una transacción solo las columnas que
  difieren y vuelve a contar; una segunda pasada da 0.
- R23: se salta la papelera y las altas bloqueantes; incluye aprobados y
  pendientes.
- R24: nunca imprime la cadena de conexión ni credenciales.
- R25: tras el relleno, lo que pinta la ficha nueva (la fila) es lo que pintaba
  la de antes, salvo el concepto de las Nueva con blanca sin descripción propia,
  que pasa a ser el del papel (P1 = (b)).

SQLite en memoria con las tablas mínimas (como ``f065_bbdd`` de sv4) y filas
como las medidas en producción (``progress/spec_F-078.md`` §1 y §3). Sin red.
"""
from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import create_engine, text

DDL = (
    "CREATE TABLE albaran_documents_merge (id VARCHAR(64) PRIMARY KEY, "
    "approved BOOLEAN NOT NULL DEFAULT 0, is_active BOOLEAN NOT NULL DEFAULT 1)",
    "CREATE TABLE albaran_valuations (id VARCHAR(64) PRIMARY KEY, "
    "document_id VARCHAR(64) NOT NULL)",
    "CREATE TABLE albaran_lines_merge (id INTEGER PRIMARY KEY, document_id VARCHAR(64), "
    "concepto TEXT)",
    "CREATE TABLE albaran_contrato_lines_merge (id INTEGER PRIMARY KEY, "
    "descripcion_linea TEXT, unidad_medida VARCHAR(32), precio_unitario DOUBLE PRECISION)",
    "CREATE TABLE contrato_lines_derived (id INTEGER PRIMARY KEY, descripcion_linea TEXT, "
    "unidad_medida VARCHAR(32), precio_unitario DOUBLE PRECISION, codigo_partida VARCHAR(64))",
    "CREATE TABLE albaran_line_valuations (id INTEGER PRIMARY KEY, "
    "valuation_id VARCHAR(64) NOT NULL, merge_line_id INTEGER, "
    "matched_contrato_line_id INTEGER, derived_contrato_line_id INTEGER, "
    "line_kind VARCHAR(32), descripcion_linea TEXT, unidad_contrato VARCHAR(32), "
    "unidad_albaran VARCHAR(32), precio_unitario_final DOUBLE PRECISION, "
    "cantidad_albaran DOUBLE PRECISION, cantidad_convertida DOUBLE PRECISION, "
    "factor_conversion DOUBLE PRECISION, importe_calculado DOUBLE PRECISION, "
    "codigo_partida_final VARCHAR(64), producto_sigrid VARCHAR(24), "
    "bloqueada BOOLEAN NOT NULL DEFAULT 0)",
)
DDL_ALTAS = (
    "CREATE TABLE albaran_altas_sigrid (document_id VARCHAR(64) PRIMARY KEY, "
    "estado VARCHAR(24) NOT NULL)"
)

#: El caso (aprobado) y otro pendiente, uno en la papelera y uno registrado.
CASO, PENDIENTE, PAPELERA, REGISTRADO = "86c13097", "4348ecdc", "papelera", "registrado"


def _ejecutar(motor, sql: str, **parametros: Any) -> None:
    with motor.begin() as conexion:
        conexion.execute(text(sql), parametros)


def _fila(motor, **campos: Any) -> None:
    fila = {
        "valuation_id": f"v-{CASO}", "merge_line_id": None, "matched_contrato_line_id": None,
        "derived_contrato_line_id": None, "line_kind": "from_albaran",
        "descripcion_linea": None, "unidad_contrato": None, "unidad_albaran": None,
        "precio_unitario_final": None, "cantidad_albaran": 1.0, "cantidad_convertida": None,
        "factor_conversion": 1.0, "importe_calculado": 10.0, "codigo_partida_final": "01.01",
        "producto_sigrid": None, "bloqueada": False,
    }
    fila.update(campos)
    _ejecutar(motor, f"INSERT INTO albaran_line_valuations ({', '.join(fila)}) "
              f"VALUES ({', '.join(':' + c for c in fila)})", **fila)


def construir(*, con_altas: bool = True):
    """Filas como las medidas en producción (§1 y §3 de ``spec_F-078.md``)."""
    motor = create_engine("sqlite://")
    with motor.begin() as conexion:
        for sentencia in DDL + ((DDL_ALTAS,) if con_altas else ()):
            conexion.execute(text(sentencia))
    for doc, aprobado, activo in (
        (CASO, True, True), (PENDIENTE, False, True), (PAPELERA, False, False),
        (REGISTRADO, True, True),
    ):
        _ejecutar(motor, "INSERT INTO albaran_documents_merge VALUES (:d, :a, :i)",
                  d=doc, a=aprobado, i=activo)
        _ejecutar(motor, "INSERT INTO albaran_valuations VALUES (:v, :d)", v=f"v-{doc}", d=doc)
    if con_altas:
        _ejecutar(motor, "INSERT INTO albaran_altas_sigrid VALUES (:d, 'no_admitido')", d=CASO)
        _ejecutar(motor, "INSERT INTO albaran_altas_sigrid VALUES (:d, 'registrado')",
                  d=REGISTRADO)
    _ejecutar(motor, "INSERT INTO albaran_lines_merge VALUES (7385, :d, 'Mortero M-5'), "
              "(7379, :p, 'DISCO C/ACERO 230 BOSCH'), (7401, :p, 'HA-25/B/20/IIa'), "
              "(7500, :p, 'ARIDO 20/40'), (7900, :x, 'PAPELERA'), (7901, :r, 'REG')",
              d=CASO, p=PENDIENTE, x=PAPELERA, r=REGISTRADO)
    _ejecutar(motor, "INSERT INTO albaran_contrato_lines_merge VALUES "
              "(50, 'HORMIGON HA-25', 'M3', 68.4), (51, 'GRAVA 20/40', 'TN', 12.87), "
              "(52, 'MATERIAL DE FERRETERIA', 'UD', 6.4)")
    _ejecutar(motor, "INSERT INTO contrato_lines_derived VALUES "
              "(238, 'MORTERO M-5', 'm3', 100.6, '01.05.07'), "
              "(239, 'CARGA INCOMPLETA', 'M3', 12.5, NULL), "
              "(231, 'MATERIAL DE FERRETERIA', 'UD', 6.4, '02.01'), "
              "(240, 'INCREMENTO — AÑO 2026', 'M3', 4.0, '03.02'), "
              "(241, 'PROPIA', 'UD', 1.0, NULL)")
    # El caso (aprobado): 385 Nueva con blanca y 386 manual sin blanca.
    _fila(motor, id=385, merge_line_id=7385, derived_contrato_line_id=238,
          unidad_contrato="m3", precio_unitario_final=100.6, cantidad_albaran=3.0,
          importe_calculado=301.8, codigo_partida_final="01.05.07")
    _fila(motor, id=386, line_kind="manual", derived_contrato_line_id=239,
          unidad_contrato="M3", precio_unitario_final=12.5, cantidad_convertida=1.0,
          importe_calculado=12.5, codigo_partida_final=None)
    # Pendiente: ferretería (Nueva con blanca), vinculada sin convertida, sintética
    # derivada, Contrato sin descripción y una ya completa.
    _fila(motor, id=379, valuation_id=f"v-{PENDIENTE}", merge_line_id=7379,
          derived_contrato_line_id=231, unidad_contrato="UD", unidad_albaran="UD",
          precio_unitario_final=6.4, cantidad_albaran=2.0, cantidad_convertida=2.0,
          importe_calculado=12.8)
    _fila(motor, id=401, valuation_id=f"v-{PENDIENTE}", merge_line_id=7401,
          matched_contrato_line_id=50, unidad_contrato="M3", unidad_albaran="M3",
          precio_unitario_final=68.4, cantidad_albaran=6.0, importe_calculado=410.4,
          producto_sigrid="MA9999", bloqueada=True)
    _fila(motor, id=402, valuation_id=f"v-{PENDIENTE}", line_kind="synthetic_modifier",
          derived_contrato_line_id=240, unidad_contrato="M3", unidad_albaran="M3",
          precio_unitario_final=4.0, cantidad_albaran=6.0, cantidad_convertida=6.0,
          importe_calculado=24.0)
    _fila(motor, id=403, valuation_id=f"v-{PENDIENTE}", merge_line_id=7500,
          matched_contrato_line_id=51, unidad_contrato="TN", unidad_albaran="TN",
          precio_unitario_final=12.87, cantidad_albaran=24.5, cantidad_convertida=24.5,
          importe_calculado=315.32)
    _fila(motor, id=404, valuation_id=f"v-{PENDIENTE}", line_kind="manual",
          derived_contrato_line_id=241, descripcion_linea="PROPIA", unidad_contrato="UD",
          unidad_albaran="UD", precio_unitario_final=1.0, cantidad_convertida=1.0)
    # Con conversión desconocida (factor nulo): no se tocan cantidades ni unidad del papel.
    _fila(motor, id=405, valuation_id=f"v-{PENDIENTE}", merge_line_id=7401,
          matched_contrato_line_id=50, unidad_contrato="M3", factor_conversion=None,
          precio_unitario_final=68.4)
    # Papelera y alta registrada: no se tocan.
    _fila(motor, id=900, valuation_id=f"v-{PAPELERA}", merge_line_id=7900,
          matched_contrato_line_id=50)
    _fila(motor, id=901, valuation_id=f"v-{REGISTRADO}", merge_line_id=7901,
          matched_contrato_line_id=50)
    return motor


def _foto(motor) -> dict[str, list[tuple]]:
    with motor.connect() as conexion:
        return {
            tabla: [tuple(f) for f in conexion.execute(
                text(f"SELECT * FROM {tabla} ORDER BY 1"))]  # noqa: S608
            for tabla in ("albaran_line_valuations", "contrato_lines_derived",
                          "albaran_documents_merge")
        }


def _fila_leida(motor, vid: int) -> dict[str, Any]:
    with motor.connect() as conexion:
        return dict(conexion.execute(
            text("SELECT * FROM albaran_line_valuations WHERE id = :id"), {"id": vid},
        ).mappings().one())


def _pasada(motor, *, aplicar: bool) -> str:
    from scripts.rellenar_filas_f078 import ejecutar

    with motor.connect() as conexion, conexion.begin():
        return ejecutar(conexion, aplicar=aplicar)


def _cambios(motor):
    from scripts.rellenar_filas_f078 import decidir, leer_filas

    with motor.connect() as conexion:
        return {c.id: dict(c.columnas) for c in decidir(leer_filas(conexion))}


# =================================================================== #
# R21 · por defecto solo lee e informa
# =================================================================== #
def test_f078_r21_por_defecto_no_escribe_nada():
    motor = construir()
    antes = _foto(motor)

    informe = _pasada(motor, aplicar=False)

    assert _foto(motor) == antes
    assert "Solo lectura" in informe


def test_f078_r21_lo_que_cambiaria_fila_a_fila():
    assert _cambios(construir()) == {
        385: {"descripcion_linea": "Mortero M-5", "unidad_albaran": "m3",
              "cantidad_convertida": 3.0},
        386: {"descripcion_linea": "CARGA INCOMPLETA", "unidad_albaran": "M3"},
        379: {"descripcion_linea": "DISCO C/ACERO 230 BOSCH"},
        401: {"descripcion_linea": "HORMIGON HA-25", "cantidad_convertida": 6.0},
        402: {"descripcion_linea": "INCREMENTO — AÑO 2026"},
        403: {"descripcion_linea": "GRAVA 20/40"},
        405: {"descripcion_linea": "HORMIGON HA-25"},
    }


def test_f078_r21_informe_por_columna_line_kind_y_estado_con_ids_y_sin_textos():
    informe = _pasada(construir(), aplicar=False)

    assert "Filas revisadas (documentos activos sin alta bloqueante): 8" in informe
    assert "Filas que cambiarían: 7" in informe
    assert "  descripcion_linea: 7" in informe
    assert "    from_albaran · aprobado: 1" in informe
    assert "    manual · aprobado: 1" in informe
    assert "    from_albaran · pendiente: 4" in informe
    assert "    synthetic_modifier · pendiente: 1" in informe
    assert "    ids: 379, 385, 386, 401, 402, 403, 405" in informe
    assert "  unidad_albaran: 2" in informe and "    ids: 385, 386" in informe
    assert "  cantidad_convertida: 2" in informe and "    ids: 385, 401" in informe
    assert "unidad_contrato:" not in informe and "precio_unitario_final:" not in informe
    for texto in ("Mortero", "CARGA", "DISCO", "HORMIGON", "GRAVA", "INCREMENTO"):
        assert texto not in informe


def test_f078_r21_la_transaccion_es_de_solo_lectura_en_postgresql():
    from scripts.rellenar_filas_f078 import solo_lectura

    class _Dialecto:
        name = "postgresql"

    class _Conexion:
        dialect = _Dialecto()

        def __init__(self):
            self.sentencias = []

        def execute(self, sentencia, *_):
            self.sentencias.append(str(sentencia))

    conexion = _Conexion()
    solo_lectura(conexion)
    assert conexion.sentencias == ["SET TRANSACTION READ ONLY"]


def test_f078_r21_sin_aplicar_pide_solo_lectura_antes_de_leer(monkeypatch):
    import scripts.rellenar_filas_f078 as script

    orden = []
    monkeypatch.setattr(script, "solo_lectura", lambda c: orden.append("solo_lectura"))
    monkeypatch.setattr(script, "leer_filas", lambda c: orden.append("leer") or [])
    monkeypatch.setattr(script, "aplicar_cambios", lambda c, x: orden.append("escribir"))

    script.ejecutar(object(), aplicar=False)

    assert orden == ["solo_lectura", "leer"]


# =================================================================== #
# R22 · --aplicar: solo lo que difiere, una transacción, idempotente
# =================================================================== #
def test_f078_r22_aplicar_escribe_lo_que_difiere_y_relee_cero():
    motor = construir()

    informe = _pasada(motor, aplicar=True)

    assert "Escritas 7 filas. Releído: 0 pendientes." in informe
    assert _cambios(motor) == {}
    f = _fila_leida(motor, 385)
    assert (f["descripcion_linea"], f["unidad_albaran"], f["cantidad_convertida"]) == (
        "Mortero M-5", "m3", 3.0)


def test_f078_r22_segunda_pasada_cero_cambios():
    motor = construir()
    _pasada(motor, aplicar=True)
    despues = _foto(motor)

    informe = _pasada(motor, aplicar=True)

    assert "Filas que cambiarían: 0" in informe and "Escritas 0 filas" in informe
    assert _foto(motor) == despues


def test_f078_r22_no_toca_importes_partidas_producto_bloqueada_ni_derivadas():
    motor = construir()
    antes = _foto(motor)

    _pasada(motor, aplicar=True)

    despues = _foto(motor)
    assert despues["contrato_lines_derived"] == antes["contrato_lines_derived"]
    columnas = [c for c in _fila_leida(motor, 385)]
    intactas = [i for i, c in enumerate(columnas) if c not in (
        "descripcion_linea", "unidad_contrato", "unidad_albaran", "precio_unitario_final",
        "cantidad_convertida")]
    for antes_f, despues_f in zip(antes["albaran_line_valuations"],
                                  despues["albaran_line_valuations"]):
        assert [antes_f[i] for i in intactas] == [despues_f[i] for i in intactas]
    f = _fila_leida(motor, 401)
    assert (f["producto_sigrid"], f["bloqueada"], f["importe_calculado"]) == (
        "MA9999", 1, 410.4)


def test_f078_r22_con_conversion_desconocida_no_toca_cantidades_ni_unidad_del_papel():
    motor = construir()

    _pasada(motor, aplicar=True)

    f = _fila_leida(motor, 405)
    assert (f["unidad_albaran"], f["cantidad_convertida"]) == (None, None)


def test_f078_r22_si_quedan_pendientes_deshace_todo(monkeypatch):
    import scripts.rellenar_filas_f078 as script

    motor = construir()
    antes = _foto(motor)
    monkeypatch.setattr(script, "aplicar_cambios", lambda conexion, cambios: 0)

    with pytest.raises(script.RellenoIncompleto, match="7 filas pendientes"):
        _pasada(motor, aplicar=True)

    assert _foto(motor) == antes


# =================================================================== #
# R23 · papelera y alta bloqueante fuera; aprobados y pendientes dentro
# =================================================================== #
def test_f078_r23_salta_papelera_y_alta_bloqueante():
    motor = construir()

    cambios = _cambios(motor)

    assert 900 not in cambios and 901 not in cambios
    assert 385 in cambios and 379 in cambios       # aprobado (alta no_admitido) y pendiente


@pytest.mark.parametrize("estado", ["en_curso", "incierto", "registrado"])
def test_f078_r23_cada_estado_bloqueante_se_salta(estado):
    motor = construir()
    _ejecutar(motor, "UPDATE albaran_altas_sigrid SET estado = :e WHERE document_id = :d",
              e=estado, d=CASO)

    cambios = _cambios(motor)

    assert 385 not in cambios and 386 not in cambios


@pytest.mark.parametrize("estado", ["no_admitido", "revisar", "simulado", "anulado"])
def test_f078_r23_un_alta_no_bloqueante_no_impide_el_relleno(estado):
    motor = construir()
    _ejecutar(motor, "UPDATE albaran_altas_sigrid SET estado = :e WHERE document_id = :d",
              e=estado, d=CASO)

    assert 385 in _cambios(motor)


def test_f078_r23_sin_tabla_de_altas_tambien_funciona():
    motor = construir(con_altas=False)

    cambios = _cambios(motor)

    assert 901 in cambios and 900 not in cambios


# =================================================================== #
# R24 · ni cadena de conexión ni credenciales en la salida
# =================================================================== #
SECRETO = "postgresql+psycopg://usuario:CLAVE-SECRETA@servidor-interno:5432/albaranes"


def test_f078_r24_un_error_de_conexion_no_imprime_la_cadena(monkeypatch, capsys):
    import scripts.rellenar_filas_f078 as script

    def _motor(env):
        raise RuntimeError(f"no conecta con {SECRETO}")

    monkeypatch.setattr(script, "_motor", _motor)

    assert script.main([]) == 1
    salida = capsys.readouterr()
    assert "CLAVE-SECRETA" not in salida.out + salida.err
    assert "servidor-interno" not in salida.out + salida.err
    assert "RuntimeError" in salida.err


def test_f078_r24_main_lee_el_env_pedido_y_solo_imprime_el_informe(monkeypatch, capsys):
    import scripts.rellenar_filas_f078 as script

    motor = construir()
    pedidos = []
    monkeypatch.setattr(script, "_motor", lambda env: pedidos.append(env) or motor)
    monkeypatch.setattr(motor, "dispose", lambda: None)

    assert script.main(["--env", "otro.env"]) == 0

    assert pedidos == ["otro.env"]
    salida = capsys.readouterr().out
    assert salida.startswith("Filas revisadas")
    assert "sqlite" not in salida.lower()


def test_f078_r24_aplicar_incompleto_sale_con_codigo_2(monkeypatch, capsys):
    import scripts.rellenar_filas_f078 as script

    motor = construir()
    monkeypatch.setattr(script, "_motor", lambda env: motor)
    monkeypatch.setattr(motor, "dispose", lambda: None)
    monkeypatch.setattr(script, "aplicar_cambios", lambda conexion, cambios: 0)

    assert script.main(["--aplicar"]) == 2
    assert "ROLLBACK" in capsys.readouterr().err


def test_f078_r24_el_settings_de_sv6_se_construye_con_el_env_pedido(monkeypatch):
    import config.settings as ajustes
    import scripts.rellenar_filas_f078 as script

    vistos = []

    class _Settings:
        def __init__(self, **kwargs):
            vistos.append(kwargs)
            self.database_url = "sqlite://"

    monkeypatch.setattr(ajustes, "Settings", _Settings)

    script._motor("otro.env").dispose()
    script._motor(None).dispose()

    assert vistos == [{"_env_file": "otro.env"}, {}]


# =================================================================== #
# R25 · lo que pinta la ficha nueva = lo que pintaba la de antes (salvo P1)
# =================================================================== #
def _pintaba_antes(motor, vid: int) -> dict[str, Any]:
    """La ficha de antes de F-078 (``_load_conciliation_map_in_session``): una
    Contrato, la descripción de la fila o la de su línea, la unidad de su línea
    y el precio de la fila o el de su línea; una Nueva, todo de su derivada.
    Q = ``cantidad_convertida ?? cantidad_albaran``."""
    f = _fila_leida(motor, vid)
    with motor.connect() as conexion:
        if f["matched_contrato_line_id"] is not None:
            cl = conexion.execute(text(
                "SELECT * FROM albaran_contrato_lines_merge WHERE id = :i"),
                {"i": f["matched_contrato_line_id"]}).mappings().one()
            desc, uni = f["descripcion_linea"] or cl["descripcion_linea"], cl["unidad_medida"]
            precio = f["precio_unitario_final"]
            precio = precio if precio is not None else cl["precio_unitario"]
        else:
            d = conexion.execute(text("SELECT * FROM contrato_lines_derived WHERE id = :i"),
                                 {"i": f["derived_contrato_line_id"]}).mappings().one()
            desc, uni, precio = d["descripcion_linea"], d["unidad_medida"], d["precio_unitario"]
    q = f["cantidad_convertida"] if f["cantidad_convertida"] is not None else f["cantidad_albaran"]
    return {"concepto": desc, "unidad": uni, "precio": precio, "q": q}


def _pinta_ahora(motor, vid: int) -> dict[str, Any]:
    """La ficha de F-078 (R6): las columnas de la fila."""
    f = _fila_leida(motor, vid)
    q = f["cantidad_convertida"] if f["cantidad_convertida"] is not None else f["cantidad_albaran"]
    return {"concepto": f["descripcion_linea"], "unidad": f["unidad_contrato"],
            "precio": f["precio_unitario_final"], "q": q}


def test_f078_r25_tras_el_relleno_la_ficha_pinta_lo_mismo_salvo_el_concepto_del_papel():
    motor = construir()
    vids = [385, 386, 379, 401, 402, 403, 404, 405]
    antes = {vid: _pintaba_antes(motor, vid) for vid in vids}

    _pasada(motor, aplicar=True)

    ahora = {vid: _pinta_ahora(motor, vid) for vid in vids}
    # P1 = (b): las Nueva con blanca sin descripción propia, el concepto del papel.
    assert (antes[385]["concepto"], ahora[385]["concepto"]) == ("MORTERO M-5", "Mortero M-5")
    assert (antes[379]["concepto"], ahora[379]["concepto"]) == (
        "MATERIAL DE FERRETERIA", "DISCO C/ACERO 230 BOSCH")
    for vid in (385, 379):
        antes[vid]["concepto"] = ahora[vid]["concepto"]
    assert ahora == antes


# =================================================================== #
# T10 · lo que la campaña de mutación pidió fijar
# =================================================================== #
def test_f078_r21_un_cambio_es_inmutable():
    import dataclasses

    from scripts.rellenar_filas_f078 import Cambio

    cambio = Cambio(id=1, line_kind="manual", aprobado=False, columnas={})
    with pytest.raises(dataclasses.FrozenInstanceError):
        cambio.id = 2  # type: ignore[misc]


def test_f078_r21_la_ayuda_dice_que_es_y_como_se_escribe(capsys):
    import scripts.rellenar_filas_f078 as script

    with pytest.raises(SystemExit) as salida:
        script.main(["--help"])

    assert salida.value.code == 0
    ayuda = capsys.readouterr().out
    assert "Relleno de F-078: cada fila valorada guarda lo que la ficha enseña." in ayuda
    assert "--aplicar" in ayuda and "--env" in ayuda


def test_f078_r24_lanzado_como_script_sin_configuracion_sale_con_1_y_sin_datos(tmp_path):
    """``python -m scripts.rellenar_filas_f078`` llega a ``main``: sin ``PG_USER`` ni
    ``PG_PASSWORD`` (un ``.env`` vacío) no conecta, sale con 1 y solo dice el tipo
    de error."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    vacio = tmp_path / "vacio.env"
    vacio.write_text("", encoding="utf-8")
    entorno = {k: v for k, v in os.environ.items() if not k.startswith("PG_")}
    hecho = subprocess.run(
        [sys.executable, "-m", "scripts.rellenar_filas_f078", "--env", str(vacio)],
        cwd=Path(__file__).resolve().parents[1], env=entorno, capture_output=True,
        text=True, timeout=120,
    )

    assert hecho.returncode == 1, hecho.stderr
    assert hecho.stdout == ""
    assert hecho.stderr.startswith("ERROR: ValidationError.")
