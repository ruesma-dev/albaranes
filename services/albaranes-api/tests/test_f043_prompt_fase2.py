# tests/test_f043_prompt_fase2.py
"""F-043 · lo que IA2 recibe de verdad: sin marcadores colgantes (R6, R16).

Los cuatro prompts de fase 2 embeben el prompt de fase 1 entero en su
marcador `{prompt_fase_1}`. Ese prompt de fase 1 trae a su vez DOS
marcadores propios —`{catalogo_familias}` (F-043 · R6) y `{obras_activas}`
(F-002 · R1)— que solo se sustituian en el camino de `extract_phase_1`.
Por el camino de `review_phase_2` viajaban EN CRUDO: IA2 leia el literal
`{catalogo_familias}` donde debia estar la lista de familias.

No es cosmetico. R16 dice que la clasificacion de fase 2 PREVALECE sobre
la de fase 1, asi que la decision central de la feature la tomaba la IA
que no habia leido el catalogo. Cadena del fallo: IA2 devuelve una
etiqueta fuera de catalogo -> el resolver la degrada a `generico` con
confianza 0 -> un documento que IA1 clasifico bien acaba en `generico` y
las puertas de residuos de sv6 no se abren.

El test que impide que vuelva a pasar CON OTRO MARCADOR es el generico:
las instructions que salen hacia el modelo no pueden llevar ningun
`{marcador}` sin sustituir. Los demas fijan las dos fugas concretas.

Sin red, sin BBDD y sin LLM: el cliente de vision es un doble que solo
captura las instructions y el proveedor de obras es una lista fija.
"""
from __future__ import annotations

import re
from pathlib import Path

from ruesma_comun.contratos import familias as cat

from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.ports.obras_activas_provider import ObraActiva
from infrastructure.prompts.revision_rules_repository import (
    RevisionRulesRepository,
)
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"

# Un marcador de plantilla es `{identificador_en_minusculas}`. Los
# ejemplos JSON del prompt llevan llaves, pero siempre con comillas o
# saltos dentro (`{"campo": ...}`), asi que no casan con esto.
MARCADOR_COLGANTE = re.compile(r"\{[a-z][a-z0-9_]*\}")

_OBRAS = (
    ObraActiva(codigo="0937", nombre="RESIDENCIAL LOS OLMOS"),
    ObraActiva(codigo="1042", nombre="NAVE INDUSTRIAL RUESMA"),
)

_JSON_FASE_1 = {
    "cabecera": {"proveedor_nombre": "SALMEDINA", "numero_albaran": "SS-1"},
    "lineas": [{"concepto": "Contenedor RCD 6 m3", "cantidad": 1}],
}


class ClienteEspia:
    """Doble de ``LlmVisionClient``: guarda las instructions recibidas."""

    def __init__(self) -> None:
        self.instructions: str | None = None

    def extract_document(
        self, *, model, instructions, user_text, attachments, response_model,
    ):
        self.instructions = instructions
        return DocumentoAlbaran(cabecera={}, lineas=[])


class ObrasFake:
    """Proveedor de obras activas con una lista fija (sin red)."""

    def obtener(self) -> list[ObraActiva] | None:
        return list(_OBRAS)


def _claves_fase2() -> tuple[str, ...]:
    """Las claves de fase 2 que el catalogo enruta, mas el generico.

    Se derivan del catalogo (R3): si manana entra una familia nueva con
    su prompt, este conjunto crece solo y los tests de abajo la exigen.
    """
    claves = {"albaran_revision_fase2_es"}
    for id_familia in cat.familias_documento():
        clave = cat.prompt_fase2_de(id_familia)
        if clave:
            claves.add(clave)
    return tuple(sorted(claves))


def _instructions_fase2(clave: str, *, obras: bool = True) -> str:
    """Ejecuta fase 2 con el YAML REAL y devuelve lo que recibio el LLM."""
    cliente = ClienteEspia()
    servicio = AlbaranExtractionService(
        providers=[
            ProviderClientSpec(
                provider="gemini", model_name="fake-model", client=cliente,
            ),
        ],
        prompt_repo=YamlPromptRepository(yaml_path=PROMPTS_REALES),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
        obras_activas_provider=ObrasFake() if obras else None,
    )
    servicio.review_phase_2(
        attachments=[],
        provider="gemini",
        prompt_key=clave,
        phase_1_json=_JSON_FASE_1,
        sigrid_context=None,
    )
    return cliente.instructions or ""


# ------------------------------------------------------------------ #
# El test generico: ningun marcador se escapa, sea cual sea.
# ------------------------------------------------------------------ #
def test_f043_r16_las_instructions_de_fase2_no_llevan_marcadores_colgantes():
    """Ninguno de los CUATRO prompts deja un `{marcador}` sin sustituir.

    Este es el test que vale para el marcador que aun no existe: cuando
    manana alguien anada `{lo_que_sea}` al prompt de fase 1 y olvide
    renderizarlo en el camino de fase 2, cae aqui y no en produccion.
    """
    for clave in _claves_fase2():
        instructions = _instructions_fase2(clave)
        colgantes = sorted(set(MARCADOR_COLGANTE.findall(instructions)))

        assert not colgantes, f"{clave} deja marcadores sin sustituir: {colgantes}"


# ------------------------------------------------------------------ #
# F-043 · R6/R16 — el catalogo de familias llega a IA2.
# ------------------------------------------------------------------ #
def test_f043_r16_el_catalogo_de_familias_llega_entero_a_fase2():
    """R16 hace prevalecer a IA2: tiene que ver el catalogo ENTERO.

    Sin el, IA2 decide la familia del documento sin saber que familias
    existen ni en que se diferencian — justo las distinciones que R5
    quiere ensenarle (hormigon vs mortero, residuos vs alquiler de
    contenedor).
    """
    for clave in _claves_fase2():
        instructions = _instructions_fase2(clave)

        assert "{catalogo_familias}" not in instructions, clave
        assert cat.render_catalogo_markdown("documento") in instructions, clave


def test_f043_r16_fase2_ve_las_cuatro_familias_de_documento_con_su_texto():
    """El catalogo entra con los tres textos de cada familia, no solo los
    ids: una etiqueta sin definicion detras es adivinar."""
    instructions = _instructions_fase2("albaran_revision_fase2_es")

    for id_familia in cat.familias_documento():
        familia = cat.obtener(id_familia)
        assert f"`{familia.id}`" in instructions
        assert familia.definicion in instructions
        assert familia.no_es in instructions
        assert familia.senales in instructions


# ------------------------------------------------------------------ #
# F-002 · R1 — la MISMA fuga, previa a F-043, cerrada de paso.
# ------------------------------------------------------------------ #
def test_f002_r1_la_lista_de_obras_activas_llega_tambien_a_fase2():
    """`{obras_activas}` sufria exactamente la misma fuga y es de F-002.

    IA2 corrige el `obra_codigo` de la fase 1; hacerlo sin la lista
    cerrada de obras es volver al problema que F-002 vino a cerrar (el
    codigo inventado 0937).
    """
    instructions = _instructions_fase2("albaran_revision_fase2_es")

    assert "{obras_activas}" not in instructions
    assert "0937 — RESIDENCIAL LOS OLMOS" in instructions
    assert "1042 — NAVE INDUSTRIAL RUESMA" in instructions


def test_f002_r2_sin_lista_de_obras_fase2_sigue_sin_marcador_colgante():
    """Lista NO disponible: el marcador se sustituye igual, por la nota.

    R2 de F-002: que la lista falte degrada la extraccion, no la impide.
    Lo que no puede ocurrir es que el hueco se lo coma el literal.
    """
    instructions = _instructions_fase2(
        "albaran_revision_fase2_es", obras=False,
    )

    assert "{obras_activas}" not in instructions
    assert "Lista de obras no disponible" in instructions
