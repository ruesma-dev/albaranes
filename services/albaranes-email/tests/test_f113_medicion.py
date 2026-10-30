# tests/test_f113_medicion.py
"""F-113 T6 · el script de medición de adjuntos con MIME genérico (R20, R21).

Solo la parte pura y el flujo con una conexión falsa: ninguna BBDD. La
ejecución real contra Azure es la MANUAL T9 (D-6).
"""
from __future__ import annotations

import re

import pytest

from scripts import medir_f113_octet_stream as medir


# --------------------------------------------------------------------- #
# R20 · la SQL: solo lectura y solo SELECT
# --------------------------------------------------------------------- #
def test_f113_r20_la_primera_sentencia_es_read_only():
    sentencias = medir.sql_medicion()
    assert sentencias[0].strip().upper() == "SET TRANSACTION READ ONLY"


def test_f113_r20_el_resto_son_solo_select():
    for sql in medir.sql_medicion()[1:]:
        assert sql.strip().upper().startswith("SELECT")
        # Una sola sentencia: ningún ';' fuera de los literales.
        assert ";" not in re.sub(r"'[^']*'", "''", sql)
        for prohibida in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "COPY"):
            assert not re.search(rf"\b{prohibida}\b", sql, re.IGNORECASE), prohibida


def test_f113_r20_la_sql_no_lee_campos_sensibles():
    todo = " ".join(medir.sql_medicion()).lower()
    for campo in ("subject", "from_address", "attachment_filename", "last_error"):
        assert campo not in todo


def test_f113_r20_agrupa_por_estado_y_dia_y_filtra_genericos_de_sv1():
    _, resumen, detalle = medir.sql_medicion()
    assert "attachment_content_type" in resumen
    assert "group by" in resumen.lower()
    assert "current_state" in resumen and "started_at_utc" in resumen
    assert "email:%" in resumen and "email:%" in detalle
    assert "'email_received'" in detalle
    assert "document_id" in detalle


def test_f113_r20_los_genericos_son_los_del_modulo_mime():
    from ruesma_comun.mime import es_mime_generico

    assert medir.GENERICOS
    assert all(es_mime_generico(m) for m in medir.GENERICOS)
    assert "application/octet-stream" in medir.GENERICOS


# --------------------------------------------------------------------- #
# R21 · resumen de filas falsas
# --------------------------------------------------------------------- #
FILAS = [
    {"current_state": "email_received", "dia": "2026-10-30", "n": 5},
    {"current_state": "completed", "dia": "2026-10-29", "n": 2},
    {"current_state": "completed", "dia": "2026-10-30", "n": 1},
]
ATASCADOS = [
    {"document_id": "11111111-1111-1111-1111-111111111111", "started_at_utc": "2026-10-30T10:02:29+00:00"},
]


def test_f113_r21_resumen_con_total_por_estado_y_dia():
    texto = medir.resumir(FILAS, ATASCADOS)
    assert "Total: 8" in texto
    assert re.search(r"2026-10-30\s+email_received\s+5", texto)
    assert re.search(r"2026-10-29\s+completed\s+2", texto)
    assert "email_received: 5" in texto and "completed: 3" in texto
    assert "11111111-1111-1111-1111-111111111111" in texto
    assert "Siguen en email_received (más de 1 h): 1" in texto


def test_f113_r21_resumen_vacio():
    texto = medir.resumir([], [])
    assert "Total: 0" in texto
    assert "Siguen en email_received (más de 1 h): 0" in texto


def test_f113_r21_csv_utf8_bom_y_punto_y_coma(tmp_path):
    destino = tmp_path / "medicion.csv"
    medir.escribir_csv(destino, FILAS)
    crudo = destino.read_bytes()
    assert crudo.startswith(b"\xef\xbb\xbf")
    lineas = crudo.decode("utf-8-sig").splitlines()
    assert lineas[0] == "dia;current_state;n"
    assert "2026-10-30;email_received;5" in lineas


# --------------------------------------------------------------------- #
# Flujo con conexión falsa: orden de sentencias, credenciales del entorno
# --------------------------------------------------------------------- #
class _Resultado:
    def __init__(self, filas):
        self._filas = filas

    def mappings(self):
        return self

    def all(self):
        return self._filas


class _Conexion:
    def __init__(self):
        self.sentencias: list[tuple[str, dict | None]] = []

    def execute(self, sql, parametros=None):
        texto = str(sql)
        self.sentencias.append((texto, parametros))
        if "GROUP BY" in texto.upper():
            return _Resultado(FILAS)
        if texto.strip().upper().startswith("SELECT"):
            return _Resultado(ATASCADOS)
        return _Resultado([])


def test_f113_r20_medir_ejecuta_read_only_antes_de_leer():
    conexion = _Conexion()
    resumen, atascados = medir.medir(conexion)
    assert conexion.sentencias[0][0].strip().upper() == "SET TRANSACTION READ ONLY"
    assert len(conexion.sentencias) == 3
    assert conexion.sentencias[1][1] == {"genericos": list(medir.GENERICOS)}
    assert resumen == FILAS and atascados == ATASCADOS


@pytest.mark.parametrize("falta", ["PG_HOST", "PG_DB", "PG_USER", "PG_PASSWORD"])
def test_f113_r20_sin_pg_del_entorno_no_conecta(monkeypatch, capsys, falta):
    for var in ("PG_HOST", "PG_DB", "PG_USER", "PG_PASSWORD"):
        monkeypatch.setenv(var, "valor-de-prueba")
    monkeypatch.delenv(falta)
    monkeypatch.setattr(medir, "_conectar", lambda url: pytest.fail("no debe conectar"))
    assert medir.main([]) == 1
    err = capsys.readouterr().err
    assert falta in err
    assert "valor-de-prueba" not in err


def test_f113_r20_url_desde_el_entorno_sin_imprimir_la_clave(monkeypatch, capsys):
    monkeypatch.setenv("PG_HOST", "servidor.ejemplo.test")
    monkeypatch.setenv("PG_DB", "albaranes")
    monkeypatch.setenv("PG_USER", "lector")
    monkeypatch.setenv("PG_PASSWORD", "clave-de-prueba")
    monkeypatch.delenv("PG_PORT", raising=False)
    urls = []

    from contextlib import contextmanager

    @contextmanager
    def _falsa(url):
        urls.append(url)
        yield _Conexion()

    monkeypatch.setattr(medir, "_conectar", _falsa)
    assert medir.main([]) == 0
    salida = capsys.readouterr()
    assert urls == ["postgresql+psycopg://lector:clave-de-prueba@servidor.ejemplo.test:5432/albaranes"]
    assert "clave-de-prueba" not in salida.out + salida.err
    assert "Total: 8" in salida.out


def test_f113_r20_error_de_conexion_sin_detalle(monkeypatch, capsys):
    for var in ("PG_HOST", "PG_DB", "PG_USER", "PG_PASSWORD"):
        monkeypatch.setenv(var, "valor-de-prueba")

    def _rompe(url):
        raise RuntimeError("connection to valor-de-prueba failed")

    monkeypatch.setattr(medir, "_conectar", _rompe)
    assert medir.main([]) == 1
    err = capsys.readouterr().err
    assert "RuntimeError" in err
    assert "valor-de-prueba" not in err


def test_f113_r21_main_con_csv(monkeypatch, tmp_path):
    for var in ("PG_HOST", "PG_DB", "PG_USER", "PG_PASSWORD"):
        monkeypatch.setenv(var, "valor-de-prueba")
    from contextlib import contextmanager

    @contextmanager
    def _falsa(url):
        yield _Conexion()

    monkeypatch.setattr(medir, "_conectar", _falsa)
    destino = tmp_path / "salida.csv"
    assert medir.main(["--csv", str(destino)]) == 0
    assert destino.read_bytes().startswith(b"\xef\xbb\xbf")


def test_f113_r20_la_ayuda_dice_que_mide(capsys):
    # Mata el superviviente de la campaña (progress/mutacion_F-113.md): la
    # descripción de --help es la primera línea del docstring, no la vacía.
    with pytest.raises(SystemExit):
        medir.main(["--help"])
    assert "Medición de F-113" in capsys.readouterr().out
