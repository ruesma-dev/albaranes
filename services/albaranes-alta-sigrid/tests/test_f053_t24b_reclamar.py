# tests/test_f053_t24b_reclamar.py
"""F-053 · T24b · ``reclamar`` de sv9 en DOS sentencias (decisión del humano,
2026-10-07, tras la review de la fase 1, pasada 3, §7.2).

Como T40 en sv3 y T19 en sv4: primero el cerrojo del merge (``SELECT ... FOR
UPDATE`` de ``albaran_documents_merge``) y, DESPUÉS, la lectura del alta con
instantánea nueva. En READ COMMITTED cada sentencia ve lo confirmado al
EMPEZAR: con UNA sola sentencia ``FOR UPDATE`` + ``LEFT JOIN``, dos
``reclamar`` simultáneos del mismo documento (dos réplicas durante un relevo de
revisión) leerían los dos «sin alta» y los dos decidirían ``procesar``. Con dos
sentencias, el segundo, que esperó el cerrojo, ve el ``en_curso`` del primero
y no vuelve a llamar a sigrid-api (R7). Así no se depende de la réplica única.

La sesión doble simula esa carrera; el control negativo (sentencia única con
``LEFT JOIN``) la pierde: ver ``progress/impl_F-053_fase2.md``.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from domain.models.alta_models import AccionAlta, Decision, EstadoAlta
from infrastructure.database.sql_alta_repository import SqlAltaRepository

AHORA = datetime(2026, 10, 8, 9, 0, tzinfo=UTC)
DESDE = datetime(2026, 10, 1, tzinfo=UTC)
ESPERA = timedelta(minutes=15)

MERGE = {"id": "d1", "is_active": True, "approved": True,
         "approved_at_utc": "2026-10-05T12:00:00+00:00", "approved_by": "ana"}
EN_CURSO_DEL_OTRO = {
    "estado": "en_curso", "modo": "simulacion", "sigrid_con_ide": None, "sigrid_cod": None,
    "adjunto_estado": None, "sigrid_gra_ide": None, "motivos_json": None, "avisos_json": None,
    "peticion_json": None, "respuesta_json": None, "historial_json": "[]", "intentos": 1,
    "ultimo_intento_at_utc": (AHORA - timedelta(seconds=5)).isoformat(),
}


def _normal(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip()


class _Resultado:
    def __init__(self, filas):
        self._filas = filas

    def mappings(self):
        return self

    def first(self):
        return self._filas[0] if self._filas else None


class _Transaccion:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class _SesionInstantanea:
    """PostgreSQL en READ COMMITTED, en miniatura: cada sentencia ve lo
    confirmado al EMPEZAR. La del ``FOR UPDATE`` espera el cerrojo del otro
    ``reclamar``, que mientras tanto confirma su ``en_curso`` y suelta."""

    def __init__(self, alta_confirmada, alta_del_otro):
        self.alta = alta_confirmada
        self.alta_del_otro = alta_del_otro
        self.sentencias: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def begin(self):
        return _Transaccion()

    def execute(self, clausula, parametros=None):
        sql = _normal(str(clausula))
        instantanea = self.alta
        self.sentencias.append(sql)
        if "FOR UPDATE" in sql and "albaran_documents_merge" in sql:
            self.alta = self.alta_del_otro          # el otro confirma y suelta
        if sql.startswith(("INSERT", "UPDATE")):
            return _Resultado([])
        lee_merge = "FROM albaran_documents_merge" in sql
        lee_alta = "albaran_altas_sigrid" in sql
        if lee_merge and lee_alta:                    # sentencia única (control)
            return _Resultado([{**MERGE, **(instantanea or {"estado": None})}])
        if lee_merge:
            return _Resultado([MERGE])
        if lee_alta:
            return _Resultado([instantanea] if instantanea else [])
        return _Resultado([])


class _Fabrica:
    def __init__(self, sesion):
        self.sesion = sesion

    def create_session(self):
        return self.sesion


def _reclamar(sesion):
    return SqlAltaRepository(_Fabrica(sesion)).reclamar(
        "d1", accion=AccionAlta.ALTA, ahora=AHORA, desde=DESDE, espera=ESPERA,
        modo="simulacion",
    )


def test_f053_t24b_el_segundo_reclamar_ve_el_en_curso_del_primero_y_no_procesa():
    sesion = _SesionInstantanea(alta_confirmada=None, alta_del_otro=EN_CURSO_DEL_OTRO)

    reclamacion = _reclamar(sesion)

    assert reclamacion.decision is Decision.IGNORAR
    assert reclamacion.alta.estado is EstadoAlta.EN_CURSO
    assert not any(s.startswith(("INSERT", "UPDATE")) for s in sesion.sentencias)


def test_f053_t24b_dos_sentencias_cerrojo_antes_que_la_lectura_del_alta():
    sesion = _SesionInstantanea(alta_confirmada=None, alta_del_otro=None)

    assert _reclamar(sesion).decision is Decision.PROCESAR

    cerrojo, lectura, upsert = sesion.sentencias
    assert cerrojo.endswith("FOR UPDATE") and "FROM albaran_documents_merge m" in cerrojo
    assert "albaran_altas_sigrid" not in cerrojo and "JOIN" not in cerrojo.upper()
    assert "FROM albaran_altas_sigrid a" in lectura and "FOR UPDATE" not in lectura
    assert "JOIN" not in lectura.upper()
    assert upsert.startswith("INSERT INTO albaran_altas_sigrid")


def test_f053_t24b_sin_documento_no_lee_el_alta():
    class _SinMerge(_SesionInstantanea):
        def execute(self, clausula, parametros=None):
            self.sentencias.append(_normal(str(clausula)))
            return _Resultado([])

    sesion = _SinMerge(None, None)
    assert _reclamar(sesion).decision is Decision.IGNORAR
    assert len(sesion.sentencias) == 1
