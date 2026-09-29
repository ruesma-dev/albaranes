# tests/test_f048_r14_fase2_sin_marcadores.py
"""F-048 · R14: el MISMO bloque del correo llega a la fase 2.

Los prompts de fase 2 embeben el prompt de fase 1 entero en
``{prompt_fase_1}`` (F-043). El bloque del correo vive en ese prompt de fase
1, asi que IA2 tiene que recibirlo igual que IA1 —mismo texto, misma
huella— y ningun prompt de ninguna fase puede salir con el literal
``{contexto_correo}`` ni con otro marcador conocido sin sustituir.

Se comprueba sobre el ``config/prompts.yaml`` REAL y recorriendo TODOS los
prompts de fase 2 del catalogo, con y sin correo.

Ademas, el bloque del correo no se vuelve a recorrer al rellenar los
marcadores de fase 2: un correo que escriba ``{json_fase_1}`` o
``{sigrid_context}`` no recibe dentro el JSON de fase 1 ni el grounding.

Sin red, sin BBDD y sin LLM. Textos inventados, con ``CENTINELA-F048``.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.ports.obras_activas_provider import ObraActiva
from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from ruesma_comun.contratos import familias as cat
from ruesma_comun.correo import (
    MARCA_FIN,
    MARCA_INICIO,
    construir_contexto_correo,
    render_bloque_correo,
)

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"
CENTINELA = "CENTINELA-F048"

MARCADORES_CONOCIDOS = (
    "{contexto_correo}",
    "{obras_activas}",
    "{catalogo_familias}",
    "{prompt_fase_1}",
    "{revision_rules}",
    "{json_fase_1}",
    "{sigrid_context}",
)
MARCADOR_COLGANTE = re.compile(r"\{[a-z][a-z0-9_]*\}")

CORREO = construir_contexto_correo("RE: albaran obra 0945", f"Para la obra 0945, gracias. {CENTINELA}")
_JSON_FASE_1 = {
    "cabecera": {"proveedor_nombre": "HORMIGONES DEL SUR", "obra_codigo": "0937"},
    "lineas": [{"concepto": "HA-25", "cantidad": 7.5}],
}
_SIGRID = {"proveedor": {"status": "validated", "cif": "B00000000", "nombre_canonico": "DEMO SL"}}


class ClienteEspia:
    def __init__(self) -> None:
        self.instructions: list[str] = []

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        self.instructions.append(instructions)
        return DocumentoAlbaran(cabecera={}, lineas=[])


class ObrasFake:
    def obtener(self) -> list[ObraActiva] | None:
        return [ObraActiva(codigo="0945", nombre="RESIDENCIAL DEMO")]


def _claves_fase2() -> tuple[str, ...]:
    """Todas las de fase 2 que enruta el catalogo, mas la generica."""
    claves = {"albaran_revision_fase2_es"}
    for id_familia in cat.familias_documento():
        clave = cat.prompt_fase2_de(id_familia)
        if clave:
            claves.add(clave)
    return tuple(sorted(claves))


def _servicio(cliente: ClienteEspia) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente)],
        prompt_repo=YamlPromptRepository(yaml_path=PROMPTS_REALES),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
        obras_activas_provider=ObrasFake(),
    )


def _fase2(clave: str, correo, sigrid=None) -> str:
    cliente = ClienteEspia()
    _servicio(cliente).review_phase_2(
        attachments=[],
        provider="gemini",
        prompt_key=clave,
        phase_1_json=_JSON_FASE_1,
        sigrid_context=sigrid,
        contexto_correo=correo,
    )
    return cliente.instructions[-1]


def _fase1(correo) -> str:
    cliente = ClienteEspia()
    _servicio(cliente).extract_phase_1(
        attachments=[], provider="gemini", prompt_key=CLAVE_FASE_1, contexto_correo=correo
    )
    return cliente.instructions[-1]


def _bloque(texto: str) -> str:
    return texto[texto.index(MARCA_INICIO): texto.index(MARCA_FIN) + len(MARCA_FIN)]


def test_f048_r14_hay_prompts_de_fase2_que_recorrer():
    """Control: si el catalogo no enrutara nada, los tests de abajo serian vacuos."""
    assert len(_claves_fase2()) >= 4


@pytest.mark.parametrize("clave", _claves_fase2())
@pytest.mark.parametrize("correo", [CORREO, None], ids=["con_correo", "sin_correo"])
def test_f048_r14_ningun_prompt_de_fase2_deja_marcadores(clave, correo):
    instructions = _fase2(clave, correo)

    assert "{contexto_correo}" not in instructions
    colgantes = sorted(set(MARCADOR_COLGANTE.findall(instructions)) & set(MARCADORES_CONOCIDOS))
    assert not colgantes, f"{clave} deja marcadores sin sustituir: {colgantes}"


@pytest.mark.parametrize("clave", _claves_fase2())
def test_f048_r14_la_fase2_recibe_el_mismo_bloque_que_la_fase1(clave):
    instructions = _fase2(clave, CORREO)

    assert instructions.count(MARCA_INICIO) == 1
    assert render_bloque_correo(CORREO) in instructions
    assert render_bloque_correo(CORREO) in _fase1(CORREO)
    assert _bloque(instructions) == _bloque(_fase1(CORREO))
    assert CORREO.sha256 in instructions


@pytest.mark.parametrize("clave", _claves_fase2())
def test_f048_r14_sin_correo_la_fase2_no_lleva_bloque(clave):
    assert MARCA_INICIO not in _fase2(clave, None)


def test_f048_r14_el_bloque_no_se_rellena_con_los_marcadores_de_fase2():
    """El correo es DATO: sus marcadores no se expanden en la fase 2."""
    tramposo = construir_contexto_correo(
        "Albaran", "Texto con {json_fase_1}, {sigrid_context}, {revision_rules} y {prompt_fase_1}"
    )

    instructions = _fase2("albaran_revision_fase2_es", tramposo, sigrid=_SIGRID)

    assert render_bloque_correo(tramposo) in instructions
    assert _bloque(instructions) == _bloque(render_bloque_correo(tramposo))
    # Y los marcadores de verdad se siguen rellenando fuera del bloque.
    assert "HORMIGONES DEL SUR" in instructions
    assert "DEMO SL" in instructions


def test_f048_r14_el_log_de_fase_2_resume_el_correo_sin_el_cuerpo(caplog):
    with caplog.at_level("INFO"):
        _fase2("albaran_revision_fase2_es", CORREO)
        _fase2("albaran_revision_fase2_es", None)

    fase2 = [r.getMessage() for r in caplog.records if "FASE 2" in r.getMessage()]
    assert f"correo=SI({CORREO.caracteres_originales}, {CORREO.sha256[:8]})" in fase2[0]
    assert fase2[1].endswith("correo=NO")
    assert CENTINELA not in caplog.text


class _RepoFase2SinSigrid:
    """El YAML real para la fase 1 y un task de fase 2 sin ``{sigrid_context}``."""

    def __init__(self) -> None:
        self._real = YamlPromptRepository(yaml_path=PROMPTS_REALES)

    def get(self, prompt_key: str):
        from domain.ports.prompt_repository import PromptSpec

        if prompt_key == CLAVE_FASE_1:
            return self._real.get(prompt_key)
        return PromptSpec(system="S", task="{prompt_fase_1}\n\n{json_fase_1}\nFIN", schema_hint="H", schema="revision_albaran_fase2")


@pytest.mark.parametrize("sigrid", [_SIGRID, None], ids=["con_grounding", "sin_grounding"])
def test_f048_r14_sin_marcador_de_sigrid_el_grounding_va_al_final(sigrid):
    """Compatibilidad de antes, conservada con la sustitucion en una pasada."""
    cliente = ClienteEspia()
    servicio = _servicio(cliente)
    servicio._prompts = _RepoFase2SinSigrid()

    servicio.review_phase_2(
        attachments=[], provider="gemini", prompt_key="otra", phase_1_json=_JSON_FASE_1,
        sigrid_context=sigrid, contexto_correo=CORREO,
    )

    instructions = cliente.instructions[-1]
    assert render_bloque_correo(CORREO) in instructions
    assert ("DEMO SL" in instructions) is (sigrid is not None)
    if sigrid is not None:
        assert instructions.index("FIN") < instructions.index("DEMO SL")
