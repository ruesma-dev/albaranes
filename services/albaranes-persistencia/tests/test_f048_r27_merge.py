# tests/test_f048_r27_merge.py
"""F-048 · R27: el merge conserva ``origen_datos`` y acaba en el
``raw_extraction_json`` de ``albaran_documents_merge``.

``AlbaranConfidenceService.build_merge_analysis`` REHACE ``data`` campo a
campo: lo que no se pasa a mano se pierde. Es el defecto que F-043 cazo con
``clasificacion`` (las seis columnas a NULL). Aqui se comprueba el recorrido
entero: envelope de sv2 → merge → fila ORM del merge, con el
``save`` REAL del repositorio sobre una sesion doble (sin BBDD).

Sin DDL: el bloque va dentro del JSON que el merge ya guarda (design §5).

Sin red, sin BBDD y sin LLM. Textos inventados.
"""
from __future__ import annotations

import copy
import json

import pytest
from application.services.albaran_confidence_service import AlbaranConfidenceService
from domain.models.extraction_models import ExtractionEnvelope
from domain.models.persistence_models import StoredFile
from infrastructure.database.orm_models import (
    AlbaranDocumentMergeOrm,
    AlbaranDocumentOrm,
)
from infrastructure.database.sqlalchemy_albaran_repository import (
    SqlAlchemyAlbaranRepository,
)

ORIGEN = {
    "version": 1,
    "correo_presente": True,
    "correo_sha256": "b" * 64,
    "correo_truncado": True,
    "evidencia": "Albaran de la obra 945",
    "obra": {
        "fuente": "papel",
        "motivo": "correo_ambiguo",
        "valor_final": "0937",
        "valor_correo": None,
        "candidatos_correo": ["0945", "0320"],
        "valor_papel": "0937",
        "discrepancia": False,
        "validada": True,
    },
}
_META = {
    "prompt_key": "albaran_revision_fase2_es",
    "schema": "albaran_v2",
    "source_filename": "SS-2.pdf",
    "source_mime_type": "application/pdf",
    "source_sha256": "c" * 64,
    "model": "modelo-de-prueba",
    "processed_at_utc": "2026-09-24T10:00:00Z",
}
_DATA = {
    "cabecera": {"proveedor_nombre": "HORMIGONES DEL SUR", "numero_albaran": "SS-2", "obra_codigo": "0937"},
    "lineas": [{"concepto": "HA-25/B/20/IIa", "cantidad": 7.5, "precio_neto": 600.0}],
}


def _envelope(*, origen: dict | None = ORIGEN, con_gemini: bool = False) -> ExtractionEnvelope:
    data = copy.deepcopy(_DATA)
    if origen is not None:
        data["origen_datos"] = copy.deepcopy(origen)
    crudo: dict = {"meta": dict(_META), "data": data}
    if con_gemini:
        # Los sub-envelopes son la extraccion CRUDA de cada IA: no llevan
        # el sello, que solo existe en el envelope final.
        crudo["gemini"] = {"meta": dict(_META), "data": copy.deepcopy(_DATA)}
    return ExtractionEnvelope.model_validate(crudo)


# ---------------------------------------------------------------- #
# El merge.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("con_gemini", [False, True], ids=["solo_openai", "con_gemini"])
def test_f048_r27_el_merge_conserva_origen_datos(con_gemini):
    envelope = _envelope(con_gemini=con_gemini)

    analisis = AlbaranConfidenceService().build_merge_analysis(
        openai=envelope, gemini=envelope.gemini,
    )

    origen = analisis.merged_envelope.data.origen_datos
    assert origen is not None
    assert origen.model_dump(mode="json") == ORIGEN


def test_f048_r27_sin_origen_datos_el_merge_sigue_como_hoy():
    analisis = AlbaranConfidenceService().build_merge_analysis(openai=_envelope(origen=None), gemini=None)

    assert analisis.merged_envelope.data.origen_datos is None


# ---------------------------------------------------------------- #
# Hasta la fila: `save` real con una sesion doble.
# ---------------------------------------------------------------- #
class _Resultado:
    def all(self):
        return []


class _Sesion:
    """Sesion doble: sin nada previo que borrar; registra lo que se anade."""

    def __init__(self) -> None:
        self.anadidos: list = []
        self.confirmada = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def scalars(self, consulta):
        return _Resultado()

    def execute(self, sentencia):  # pragma: no cover - no hay merges previos que borrar
        return None

    def delete(self, objeto):  # pragma: no cover
        pass

    def flush(self):
        pass

    def add(self, objeto):
        self.anadidos.append(objeto)

    def commit(self):
        self.confirmada = True

    def rollback(self):  # pragma: no cover
        pass


class _FabricaSesiones:
    generation = 1

    def __init__(self) -> None:
        self.sesion = _Sesion()

    def ensure_database_and_engine(self):
        pass

    def create_session(self):
        return self.sesion


def _stored_file() -> StoredFile:
    return StoredFile(drive_id="d", item_id="i", relative_path="albaranes/SS-2.pdf", web_url=None, share_url=None)


def _guardar(envelope: ExtractionEnvelope) -> list:
    fabrica = _FabricaSesiones()
    repositorio = SqlAlchemyAlbaranRepository(session_factory=fabrica)
    repositorio._initialized_generation = fabrica.generation  # sin crear tablas: no hay BBDD

    repositorio.save(envelope=envelope, context={}, stored_file=_stored_file())

    assert fabrica.sesion.confirmada
    return fabrica.sesion.anadidos


def _merge(anadidos: list) -> AlbaranDocumentMergeOrm:
    (merge,) = [d for d in anadidos if isinstance(d, AlbaranDocumentMergeOrm)]
    return merge


def test_f048_r27_origen_datos_acaba_en_el_raw_extraction_json_del_merge():
    anadidos = _guardar(_envelope())

    guardado = json.loads(_merge(anadidos).raw_extraction_json)
    assert guardado["data"]["origen_datos"] == ORIGEN


def test_f048_r27_la_obra_de_la_fila_es_la_de_la_cabecera_no_la_del_bloque():
    """El bloque es informacion: la columna ``obra_codigo`` sale de la cabecera,
    que ya viene resuelta de sv2. sv3 no decide la obra con el bloque."""
    merge = _merge(_guardar(_envelope()))

    assert merge.obra_codigo == "0937"


def test_f048_r27_la_fila_cruda_de_la_ia_tambien_lo_guarda_sin_tocarlo():
    """La fila por proveedor (``albaran_documents``) es el envelope tal cual."""
    anadidos = _guardar(_envelope())
    (crudo,) = [d for d in anadidos if type(d) is AlbaranDocumentOrm]

    assert json.loads(crudo.raw_extraction_json)["data"]["origen_datos"] == ORIGEN


def test_f048_r27_un_envelope_viejo_guarda_el_merge_sin_bloque():
    guardado = json.loads(_merge(_guardar(_envelope(origen=None))).raw_extraction_json)

    assert guardado["data"].get("origen_datos") is None
