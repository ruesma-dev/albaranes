# tests/test_f053_r45_reingreso_con_alta.py
"""F-053 · R45 (decisión D1 del humano, 2026-10-06): reingresar un PDF cuyo
merge tiene un alta en Sigrid bloqueante NO lo borra.

``save`` borraba todos los documentos con el mismo ``source_sha256``
(``_delete_existing_records``) y el FK ``ON DELETE CASCADE`` se llevaba la fila
del alta, también ``registrado``. Ahora, si el alta es bloqueante
(``en_curso``, ``incierto`` o ``registrado``; ``ruesma_comun.alta_sigrid``),
sv3 lo trata como duplicado: conserva documento, merge y alta, no lo
reprocesa (ni enriquece ni revalora) y lo deja en el log. Con un alta en otro
estado, o sin alta, todo sigue como hoy.

``save`` REAL del repositorio sobre una sesión doble (sin BBDD) y el pipeline
con dobles. Sin red ni BBDD.
"""
from __future__ import annotations

import hashlib
import logging

import pytest

from application.pipelines.persist_albaran_pipeline import (
    PersistAlbaranPipeline,
    PersistAlbaranRequest,
)
from domain.models.extraction_models import ExtractionEnvelope
from domain.models.persistence_models import ExistingDocument, StoredFile
from infrastructure.database.orm_models import (
    AlbaranDocumentMergeOrm,
    AlbaranDocumentOrm,
)
from infrastructure.database.sqlalchemy_albaran_repository import (
    SqlAlchemyAlbaranRepository,
)

_PDF = b"%PDF-1.4 albaran reingresado"
_SHA = hashlib.sha256(_PDF).hexdigest()
_MERGE_ID = "6f1d2c3b-0000-4000-8000-00000000f053"


def _envelope_dict() -> dict:
    return {
        "meta": {
            "prompt_key": "albaran_revision_fase2", "schema": "albaran_v2",
            "source_filename": "ALB.pdf", "source_mime_type": "application/pdf",
            "source_sha256": _SHA, "model": "gpt-5.2",
            "processed_at_utc": "2026-10-06T08:00:00+00:00",
        },
        "data": {
            "cabecera": {"proveedor_nombre": "PROVEEDOR", "proveedor_cif": "B00000000",
                         "numero_albaran": "A-1", "fecha": "2026-10-01"},
            "lineas": [{"codigo": "X", "concepto": "Material", "cantidad": 1.0,
                        "confianza_pct": 90.0}],
        },
        "debug": {},
    }


# ------------------------------------------------------------------ #
# Sesión doble: el merge previo, su alta y lo que se borra o se añade.
# ------------------------------------------------------------------ #
class _Filas:
    def __init__(self, filas) -> None:
        self._filas = list(filas)

    def all(self):
        return list(self._filas)

    def mappings(self):
        return self

    def __iter__(self):
        return iter(self._filas)

    def scalar(self):
        return self._filas[0] if self._filas else None


class _Sesion:
    def __init__(self, *, estado_alta: str | None, hay_tabla_altas: bool = True) -> None:
        self.estado_alta = estado_alta
        self.hay_tabla_altas = hay_tabla_altas
        self.merge_previo = AlbaranDocumentMergeOrm(
            id=_MERGE_ID, source_sha256=_SHA, sharepoint_share_url="https://sp/albaran.pdf",
        )
        self.raw_previo = AlbaranDocumentOrm(id="raw-1", source_sha256=_SHA)
        self.sql: list[str] = []
        self.borrados: list = []
        self.anadidos: list = []
        self.confirmada = False
        self.deshecha = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sentencia, parametros=None):
        texto = str(sentencia)
        self.sql.append(texto)
        if "to_regclass" in texto:
            return _Filas([self.hay_tabla_altas])
        if "albaran_altas_sigrid" in texto:
            assert parametros == {"sha": _SHA}
            return _Filas([{"document_id": _MERGE_ID, "estado": self.estado_alta,
                            "sigrid_cod": "AC26/0001"}])
        return _Filas([])  # el DELETE de contratos

    def scalars(self, consulta):
        entidad = consulta.column_descriptions[0]["entity"]
        if entidad is AlbaranDocumentMergeOrm:
            return _Filas([self.merge_previo])
        if entidad is AlbaranDocumentOrm:
            return _Filas([self.raw_previo])
        return _Filas([])

    def scalar(self, consulta):  # nº de líneas del conservado
        return 4

    def get(self, entidad, clave):
        assert entidad is AlbaranDocumentMergeOrm and clave == _MERGE_ID
        return self.merge_previo

    def delete(self, objeto):
        self.borrados.append(objeto)

    def flush(self):
        pass

    def add(self, objeto):
        self.anadidos.append(objeto)

    def commit(self):
        self.confirmada = True

    def rollback(self):
        self.deshecha = True


class _Fabrica:
    generation = 1

    def __init__(self, sesion: _Sesion) -> None:
        self.sesion = sesion

    def ensure_database_and_engine(self):
        pass

    def create_session(self):
        return self.sesion


def _guardar(sesion: _Sesion) -> ExistingDocument:
    repositorio = SqlAlchemyAlbaranRepository(session_factory=_Fabrica(sesion))
    repositorio._initialized_generation = _Fabrica.generation  # sin crear tablas
    return repositorio.save(
        envelope=ExtractionEnvelope.model_validate(_envelope_dict()), context={},
        stored_file=StoredFile(drive_id="d", item_id="i", relative_path="albaranes/A-1.pdf",
                               web_url=None, share_url="https://sp/nuevo.pdf"),
    )


@pytest.mark.parametrize("estado", ["en_curso", "incierto", "registrado"])
def test_f053_r45_reingreso_con_alta_bloqueante_no_borra_y_conserva(estado, caplog):
    caplog.set_level(logging.WARNING)
    sesion = _Sesion(estado_alta=estado)
    guardado = _guardar(sesion)
    # Nada borrado (ni merge, ni crudo, ni contratos), nada nuevo, nada confirmado.
    assert sesion.borrados == [] and sesion.anadidos == []
    assert not sesion.confirmada and sesion.deshecha
    assert not any(s.lstrip().upper().startswith("DELETE") for s in sesion.sql)
    # Devuelve el documento conservado, marcado para que el pipeline no lo toque.
    assert guardado == ExistingDocument(
        document_id=_MERGE_ID, source_sha256=_SHA, sharepoint_url="https://sp/albaran.pdf",
        stored_lines=4, conservado_por_alta=True,
    )
    # El merge queda bloqueado mientras se mira el alta (carrera con sv9).
    (consulta,) = [s for s in sesion.sql if "albaran_altas_sigrid" in s and "to_regclass" not in s]
    assert "FOR UPDATE" in consulta
    # Log claro: documento, estado y código de Sigrid.
    assert _MERGE_ID in caplog.text and estado in caplog.text and "AC26/0001" in caplog.text


@pytest.mark.parametrize("estado", [
    None, "no_admitido", "ya_en_sigrid", "simulado", "revisar", "error", "anulado",
])
def test_f053_r45_sin_alta_o_no_bloqueante_se_borra_y_se_guarda_como_hoy(estado):
    sesion = _Sesion(estado_alta=estado)
    guardado = _guardar(sesion)
    assert sesion.merge_previo in sesion.borrados and sesion.raw_previo in sesion.borrados
    assert sesion.confirmada and not sesion.deshecha
    assert any(isinstance(d, AlbaranDocumentMergeOrm) for d in sesion.anadidos)
    assert guardado.document_id != _MERGE_ID and guardado.conservado_por_alta is False


def test_f053_r45_sin_tabla_de_altas_se_borra_como_hoy():
    """Si el DDL de la fase 2 no se aplicó, la consulta del alta no se lanza
    (abortaría la transacción) y ``save`` sigue como hoy."""
    sesion = _Sesion(estado_alta="registrado", hay_tabla_altas=False)
    guardado = _guardar(sesion)
    assert not any("albaran_altas_sigrid" in s and "to_regclass" not in s for s in sesion.sql)
    assert sesion.merge_previo in sesion.borrados and sesion.confirmada
    assert guardado.conservado_por_alta is False


# ------------------------------------------------------------------ #
# Pipeline: el conservado no se reprocesa.
# ------------------------------------------------------------------ #
class _RepoConservado:
    """``get_by_sha256`` no lo ve (p. ej. está en la papelera) y ``save`` lo
    conserva por su alta. Cualquier otro método del repositorio es un fallo."""

    def __init__(self) -> None:
        self.guardados = 0

    def get_by_sha256(self, source_sha256: str):
        return None

    def save(self, **_kwargs) -> ExistingDocument:
        self.guardados += 1
        return ExistingDocument(document_id=_MERGE_ID, source_sha256=_SHA,
                                sharepoint_url="https://sp/albaran.pdf", stored_lines=4,
                                conservado_por_alta=True)

    def __getattr__(self, nombre):
        raise AssertionError(f"el documento conservado no se toca: {nombre}")


class _Almacen:
    def upload(self, **_kwargs) -> StoredFile:
        return StoredFile(drive_id="d", item_id="i", relative_path="albaranes/A-1.pdf",
                          web_url=None, share_url=None)


class _Normalizador:
    def normalize_provider_document(self, *, document, provider_origin):
        return document


class _Valoracion:
    def trigger_async(self, **_kwargs):
        raise AssertionError("el documento conservado no se revalora")

    def trigger_sync(self, **_kwargs):  # pragma: no cover
        raise AssertionError("el documento conservado no se revalora")


def test_f053_r45_el_pipeline_no_reprocesa_el_documento_conservado(caplog):
    caplog.set_level(logging.INFO)
    repo = _RepoConservado()
    pipeline = PersistAlbaranPipeline(
        repository=repo, document_storage=_Almacen(), normalizer=_Normalizador(),
        valuation_trigger=_Valoracion(),
    )
    resultado = pipeline.run(PersistAlbaranRequest(
        filename="ALB.pdf", mime_type="application/pdf", file_bytes=_PDF,
        extraction_envelope=_envelope_dict(), context={},
    ))
    assert repo.guardados == 1
    assert resultado.ok and resultado.duplicate is True
    assert resultado.document_id == _MERGE_ID and resultado.stored_lines == 4
    assert _MERGE_ID in caplog.text
