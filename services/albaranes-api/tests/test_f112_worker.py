# tests/test_f112_worker.py
"""F-112 · R12–R14: la fecha de recepción viaja del worker a las dos fases.

- ``ExtractAlbaranRequest`` y ``ReviewAlbaranRequest`` ganan
  ``fecha_recepcion`` (``None`` por defecto) y el pipeline la pasa tal cual.
- El worker la calcula UNA vez con ``fecha_recepcion_de`` desde el correo y
  da la MISMA a la fase 1 y a la fase 2.
- Sin correo (sin ``correo_blob``, blob ausente o ilegible) va ``None`` a las
  dos y el documento sigue como hoy: sin fallo y publicado.

Sin red, sin BBDD y sin LLM: pipeline, servicio, puertos y almacén son dobles.
"""
from __future__ import annotations

from dataclasses import fields
from datetime import date

import pytest
from application.pipelines.extract_albaran_pipeline import (
    ExtractAlbaranPipeline,
    ExtractAlbaranRequest,
    ReviewAlbaranRequest,
)
from application.services.albaran_extraction_service import ProviderExtractionResult
from domain.models.albaran_models import DocumentoAlbaran
from interface_adapters.worker import extraction_worker
from interface_adapters.worker.correo_adapter import FuenteContextoCorreoBlob
from interface_adapters.worker.extraction_worker import construir_handler_extraccion
from interface_adapters.worker.ports import DocumentoPdf
from ruesma_comun.colas import COLA_PERSISTENCIA, MensajeExtraccion
from ruesma_comun.correo import construir_contexto_correo, nombre_blob_correo

DOC = "doc-f112"
BLOB = nombre_blob_correo(DOC)
# Nochevieja: 23:30 UTC del 31-12 es ya 01-01 en Madrid (D2 = b).
CORREO = construir_contexto_correo("Albarán", "Cuerpo", recibido_utc="2026-12-31T23:30:00Z")
FECHA = date(2027, 1, 1)
PDF = b"%PDF-1.4 f112"


# ---------------------------------------------------------------- #
# R12 · requests y pipeline.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("clase", [ExtractAlbaranRequest, ReviewAlbaranRequest])
def test_f112_r12_las_requests_tienen_fecha_recepcion_opcional(clase):
    campo = {f.name: f for f in fields(clase)}["fecha_recepcion"]
    assert campo.default is None


class ServicioEspia:
    """Doble de ``AlbaranExtractionService``: guarda los kwargs de cada fase."""

    def __init__(self) -> None:
        self.kwargs1: dict | None = None
        self.kwargs2: dict | None = None

    def has_prompt(self, prompt_key: str) -> bool:
        return True

    def _resultado(self, prompt_key: str) -> ProviderExtractionResult:
        return ProviderExtractionResult(
            provider="fake", model_name="fake", schema_name="documento_albaran",
            prompt_key=prompt_key, parsed=DocumentoAlbaran(cabecera={}, lineas=[]),
            debug_payload={},
        )

    def extract_phase_1(self, **kwargs):
        self.kwargs1 = kwargs
        return self._resultado(kwargs["prompt_key"])

    def review_phase_2(self, **kwargs):
        self.kwargs2 = kwargs
        return self._resultado(kwargs["prompt_key"])


def _pipeline(servicio: ServicioEspia) -> ExtractAlbaranPipeline:
    return ExtractAlbaranPipeline(
        extraction_service=servicio, max_file_mb=5, service_version="t",
        provider_phase_1="fake", provider_phase_2="fake",
        prompt_key_phase_1="f1", prompt_key_phase_2="f2",
    )


@pytest.mark.parametrize("fecha", [FECHA, None], ids=["con_fecha", "sin_fecha"])
def test_f112_r12_el_pipeline_pasa_la_fecha_tal_cual(fecha, monkeypatch):
    monkeypatch.setenv("PREPROCESO_IMAGEN", "false")
    servicio = ServicioEspia()
    pipeline = _pipeline(servicio)

    pipeline.run_phase_1(ExtractAlbaranRequest(
        filename="a.pdf", mime_type="application/pdf", file_bytes=PDF, fecha_recepcion=fecha,
    ))
    pipeline.run_phase_2(ReviewAlbaranRequest(
        filename="a.pdf", mime_type="application/pdf", file_bytes=PDF,
        phase_1_json={}, fecha_recepcion=fecha,
    ))

    assert servicio.kwargs1["fecha_recepcion"] is fecha
    assert servicio.kwargs2["fecha_recepcion"] is fecha


# ---------------------------------------------------------------- #
# R13, R14 · el worker.
# ---------------------------------------------------------------- #
class PipelineDoble:
    def __init__(self) -> None:
        self.peticion1: ExtractAlbaranRequest | None = None
        self.peticion2: ReviewAlbaranRequest | None = None

    def run_phase_1(self, request):
        self.peticion1 = request
        return {"meta": {"phase": "phase_1"}, "data": {"cabecera": {}, "lineas": []}, "debug": {}}

    def run_phase_2(self, request):
        self.peticion2 = request
        return {
            "meta": {"phase": "phase_2"},
            "data": {"review_status": "ok", "documento_revisado": {"cabecera": {}, "lineas": []},
                     "razonamientos": []},
            "debug": {},
        }


class FuenteDoble:
    def obtener(self, document_id):
        return DocumentoPdf(filename="a.pdf", mime_type="application/pdf", file_bytes=PDF)


class GroundingDoble:
    def contexto(self, *, document_id, phase_1_json):
        return None


class SumideroDoble:
    def persistir(self, *, document_id, envelope, fase) -> None:
        pass


class PublicadorDoble:
    def __init__(self) -> None:
        self.publicados: list = []

    def publicar(self, cola, mensaje) -> None:
        self.publicados.append((cola, mensaje))


class FuenteCorreoDoble:
    def __init__(self, correo) -> None:
        self.correo = correo

    def obtener(self, nombre_blob: str):
        return self.correo


class AlmacenVacio:
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error

    def get_json(self, contenedor, nombre):
        raise self.error or FileNotFoundError(nombre)


def _ejecutar(*, correo_blob=BLOB, fuente_correo=None):
    pipeline, publicador = PipelineDoble(), PublicadorDoble()
    handler = construir_handler_extraccion(
        pipeline=pipeline, fuente=FuenteDoble(), grounding=GroundingDoble(),
        sumidero=SumideroDoble(), publicador=publicador, fuente_correo=fuente_correo,
    )
    handler(MensajeExtraccion(document_id=DOC, correlation_key="c-1", correo_blob=correo_blob))
    return pipeline, publicador


def test_f112_r13_la_misma_fecha_a_las_dos_fases():
    pipeline, publicador = _ejecutar(fuente_correo=FuenteCorreoDoble(CORREO))

    assert pipeline.peticion1.fecha_recepcion == FECHA
    assert pipeline.peticion2.fecha_recepcion is pipeline.peticion1.fecha_recepcion
    assert [cola for cola, _ in publicador.publicados] == [COLA_PERSISTENCIA]


def test_f112_r13_se_calcula_una_sola_vez(monkeypatch):
    llamadas: list = []

    def espia(correo):
        llamadas.append(correo)
        return FECHA

    monkeypatch.setattr(extraction_worker, "fecha_recepcion_de", espia)

    pipeline, _ = _ejecutar(fuente_correo=FuenteCorreoDoble(CORREO))

    assert llamadas == [CORREO]
    assert pipeline.peticion1.fecha_recepcion is FECHA
    assert pipeline.peticion2.fecha_recepcion is FECHA


def test_f112_r13_un_correo_sin_recibido_va_sin_fecha():
    sin_hora = construir_contexto_correo("Albarán", "Cuerpo")
    pipeline, _ = _ejecutar(fuente_correo=FuenteCorreoDoble(sin_hora))

    assert pipeline.peticion1.contexto_correo is sin_hora
    assert pipeline.peticion1.fecha_recepcion is None
    assert pipeline.peticion2.fecha_recepcion is None


@pytest.mark.parametrize(
    ("correo_blob", "fuente_correo"),
    [
        (None, FuenteCorreoDoble(CORREO)),
        (BLOB, None),
        (BLOB, FuenteContextoCorreoBlob(AlmacenVacio())),
        (BLOB, FuenteContextoCorreoBlob(AlmacenVacio(ValueError("json roto")))),
    ],
    ids=["sin_correo_blob", "sin_fuente", "blob_ausente", "blob_ilegible"],
)
def test_f112_r14_sin_correo_none_a_las_dos_y_sigue(correo_blob, fuente_correo):
    pipeline, publicador = _ejecutar(correo_blob=correo_blob, fuente_correo=fuente_correo)

    assert pipeline.peticion1.fecha_recepcion is None
    assert pipeline.peticion2.fecha_recepcion is None
    assert [cola for cola, _ in publicador.publicados] == [COLA_PERSISTENCIA]
