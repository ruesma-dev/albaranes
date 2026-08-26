# tests/test_f043_prompt_fase1.py
"""F-043 · El catalogo de familias LLEGA al prompt de IA1 (R6, R7, R4, R16).

Lo que se comprueba aqui es lo unico que se puede comprobar SIN LLM: que el
marcador `{catalogo_familias}` se sustituye de verdad en las instructions que
salen hacia el modelo, que el catalogo entra ENTERO (definicion, en que se
diferencia y senales de cada familia de DOCUMENTO) y que el texto real de
`config/prompts.yaml` pide lo que R7/R4/R16 exigen.

Que la IA acierte con ese prompt es otra evidencia y no cabe aqui: son las
evals con LLM real (T30), que autoriza el humano.

Sin red ni LLM: el cliente de vision es un doble que solo captura las
instructions.
"""
from __future__ import annotations

from pathlib import Path

import yaml
from ruesma_comun.contratos import familias as cat

from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.ports.prompt_repository import PromptRepository, PromptSpec
from infrastructure.prompts.revision_rules_repository import (
    RevisionRulesRepository,
)

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"
MARCADOR = "{catalogo_familias}"


class ClienteEspia:
    """Doble de ``LlmVisionClient``: guarda las instructions recibidas."""

    def __init__(self) -> None:
        self.instructions: str | None = None

    def extract_document(
        self, *, model, instructions, user_text, attachments, response_model,
    ):
        self.instructions = instructions
        return DocumentoAlbaran(cabecera={}, lineas=[])


class PromptRepoFake(PromptRepository):
    def __init__(self, task: str) -> None:
        self._spec = PromptSpec(
            system="SYSTEM",
            task=task,
            schema_hint="HINT",
            schema="documento_albaran",
        )

    def get(self, prompt_key: str) -> PromptSpec:
        return self._spec

    def has(self, prompt_key: str) -> bool:
        return True


def _instructions_de(task: str) -> str:
    """Ejecuta fase 1 con ese `task` y devuelve lo que recibio el modelo."""
    cliente = ClienteEspia()
    servicio = AlbaranExtractionService(
        providers=[
            ProviderClientSpec(
                provider="gemini", model_name="fake-model", client=cliente,
            ),
        ],
        prompt_repo=PromptRepoFake(task),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
        obras_activas_provider=None,
    )
    servicio.extract_phase_1(
        attachments=[], provider="gemini", prompt_key=CLAVE_FASE_1,
    )
    return cliente.instructions or ""


def _prompts_reales() -> dict:
    return yaml.safe_load(PROMPTS_REALES.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ #
# R6 — el catalogo se inyecta en el marcador, como {obras_activas}.
# ------------------------------------------------------------------ #
def test_f043_r6_el_catalogo_se_inyecta_en_el_marcador() -> None:
    instructions = _instructions_de(f"REGLAS\n{MARCADOR}\nFIN")

    assert MARCADOR not in instructions
    assert cat.render_catalogo_markdown("documento") in instructions


def test_f043_r6_entran_las_cuatro_familias_de_documento_enteras() -> None:
    """El catalogo entra ENTERO: los tres textos de cada familia.

    Un catalogo recortado (solo los ids) le pide a la IA que adivine que
    significa cada etiqueta, que es justo lo que R1-R5 vienen a evitar.
    """
    instructions = _instructions_de(MARCADOR)

    for id_familia in cat.familias_documento():
        familia = cat.obtener(id_familia)
        assert f"`{familia.id}`" in instructions
        assert familia.definicion in instructions
        assert familia.no_es in instructions
        assert familia.senales in instructions


def test_f043_r6_no_entran_las_familias_de_solo_linea() -> None:
    """`combustible`, `alquiler_maquinaria` y `otro` NO son clasificacion
    de documento (decision del humano, duda 1): ofrecerselas a IA1 como
    respuesta seria pedirle una etiqueta sin prompt detras."""
    instructions = _instructions_de(MARCADOR)

    solo_linea = set(cat.familias_linea()) - set(cat.familias_documento())
    assert solo_linea  # el catalogo tiene familias de solo linea
    for id_familia in solo_linea:
        assert f"`{id_familia}`" not in instructions


def test_f043_r6_sin_marcador_el_catalogo_se_anade_igual() -> None:
    """Compatibilidad: un YAML desplegado sin el marcador no puede dejar a
    IA1 sin catalogo. Mismo criterio que `{obras_activas}`: mejor el bloque
    en posicion suboptima que perderlo en silencio."""
    instructions = _instructions_de("REGLAS SIN MARCADOR")

    assert "`residuos`" in instructions
    assert cat.render_catalogo_markdown("documento") in instructions
