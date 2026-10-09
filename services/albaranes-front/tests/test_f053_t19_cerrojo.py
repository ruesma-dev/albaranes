# tests/test_f053_t19_cerrojo.py
"""F-053 · T19 · el repositorio de sv4 comprueba el alta dentro de su
transacción, con el merge bloqueado (R25, R26), y nunca escribe la tabla del
alta (R34).

``_exigir_desbloqueado`` va en DOS sentencias (review fase 1, pasada 3, §7.1,
como H4/T40 en sv3): primero el cerrojo del merge (``FOR UPDATE``) y, después,
la lectura del alta con instantánea nueva. En READ COMMITTED la instantánea se
toma al EMPEZAR cada sentencia: una sola sentencia ``FOR UPDATE`` + ``LEFT
JOIN`` que esperase el cerrojo de sv9 (``reclamar``) no vería el ``en_curso``
que sv9 confirma mientras tanto y dejaría editar mientras sv9 graba. La sesión
doble de abajo simula exactamente eso; el control negativo (una sola
sentencia) la deja pasar.

Después, el repositorio REAL sobre SQLite: con alta bloqueante cada método
de R26 lanza ``AlbaranBloqueadoError`` y no cambia nada; con un alta no
bloqueante, o sin la tabla (DDL de sv3 sin aplicar), funciona como hoy.
También el «paso a aprobado» que usa T18 (R1, R2).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from f053_sv4_bbdd import (
    DOC,
    DOC_AJENO,
    construir,
    foto,
    poner_alta,
    repositorio,
)
from sqlalchemy.dialects import postgresql

from domain.models.alta_sigrid_models import AlbaranBloqueadoError, AltaSigridVista
from domain.models.review_models import MergeDocumentUpdatePayload

BLOQUEANTES = ("en_curso", "incierto", "registrado")
NO_BLOQUEANTES = ("no_admitido", "ya_en_sigrid", "simulado", "revisar", "error", "anulado")


# =================================================================== #
# Dos sentencias: cerrojo y, después, lectura con instantánea nueva
# =================================================================== #
class _Resultado:
    def __init__(self, filas):
        self._filas = filas

    def mappings(self):
        return self

    def first(self):
        return self._filas[0] if self._filas else None

    def all(self):
        return list(self._filas)


class _SesionInstantanea:
    """PostgreSQL en READ COMMITTED, en miniatura.

    Cada sentencia ve lo confirmado AL EMPEZAR. La que pide ``FOR UPDATE``
    espera el cerrojo que tiene sv9; mientras espera, sv9 confirma su alta
    (``pendiente``) y suelta. Lo que esa misma sentencia lea de la tabla del
    alta sale de su instantánea vieja; la sentencia siguiente ya lo ve.
    """

    def __init__(self, confirmada, pendiente):
        self.confirmada = confirmada
        self.pendiente = pendiente
        self.sentencias: list[str] = []

    def execute(self, sentencia, parametros=None):
        sql = str(sentencia.compile(dialect=postgresql.dialect()))
        instantanea = self.confirmada
        self.sentencias.append(re.sub(r"\s+", " ", sql))
        if "FOR UPDATE" in sql:
            self.confirmada = self.pendiente
        if "albaran_altas_sigrid" in sql:
            return _Resultado([instantanea] if instantanea else [])
        return _Resultado([{"id": DOC}])


def _repo_sin_bbdd(monkeypatch):
    from infrastructure.database.review_repository import AlbaranReviewRepository

    repo = AlbaranReviewRepository(None)  # type: ignore[arg-type]
    monkeypatch.setattr(repo, "_existe_tabla_altas", lambda sesion: True)
    return repo


def test_f053_r26_h4_alta_confirmada_mientras_espera_el_cerrojo_bloquea(monkeypatch):
    repo = _repo_sin_bbdd(monkeypatch)
    sesion = _SesionInstantanea(
        confirmada=None, pendiente={"estado": "en_curso", "sigrid_cod": None},
    )

    with pytest.raises(AlbaranBloqueadoError) as error:
        repo._exigir_desbloqueado(sesion, DOC)

    assert error.value.estado == "en_curso"
    assert error.value.aviso == (
        'Registrado en Sigrid: corrígelo en Sigrid y pulsa "Ya lo he anulado en Sigrid"'
    )


def test_f053_r26_dos_sentencias_cerrojo_antes_que_la_lectura(monkeypatch):
    repo = _repo_sin_bbdd(monkeypatch)
    sesion = _SesionInstantanea(confirmada=None, pendiente=None)

    repo._exigir_desbloqueado(sesion, DOC)

    cerrojo, lectura = sesion.sentencias
    assert "FOR UPDATE" in cerrojo and "albaran_documents_merge" in cerrojo
    assert "albaran_altas_sigrid" not in cerrojo
    assert "albaran_altas_sigrid" in lectura
    assert "FOR UPDATE" not in lectura and "JOIN" not in lectura.upper()


def test_f053_r26_sin_tabla_del_alta_no_la_lee(monkeypatch):
    from infrastructure.database.review_repository import AlbaranReviewRepository

    repo = AlbaranReviewRepository(None)  # type: ignore[arg-type]
    monkeypatch.setattr(repo, "_existe_tabla_altas", lambda sesion: False)
    sesion = _SesionInstantanea(confirmada=None, pendiente={"estado": "registrado"})

    repo._exigir_desbloqueado(sesion, DOC)

    assert len(sesion.sentencias) == 1 and "FOR UPDATE" in sesion.sentencias[0]


@pytest.mark.parametrize("estado", NO_BLOQUEANTES)
def test_f053_r26_alta_no_bloqueante_deja_seguir(monkeypatch, estado):
    repo = _repo_sin_bbdd(monkeypatch)
    sesion = _SesionInstantanea(confirmada={"estado": estado, "sigrid_cod": "AC/1"},
                                pendiente={"estado": estado, "sigrid_cod": "AC/1"})
    repo._exigir_desbloqueado(sesion, DOC)


@pytest.mark.parametrize("estado", BLOQUEANTES)
def test_f053_r26_alta_bloqueante_ya_confirmada_bloquea_con_su_cod(monkeypatch, estado):
    repo = _repo_sin_bbdd(monkeypatch)
    fila = {"estado": estado, "sigrid_cod": "AC26/0042"}
    sesion = _SesionInstantanea(confirmada=fila, pendiente=fila)
    with pytest.raises(AlbaranBloqueadoError) as error:
        repo._exigir_desbloqueado(sesion, DOC)
    assert error.value.cod == "AC26/0042"
    assert str(error.value) == (
        'Registrado en Sigrid como AC26/0042: corrígelo en Sigrid y pulsa '
        '"Ya lo he anulado en Sigrid"'
    )


# =================================================================== #
# Repositorio real (SQLite): cada método de R26
# =================================================================== #
def _undo_de_doc(motor):
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    with Session(motor) as s:
        s.execute(text(
            "INSERT INTO undo_log (created_at_utc, action, description, payload, undone, "
            "document_id) VALUES ('t', 'guardar', 'x', :p, 0, :d)"),
            {"p": json.dumps({"restore": [{"table": "albaran_documents_merge",
                                           "values": {"id": DOC, "numero_albaran": "OTRO"}}]}),
             "d": DOC})
        s.commit()


OPERACIONES = {
    "update_document": lambda r: r.update_document_y_transicion(
        document_id=DOC, payload=MergeDocumentUpdatePayload(numero_albaran="CAMBIADO")),
    "desaprobar": lambda r: r.set_approved(document_id=DOC, approved=False, approved_by=None),
    "borrar": lambda r: r.soft_delete_document(document_id=DOC, deleted_by="ana"),
    "purgar": lambda r: r.hard_delete_document(document_id=DOC),
    "deshacer": lambda r: r.undo_last(document_id=DOC),
    "editar_linea": lambda r: r.update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, descripcion="OTRA"),
    "conciliar": lambda r: r.set_line_conciliacion(
        document_id=DOC, valuation_line_id=12, mode="contract_line",
        matched_contrato_line_id=501),
    "borrar_linea": lambda r: r.remove_line_valuation(document_id=DOC, valuation_line_id=12),
    "casar_linea_blanca": lambda r: r.add_conciliacion_for_merge_line(
        document_id=DOC, merge_line_id=703, mode="nueva"),
    "linea_suelta": lambda r: r.add_standalone_valuation_line(document_id=DOC),
    "lineas_de_contrato": lambda r: r.add_valuation_lines_from_contrato(
        document_id=DOC, contrato_line_ids=[501]),
    "almacen": lambda r: r.asignar_almacen(document_id=DOC, valuation_line_ids=[12]),
    "almacen_todas": lambda r: r.asignar_almacen(document_id=DOC, valuation_line_ids=None),
}


@pytest.mark.parametrize("estado", BLOQUEANTES)
@pytest.mark.parametrize("operacion", sorted(OPERACIONES))
def test_f053_r26_con_alta_bloqueante_se_rechaza_sin_cambiar_nada(operacion, estado):
    motor = construir(aprobado=True)
    _undo_de_doc(motor)
    poner_alta(motor, estado, cod="AC26/7")
    repo = repositorio(motor)
    antes = foto(motor)

    with pytest.raises(AlbaranBloqueadoError) as error:
        OPERACIONES[operacion](repo)

    assert error.value.document_id == DOC and error.value.cod == "AC26/7"
    assert foto(motor) == antes


#: Las que el SQLite de los tests sabe ejecutar enteras (el resto usa SQL de
#: PostgreSQL: ``to_regclass``, ``ANY``, ``FOR UPDATE`` en texto...).
QUE_FUNCIONAN_EN_SQLITE = (
    "desaprobar", "borrar", "editar_linea", "borrar_linea", "linea_suelta",
    "almacen", "almacen_todas",
)


@pytest.mark.parametrize("estado", NO_BLOQUEANTES)
@pytest.mark.parametrize("operacion", QUE_FUNCIONAN_EN_SQLITE)
def test_f053_r26_con_alta_no_bloqueante_se_hace(operacion, estado):
    motor = construir(aprobado=True)
    _undo_de_doc(motor)
    poner_alta(motor, estado)
    antes = foto(motor)

    OPERACIONES[operacion](repositorio(motor))

    assert foto(motor) != antes


@pytest.mark.parametrize("operacion", QUE_FUNCIONAN_EN_SQLITE)
def test_f053_r26_sin_tabla_del_alta_se_hace_como_hoy(operacion):
    motor = construir(con_altas=False, aprobado=True)
    _undo_de_doc(motor)
    antes = foto(motor)

    OPERACIONES[operacion](repositorio(motor))

    assert foto(motor) != antes


def test_f053_r26_el_alta_de_otro_documento_no_bloquea():
    motor = construir(aprobado=True)
    poner_alta(motor, "registrado", document_id=DOC_AJENO)
    repo = repositorio(motor)
    assert repo.update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, descripcion="OTRA") is True


def test_f053_r26_todos_los_metodos_que_escriben_llaman_al_cerrojo():
    """Guardián estructural: cada método de R26 llama a ``_exigir_desbloqueado``
    (``guardar_producto_sigrid`` lo comprueba su propio test, T19b)."""
    import inspect

    from infrastructure.database.review_repository import AlbaranReviewRepository

    for metodo in (
        "update_document_y_transicion", "soft_delete_document", "hard_delete_document",
        "undo_last", "update_line_conciliacion", "set_line_conciliacion",
        "remove_line_valuation", "add_conciliacion_for_merge_line",
        "add_standalone_valuation_line", "add_valuation_lines_from_contrato",
        "asignar_almacen", "set_approved",
    ):
        fuente = inspect.getsource(getattr(AlbaranReviewRepository, metodo))
        assert "self._exigir_desbloqueado(session, document_id)" in fuente, metodo


# =================================================================== #
# R1, R2 · el repositorio dice si el documento PASÓ a aprobado
# =================================================================== #
def test_f053_r2_repositorio_aprobar_dice_si_paso_a_aprobado():
    motor = construir(aprobado=False)
    repo = repositorio(motor)
    assert repo.set_approved(document_id=DOC, approved=True, approved_by="ana") is True
    assert repo.set_approved(document_id=DOC, approved=True, approved_by="ana") is False
    assert repo.set_approved(document_id=DOC, approved=False, approved_by=None) is False


def test_f053_r2_repositorio_aprobar_con_alta_bloqueante_no_lo_rechaza():
    """Aprobar uno ya aprobado no está en R25 (no lo desaprueba ni lo edita)."""
    motor = construir(aprobado=True)
    poner_alta(motor, "registrado")
    assert repositorio(motor).set_approved(
        document_id=DOC, approved=True, approved_by="ana") is False


@pytest.mark.parametrize("antes, aprueba, paso", [
    (False, True, True), (True, True, False), (False, False, False), (True, False, False),
])
def test_f053_r2_repositorio_guardar_dice_si_paso_a_aprobado(monkeypatch, antes, aprueba, paso):
    motor = construir(aprobado=antes)
    repo = repositorio(motor)
    monkeypatch.setattr(repo, "get_document_detail", lambda document_id: "detalle")

    detalle, paso_a_aprobado = repo.update_document_y_transicion(
        document_id=DOC, payload=MergeDocumentUpdatePayload(approved=aprueba, approved_by="ana"),
    )

    assert detalle == "detalle" and paso_a_aprobado is paso


# =================================================================== #
# Lectura del alta y R34
# =================================================================== #
def test_f053_r34_leer_alta_sin_tabla_es_ninguna():
    assert repositorio(construir(con_altas=False)).leer_alta_sigrid(DOC) is None


def test_f053_r34_leer_alta_traduce_la_fila():
    motor = construir(aprobado=True)
    poner_alta(
        motor, "simulado", cod="AC26/9", modo="simulacion", sigrid_con_ide=9, intentos=2,
        motivos_json=json.dumps([{"codigo": "importe_distinto", "detalle": "x",
                                  "referencia_linea": "12"}]),
        avisos_json=json.dumps([{"codigo": "stock_negativo"}]),
        peticion_json=json.dumps({"lineas": [{"referencia_linea": "12", "producto": "QA9999"}]}),
        respuesta_json=json.dumps({"totales": {"totbas": 20.0, "totdoc": 24.2},
                                   "lineas": [{"referencia_linea": "12", "total": 20.0}]}),
        ultimo_intento_at_utc="2026-10-08T09:05:00+00:00",
    )

    alta = repositorio(motor).leer_alta_sigrid(DOC)

    assert isinstance(alta, AltaSigridVista)
    assert (alta.estado, alta.sigrid_cod, alta.sigrid_con_ide, alta.intentos) == (
        "simulado", "AC26/9", 9, 2)
    assert alta.bloqueante is False and alta.simulacion is True
    assert alta.total_previa == 20.0 and alta.total_documento == 24.2
    assert alta.lineas[0]["producto"] == "QA9999" and alta.lineas[0]["total"] == 20.0
    assert alta.lineas[0]["motivos"][0]["codigo"] == "importe_distinto"
    assert alta.avisos == [{"codigo": "stock_negativo"}]


def test_f053_r34_leer_alta_con_json_roto_no_rompe_la_ficha():
    motor = construir(aprobado=True)
    poner_alta(motor, "error", motivos_json="{roto", peticion_json="[]", respuesta_json="7")
    alta = repositorio(motor).leer_alta_sigrid(DOC)
    assert alta.estado == "error" and alta.motivos == [] and alta.lineas == []


def test_f053_r34_sv4_nunca_escribe_la_tabla_del_alta():
    raiz = Path(__file__).resolve().parents[1]
    escritura = re.compile(
        r"(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+albaran_altas_sigrid", re.IGNORECASE,
    )
    culpables = [
        str(f.relative_to(raiz)) for f in raiz.rglob("*.py")
        if "tests" not in f.parts and ".venv" not in f.parts
        and escritura.search(f.read_text(encoding="utf-8"))
    ]
    assert culpables == []
