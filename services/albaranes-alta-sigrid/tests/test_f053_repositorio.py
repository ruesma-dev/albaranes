# tests/test_f053_repositorio.py
"""F-053 · T14 · ``SqlAltaRepository``: SQL generado y traducción de filas.

Sesión simulada (sin BBDD): registra cada sentencia con sus parámetros y
devuelve filas programadas. La prueba contra PostgreSQL de verdad es la MANUAL
T26 del humano.

- Reclamación en UNA transacción con ``FOR UPDATE OF m`` sobre el merge, y su
  efecto: UPSERT a ``en_curso`` con ``intentos + 1`` (R5) o ``incierto`` (R8).
- Lectura de datos con ``tipologia``, ``tipologia_mixta``,
  ``contexto_linea_json``, ``line_index`` y ``producto_sigrid``.
- Guardado con ``historial_json`` (``{ts, estado, cod, motivos}``).
- R34: sv9 solo escribe en ``albaran_altas_sigrid``.
"""
from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta

import pytest

from domain.models.alta_models import (
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    CabeceraAlta,
    Decision,
    EstadoAlta,
    LineaAlta,
    Motivo,
    ResultadoAlta,
)
from infrastructure.database import sql_alta_repository as modulo
from infrastructure.database.sql_alta_repository import SqlAltaRepository

AHORA = datetime(2026, 10, 6, 9, 0, tzinfo=UTC)
DESDE = datetime(2026, 10, 1, tzinfo=UTC)
ESPERA = timedelta(minutes=15)


class _Resultado:
    def __init__(self, filas, rowcount=1):
        self._filas = filas
        self.rowcount = rowcount

    def mappings(self):
        return self

    def first(self):
        return self._filas[0] if self._filas else None

    def all(self):
        return list(self._filas)


class _Transaccion:
    def __init__(self, sesion):
        self._sesion = sesion

    def __enter__(self):
        self._sesion.transacciones += 1
        return self

    def __exit__(self, tipo, *_):
        if tipo is None:
            self._sesion.confirmadas += 1
        return False


class SesionFalsa:
    """Responde según un trozo de la SQL; registra todo lo ejecutado."""

    def __init__(self, respuestas: dict[str, list[dict]], rowcount: int = 1):
        self.respuestas = respuestas
        self.rowcount = rowcount
        self.ejecutadas: list[tuple[str, dict]] = []
        self.transacciones = 0
        self.confirmadas = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def begin(self):
        return _Transaccion(self)

    def execute(self, clausula, parametros=None):
        sql = str(clausula)
        self.ejecutadas.append((sql, dict(parametros or {})))
        for trozo, filas in self.respuestas.items():
            if trozo in sql:
                return _Resultado(filas, self.rowcount)
        return _Resultado([], self.rowcount)

    def sql(self, trozo: str) -> list[tuple[str, dict]]:
        return [(s, p) for s, p in self.ejecutadas if trozo in s]


class FabricaFalsa:
    def __init__(self, sesion):
        self.sesion = sesion

    def create_session(self):
        return self.sesion


def _normal(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip()


def _fila_merge(**cambios) -> dict:
    fila = {
        "id": "d1", "is_active": True, "approved": True,
        "approved_at_utc": "2026-10-05T12:00:00.123456+00:00", "approved_by": "ana",
        "estado": None, "modo": None, "sigrid_con_ide": None, "sigrid_cod": None,
        "adjunto_estado": None, "sigrid_gra_ide": None, "motivos_json": None,
        "avisos_json": None, "peticion_json": None, "respuesta_json": None,
        "historial_json": None, "intentos": None, "ultimo_intento_at_utc": None,
    }
    fila.update(cambios)
    return fila


_CAMPOS_MERGE = ("id", "is_active", "approved", "approved_at_utc", "approved_by")


def _repo(respuestas, rowcount=1):
    # T24b: ``reclamar`` lee el merge y, en otra sentencia, el alta. Las filas
    # «merge + alta» de los tests se reparten entre las dos lecturas.
    merges = respuestas.get("FROM albaran_documents_merge m")
    if merges and "FROM albaran_altas_sigrid a" not in respuestas:
        respuestas = {
            **respuestas,
            "FROM albaran_altas_sigrid a": [
                {k: v for k, v in f.items() if k not in _CAMPOS_MERGE}
                for f in merges if f.get("estado") is not None
            ],
        }
    sesion = SesionFalsa(respuestas, rowcount)
    return SqlAltaRepository(FabricaFalsa(sesion)), sesion


def _reclamar(repo, accion=AccionAlta.ALTA):
    return repo.reclamar("d1", accion=accion, ahora=AHORA, desde=DESDE, espera=ESPERA,
                         modo="simulacion")


# ------------------------------------------------------------------ #
# reclamar
# ------------------------------------------------------------------ #
def test_f053_repositorio_reclamar_bloquea_el_merge_en_una_transaccion():
    repo, sesion = _repo({"FROM albaran_documents_merge m": [_fila_merge()]})
    _reclamar(repo)
    sql, params = sesion.ejecutadas[0]
    texto = _normal(sql)
    # T24b: el cerrojo, solo; el alta se lee en la sentencia siguiente.
    assert "FROM albaran_documents_merge m WHERE m.id = :document_id" in texto
    assert texto.endswith("FOR UPDATE") and "albaran_altas_sigrid" not in texto
    assert params == {"document_id": "d1"}
    alta, params_alta = sesion.ejecutadas[1]
    assert "FROM albaran_altas_sigrid a" in _normal(alta) and params_alta == {"document_id": "d1"}
    assert sesion.transacciones == 1 and sesion.confirmadas == 1


def test_f053_repositorio_reclamar_sin_alta_hace_upsert_a_en_curso():
    repo, sesion = _repo({"FROM albaran_documents_merge m": [_fila_merge()]})
    reclamacion = _reclamar(repo)
    assert reclamacion.decision is Decision.PROCESAR and reclamacion.alta is None
    ((sql, params),) = sesion.sql("INSERT INTO albaran_altas_sigrid")
    texto = _normal(sql)
    assert "ON CONFLICT (document_id) DO UPDATE SET" in texto
    assert "estado = 'en_curso'" in texto
    assert "intentos = albaran_altas_sigrid.intentos + 1" in texto
    assert params["document_id"] == "d1" and params["modo"] == "simulacion"
    assert params["ahora"] == AHORA.isoformat()
    assert params["approved_at_utc"] == "2026-10-05T12:00:00.123456+00:00"
    assert params["approved_by"] == "ana"
    historial = json.loads(params["historial_json"])
    assert historial == [{"ts": AHORA.isoformat(), "estado": "en_curso", "cod": None, "motivos": []}]


def test_f053_repositorio_reclamar_traduce_el_alta_existente():
    fila = _fila_merge(
        estado="error", modo="real", sigrid_con_ide=5, sigrid_cod="AC26/5", adjunto_estado="error",
        sigrid_gra_ide=8, motivos_json=json.dumps([{"codigo": "x", "detalle": "d",
                                                     "referencia_linea": "1"}]),
        avisos_json='[{"codigo": "cod_provisional"}]', peticion_json='{"a": 1}',
        respuesta_json='{"estado": "previsto"}', intentos=2,
        historial_json='[{"ts": "t", "estado": "error", "cod": null, "motivos": ["x"]}]',
        ultimo_intento_at_utc="2026-10-06T08:00:00+00:00",
    )
    repo, sesion = _repo({"FROM albaran_documents_merge m": [fila]})
    alta = _reclamar(repo).alta
    assert alta == AltaActual(
        estado=EstadoAlta.ERROR, modo="real", sigrid_con_ide=5, sigrid_cod="AC26/5",
        adjunto_estado=AdjuntoEstado.ERROR, sigrid_gra_ide=8, motivos=(Motivo("x", "d", "1"),),
        avisos=({"codigo": "cod_provisional"},), peticion={"a": 1},
        respuesta={"estado": "previsto"}, intentos=2,
        ultimo_intento_at_utc=datetime(2026, 10, 6, 8, 0, tzinfo=UTC),
    )
    historial = json.loads(sesion.sql("INSERT INTO albaran_altas_sigrid")[0][1]["historial_json"])
    assert [h["estado"] for h in historial] == ["error", "en_curso"]


@pytest.mark.parametrize("fila", [
    None, _fila_merge(approved=False), _fila_merge(is_active=False),
    _fila_merge(approved_at_utc="2026-09-01T00:00:00+00:00"), _fila_merge(approved_at_utc="basura"),
])
def test_f053_repositorio_reclamar_ignorar_no_escribe(fila):
    repo, sesion = _repo({"FROM albaran_documents_merge m": [] if fila is None else [fila]})
    assert _reclamar(repo).decision is Decision.IGNORAR
    # el SELECT ... FOR UPDATE y, si hay documento, la lectura del alta (T24b)
    assert len(sesion.ejecutadas) == (1 if fila is None else 2)
    assert sesion.sql("INSERT INTO") == [] and sesion.sql("UPDATE ") == []


def test_f053_repositorio_reclamar_a_incierto():
    fila = _fila_merge(estado="en_curso", intentos=1,
                       ultimo_intento_at_utc=(AHORA - timedelta(hours=1)).isoformat())
    repo, sesion = _repo({"FROM albaran_documents_merge m": [fila]})
    assert _reclamar(repo).decision is Decision.A_INCIERTO
    ((sql, params),) = sesion.sql("UPDATE albaran_altas_sigrid")
    assert "estado = 'incierto'" in _normal(sql)
    assert params["document_id"] == "d1"
    assert json.loads(params["historial_json"])[-1]["estado"] == "incierto"
    assert sesion.sql("INSERT INTO") == []


def test_f053_repositorio_fecha_sin_zona_se_lee_como_utc():
    fila = _fila_merge(approved_at_utc="2026-10-05T12:00:00")
    repo, _ = _repo({"FROM albaran_documents_merge m": [fila]})
    assert _reclamar(repo).decision is Decision.PROCESAR


# ------------------------------------------------------------------ #
# leer_datos
# ------------------------------------------------------------------ #
CABECERA = {
    "id": "d1", "obra_codigo": "0404", "proveedor_cif": "B1", "numero_albaran": "N-1",
    "fecha": "2026-10-03", "tipologia": "residuos", "tipologia_mixta": True,
    "sharepoint_relative_path": "albaranes/x.pdf", "valoracion_status": "ok",
    "contrato_codigo": "CT/1",
}
LINEA = {
    "id": 77, "merge_line_id": 9, "line_index": 2, "cantidad_albaran": 6.0,
    "cantidad_convertida": 6.5, "unidad_albaran": "M3", "importe_calculado": 410.4,
    "matched_contrato_line_id": 50, "derived_contrato_line_id": None, "ctrpro_ide": 700101,
    "contrato_linea": "CT/1", "codigo_partida_final": "03.02", "descripcion_linea": "HA-25",
    "descripcion_merge": "HORMIGON", "producto_sigrid": "XA9999",
    "contexto_linea_json": json.dumps({"tipo_familia": "alquiler_maquinaria", "rol_linea": "base"}),
}


def test_f053_repositorio_leer_datos_traduce_cabecera_y_lineas():
    manual = {**LINEA, "id": 78, "merge_line_id": None, "line_index": None,
              "descripcion_merge": None, "contexto_linea_json": None, "producto_sigrid": None}
    roto = {**LINEA, "id": 79, "contexto_linea_json": "{no es json"}
    repo, _ = _repo({"FROM albaran_documents_merge m": [CABECERA],
                     "JOIN albaran_line_valuations lv": [LINEA, manual, roto]})
    datos = repo.leer_datos("d1")
    assert datos.cabecera == CabeceraAlta(
        document_id="d1", obra_codigo="0404", proveedor_cif="B1", numero_albaran="N-1",
        fecha="2026-10-03", valoracion_status="ok", contrato_codigo="CT/1",
        tipologia="residuos", tipologia_mixta=True, sharepoint_relative_path="albaranes/x.pdf",
    )
    assert datos.lineas[0] == LineaAlta(
        id=77, merge_line_id=9, line_index=2, cantidad_albaran=6.0, cantidad_convertida=6.5,
        unidad_albaran="M3", importe_calculado=410.4, matched_contrato_line_id=50,
        derived_contrato_line_id=None, ctrpro_ide=700101, contrato_linea="CT/1",
        codigo_partida_final="03.02", descripcion_linea="HA-25", descripcion_merge="HORMIGON",
        tipo_familia="alquiler_maquinaria", producto_sigrid="XA9999",
    )
    assert datos.lineas[1].tipo_familia is None and datos.lineas[1].line_index is None
    assert datos.lineas[2].tipo_familia is None


def test_f053_repositorio_leer_datos_sql():
    repo, sesion = _repo({"FROM albaran_documents_merge m": [CABECERA],
                          "JOIN albaran_line_valuations lv": []})
    repo.leer_datos("d1")
    cabecera, lineas = (_normal(s) for s, _ in sesion.ejecutadas)
    for columna in ("m.obra_codigo", "m.proveedor_cif", "m.numero_albaran", "m.fecha",
                    "m.tipologia", "m.tipologia_mixta", "m.sharepoint_relative_path",
                    "v.status AS valoracion_status", "v.contrato_codigo"):
        assert columna in cabecera
    for columna in ("lv.producto_sigrid", "lv.importe_calculado", "lv.cantidad_convertida",
                    "lv.matched_contrato_line_id", "lv.derived_contrato_line_id",
                    "lv.codigo_partida_final", "lv.descripcion_linea", "l.line_index",
                    "l.concepto AS descripcion_merge", "l.contexto_linea_json",
                    "cl.sigrid_ide AS ctrpro_ide", "cl.codigo_contrato AS contrato_linea"):
        assert columna in lineas
    assert "WHERE v.document_id = :document_id" in lineas
    assert all(p == {"document_id": "d1"} for _, p in sesion.ejecutadas)


def test_f053_repositorio_leer_datos_de_documento_que_no_existe():
    repo, _ = _repo({})
    with pytest.raises(LookupError):
        repo.leer_datos("d1")


# ------------------------------------------------------------------ #
# guardar y leer_alta
# ------------------------------------------------------------------ #
def test_f053_repositorio_guardar_escribe_todo_y_apunta_el_historial():
    previo = '[{"ts": "t0", "estado": "en_curso", "cod": null, "motivos": []}]'
    repo, sesion = _repo({"SELECT historial_json": [{"historial_json": previo}]})
    resultado = ResultadoAlta(
        estado=EstadoAlta.REGISTRADO, modo="real", sigrid_con_ide=9, sigrid_cod="AC26/9",
        adjunto_estado=AdjuntoEstado.COLGADO, sigrid_gra_ide=4,
        motivos=(Motivo("registrado_distinto", "d", "1"),),
        avisos=({"codigo": "stock_negativo", "referencia_linea": "1"},),
        peticion={"cod_obra": "0404"}, respuesta={"estado": "creado"},
    )
    repo.guardar("d1", resultado, ahora=AHORA)
    bloqueo, = sesion.sql("SELECT historial_json")
    assert _normal(bloqueo[0]).endswith("FOR UPDATE")
    ((sql, params),) = sesion.sql("UPDATE albaran_altas_sigrid")
    assert "WHERE document_id = :document_id" in _normal(sql)
    assert params["estado"] == "registrado" and params["modo"] == "real"
    assert params["sigrid_con_ide"] == 9 and params["sigrid_cod"] == "AC26/9"
    assert params["adjunto_estado"] == "colgado" and params["sigrid_gra_ide"] == 4
    assert json.loads(params["motivos_json"]) == [
        {"codigo": "registrado_distinto", "detalle": "d", "referencia_linea": "1"}]
    assert json.loads(params["avisos_json"]) == [{"codigo": "stock_negativo", "referencia_linea": "1"}]
    assert json.loads(params["peticion_json"]) == {"cod_obra": "0404"}
    assert json.loads(params["respuesta_json"]) == {"estado": "creado"}
    assert params["actualizado_at_utc"] == AHORA.isoformat()
    historial = json.loads(params["historial_json"])
    assert historial[-1] == {"ts": AHORA.isoformat(), "estado": "registrado", "cod": "AC26/9",
                             "motivos": ["registrado_distinto"]}
    assert len(historial) == 2
    assert sesion.confirmadas == 1


def test_f053_repositorio_guardar_nulos_como_null():
    repo, sesion = _repo({"SELECT historial_json": [{"historial_json": None}]})
    repo.guardar("d1", ResultadoAlta(estado=EstadoAlta.NO_ADMITIDO, modo="simulacion"), ahora=AHORA)
    params = sesion.sql("UPDATE albaran_altas_sigrid")[0][1]
    assert params["peticion_json"] is None and params["respuesta_json"] is None
    assert params["adjunto_estado"] is None and json.loads(params["motivos_json"]) == []


def test_f053_repositorio_guardar_sin_fila_falla():
    repo, _ = _repo({"SELECT historial_json": []}, rowcount=0)
    with pytest.raises(LookupError):
        repo.guardar("d1", ResultadoAlta(estado=EstadoAlta.ERROR), ahora=AHORA)


def test_f053_repositorio_leer_alta():
    fila = {k: v for k, v in _fila_merge(estado="simulado", sigrid_cod="AC26/1").items()
            if k not in ("id", "is_active", "approved", "approved_at_utc", "approved_by")}
    repo, _ = _repo({"FROM albaran_altas_sigrid": [fila]})
    alta = repo.leer_alta("d1")
    assert alta.estado is EstadoAlta.SIMULADO and alta.sigrid_cod == "AC26/1"
    vacio, _ = _repo({})
    assert vacio.leer_alta("d1") is None


# ------------------------------------------------------------------ #
# R34 · solo escribe su tabla
# ------------------------------------------------------------------ #
def test_f053_r34_solo_escribe_albaran_altas_sigrid():
    sentencias = [v for k, v in vars(modulo).items() if k.startswith("SQL_") and isinstance(v, str)]
    assert sentencias
    escrituras = re.compile(r"(?<!FOR )(?<!DO )\b(INSERT INTO|UPDATE|DELETE FROM)\s+(\w+)")
    escritas = set()
    for sql in sentencias:
        texto = _normal(sql).upper()
        escritas |= {tabla for _, tabla in escrituras.findall(texto)}
        assert "DROP " not in texto and "ALTER " not in texto and "TRUNCATE" not in texto
    assert escritas == {"ALBARAN_ALTAS_SIGRID"}


def test_f053_r47_repositorio_reclamar_devuelve_el_approved_by_del_merge():
    """v8: el ``usu`` sale del ``approved_by`` leído bajo el cerrojo (R5, R47)."""
    repo, _ = _repo({"FROM albaran_documents_merge m": [
        {**_fila_merge(), "approved_by": "ana@ruesma.es"}]})
    assert _reclamar(repo).approved_by == "ana@ruesma.es"
