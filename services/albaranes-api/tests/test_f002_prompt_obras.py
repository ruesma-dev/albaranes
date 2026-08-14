# tests/test_f002_prompt_obras.py
"""F-002 · Prompt de IA1: obras de la lista y proveedor del bloque fiscal
(R1, R2, R4).

La IA se inventaba códigos de obra y tomaba la marca del logotipo como
proveedor. Aquí se comprueba lo que de verdad LLEGA al modelo: el bloque
de obras renderizado en las instructions y las reglas del prompt real de
``config/prompts.yaml``.

Sin red ni LLM: el cliente de visión es un doble que solo captura las
instructions.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.ports.obras_activas_provider import ObraActiva
from domain.ports.prompt_repository import PromptRepository, PromptSpec
from infrastructure.prompts.revision_rules_repository import (
    RevisionRulesRepository,
)
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"


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


class ProveedorObras:
    def __init__(self, obras, *, error: Exception | None = None) -> None:
        self._obras = obras
        self._error = error
        self.llamadas = 0

    def obtener(self):
        self.llamadas += 1
        if self._error is not None:
            raise self._error
        return self._obras


def _servicio(
    cliente, prompt_repo, *, proveedor=None, **kwargs,
) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[
            ProviderClientSpec(
                provider="gemini", model_name="fake-model", client=cliente,
            ),
        ],
        prompt_repo=prompt_repo,
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
        obras_activas_provider=proveedor,
        **kwargs,
    )


def _extraer(servicio) -> None:
    servicio.extract_phase_1(
        attachments=[], provider="gemini", prompt_key=CLAVE_FASE_1,
    )


def _obras(*codigos: str):
    return [ObraActiva(codigo=c, nombre=f"OBRA {c}") for c in codigos]


# ---------------------------------------------------------------- #
# R1 — la lista va en el prompt, ordenada, capada y con la prohibición.
# ---------------------------------------------------------------- #
def test_f002_r1_el_bloque_de_obras_se_inyecta_en_el_placeholder() -> None:
    cliente = ClienteEspia()
    servicio = _servicio(
        cliente,
        PromptRepoFake("REGLAS\n{obras_activas}\nFIN"),
        proveedor=ProveedorObras(_obras("0451")),
    )

    _extraer(servicio)

    assert "{obras_activas}" not in cliente.instructions
    assert "0451 — OBRA 0451" in cliente.instructions


def test_f002_r1_las_obras_van_ordenadas_por_codigo_ascendente() -> None:
    """Orden y formato fijos = prompt determinista (compatible con las
    evals de ground truth de F-011)."""
    cliente = ClienteEspia()
    servicio = _servicio(
        cliente,
        PromptRepoFake("{obras_activas}"),
        proveedor=ProveedorObras(_obras("0999", "0451", "0700")),
    )

    _extraer(servicio)

    posiciones = [
        cliente.instructions.index(c) for c in ("0451", "0700", "0999")
    ]
    assert posiciones == sorted(posiciones)


def test_f002_r1_la_lista_se_capa_a_obras_activas_max() -> None:
    cliente = ClienteEspia()
    servicio = _servicio(
        cliente,
        PromptRepoFake("{obras_activas}"),
        proveedor=ProveedorObras(_obras("0451", "0452", "0453")),
        obras_activas_max=2,
    )

    _extraer(servicio)

    assert "0451 — OBRA 0451" in cliente.instructions
    assert "0453" not in cliente.instructions


def test_f002_r1_el_bloque_prohibe_codigos_fuera_de_la_lista() -> None:
    cliente = ClienteEspia()
    servicio = _servicio(
        cliente,
        PromptRepoFake("{obras_activas}"),
        proveedor=ProveedorObras(_obras("0451")),
    )

    _extraer(servicio)

    texto = cliente.instructions.lower()
    assert "solo" in texto and "lista" in texto
    assert "null" in texto


def test_f002_r1_la_obra_sin_nombre_no_rompe_el_bloque() -> None:
    cliente = ClienteEspia()
    servicio = _servicio(
        cliente,
        PromptRepoFake("{obras_activas}"),
        proveedor=ProveedorObras([ObraActiva(codigo="0451", nombre=None)]),
    )

    _extraer(servicio)

    assert "0451" in cliente.instructions


def test_f002_r1_el_prompt_real_tiene_el_placeholder() -> None:
    spec = YamlPromptRepository(PROMPTS_REALES).get(CLAVE_FASE_1)

    assert "{obras_activas}" in spec.task


def test_f002_r1_compatibilidad_yaml_sin_placeholder_appendea_el_bloque() -> None:
    """Si el YAML desplegado aún no tiene el placeholder, el bloque se
    añade al final del task: mejor en posición subóptima que perdido."""
    cliente = ClienteEspia()
    servicio = _servicio(
        cliente,
        PromptRepoFake("TASK VIEJO SIN PLACEHOLDER"),
        proveedor=ProveedorObras(_obras("0451")),
    )

    _extraer(servicio)

    assert "TASK VIEJO SIN PLACEHOLDER" in cliente.instructions
    assert "0451 — OBRA 0451" in cliente.instructions


# ---------------------------------------------------------------- #
# R2 — sin lista, nota de "no disponible" y la extracción sigue.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("respuesta", [None, []])
def test_f002_r2_sin_lista_se_pone_la_nota_de_no_disponible(respuesta) -> None:
    cliente = ClienteEspia()
    servicio = _servicio(
        cliente,
        PromptRepoFake("{obras_activas}"),
        proveedor=ProveedorObras(respuesta),
    )

    _extraer(servicio)

    assert "{obras_activas}" not in cliente.instructions
    assert "no disponible" in cliente.instructions.lower()


def test_f002_r2_sin_proveedor_cableado_la_extraccion_sigue() -> None:
    cliente = ClienteEspia()
    servicio = _servicio(cliente, PromptRepoFake("{obras_activas}"))

    _extraer(servicio)

    assert "no disponible" in cliente.instructions.lower()


def test_f002_r2_un_proveedor_que_revienta_no_rompe_la_extraccion() -> None:
    cliente = ClienteEspia()
    proveedor = ProveedorObras(None, error=RuntimeError("sigrid-api 500"))
    servicio = _servicio(
        cliente, PromptRepoFake("{obras_activas}"), proveedor=proveedor,
    )

    _extraer(servicio)

    assert proveedor.llamadas == 1
    assert "no disponible" in cliente.instructions.lower()


def test_f002_r2_sin_lista_y_sin_placeholder_no_se_appendea_nada() -> None:
    cliente = ClienteEspia()
    servicio = _servicio(cliente, PromptRepoFake("TASK VIEJO"))

    _extraer(servicio)

    assert "no disponible" not in cliente.instructions.lower()


# ---------------------------------------------------------------- #
# R4 — proveedor = razón social del bloque fiscal, NUNCA el logotipo.
# ---------------------------------------------------------------- #
def _task_real() -> str:
    return YamlPromptRepository(PROMPTS_REALES).get(CLAVE_FASE_1).task


def test_f002_r4_el_prompt_exige_la_razon_social_del_bloque_fiscal() -> None:
    task = _task_real().lower()

    assert "razón social" in task or "razon social" in task
    assert "fiscal" in task


def test_f002_r4_el_prompt_veta_la_marca_del_logotipo() -> None:
    task = _task_real().lower()

    assert "logo" in task
    # La regla vieja ("Puede venir en el logo") invitaba justo al error.
    assert "puede venir en el logo" not in task


def test_f002_r4_las_reglas_llegan_a_las_instructions() -> None:
    cliente = ClienteEspia()
    servicio = _servicio(
        cliente,
        YamlPromptRepository(PROMPTS_REALES),
        proveedor=ProveedorObras(_obras("0451")),
    )

    _extraer(servicio)

    texto = cliente.instructions.lower()
    assert "fiscal" in texto
    assert "0451 — OBRA 0451" in cliente.instructions
