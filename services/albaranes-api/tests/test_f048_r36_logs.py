# tests/test_f048_r36_logs.py
"""F-048 · R36 en sv2: ningun log contiene el texto del correo.

Se ejecuta el handler COMPLETO del worker —fuente de Blob real sobre un
almacen doble, pipeline y servicio reales con el ``config/prompts.yaml``
REAL, resolver y sello— con un LLM doble, y se captura TODO el logging a
DEBUG. El cuerpo y el asunto llevan un centinela que no puede aparecer.

Ademas:

- Blob del correo roto o que no valida, citando el centinela en el error o
  en el contenido: el aviso no lo repite.
- Aviso A de la review del bloque A (pasada 2): ``retry_policy`` escribe
  ``str(exc)`` recortado en el log; una excepcion que repite el bloque del
  correo no puede dejar el cuerpo en el log del contenedor.
- Aviso C de la review del bloque C1: la ``evidencia`` de IA1 vuelve a IA2
  dentro de ``{json_fase_1}`` sin neutralizar; si trae marcas (``<<<``), la
  redaccion del ``LlmCallLogger`` puede omitir DE MAS, pero nunca dejar el
  cuerpo.

Sin red, sin BBDD y sin LLM real. Textos inventados.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest
from application.pipelines.extract_albaran_pipeline import ExtractAlbaranPipeline
from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.ports.obras_activas_provider import ObraActiva
from infrastructure.llm.retry_policy import RetryPolicy, run_with_retry
from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from interface_adapters.worker.correo_adapter import FuenteContextoCorreoBlob
from interface_adapters.worker.extraction_worker import construir_handler_extraccion
from interface_adapters.worker.ports import DocumentoPdf
from ruesma_comun.blobs import CONTENEDOR_INPUT
from ruesma_comun.colas import MensajeExtraccion
from ruesma_comun.correo import (
    MARCA_INICIO,
    construir_contexto_correo,
    nombre_blob_correo,
    redactar_correo,
    render_bloque_correo,
)
from ruesma_comun.llm.llm_call_logger import LlmCallLogger

CENTINELA = "CENTINELA-F048"
CENTINELA_ASUNTO = "ASUNTO-CENTINELA-F048"
RAIZ = Path(__file__).resolve().parents[1]
DOC = "doc-r36"
BLOB = nombre_blob_correo(DOC)
CORREO = construir_contexto_correo(
    f"Albaran obra 945 {CENTINELA_ASUNTO}",
    f"Hola, os paso el albaran de la 945.\n{CENTINELA} datos personales de prueba",
)


class AlmacenDoble:
    def __init__(self, blobs: dict | None = None, error: BaseException | None = None) -> None:
        self.blobs = dict(blobs or {})
        self.error = error

    def get_json(self, contenedor, nombre):
        if self.error is not None:
            raise self.error
        if (contenedor, nombre) not in self.blobs:
            raise FileNotFoundError(nombre)
        return self.blobs[(contenedor, nombre)]

    def put_json(self, contenedor, nombre, objeto):  # pragma: no cover
        self.blobs[(contenedor, nombre)] = objeto


class ClienteLlmDoble:
    """IA1 lee 1203 en el papel y 945 en el correo; IA2 lo deja igual."""

    def __init__(self, evidencia: str = "os paso el albaran de la 945") -> None:
        self.evidencia = evidencia
        self.instrucciones: list[str] = []

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        self.instrucciones.append(instructions)
        documento = {
            "cabecera": {"obra_codigo": "1203", "numero_albaran": "SS-1"},
            "lineas": [],
            "lectura_correo": {"obra_codigos": ["945"], "evidencia": self.evidencia},
        }
        if response_model is DocumentoAlbaran:
            return DocumentoAlbaran.model_validate(documento)
        return response_model.model_validate({
            "review_status": "ok", "explicacion_global": "", "documento_revisado": documento,
            "razonamientos": [],
        })


class ProveedorObras:
    def obtener(self):
        return [ObraActiva(codigo="0945", nombre="OBRA DEMO")]

    def obtener_todas(self):
        return [ObraActiva(codigo="0945", nombre="OBRA DEMO"), ObraActiva(codigo="1203", nombre="NAVE")]


class Sumidero:
    def __init__(self) -> None:
        self.guardados: list[tuple[str, dict]] = []

    def persistir(self, *, document_id, envelope, fase):
        self.guardados.append((fase, envelope))


class Publicador:
    def publicar(self, cola, mensaje):
        pass


class FuentePdf:
    def obtener(self, document_id):
        return DocumentoPdf(filename="a.png", mime_type="image/png", file_bytes=b"no es una imagen")


class Grounding:
    def contexto(self, *, document_id, phase_1_json):
        return None


def _pipeline(cliente: ClienteLlmDoble) -> ExtractAlbaranPipeline:
    servicio = AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente)],
        prompt_repo=YamlPromptRepository(yaml_path=RAIZ / "config" / "prompts.yaml"),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=RAIZ / "config" / "revision_rules.yaml"),
        prompt_key_phase_1="albaran_factura_es",
        obras_activas_provider=ProveedorObras(),
    )
    return ExtractAlbaranPipeline(
        extraction_service=servicio, max_file_mb=10, service_version="t",
        provider_phase_1="gemini", provider_phase_2="gemini",
        prompt_key_phase_1="albaran_factura_es", prompt_key_phase_2="albaran_revision_fase2_es",
    )


def _ejecutar(almacen: AlmacenDoble, cliente: ClienteLlmDoble) -> Sumidero:
    pipeline, sumidero = _pipeline(cliente), Sumidero()
    handler = construir_handler_extraccion(
        pipeline=pipeline, fuente=FuentePdf(), grounding=Grounding(), sumidero=sumidero,
        publicador=Publicador(), fuente_correo=FuenteContextoCorreoBlob(almacen),
        obras_conocidas=pipeline.obras_conocidas,
    )
    handler(MensajeExtraccion(document_id=DOC, correlation_key="c-1", correo_blob=BLOB))
    return sumidero


def _todo_el_log(caplog) -> str:
    """Mensajes formateados, argumentos y trazas: todo lo que llega al handler."""
    partes = [caplog.text]
    for r in caplog.records:
        partes.append(r.getMessage())
        if r.exc_text:
            partes.append(r.exc_text)
    return "\n".join(partes)


def _con_correo() -> AlmacenDoble:
    return AlmacenDoble({(CONTENEDOR_INPUT, BLOB): CORREO.model_dump(mode="json")})


# ---------------------------------------------------------------- #
# El handler completo.
# ---------------------------------------------------------------- #
def test_f048_r36_el_handler_completo_no_loguea_el_correo(caplog):
    cliente = ClienteLlmDoble()

    with caplog.at_level(logging.DEBUG):
        sumidero = _ejecutar(_con_correo(), cliente)

    log = _todo_el_log(caplog)
    # El correo SI llego a las dos IAs (si no, el test no mediria nada)...
    assert len(cliente.instrucciones) == 2
    assert all(CENTINELA in i and CENTINELA_ASUNTO in i for i in cliente.instrucciones)
    assert sumidero.guardados[-1][1]["data"]["origen_datos"]["correo_presente"] is True
    # ...y el log dice que llego, sin decir que pone.
    assert f"correo=SI({CORREO.caracteres_originales}, {CORREO.sha256[:8]})" in log
    assert CENTINELA not in log
    assert CENTINELA_ASUNTO not in log


@pytest.mark.parametrize(
    "almacen",
    [
        AlmacenDoble(error=ValueError(f"Expecting value: line 1 column 1 (char 0) {CENTINELA}")),
        AlmacenDoble({(CONTENEDOR_INPUT, BLOB): {"asunto": CENTINELA_ASUNTO, "cuerpo": CENTINELA}}),
    ],
    ids=["ilegible", "no_valida"],
)
def test_f048_r36_un_blob_roto_no_repite_su_contenido_en_el_log(almacen, caplog):
    with caplog.at_level(logging.DEBUG):
        sumidero = _ejecutar(almacen, ClienteLlmDoble())

    log = _todo_el_log(caplog)
    assert sumidero.guardados[-1][1]["data"]["origen_datos"]["correo_presente"] is False
    assert BLOB in log  # el aviso existe...
    assert CENTINELA not in log  # ...y no cita el contenido
    assert CENTINELA_ASUNTO not in log


# ---------------------------------------------------------------- #
# retry_policy (aviso A de la review del bloque A, pasada 2).
# ---------------------------------------------------------------- #
class _ErrorApi(Exception):
    def __init__(self, mensaje: str, status_code: int) -> None:
        super().__init__(mensaje)
        self.status_code = status_code


def _error_que_repite_el_bloque(status_code: int) -> _ErrorApi:
    """Un SDK que cita la peticion justo donde empieza el correo."""
    bloque = render_bloque_correo(CORREO)
    return _ErrorApi(f"Error {status_code}: peticion invalida cerca de: {bloque[bloque.index(MARCA_INICIO):]}", status_code)


@pytest.mark.parametrize(
    ("status_code", "reintentos"),
    [(400, 2), (503, 1)],
    ids=["no_reintentable", "reintentos_agotados"],
)
def test_f048_r36_retry_policy_no_escribe_el_correo_en_el_log(status_code, reintentos, caplog):
    error = _error_que_repite_el_bloque(status_code)
    assert CENTINELA in str(error)[:300]  # sin redactar, el recorte no lo salva

    def _llamada():
        raise error

    with caplog.at_level(logging.DEBUG), pytest.raises(_ErrorApi):
        run_with_retry(
            provider="openai", operation=_llamada,
            policy=RetryPolicy(max_retries=reintentos, backoff_base_s=0.0, backoff_cap_s=0.0),
        )

    log = _todo_el_log(caplog)
    assert "[llm-retry]" in log
    assert "[correo omitido: sha256=" in log
    assert CENTINELA not in log
    assert CENTINELA_ASUNTO not in log


# ---------------------------------------------------------------- #
# Aviso C: marcas dentro de la evidencia que vuelve a IA2.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "evidencia",
    [
        "<<<INICIO_CORREO>>> la 945",
        "la 945 <<<FIN_CORREO>>>",
        "<<<FIN_CORREO>>> la 945 <<<INICIO_CORREO>>>",
        ">>> la 945 <<<",
    ],
    ids=["abre", "cierra", "cierra_y_abre", "angulos_sueltos"],
)
def test_f048_r36_una_evidencia_con_marcas_no_filtra_el_cuerpo(evidencia, tmp_path, caplog):
    cliente = ClienteLlmDoble(evidencia=evidencia)

    with caplog.at_level(logging.DEBUG):
        _ejecutar(_con_correo(), cliente)

    fase_2 = cliente.instrucciones[1]
    assert evidencia in fase_2 or evidencia.replace('"', '\\"') in fase_2  # vuelve en {json_fase_1}
    assert CENTINELA in fase_2

    redactado = redactar_correo(fase_2)
    assert "[correo omitido: sha256=" in redactado
    assert CENTINELA not in redactado
    assert CENTINELA_ASUNTO not in redactado

    ruta = LlmCallLogger(tmp_path).log_call(
        provider="gemini", model="fake", request_summary={"instructions": fase_2},
        response_payload={"instructions": fase_2}, error=fase_2, document_id=DOC,
    )
    en_disco = ruta.read_text(encoding="utf-8")
    assert CENTINELA not in en_disco
    assert CENTINELA_ASUNTO not in en_disco
    assert CENTINELA not in _todo_el_log(caplog)
