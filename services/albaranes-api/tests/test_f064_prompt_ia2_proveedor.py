# tests/test_f064_prompt_ia2_proveedor.py
"""F-064 · R9–R12: IA2 confirma el proveedor; sv2 no filtra.

- R9: regla ``proveedor_emisor`` en ``revision_rules.yaml`` (texto de
  design.md §5): IA2 revisa SIEMPRE nombre y CIF de fase 1 contra el
  documento; si son del cliente o no del emisor, los corrige (o deja el CIF
  null); prevalece sobre el contexto de Sigrid.
- R10: los cuatro prompts de fase 2 reciben la lista (dentro de
  ``{prompt_fase_1}``) y la regla (dentro de ``{revision_rules}``), sin
  marcadores sin sustituir y sin editarlos.
- R11: sin campos nuevos en los schemas que rellena la IA.
- R12: lo que devuelve IA2 llega a sv3 tal cual en el envelope final (la red
  de F-063 lo descarta y deja su motivo, que es la métrica).

Sin red ni LLM: el cliente de visión es un doble que captura las
instructions; el worker se ejerce con dobles de sus puertos.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
import yaml
from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.empresas_cliente import CABECERA_BLOQUE
from application.services.phase_merge import construir_envelope_final
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import (
    CabeceraAlbaran,
    DocumentoAlbaran,
    LineaAlbaran,
)
from domain.models.revision_models import Razonamiento, RevisionAlbaranFase2
from infrastructure.prompts.revision_rules_repository import (
    RevisionRulesRepository,
)
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from interface_adapters.worker.extraction_worker import construir_handler_extraccion
from interface_adapters.worker.ports import DocumentoPdf
from ruesma_comun.colas import COLA_PERSISTENCIA, MensajeExtraccion
from ruesma_comun.contratos import familias as cat
from ruesma_comun.contratos.origen_datos import OrigenDatos

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"
ID_REGLA = "proveedor_emisor"
CIF_CLIENTE = "A81873903"
LINEA_CLIENTE = f"  - {CIF_CLIENTE} — Construcciones Ruesma"


def _claves_fase_2() -> tuple[str, ...]:
    """El genérico y los de familia que enruta el catálogo."""
    claves = {"albaran_revision_fase2_es"}
    for id_familia in cat.familias_documento():
        clave = cat.prompt_fase2_de(id_familia)
        if clave:
            claves.add(clave)
    return tuple(sorted(claves))


CLAVES_FASE_2 = _claves_fase_2()

#: Frases clave de design.md §5 (espacios colapsados).
FRASES_REGLA = (
    "Confirma SIEMPRE el proveedor de la fase 1, sea cual sea la familia del "
    "albarán: compara cabecera.proveedor_nombre y cabecera.proveedor_cif con "
    "el documento.",
    "El proveedor es la empresa que EMITE el albarán: su membrete, su bloque "
    "fiscal o el pie con la inscripción en el Registro Mercantil.",
    "Las EMPRESAS DEL CLIENTE que listan las reglas de la fase 1 somos "
    "nosotros y nunca son el proveedor.",
    "Esta regla prevalece sobre cualquier otra de la cabecera, también sobre "
    "el contexto del ERP Sigrid aunque dé ese CIF por validado.",
    "Si el nombre o el CIF de fase 1 son de una empresa del cliente, o no son "
    "los del emisor, corrígelos con los del emisor leídos en el documento.",
    "Si el CIF del emisor no aparece, deja proveedor_cif en null: el sistema "
    "buscará el proveedor por su nombre.",
    "Si son correctos, cópialos tal cual y no añadas razonamiento.",
    'Cada cambio lleva su razonamiento con campo "cabecera.proveedor_cif" o '
    '"cabecera.proveedor_nombre" y patron_aplicado "proveedor_emisor".',
)
TITULO_REGLA = "El proveedor es el EMISOR del albarán, nunca una empresa del cliente"

#: Cualquier marcador conocido de fase 1 o de fase 2 sin sustituir.
_MARCADORES = re.compile(
    r"\{(?:prompt_fase_1|revision_rules|json_fase_1|sigrid_context|"
    r"obras_activas|catalogo_familias|contexto_correo|empresas_cliente)\}"
)


def _plano(texto: str) -> str:
    return re.sub(r"\s+", " ", texto)


def _regla_cruda() -> dict:
    reglas = yaml.safe_load(REGLAS_REALES.read_text(encoding="utf-8"))["reglas"]
    return next(regla for regla in reglas if regla["id"] == ID_REGLA)


class ClienteEspia:
    """Doble de ``LlmVisionClient``: guarda las instructions recibidas."""

    def __init__(self) -> None:
        self.instructions: str | None = None

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        self.instructions = instructions
        documento = DocumentoAlbaran(cabecera={}, lineas=[])
        if response_model is RevisionAlbaranFase2:
            return RevisionAlbaranFase2(review_status="ok", documento_revisado=documento, razonamientos=[])
        return documento


def _servicio(cliente: ClienteEspia) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente)],
        prompt_repo=YamlPromptRepository(yaml_path=PROMPTS_REALES),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
        obras_activas_provider=None,
    )


def _instructions_fase_2(clave: str, sigrid_context: dict | None = None) -> str:
    cliente = ClienteEspia()
    _servicio(cliente).review_phase_2(
        attachments=[],
        provider="gemini",
        prompt_key=clave,
        phase_1_json={"cabecera": {"proveedor_cif": CIF_CLIENTE}, "lineas": []},
        sigrid_context=sigrid_context,
    )
    return cliente.instructions or ""


# ------------------------------------------------------------------ #
# R9 · la regla proveedor_emisor
# ------------------------------------------------------------------ #
def test_f064_r9_la_regla_se_carga_tras_las_existentes() -> None:
    ids = RevisionRulesRepository(yaml_path=REGLAS_REALES).rule_ids

    assert ids == ["importe_minimo", "unidad_medida_camion", ID_REGLA]


def test_f064_r9_titulo_y_texto_de_la_regla() -> None:
    regla = _regla_cruda()
    descripcion = _plano(regla["descripcion"])

    assert regla["titulo"] == TITULO_REGLA
    for frase in FRASES_REGLA:
        assert frase in descripcion, frase[:50]


def test_f064_r9_el_ejemplo_es_el_caso_feymaco() -> None:
    ejemplo = _plano(_regla_cruda()["ejemplo"])

    assert "C.I.F. A-28/733558» ⇒ proveedor_cif \"A28733558\"" in ejemplo
    assert "el CIF de fase 1 es del cliente; el del emisor está en el pie" in ejemplo
    assert CIF_CLIENTE not in ejemplo


def test_f064_r9_la_regla_llega_renderizada_a_la_checklist() -> None:
    texto = _plano(RevisionRulesRepository(yaml_path=REGLAS_REALES).render_for_prompt())

    assert f"3. {TITULO_REGLA} *(id: `{ID_REGLA}`)*" in texto
    for frase in FRASES_REGLA:
        assert frase in texto, frase[:50]


# ------------------------------------------------------------------ #
# R10 · lista y regla en los cuatro prompts de fase 2
# ------------------------------------------------------------------ #
def test_f064_r10_hay_cuatro_prompts_de_fase_2() -> None:
    assert len(CLAVES_FASE_2) == 4


@pytest.mark.parametrize("clave", CLAVES_FASE_2)
def test_f064_r10_fase_2_recibe_la_lista_y_la_regla(clave) -> None:
    instructions = _instructions_fase_2(clave)
    plano = _plano(instructions)

    assert instructions.count(CABECERA_BLOQUE) == 1
    assert LINEA_CLIENTE in instructions
    assert plano.count(FRASES_REGLA[0]) == 1
    assert _MARCADORES.search(instructions) is None


@pytest.mark.parametrize("clave", CLAVES_FASE_2)
def test_f064_r10_la_lista_va_en_el_prompt_de_fase_1_y_la_regla_en_la_checklist(clave) -> None:
    """La lista llega por ``{prompt_fase_1}`` y la regla por
    ``{revision_rules}``: los prompts de fase 2 no llevan copia propia."""
    task = yaml.safe_load(PROMPTS_REALES.read_text(encoding="utf-8"))[clave]["task"]

    assert "{prompt_fase_1}" in task and "{revision_rules}" in task
    assert "empresas_cliente" not in task
    assert ID_REGLA not in task
    assert CABECERA_BLOQUE not in task


@pytest.mark.parametrize("clave", CLAVES_FASE_2)
def test_f064_r10_con_contexto_de_sigrid_la_regla_sigue(clave) -> None:
    """Con grounding (aunque «valide» el CIF del cliente) la regla que
    prevalece sigue en las instructions."""
    contexto = {"proveedor": {"status": "validated", "cif": CIF_CLIENTE, "nombre_canonico": "CNES. DEMO"}}

    plano = _plano(_instructions_fase_2(clave, sigrid_context=contexto))

    assert FRASES_REGLA[3] in plano
    assert _MARCADORES.search(plano) is None


# ------------------------------------------------------------------ #
# R11 · sin campos nuevos
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("modelo", "campos"),
    [
        (CabeceraAlbaran, [
            "proveedor_nombre", "proveedor_cif", "fecha", "numero_albaran",
            "forma_pago", "obra_codigo", "obra_nombre", "obra_direccion", "id",
        ]),
        (DocumentoAlbaran, ["cabecera", "lineas", "clasificacion", "lectura_correo"]),
        (LineaAlbaran, [
            "id", "cabecera_id", "codigo", "cantidad", "concepto", "precio",
            "descuento", "precio_neto", "codigo_imputacion", "confianza_pct",
            "contexto_linea",
        ]),
        (RevisionAlbaranFase2, ["review_status", "explicacion_global", "documento_revisado", "razonamientos"]),
        (Razonamiento, ["campo", "descripcion", "patron_aplicado"]),
        (OrigenDatos, ["version", "correo_presente", "correo_sha256", "correo_truncado", "evidencia", "obra"]),
    ],
    ids=lambda valor: getattr(valor, "__name__", ""),
)
def test_f064_r11_los_schemas_no_cambian(modelo, campos) -> None:
    assert list(modelo.model_fields) == campos


# ------------------------------------------------------------------ #
# R12 · sv2 no filtra el CIF del cliente
# ------------------------------------------------------------------ #
def _env_fase_2(cif: str | None) -> dict:
    documento = {"cabecera": {"proveedor_nombre": "CNES. DEMO", "proveedor_cif": cif}, "lineas": []}
    return {
        "meta": {"phase": "phase_2"},
        "data": {
            "review_status": "ok",
            "documento_revisado": documento,
            "razonamientos": [],
        },
        "debug": {},
    }


def test_f064_r12_el_envelope_final_lleva_el_cif_que_devuelve_ia2_tal_cual() -> None:
    final = construir_envelope_final(
        env_fase1={"meta": {}, "data": {"cabecera": {}, "lineas": []}, "debug": {}},
        env_fase2=_env_fase_2(CIF_CLIENTE),
    )

    assert final["data"]["cabecera"]["proveedor_cif"] == CIF_CLIENTE
    assert final["data"]["cabecera"]["proveedor_nombre"] == "CNES. DEMO"


class _PipelineDoble:
    def run_phase_1(self, request):
        return {"meta": {"phase": "phase_1"}, "data": {"cabecera": {}, "lineas": []}, "debug": {}}

    def run_phase_2(self, request):
        return _env_fase_2(CIF_CLIENTE)


class _Fuente:
    def obtener(self, document_id):
        return DocumentoPdf(filename="a.pdf", mime_type="application/pdf", file_bytes=b"%PDF-")


class _Grounding:
    def contexto(self, *, document_id, phase_1_json):
        return None


class _Sumidero:
    def __init__(self) -> None:
        self.guardados: list[tuple[str, dict]] = []

    def persistir(self, *, document_id, envelope, fase) -> None:
        self.guardados.append((fase, envelope))


class _Publicador:
    def __init__(self) -> None:
        self.publicados: list = []

    def publicar(self, cola, mensaje) -> None:
        self.publicados.append((cola, mensaje))


def test_f064_r12_el_worker_publica_el_cif_del_cliente_sin_tocarlo() -> None:
    """Extremo a extremo de sv2: lo que IA2 deja en la cabecera es lo que se
    guarda como envelope final y se anuncia a sv3 (F-063 lo descarta allí)."""
    sumidero, publicador = _Sumidero(), _Publicador()
    handler = construir_handler_extraccion(
        pipeline=_PipelineDoble(), fuente=_Fuente(), grounding=_Grounding(),
        sumidero=sumidero, publicador=publicador,
    )

    handler(MensajeExtraccion(document_id="doc-f064", correlation_key="c-1"))

    fase, final = sumidero.guardados[-1]
    assert fase == "phase_1"
    assert final["data"]["cabecera"]["proveedor_cif"] == CIF_CLIENTE
    assert publicador.publicados[0][0] == COLA_PERSISTENCIA


def test_f064_r12_ningun_modulo_de_sv2_salvo_el_bloque_importa_la_lista_propia() -> None:
    """Sin ``if`` determinista: solo ``empresas_cliente.py`` (que pinta el
    bloque del prompt) importa ``ruesma_comun.proveedores``."""
    importadores = set()
    for ruta in RAIZ.rglob("*.py"):
        relativa = ruta.relative_to(RAIZ)
        if "tests" in relativa.parts or ".venv" in relativa.parts:
            continue
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
            modulo = getattr(nodo, "module", None) if isinstance(nodo, ast.ImportFrom) else None
            nombres = [a.name for a in nodo.names] if isinstance(nodo, ast.Import) else []
            if (modulo or "").startswith("ruesma_comun.proveedores") or any(
                n.startswith("ruesma_comun.proveedores") for n in nombres
            ):
                importadores.add(relativa.as_posix())

    assert importadores == {"application/services/empresas_cliente.py"}
