# tests/test_f048_r24_lectura_tolerante.py
"""F-048 · R24 y R17 (CR-C3 de la review del bloque C2): ``LecturaCorreo``
recorta y tolera en el ORIGEN.

- **R24 en el origen**: la ``evidencia`` se recorta a 160 caracteres al
  validar la respuesta de IA1, no solo al sellar ``origen_datos``. Asi no
  llega entera a ``env1``, a ``debug.phase_1_json`` (que viaja dentro del
  envelope final hasta sv3), a los blobs de fase ni a la BBDD. Sin
  ``max_length``: una evidencia larga no puede tumbar la extraccion.
- **Un bloque mal formado no tumba la fase 1**: un codigo que la IA
  devuelve como numero (``[945]``) pasa a ``"945"``; un valor suelto que no
  es lista se envuelve si es texto o numero y se descarta si no; los
  elementos que no son ni texto ni numero se descartan.

El schema que ve el LLM NO cambia: sigue pidiendo una lista de textos y un
texto o null. La tolerancia es solo de lectura.

Sin red, sin BBDD y sin LLM real. Textos inventados.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from application.pipelines.extract_albaran_pipeline import ExtractAlbaranPipeline
from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.models.lectura_correo import LecturaCorreo
from domain.ports.obras_activas_provider import ObraActiva
from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from interface_adapters.worker.correo_adapter import FuenteContextoCorreoBlob
from interface_adapters.worker.extraction_worker import construir_handler_extraccion
from interface_adapters.worker.ports import DocumentoPdf
from ruesma_comun.blobs import CONTENEDOR_INPUT
from ruesma_comun.colas import MensajeExtraccion
from ruesma_comun.correo import construir_contexto_correo, nombre_blob_correo

RAIZ = Path(__file__).resolve().parents[1]
DOC = "doc-r24"
BLOB = nombre_blob_correo(DOC)
CORREO = construir_contexto_correo("Albaran obra 945", "Hola, os paso el albaran de la 945. CENTINELA-F048")
# 1.000 caracteres, con un principio reconocible para comprobar el recorte.
EVIDENCIA_LARGA = "Para la obra 945: " + "x" * 982
assert len(EVIDENCIA_LARGA) == 1000


# ---------------------------------------------------------------- #
# El modelo: evidencia.
# ---------------------------------------------------------------- #
def test_f048_r24_la_evidencia_larga_se_recorta_a_160_al_validar():
    lectura = LecturaCorreo.model_validate({"obra_codigos": ["945"], "evidencia": EVIDENCIA_LARGA})

    assert lectura.evidencia == EVIDENCIA_LARGA[:160]
    assert len(lectura.evidencia) == 160


@pytest.mark.parametrize("evidencia", [None, "", "Para la obra 945", "y" * 160])
def test_f048_r24_la_evidencia_corta_o_nula_no_cambia(evidencia):
    assert LecturaCorreo.model_validate({"evidencia": evidencia}).evidencia == evidencia


@pytest.mark.parametrize(
    ("evidencia", "esperada"),
    [(945, "945"), (9.5, "9.5"), ({"texto": "obra 945"}, None), (["obra 945"], None), (True, None)],
)
def test_f048_r17_una_evidencia_que_no_es_texto_no_tumba_la_lectura(evidencia, esperada):
    assert LecturaCorreo.model_validate({"evidencia": evidencia}).evidencia == esperada


# ---------------------------------------------------------------- #
# El modelo: obra_codigos.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("codigos", "esperados"),
    [
        ([945], ["945"]),
        ([945.0], ["945"]),
        ([9.45], ["9.45"]),
        (["0945", 1203], ["0945", "1203"]),
        (["0945", None, {"obra": "1"}, ["1203"], True, False, "1203"], ["0945", "1203"]),
        ([], []),
    ],
)
def test_f048_r17_obra_codigos_tolera_numeros_y_descarta_lo_demas(codigos, esperados):
    assert LecturaCorreo.model_validate({"obra_codigos": codigos}).obra_codigos == esperados


@pytest.mark.parametrize(
    ("valor", "esperados"),
    [("945", ["945"]), (945, ["945"]), (None, []), ({"obra": "945"}, []), (True, [])],
)
def test_f048_r17_un_valor_suelto_se_envuelve_si_es_codigo_y_si_no_se_descarta(valor, esperados):
    assert LecturaCorreo.model_validate({"obra_codigos": valor}).obra_codigos == esperados


def test_f048_r17_un_documento_con_la_lectura_mal_formada_sigue_validando():
    """La fase 1 no cae: el documento entero valida y la lectura se aprovecha."""
    documento = DocumentoAlbaran.model_validate({
        "cabecera": {"obra_codigo": "1203"},
        "lineas": [],
        "lectura_correo": {"obra_codigos": [945, None], "evidencia": EVIDENCIA_LARGA},
    })

    assert documento.lectura_correo.obra_codigos == ["945"]
    assert documento.lectura_correo.evidencia == EVIDENCIA_LARGA[:160]


def test_f048_r17_el_schema_que_ve_el_llm_no_cambia():
    """La tolerancia es de lectura: al LLM se le sigue pidiendo lo mismo."""
    lectura = DocumentoAlbaran.model_json_schema()["$defs"]["LecturaCorreo"]["properties"]

    assert lectura["obra_codigos"]["type"] == "array"
    assert lectura["obra_codigos"]["items"] == {"type": "string"}
    assert "maxLength" not in str(lectura["evidencia"])


# ---------------------------------------------------------------- #
# El handler completo: el recorte llega a TODOS los sitios.
# ---------------------------------------------------------------- #
class _Almacen:
    def __init__(self, blobs: dict) -> None:
        self.blobs = blobs

    def get_json(self, contenedor, nombre):
        if (contenedor, nombre) not in self.blobs:
            raise FileNotFoundError(nombre)
        return self.blobs[(contenedor, nombre)]


class _ClienteLlm:
    """IA1 y IA2 devuelven la MISMA lectura del correo, tal cual se le pase."""

    def __init__(self, lectura: dict) -> None:
        self.lectura = lectura

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        documento = {
            "cabecera": {"obra_codigo": "1203", "numero_albaran": "SS-1"},
            "lineas": [],
            "lectura_correo": self.lectura,
        }
        if response_model is DocumentoAlbaran:
            return DocumentoAlbaran.model_validate(documento)
        return response_model.model_validate({
            "review_status": "ok", "explicacion_global": "", "documento_revisado": documento,
            "razonamientos": [],
        })


class _Obras:
    def obtener(self):
        return [ObraActiva(codigo="0945", nombre="OBRA DEMO")]

    def obtener_todas(self):
        return [ObraActiva(codigo="0945", nombre="OBRA DEMO"), ObraActiva(codigo="1203", nombre="NAVE")]


class _Sumidero:
    def __init__(self) -> None:
        self.guardados: list[tuple[str, dict]] = []

    def persistir(self, *, document_id, envelope, fase):
        self.guardados.append((fase, envelope))


class _Publicador:
    def publicar(self, cola, mensaje):
        pass


class _FuentePdf:
    def obtener(self, document_id):
        return DocumentoPdf(filename="a.png", mime_type="image/png", file_bytes=b"no es una imagen")


class _Grounding:
    def contexto(self, *, document_id, phase_1_json):
        return None


def _ejecutar(lectura: dict) -> dict[str, dict]:
    servicio = AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=_ClienteLlm(lectura))],
        prompt_repo=YamlPromptRepository(yaml_path=RAIZ / "config" / "prompts.yaml"),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=RAIZ / "config" / "revision_rules.yaml"),
        prompt_key_phase_1="albaran_factura_es",
        obras_activas_provider=_Obras(),
    )
    pipeline = ExtractAlbaranPipeline(
        extraction_service=servicio, max_file_mb=10, service_version="t",
        provider_phase_1="gemini", provider_phase_2="gemini",
        prompt_key_phase_1="albaran_factura_es", prompt_key_phase_2="albaran_revision_fase2_es",
    )
    sumidero = _Sumidero()
    handler = construir_handler_extraccion(
        pipeline=pipeline, fuente=_FuentePdf(), grounding=_Grounding(), sumidero=sumidero,
        publicador=_Publicador(),
        fuente_correo=FuenteContextoCorreoBlob(_Almacen({(CONTENEDOR_INPUT, BLOB): CORREO.model_dump(mode="json")})),
        obras_conocidas=pipeline.obras_conocidas,
    )
    handler(MensajeExtraccion(document_id=DOC, correlation_key="c-1", correo_blob=BLOB))
    env1, env2, final = sumidero.guardados
    return {"env1": env1[1], "env2": env2[1], "final": final[1]}


def _evidencias(objeto) -> list[str]:
    """Todos los valores de una clave ``evidencia``, a cualquier profundidad."""
    if isinstance(objeto, dict):
        propias = [v for k, v in objeto.items() if k == "evidencia" and isinstance(v, str)]
        return propias + [e for v in objeto.values() for e in _evidencias(v)]
    if isinstance(objeto, list):
        return [e for v in objeto for e in _evidencias(v)]
    return []


def test_f048_r24_la_evidencia_de_1000_llega_recortada_a_env1_phase_1_json_y_final():
    envelopes = _ejecutar({"obra_codigos": ["945"], "evidencia": EVIDENCIA_LARGA})
    recortada = EVIDENCIA_LARGA[:160]

    assert envelopes["env1"]["data"]["lectura_correo"]["evidencia"] == recortada
    assert envelopes["env2"]["debug"]["phase_1_json"]["data"]["lectura_correo"]["evidencia"] == recortada
    final = envelopes["final"]
    assert final["debug"]["phase_2"]["debug"]["phase_1_json"]["data"]["lectura_correo"]["evidencia"] == recortada
    assert final["data"]["origen_datos"]["evidencia"] == recortada
    # Y en ningun otro sitio de ningun envelope queda la evidencia entera.
    for nombre, envelope in envelopes.items():
        evidencias = _evidencias(envelope)
        assert evidencias, nombre
        assert all(len(e) <= 160 for e in evidencias), nombre


def test_f048_r17_un_codigo_numerico_no_tumba_la_fase_1_y_cruza_con_la_lista():
    """``[945]``: la fase 1 sigue, el codigo vale ``"945"`` y casa con ``0945``."""
    final = _ejecutar({"obra_codigos": [945], "evidencia": "la 945"})["final"]
    obra = final["data"]["origen_datos"]["obra"]

    assert obra["motivo"] == "correo_unico"
    assert obra["valor_final"] == "0945"
    assert obra["discrepancia"] is True  # el papel dice 1203
    assert final["data"]["cabecera"]["obra_codigo"] == "0945"
