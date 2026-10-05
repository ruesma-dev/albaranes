# tests/test_f051_prompt_partida.py
"""F-051 · IA1 decide a qué líneas va cada partida (solo prompt).

Regla del humano (2026-09-29, concretada el 2026-10-02): «si hay una
partida en el documento esta aplica a todas las lineas, si hay partidas
por linea, en general aplica a las que esten marcadas». Lo decide IA1
leyendo el papel, nunca una regla aguas abajo: por eso F-051 solo cambia
la sección «## Código de imputación manuscrito» de ``config/prompts.yaml``
(``albaran_factura_es``). La viñeta del «código único se aplica a todas»
—la que hacía copiar «03.02» a las tres líneas— se SUSTITUYE por las
cuatro viñetas literales de ``specs/F-051-almacen-por-linea/design.md``.

Aquí se comprueba lo único que se puede comprobar sin LLM: que el texto
real del YAML dice eso (R25, R26, R29, R30) y que llega a las
instructions de fase 1 y de los cuatro prompts de fase 2 por
``{prompt_fase_1}``, sin copia propia (R27). Que la IA acierte con ese
texto lo miden las evals (T21) y la verificación MANUAL (T23).

Sin red ni LLM: el cliente de visión es un doble que captura las
instructions (patrón de ``test_f043_prompt_fase1.py`` y ``_fase2.py``).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from ruesma_comun.contratos import familias as cat

from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from infrastructure.prompts.revision_rules_repository import (
    RevisionRulesRepository,
)
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"

# ------------------------------------------------------------------ #
# Texto exacto de design.md (sv2). Se compara con los espacios
# colapsados: el YAML es un escalar plegado y parte las frases en líneas.
# ------------------------------------------------------------------ #
VINETA_1_CODIGO_DE_LINEA = (
    "Un código escrito junto a una línea, o que agrupa varias, se aplica "
    "SOLO a esas líneas, aunque sea el único código del documento."
)
VINETA_2_CODIGO_DE_DOCUMENTO = (
    "Un código de documento (en la cabecera, un sello o el margen superior "
    "o inferior, sin estar junto a ninguna línea) se aplica a todas las "
    "líneas que no tengan uno propio. Si además hay códigos junto a algunas "
    "líneas, esas llevan el suyo y las demás el de documento."
)
VINETA_3_COMPLEMENTOS = (
    "Portes, bombeo, recargos, excesos y demás complementos sin código "
    "propio llevan el de la línea base a la que acompañan."
)
VINETA_4_SIN_CODIGO_NULL = (
    "Una línea sin código propio, que no sea complemento de otra, en un "
    "documento sin código de documento, se devuelve con codigo_imputacion "
    "null: NO le copies el de otra línea. Esa línea irá a almacén (sin "
    "partida). Ejemplo: tres líneas y 03.02 escrito solo junto a la "
    "segunda ⇒ la segunda lleva 03.02; la primera y la tercera, null."
)
VINETAS_NUEVAS = (
    VINETA_1_CODIGO_DE_LINEA,
    VINETA_2_CODIGO_DE_DOCUMENTO,
    VINETA_3_COMPLEMENTOS,
    VINETA_4_SIN_CODIGO_NULL,
)
#: La viñeta que F-051 sustituye (copiaba el código de una línea a todas).
VINETA_VIEJA = (
    "Si solo hay un código claro en todo el documento, se aplica a "
    "todas las líneas."
)
#: Lo que IA1 ya hacía bien y no puede perderse (R26).
REGLAS_QUE_SIGUEN = (
    "Puede estar asociado a una línea por cercanía, raya, flecha o llave.",
    "Formatos válidos: XX.XX, XX.XX.XX, XX.X.X, CI.XX.XX y variantes con "
    "más segmentos.",
    "Cuando un segmento numérico tenga un solo dígito, normalízalo con "
    "cero a la izquierda.",
    "Si no puede asociarse con claridad, devuelve null.",
    "Revisa la parte superior e inferior, pueden estar escritos allí y "
    "aplicar a todo el documento.",
    "Si hay varios escritos en los márgenes sin relación clara con una "
    "línea, aplica solo el primero a todo el documento.",
)
MISMO_VERTIDO = (
    "Todas las líneas derivadas de un mismo vertido o servicio deben "
    "compartir el mismo `codigo_imputacion`."
)


def _plano(texto: str) -> str:
    """Colapsa cualquier secuencia de espacios o saltos en un espacio."""
    return re.sub(r"\s+", " ", texto)


def _prompts() -> dict:
    return yaml.safe_load(PROMPTS_REALES.read_text(encoding="utf-8"))


def _task_fase_1() -> str:
    return _plano(_prompts()[CLAVE_FASE_1]["task"])


def _seccion_imputacion() -> str:
    """La sección «## Código de imputación manuscrito» del task."""
    task = _task_fase_1()
    inicio = task.index("## Código de imputación manuscrito")
    fin = task.index("## Clasificación del albarán", inicio)
    return task[inicio:fin]


class ClienteEspia:
    """Doble de ``LlmVisionClient``: guarda las instructions recibidas."""

    def __init__(self) -> None:
        self.instructions: str | None = None

    def extract_document(
        self, *, model, instructions, user_text, attachments, response_model,
    ):
        self.instructions = instructions
        return DocumentoAlbaran(cabecera={}, lineas=[])


def _servicio(cliente: ClienteEspia) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[
            ProviderClientSpec(
                provider="gemini", model_name="fake-model", client=cliente,
            ),
        ],
        prompt_repo=YamlPromptRepository(yaml_path=PROMPTS_REALES),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
        obras_activas_provider=None,
    )


def _instructions_fase_1() -> str:
    cliente = ClienteEspia()
    _servicio(cliente).extract_phase_1(
        attachments=[], provider="gemini", prompt_key=CLAVE_FASE_1,
    )
    return _plano(cliente.instructions or "")


def _claves_fase2() -> tuple[str, ...]:
    """El genérico y los de familia que enruta el catálogo (R27)."""
    claves = {"albaran_revision_fase2_es"}
    for id_familia in cat.familias_documento():
        clave = cat.prompt_fase2_de(id_familia)
        if clave:
            claves.add(clave)
    return tuple(sorted(claves))


def _instructions_fase_2(clave: str) -> str:
    cliente = ClienteEspia()
    _servicio(cliente).review_phase_2(
        attachments=[],
        provider="gemini",
        prompt_key=clave,
        phase_1_json={"cabecera": {}, "lineas": []},
        sigrid_context=None,
    )
    return _plano(cliente.instructions or "")


# ------------------------------------------------------------------ #
# R25 · código de línea solo a sus líneas; sin código ⇒ null
# ------------------------------------------------------------------ #
def test_f051_r25_codigo_de_linea_solo_a_sus_lineas() -> None:
    assert VINETA_1_CODIGO_DE_LINEA in _seccion_imputacion()


def test_f051_r25_linea_sin_codigo_sale_null_con_el_ejemplo_03_02() -> None:
    seccion = _seccion_imputacion()

    assert VINETA_4_SIN_CODIGO_NULL in seccion
    assert "irá a almacén" in seccion


def test_f051_r25_las_cuatro_vinetas_van_tras_la_de_cercania_y_en_orden() -> None:
    """Sustituyen a la vieja en su sitio, tras «cercanía, raya, flecha o
    llave», y en el orden de design.md."""
    seccion = _seccion_imputacion()
    posiciones = [seccion.index(v) for v in VINETAS_NUEVAS]

    assert posiciones == sorted(posiciones)
    assert seccion.index(REGLAS_QUE_SIGUEN[0]) < posiciones[0]
    # Justo detrás: entre la de cercanía y la primera nueva no hay nada más.
    fin_cercania = seccion.index(REGLAS_QUE_SIGUEN[0]) + len(
        REGLAS_QUE_SIGUEN[0],
    )
    assert seccion[fin_cercania:posiciones[0]].strip() == "-"


# ------------------------------------------------------------------ #
# R30 · código de documento + códigos de línea (D9)
# ------------------------------------------------------------------ #
def test_f051_r30_codigo_de_documento_y_codigos_de_linea() -> None:
    assert VINETA_2_CODIGO_DE_DOCUMENTO in _seccion_imputacion()


# ------------------------------------------------------------------ #
# R29 · complementos sin código siguen a su base (excepción (c))
# ------------------------------------------------------------------ #
def test_f051_r29_complementos_llevan_el_codigo_de_su_base() -> None:
    assert VINETA_3_COMPLEMENTOS in _seccion_imputacion()


# ------------------------------------------------------------------ #
# R26 · regresión: lo que IA1 ya hacía bien sigue; la viñeta vieja no
# ------------------------------------------------------------------ #
def test_f051_r26_la_vineta_del_codigo_unico_ya_no_esta() -> None:
    assert VINETA_VIEJA not in _task_fase_1()
    assert VINETA_VIEJA not in _instructions_fase_1()


@pytest.mark.parametrize("regla", REGLAS_QUE_SIGUEN)
def test_f051_r26_siguen_las_reglas_de_asociacion_y_margenes(regla) -> None:
    assert regla in _seccion_imputacion()


def test_f051_r26_sigue_mismo_vertido_o_servicio_mismo_codigo() -> None:
    assert MISMO_VERTIDO in _instructions_fase_1()


def test_f051_r26_fase_1_entrega_las_cuatro_vinetas_al_modelo() -> None:
    instructions = _instructions_fase_1()

    for vineta in VINETAS_NUEVAS:
        assert vineta in instructions


# ------------------------------------------------------------------ #
# R27 · fase 2 las recibe por {prompt_fase_1}, sin copia propia
# ------------------------------------------------------------------ #
def test_f051_r27_hay_cuatro_prompts_de_fase_2() -> None:
    assert len(_claves_fase2()) == 4


@pytest.mark.parametrize("clave", _claves_fase2())
def test_f051_r27_fase_2_recibe_las_vinetas_una_sola_vez(clave) -> None:
    instructions = _instructions_fase_2(clave)

    for vineta in VINETAS_NUEVAS:
        assert instructions.count(vineta) == 1, (clave, vineta[:40])
    assert VINETA_VIEJA not in instructions


@pytest.mark.parametrize("clave", _claves_fase2())
def test_f051_r27_fase_2_no_lleva_copia_propia_de_las_vinetas(clave) -> None:
    task = _plano(_prompts()[clave]["task"])

    assert "{prompt_fase_1}" in task
    for vineta in VINETAS_NUEVAS:
        assert vineta not in task
