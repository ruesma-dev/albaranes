# tests/test_f048_r26_modelo.py
"""F-048 · R26: sv3 acepta ``data.origen_datos`` opcional.

sv2 sella ``origen_datos`` en TODOS los envelopes (tambien sin correo), y
``DocumentoAlbaran`` de sv3 es ``extra='forbid'``: sin declararlo, el
envelope no valida, el handler lanza y el mensaje acaba en poison. Por eso
el orden de despliegue es sv3 → sv2 → sv1 (design §8).

- Envelope viejo (sin el bloque) y nuevo (con el bloque) validan.
- El tipo es el MISMO contrato de ``comun``, no una copia (R31).
- Un envelope con ``origen_datos`` recorre el handler del worker entero
  (saneado de ``meta`` + pipeline) sin lanzar: no va a poison.

Sin red, sin BBDD y sin LLM. Textos inventados.
"""
from __future__ import annotations

import copy
import hashlib

import pytest
from application.pipelines.persist_albaran_pipeline import PersistAlbaranPipeline
from application.services.albaran_normalizer import AlbaranNormalizer
from domain.models.extraction_models import DocumentoAlbaran, ExtractionEnvelope
from domain.models.persistence_models import ExistingDocument, StoredFile
from interface_adapters.worker.persistence_worker import (
    _sanear_envelope,
    construir_handler_persistencia,
)
from interface_adapters.worker.ports import DocumentoPdf
from pydantic import ValidationError
from ruesma_comun.colas import MensajePersistencia
from ruesma_comun.contratos import OrigenDatos

PDF = b"%PDF-1.4 albaran de prueba F-048"
SHA = hashlib.sha256(PDF).hexdigest()

# La forma exacta que deja sv2 (progress/impl_F-048.md, «Para el bloque D»).
ORIGEN = {
    "version": 1,
    "correo_presente": True,
    "correo_sha256": "a" * 64,
    "correo_truncado": False,
    "evidencia": "Os paso el albaran de la 945",
    "obra": {
        "fuente": "correo",
        "motivo": "correo_unico",
        "valor_final": "0945",
        "valor_correo": "0945",
        "candidatos_correo": ["0945"],
        "valor_papel": "0937",
        "discrepancia": True,
        "validada": True,
    },
}
SIN_CORREO = {
    "version": 1, "correo_presente": False, "correo_sha256": None, "correo_truncado": False,
    "evidencia": None,
    "obra": {"fuente": "papel", "motivo": "sin_correo", "valor_final": "0937", "valor_correo": None,
             "candidatos_correo": [], "valor_papel": "0937", "discrepancia": False, "validada": None},
}
_META = {
    "prompt_key": "albaran_revision_fase2_es",
    "schema": "albaran_v2",
    "source_filename": "SS-1.pdf",
    "source_mime_type": "application/pdf",
    "source_sha256": SHA,
    "model": "modelo-de-prueba",
    "processed_at_utc": "2026-09-24T10:00:00Z",
}


def _envelope_de_sv2(origen: dict | None = ORIGEN) -> dict:
    """El envelope FINAL de sv2: ``meta`` con claves que sv3 no declara."""
    data: dict = {
        "cabecera": {"proveedor_nombre": "HORMIGONES DEL SUR", "numero_albaran": "SS-1", "obra_codigo": "0945"},
        "lineas": [{"concepto": "HA-25/B/20/IIa", "cantidad": 7.5}],
    }
    if origen is not None:
        data["origen_datos"] = copy.deepcopy(origen)
    meta = {**_META, "phase": "phase_2", "merged": True, "provider": "openai"}
    return {"meta": meta, "data": data, "debug": {"phase_1": {}, "phase_2": {}}}


# ---------------------------------------------------------------- #
# El modelo.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("origen", [ORIGEN, SIN_CORREO], ids=["con_correo", "sin_correo"])
def test_f048_r26_el_documento_acepta_origen_datos(origen):
    documento = DocumentoAlbaran.model_validate(_envelope_de_sv2(origen)["data"])

    assert isinstance(documento.origen_datos, OrigenDatos)
    assert documento.origen_datos.model_dump(mode="json") == origen


def test_f048_r26_un_envelope_viejo_sin_el_bloque_sigue_validando():
    envelope = ExtractionEnvelope.model_validate(_sanear_envelope(_envelope_de_sv2(None)))

    assert envelope.data.origen_datos is None


def test_f048_r26_usa_el_contrato_de_comun_no_una_copia():
    anotacion = DocumentoAlbaran.model_fields["origen_datos"].annotation

    assert OrigenDatos in getattr(anotacion, "__args__", (anotacion,))


def test_f048_r26_un_campo_futuro_dentro_del_bloque_no_rompe():
    """F-049 anadira ``origen_datos.partida``: con ``extra='ignore'`` de comun,
    un sv3 de hoy la ignora en vez de mandar el documento a poison."""
    futuro = {**ORIGEN, "version": 2, "partida": {"fuente": "correo"}}

    documento = DocumentoAlbaran.model_validate({**_envelope_de_sv2()["data"], "origen_datos": futuro})

    assert documento.origen_datos.obra.valor_final == "0945"


def test_f048_r26_el_documento_sigue_rechazando_campos_no_declarados():
    """Declarar ``origen_datos`` no abre la puerta a cualquier cosa."""
    with pytest.raises(ValidationError):
        DocumentoAlbaran.model_validate({**_envelope_de_sv2()["data"], "lectura_correo": {"obra_codigos": []}})


# ---------------------------------------------------------------- #
# El handler del worker: con el bloque, NO va a poison.
# ---------------------------------------------------------------- #
class _Repositorio:
    """Doble del repositorio: documento nuevo; ``save`` guarda lo que recibe."""

    def __init__(self) -> None:
        self.guardados: list[ExtractionEnvelope] = []

    def get_by_sha256(self, sha256):
        return None

    def save(self, *, envelope, context, stored_file):
        self.guardados.append(envelope)
        return ExistingDocument(document_id="merge-1", source_sha256=SHA, sharepoint_url=None, stored_lines=1)

    def get_selected_contrato_codigo(self, *, document_id):
        return None


class _Almacen:
    def upload(self, **kwargs):
        return StoredFile(drive_id="d", item_id="i", relative_path="albaranes/SS-1.pdf", web_url=None, share_url=None)


class _FuentePdf:
    def obtener(self, document_id):
        return DocumentoPdf(filename="SS-1.pdf", mime_type="application/pdf", file_bytes=PDF)


class _FuenteEnvelope:
    def __init__(self, envelope: dict) -> None:
        self.envelope = envelope

    def obtener(self, document_id):
        return self.envelope


@pytest.mark.parametrize("origen", [ORIGEN, SIN_CORREO, None], ids=["con_correo", "sin_correo", "envelope_viejo"])
def test_f048_r26_el_handler_persiste_un_envelope_con_origen_datos_sin_ir_a_poison(origen):
    repositorio = _Repositorio()
    pipeline = PersistAlbaranPipeline(
        repository=repositorio, document_storage=_Almacen(), normalizer=AlbaranNormalizer(),
    )
    handler = construir_handler_persistencia(
        pipeline=pipeline, fuente_documento=_FuentePdf(), fuente_envelope=_FuenteEnvelope(_envelope_de_sv2(origen)),
    )

    handler(MensajePersistencia(document_id="doc-1", correlation_key="c-1"))

    (guardado,) = repositorio.guardados
    if origen is None:
        assert guardado.data.origen_datos is None
    else:
        assert guardado.data.origen_datos.model_dump(mode="json") == origen
