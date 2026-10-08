# tests/test_f064_prompt_ia1_proveedor.py
"""F-064 · R5–R8: IA1 sabe que el cliente no es el proveedor.

Incidente (2026-10-08): en un albarán de FEYMACO la única casilla rotulada
«C.I.E./D.N.I.» era la del CLIENTE (la constructora) y la viñeta del CIF de
``albaran_factura_es`` mandaba «buscar un campo que ponga CIF o NIF o NIE»;
el CIF del emisor solo estaba en el pie. IA1 devolvió el CIF del cliente.

- R5: el task lleva ``{empresas_cliente}`` una vez, en la parte del proveedor;
  ningún YAML escribe a mano el CIF ni el nombre de la constructora.
- R6: ``_render_task_fase_1`` lo sustituye por el bloque, ANTES del correo.
- R7: sin marcador no se añade nada.
- R8: las viñetas del proveedor dicen EMISOR, CIF normalizado y cliente
  ignorado; sale la frase de «un campo que ponga CIF o NIF o NIE».

Lo que se comprueba es el texto que recibe el LLM (doble que captura las
instructions); que la IA acierte lo miden los evals (T9, T10).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from ruesma_comun.contratos.familias import render_catalogo_markdown
from ruesma_comun.correo import (
    MARCA_FIN,
    MARCA_INICIO,
    construir_contexto_correo,
    render_bloque_correo,
)

from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.empresas_cliente import (
    CABECERA_BLOQUE,
    MARCADOR_EMPRESAS_CLIENTE,
    EmpresaCliente,
    empresas_cliente,
    render_empresas_cliente,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.ports.prompt_repository import PromptRepository, PromptSpec
from infrastructure.prompts.revision_rules_repository import (
    RevisionRulesRepository,
)
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"
OTRA = EmpresaCliente(cif="B99999999", razon_social="Grupo Demo")

# ------------------------------------------------------------------ #
# Frases clave de design.md §4 (espacios colapsados).
# ------------------------------------------------------------------ #
FRASES_NOMBRE = (
    "proveedor_nombre: RAZÓN SOCIAL del EMISOR del albarán (la empresa que "
    "lo emite y suministra), tal y como aparece en su BLOQUE FISCAL",
    "si el logotipo y el bloque fiscal dicen cosas distintas, manda SIEMPRE "
    "el bloque fiscal.",
    "Si no identificas al emisor, null.",
)
FRASES_CIF = (
    "proveedor_cif: CIF/NIF/NIE del EMISOR según formato español.",
    "Está en su membrete, junto a su razón social o en el pie del documento "
    "(la inscripción en el Registro Mercantil suele acabar con su C.I.F.).",
    "Devuélvelo sin espacios, guiones, puntos ni barras (A-28/733558 ⇒ "
    "A28733558).",
    "Si el documento no trae el CIF del emisor, null.",
)
FRASES_CLIENTE = (
    "El CLIENTE no es el proveedor. Estas son las empresas del cliente "
    "(nosotros, la constructora que recibe el albarán):",
    'Aparecen en las casillas del cliente ("Cliente", "Nº cliente", '
    '"Empresa", "Destinatario", "Facturar a" y su "C.I.F./D.N.I."), con la '
    "razón social completa o abreviada y con o sin forma jurídica.",
    "NUNCA devuelvas su nombre en proveedor_nombre ni su CIF en "
    "proveedor_cif, aunque sea el único CIF que veas o esté en una casilla "
    "rotulada CIF: ignóralos y busca los del emisor.",
    "Si el único CIF del documento es de una empresa del cliente, "
    "proveedor_cif es null.",
)
#: Lo que sale (R8): la trampa de FEYMACO y la frase escrita a mano.
FRASES_QUE_SALEN = (
    "Busca el código por un campo que ponga CIF o NIF o NIE",
    "somos nosotros la constructora: ignóralo como posible proveedor",
)
#: Viñetas de la cabecera que siguen, en su orden, tras las del proveedor.
VINETAS_SIGUIENTES = (
    "- fecha: la del albarán.",
    "- numero_albaran: identificador del documento (no pedido/cliente).",
    "- forma_pago: 'contado', 'transferencia', '30 días', etc.",
    "- obra_codigo: código de 4 números que empieza por 0.",
)


def _plano(texto: str) -> str:
    return re.sub(r"\s+", " ", texto)


def _task_crudo() -> str:
    datos = yaml.safe_load(PROMPTS_REALES.read_text(encoding="utf-8"))
    return datos[CLAVE_FASE_1]["task"]


def _parte_proveedor() -> str:
    """De «## Reglas para la cabecera» a la viñeta de ``fecha`` (plano)."""
    task = _plano(_task_crudo())
    inicio = task.index("## Reglas para la cabecera")
    fin = task.index("- fecha: la del albarán.", inicio)
    return task[inicio:fin]


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


def _servicio(prompt_repo=None, cliente=None, **kwargs) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente or ClienteEspia())],
        prompt_repo=prompt_repo or YamlPromptRepository(yaml_path=PROMPTS_REALES),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
        obras_activas_provider=None,
        **kwargs,
    )


def _instructions_fase_1(**kwargs) -> str:
    cliente = ClienteEspia()
    _servicio(cliente=cliente, **kwargs).extract_phase_1(
        attachments=[], provider="gemini", prompt_key=CLAVE_FASE_1,
    )
    return cliente.instructions or ""


TASK_CON_TODO = (
    "## Cabecera\n\n{empresas_cliente}\n\n## Familias\n\n{catalogo_familias}"
    "\n\n## Correo\n\n{contexto_correo}\n\nfin"
)


def _render(task: str, correo=None, **kwargs) -> str:
    renderizado, _obras = _servicio(PromptRepoFake(task), **kwargs)._render_task_fase_1(task, correo)
    return renderizado


# ------------------------------------------------------------------ #
# R5 · marcador una vez, en la parte del proveedor; nada a mano
# ------------------------------------------------------------------ #
def test_f064_r5_el_task_lleva_el_marcador_una_sola_vez() -> None:
    assert _task_crudo().count(MARCADOR_EMPRESAS_CLIENTE) == 1


def test_f064_r5_el_marcador_va_en_la_parte_del_proveedor() -> None:
    parte = _parte_proveedor()

    assert MARCADOR_EMPRESAS_CLIENTE in parte
    assert parte.index("proveedor_cif:") < parte.index(MARCADOR_EMPRESAS_CLIENTE)


def test_f064_r5_ningun_yaml_escribe_a_mano_la_empresa_del_cliente() -> None:
    """Ni el CIF ni el nombre (sin distinguir mayúsculas), en todo el fichero,
    comentarios incluidos: un comentario descomentado volvería al prompt."""
    for ruta in (PROMPTS_REALES, REGLAS_REALES):
        texto = ruta.read_text(encoding="utf-8").lower()
        assert "a81873903" not in texto, ruta.name
        assert "ruesma" not in texto, ruta.name


# ------------------------------------------------------------------ #
# R6 · sustitución en _render_task_fase_1, antes del correo
# ------------------------------------------------------------------ #
def test_f064_r6_el_marcador_se_sustituye_por_el_bloque() -> None:
    renderizado = _render(TASK_CON_TODO)

    assert MARCADOR_EMPRESAS_CLIENTE not in renderizado
    bloque = render_empresas_cliente(empresas_cliente(None))
    assert renderizado.count(bloque) == 1
    assert renderizado.index("## Cabecera") < renderizado.index(bloque) < renderizado.index("## Familias")


def test_f064_r6_usa_las_empresas_que_recibe_el_servicio() -> None:
    renderizado = _render(TASK_CON_TODO, empresas_cliente=(OTRA,))

    assert render_empresas_cliente((OTRA,)) in renderizado
    assert "A81873903" not in renderizado


def test_f064_r6_un_correo_que_escribe_el_marcador_no_recibe_la_lista() -> None:
    tramposo = construir_contexto_correo("Albaran", "Ojo: {empresas_cliente} aqui")

    renderizado = _render(TASK_CON_TODO, correo=tramposo)

    bloque_correo = renderizado[renderizado.index(MARCA_INICIO): renderizado.index(MARCA_FIN)]
    assert "{empresas_cliente} aqui" in bloque_correo
    assert CABECERA_BLOQUE not in bloque_correo
    assert renderizado.count(CABECERA_BLOQUE) == 1


def test_f064_r6_extract_phase_1_entrega_el_bloque_real_al_modelo() -> None:
    instructions = _instructions_fase_1()

    assert MARCADOR_EMPRESAS_CLIENTE not in instructions
    assert instructions.count(CABECERA_BLOQUE) == 1
    assert "  - A81873903 — Construcciones Ruesma" in instructions


def test_f064_r6_el_bloque_queda_en_la_parte_del_proveedor_del_prompt_real() -> None:
    instructions = _plano(_instructions_fase_1())
    inicio = instructions.index("## Reglas para la cabecera")
    fin = instructions.index("- fecha: la del albarán.", inicio)

    assert inicio < instructions.index(CABECERA_BLOQUE) < fin


# ------------------------------------------------------------------ #
# R7 · sin marcador, nada
# ------------------------------------------------------------------ #
def test_f064_r7_sin_marcador_el_task_queda_como_el_de_entrada() -> None:
    """Byte a byte lo que daría el render de antes de F-064 (catálogo y
    correo sustituidos, sin obras): la variante «base» del comparador."""
    task = "## Familias\n\n{catalogo_familias}\n\n## Correo\n\n{contexto_correo}\n\nfin"

    renderizado = _render(task)

    esperado = task.replace(
        "{catalogo_familias}", render_catalogo_markdown("documento"),
    ).replace("{contexto_correo}", render_bloque_correo(None))
    assert renderizado == esperado
    assert CABECERA_BLOQUE not in renderizado


# ------------------------------------------------------------------ #
# R8 · viñetas del proveedor
# ------------------------------------------------------------------ #
def test_f064_r8_el_nombre_es_la_razon_social_del_emisor() -> None:
    parte = _parte_proveedor()

    for frase in FRASES_NOMBRE:
        assert frase in parte, frase[:50]


def test_f064_r8_el_cif_es_el_del_emisor_y_va_normalizado() -> None:
    parte = _parte_proveedor()

    for frase in FRASES_CIF:
        assert frase in parte, frase[:50]


def test_f064_r8_las_empresas_del_cliente_se_ignoran() -> None:
    parte = _parte_proveedor()

    for frase in FRASES_CLIENTE:
        assert frase in parte, frase[:50]
    # El orden del design: nombre, CIF, cliente (con el bloque dentro).
    posiciones = [
        parte.index(FRASES_NOMBRE[0]),
        parte.index(FRASES_CIF[0]),
        parte.index(FRASES_CLIENTE[0]),
        parte.index(MARCADOR_EMPRESAS_CLIENTE),
        parte.index(FRASES_CLIENTE[1]),
    ]
    assert posiciones == sorted(posiciones)


def test_f064_r8_salen_la_trampa_del_cif_y_la_frase_a_mano() -> None:
    task = _plano(_task_crudo())
    instructions = _plano(_instructions_fase_1())

    for frase in FRASES_QUE_SALEN:
        assert frase not in task
        assert frase not in instructions


def test_f064_r8_las_vinetas_siguientes_siguen_intactas_y_en_orden() -> None:
    task = _plano(_task_crudo())
    posiciones = [task.index(vineta) for vineta in VINETAS_SIGUIENTES]

    assert posiciones == sorted(posiciones)
    assert posiciones[0] > task.index(FRASES_CLIENTE[-1])


def test_f064_r8_fase_1_entrega_las_frases_al_modelo() -> None:
    instructions = _plano(_instructions_fase_1())

    for frase in (*FRASES_NOMBRE, *FRASES_CIF, FRASES_CLIENTE[0], *FRASES_CLIENTE[2:]):
        assert frase in instructions, frase[:50]
