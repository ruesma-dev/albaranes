# tests/test_f048_r12_render_fase1.py
"""F-048 · R12: el texto del correo llega al task de fase 1.

``_render_task_fase_1(task, correo)`` es el UNICO sitio donde se sustituyen
los marcadores del task de fase 1 (F-043), y ahora tambien
``{contexto_correo}``: con contexto, por el bloque delimitado de
``ruesma_comun`` (asunto y cuerpo entre marcas, con la advertencia de DATO);
sin contexto, por la nota fija; y si el YAML desplegado no trae el marcador,
el bloque se anade al final del task para no perderlo.

El correo se sustituye EL ULTIMO: su texto es de un tercero y no se vuelve a
recorrer, asi que un correo que escriba ``{obras_activas}`` no recibe la
lista de obras dentro del bloque.

Sin red ni LLM: el cliente de vision es un doble que captura las
instructions. Textos inventados, con el centinela ``CENTINELA-F048``.
"""
from __future__ import annotations

import logging

from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.ports.obras_activas_provider import ObraActiva
from domain.ports.prompt_repository import PromptRepository, PromptSpec
from ruesma_comun.correo import (
    MARCA_FIN,
    MARCA_INICIO,
    NOTA_SIN_CORREO,
    construir_contexto_correo,
    render_bloque_correo,
)

CENTINELA = "CENTINELA-F048"
MARCADOR = "{contexto_correo}"
CORREO = construir_contexto_correo(
    "RE: albaran obra 0945", f"Buenos dias, va para la obra 0945. {CENTINELA}"
)
TASK_CON_MARCADOR = f"## Obras\n\n{{obras_activas}}\n\n## Correo\n\n{MARCADOR}\n\n## Lineas\n\nfin"
TASK_SIN_MARCADOR = "## Obras\n\n{obras_activas}\n\n## Lineas\n\nfin"


class ClienteEspia:
    """Doble de ``LlmVisionClient``: guarda las instructions recibidas."""

    def __init__(self) -> None:
        self.instructions: str | None = None

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        self.instructions = instructions
        return DocumentoAlbaran(cabecera={}, lineas=[])


class PromptRepoFake(PromptRepository):
    def __init__(self, task: str) -> None:
        self._spec = PromptSpec(system="SYSTEM", task=task, schema_hint="HINT", schema="documento_albaran")

    def get(self, prompt_key: str) -> PromptSpec:
        return self._spec

    def has(self, prompt_key: str) -> bool:
        return True


class ObrasFake:
    def obtener(self) -> list[ObraActiva] | None:
        return [ObraActiva(codigo="0945", nombre="RESIDENCIAL DEMO")]


class _ReglasFake:
    count = 0
    rule_ids: tuple[str, ...] = ()

    def render_for_prompt(self) -> str:
        return "REGLAS"


def _servicio(task: str, cliente: ClienteEspia | None = None) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente or ClienteEspia())],
        prompt_repo=PromptRepoFake(task),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=_ReglasFake(),
        prompt_key_phase_1="albaran_factura_es",
        obras_activas_provider=ObrasFake(),
    )


def _render(task: str, correo=CORREO) -> str:
    renderizado, _obras = _servicio(task)._render_task_fase_1(task, correo)
    return renderizado


def test_f048_r12_el_marcador_se_sustituye_por_el_bloque_del_correo():
    renderizado = _render(TASK_CON_MARCADOR)

    assert MARCADOR not in renderizado
    assert render_bloque_correo(CORREO) in renderizado
    # En su sitio: entre la seccion de obras y la de lineas.
    assert renderizado.index("## Correo") < renderizado.index(MARCA_INICIO) < renderizado.index("## Lineas")
    assert renderizado.count(MARCA_INICIO) == renderizado.count(MARCA_FIN) == 1


def test_f048_r12_sin_contexto_el_marcador_se_sustituye_por_la_nota_fija():
    renderizado = _render(TASK_CON_MARCADOR, correo=None)

    assert MARCADOR not in renderizado
    assert NOTA_SIN_CORREO in renderizado
    assert MARCA_INICIO not in renderizado


def test_f048_r12_sin_marcador_el_bloque_se_anade_al_final():
    """YAML desplegado sin el marcador: mejor el bloque al final que perderlo."""
    renderizado = _render(TASK_SIN_MARCADOR)

    assert renderizado.rstrip().endswith(render_bloque_correo(CORREO))
    assert renderizado.count(MARCA_INICIO) == 1


def test_f048_r12_sin_marcador_y_sin_contexto_el_task_no_cambia_por_el_correo():
    """Sin bloque que conservar no se anade nada: el task es el de hoy."""
    servicio = _servicio(TASK_SIN_MARCADOR)

    con_parametro, _ = servicio._render_task_fase_1(TASK_SIN_MARCADOR, None)

    assert NOTA_SIN_CORREO not in con_parametro
    assert MARCA_INICIO not in con_parametro


def test_f048_r12_el_correo_no_se_vuelve_a_recorrer_buscando_marcadores():
    """Un correo que escribe marcadores no recibe la lista de obras ni el catalogo."""
    tramposo = construir_contexto_correo("Albaran", "Ojo: {obras_activas} y {catalogo_familias}")

    renderizado = _render(TASK_CON_MARCADOR, correo=tramposo)

    bloque = renderizado[renderizado.index(MARCA_INICIO): renderizado.index(MARCA_FIN)]
    assert "{obras_activas} y {catalogo_familias}" in bloque
    assert "RESIDENCIAL DEMO" not in bloque


def test_f048_r12_extract_phase_1_lleva_el_correo_a_las_instructions():
    cliente = ClienteEspia()

    _servicio(TASK_CON_MARCADOR, cliente).extract_phase_1(
        attachments=[], provider="gemini", prompt_key="albaran_factura_es", contexto_correo=CORREO
    )

    assert render_bloque_correo(CORREO) in cliente.instructions
    assert MARCADOR not in cliente.instructions


def test_f048_r12_extract_phase_1_sin_correo_lleva_la_nota():
    """Compatibilidad: quien no pasa el parametro obtiene la nota fija."""
    cliente = ClienteEspia()

    _servicio(TASK_CON_MARCADOR, cliente).extract_phase_1(
        attachments=[], provider="gemini", prompt_key="albaran_factura_es"
    )

    assert NOTA_SIN_CORREO in cliente.instructions
    assert MARCADOR not in cliente.instructions


def test_f048_r12_el_log_de_fase_1_resume_el_correo_sin_el_cuerpo(caplog):
    with caplog.at_level(logging.INFO):
        _servicio(TASK_CON_MARCADOR).extract_phase_1(
            attachments=[], provider="gemini", prompt_key="k", contexto_correo=CORREO
        )
        _servicio(TASK_CON_MARCADOR).extract_phase_1(attachments=[], provider="gemini", prompt_key="k")

    assert f"correo=SI({CORREO.caracteres_originales}, {CORREO.sha256[:8]})" in caplog.text
    assert "correo=NO" in caplog.text
    assert CENTINELA not in caplog.text
