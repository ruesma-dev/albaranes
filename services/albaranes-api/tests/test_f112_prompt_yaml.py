# tests/test_f112_prompt_yaml.py
"""F-112 · R15–R18 sobre los YAML REALES de sv2.

- El task de ``albaran_factura_es`` lleva ``{fecha_recepcion}`` UNA vez, en
  «Reglas para la cabecera», justo tras la regla de ``fecha``, y esa regla
  dice que día y mes salen del papel y el año se contrasta con la recepción.
- Los cuatro ``albaran_revision_fase2_*`` llevan ``{revision_fecha}`` UNA vez,
  en su sección propia «Fecha del albarán (revisión obligatoria)», tras la
  checklist y antes del grounding, y siguen llevando ``{prompt_fase_1}``.
- ``revision_rules.yaml`` no gana regla de fecha.
- De extremo a extremo con los YAML reales: IA1 e IA2 reciben los bloques y
  no queda ningún marcador sin sustituir.

Sin red ni LLM.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest
import yaml
from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.fecha_recepcion import (
    NOTA_REVISION_SIN_RECEPCION,
    NOTA_SIN_RECEPCION,
    render_fecha_recepcion,
    render_revision_fecha,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"
CLAVES_FASE_2 = (
    "albaran_revision_fase2_es",
    "albaran_revision_fase2_residuos",
    "albaran_revision_fase2_hormigon",
    "albaran_revision_fase2_mortero",
)
SECCION = "## Fecha del albarán (revisión obligatoria)"
FECHA = date(2026, 10, 28)
MARCADOR_COLGANTE = re.compile(r"\{[a-z][a-z0-9_]*\}")


def _prompts() -> dict:
    return yaml.safe_load(PROMPTS_REALES.read_text(encoding="utf-8"))


def _plano(texto: str) -> str:
    return re.sub(r"\s+", " ", texto)


# ---------------------------------------------------------------- #
# R15, R16 · el task de IA1.
# ---------------------------------------------------------------- #
def test_f112_r15_el_marcador_va_una_vez_tras_la_regla_de_fecha():
    task = _prompts()[CLAVE_FASE_1]["task"]

    assert task.count("{fecha_recepcion}") == 1
    cabecera = task.index("## Reglas para la cabecera")
    regla_fecha = task.index("- fecha:", cabecera)
    marcador = task.index("{fecha_recepcion}")
    siguiente = task.index("- numero_albaran:", cabecera)
    assert cabecera < regla_fecha < marcador < siguiente
    # Justo después: entre la regla de fecha y el marcador no hay otra viñeta.
    assert "\n- " not in task[regla_fecha + 1: marcador]


def test_f112_r16_la_regla_de_fecha_dice_papel_y_recepcion():
    task = _plano(_prompts()[CLAVE_FASE_1]["task"])
    regla = task[task.index("- fecha:"): task.index("{fecha_recepcion}")]

    assert "la del albarán (emisión o servicio)" in regla
    assert "no la de un pedido, contrato o autorización" in regla
    assert "El día y el mes se leen SIEMPRE del papel" in regla
    assert "El AÑO se contrasta con la fecha de recepción del correo" in regla


# ---------------------------------------------------------------- #
# R17, R18 · los cuatro prompts de IA2.
# ---------------------------------------------------------------- #
def test_f112_r17_los_cuatro_prompts_de_fase_2_existen():
    assert set(CLAVES_FASE_2) <= set(_prompts())
    reales = {k for k in _prompts() if k.startswith("albaran_revision_fase2_")}
    assert reales == set(CLAVES_FASE_2)


@pytest.mark.parametrize("clave", CLAVES_FASE_2)
def test_f112_r17_seccion_propia_con_el_marcador(clave):
    task = _prompts()[clave]["task"]

    assert task.count("{revision_fecha}") == 1
    assert task.count(SECCION) == 1
    seccion = task.index(SECCION)
    marcador = task.index("{revision_fecha}")
    siguiente_seccion = task.index("\n## ", seccion + 1)
    assert seccion < marcador < siguiente_seccion


@pytest.mark.parametrize("clave", CLAVES_FASE_2)
def test_f112_r17_tras_la_checklist_y_antes_del_grounding(clave):
    task = _prompts()[clave]["task"]

    checklist = task.index("{revision_rules}")
    grounding = task.index("## GROUNDING CONTRA EL ERP SIGRID")
    assert checklist < task.index(SECCION) < grounding


@pytest.mark.parametrize("clave", CLAVES_FASE_2)
def test_f112_r18_siguen_llevando_el_prompt_de_fase_1(clave):
    assert _prompts()[clave]["task"].count("{prompt_fase_1}") == 1


@pytest.mark.parametrize("clave", CLAVES_FASE_2)
def test_f112_r18_el_ejemplo_fijo_del_yaml(clave):
    seccion = _plano(_prompts()[clave]["task"])
    seccion = seccion[seccion.index(SECCION): seccion.index("## GROUNDING")]
    assert "2020-10-17" in seccion and "17/10/26" in seccion and "2026-10-17" in seccion
    assert "anio_fecha_recepcion" in seccion


def test_f112_r18_revision_rules_no_gana_regla_de_fecha():
    reglas = yaml.safe_load(REGLAS_REALES.read_text(encoding="utf-8"))
    texto = REGLAS_REALES.read_text(encoding="utf-8")
    ids = [r["id"] for r in reglas["reglas"]]

    assert not [i for i in ids if "fecha" in i]
    assert "anio_fecha_recepcion" not in texto
    assert "recepción" not in texto.lower() and "recepcion" not in texto.lower()


# ---------------------------------------------------------------- #
# De extremo a extremo con los YAML reales.
# ---------------------------------------------------------------- #
class ClienteEspia:
    def __init__(self) -> None:
        self.instructions: list[str] = []

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        self.instructions.append(instructions)
        return DocumentoAlbaran(cabecera={}, lineas=[])


def _servicio(cliente: ClienteEspia) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente)],
        prompt_repo=YamlPromptRepository(yaml_path=PROMPTS_REALES),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
    )


@pytest.mark.parametrize("fecha", [FECHA, None], ids=["con_fecha", "sin_fecha"])
def test_f112_r9_r15_ia1_recibe_el_bloque_del_yaml_real(fecha):
    cliente = ClienteEspia()
    _servicio(cliente).extract_phase_1(
        attachments=[], provider="gemini", prompt_key=CLAVE_FASE_1, fecha_recepcion=fecha,
    )
    instructions = cliente.instructions[-1]

    assert "{fecha_recepcion}" not in instructions
    assert render_fecha_recepcion(fecha) in instructions
    if fecha is None:
        assert NOTA_SIN_RECEPCION in instructions


@pytest.mark.parametrize("clave", CLAVES_FASE_2)
@pytest.mark.parametrize("fecha", [FECHA, None], ids=["con_fecha", "sin_fecha"])
def test_f112_r17_ia2_recibe_los_dos_bloques_sin_marcadores(clave, fecha):
    cliente = ClienteEspia()
    _servicio(cliente).review_phase_2(
        attachments=[], provider="gemini", prompt_key=clave,
        phase_1_json={"cabecera": {"fecha": "2020-10-17"}, "lineas": []}, fecha_recepcion=fecha,
    )
    instructions = cliente.instructions[-1]

    assert not MARCADOR_COLGANTE.findall(instructions)
    assert render_fecha_recepcion(fecha) in instructions  # dentro de {prompt_fase_1}
    assert render_revision_fecha(fecha) in instructions
    if fecha is None:
        assert NOTA_REVISION_SIN_RECEPCION in instructions
    plano = _plano(instructions)
    assert plano.index(SECCION) < plano.index(_plano(render_revision_fecha(fecha))) < plano.index("## GROUNDING")
