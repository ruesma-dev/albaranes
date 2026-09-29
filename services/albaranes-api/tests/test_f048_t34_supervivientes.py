# tests/test_f048_t34_supervivientes.py
"""F-048 · T34: los supervivientes de la campaña de mutación que eran huecos reales (sv2).

Cada test nombra el mutante que mata (numeración de
``progress/mutacion_F-048.md``) y el requisito que lo pide. El análisis de
los 26 está en ``progress/impl_F-048_T34_supervivientes.md``.

Sin red, sin BBDD y sin LLM. Textos inventados, con ``CENTINELA-F048``.
"""
from __future__ import annotations

import json
from pathlib import Path

import encolar_extraccion
import pytest
from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.origen_datos_resolver import sellar_origen_datos
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from domain.ports.obras_activas_provider import ObraActiva
from domain.ports.prompt_repository import PromptSpec
from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from ruesma_comun.correo import construir_contexto_correo

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"
CLAVE_FASE_2 = "albaran_revision_fase2_es"
CENTINELA = "CENTINELA-F048"

CORREO = construir_contexto_correo("Obra 0945", f"Os paso los albaranes. {CENTINELA}")
_JSON_FASE_1 = {"cabecera": {"obra_codigo": "0937"}, "lineas": []}
_SIGRID = {"proveedor": {"status": "validated", "cif": "B00000000", "nombre_canonico": "DEMO SL"}}


class _ClienteEspia:
    def __init__(self) -> None:
        self.instructions: list[str] = []

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        self.instructions.append(instructions)
        return DocumentoAlbaran(cabecera={}, lineas=[])


class _ObrasFake:
    def obtener(self) -> list[ObraActiva] | None:
        return [ObraActiva(codigo="0945", nombre="RESIDENCIAL DEMO")]


class _RepoFase2SinSigrid:
    """El YAML real para la fase 1 y un task de fase 2 sin ``{sigrid_context}``."""

    def __init__(self) -> None:
        self._real = YamlPromptRepository(yaml_path=PROMPTS_REALES)

    def get(self, prompt_key: str):
        if prompt_key == CLAVE_FASE_1:
            return self._real.get(prompt_key)
        return PromptSpec(system="S", task="{prompt_fase_1}\n\n{json_fase_1}\nFIN", schema_hint="H",
                          schema="revision_albaran_fase2")


def _fase2(*, sigrid, sin_marcador: bool = False) -> str:
    cliente = _ClienteEspia()
    servicio = AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente)],
        prompt_repo=YamlPromptRepository(yaml_path=PROMPTS_REALES),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
        obras_activas_provider=_ObrasFake(),
    )
    if sin_marcador:
        servicio._prompts = _RepoFase2SinSigrid()
    servicio.review_phase_2(
        attachments=[], provider="gemini", prompt_key="otra" if sin_marcador else CLAVE_FASE_2,
        phase_1_json=_JSON_FASE_1, sigrid_context=sigrid, contexto_correo=CORREO,
    )
    return cliente.instructions[-1]


# ---------------------------------------------------------------- #
# Mutante 1 · albaran_extraction_service.py:454 (``and`` -> ``or``).
# R14: la sustitución de fase 2 es de UNA pasada; el grounding solo se
# añade al final cuando la plantilla no trae su marcador Y hay grounding.
# ---------------------------------------------------------------- #
def test_f048_r14_con_marcador_de_sigrid_el_grounding_sale_una_sola_vez():
    grounding = AlbaranExtractionService._render_sigrid_context(_SIGRID)
    assert "{sigrid_context}" in YamlPromptRepository(yaml_path=PROMPTS_REALES).get(CLAVE_FASE_2).task

    instructions = _fase2(sigrid=_SIGRID)

    assert instructions.count(grounding) == 1
    assert instructions.count("DEMO SL") == 1


def test_f048_r14_sin_marcador_y_sin_grounding_no_se_anade_la_nota():
    nota = AlbaranExtractionService._render_sigrid_context(None)

    instructions = _fase2(sigrid=None, sin_marcador=True)

    assert nota not in instructions
    assert "FIN" in instructions  # control: la plantilla sin marcador es la que se usó


# ---------------------------------------------------------------- #
# Mutante 2 · origen_datos_resolver.py:174 (``cabecera or {}`` ->
# ``cabecera and {}``). R19/R22: el correo cambia SOLO ``obra_codigo``; el
# resto de la cabecera es el de la IA. Sin cabecera, se crea con la obra.
# ---------------------------------------------------------------- #
_OBRAS = {"945": "0945"}
_LECTURA = {"obra_codigos": ["0945"], "evidencia": "Obra 0945"}


def test_f048_r19_el_correo_cambia_la_obra_y_conserva_el_resto_de_la_cabecera():
    cabecera = {"obra_codigo": "0937", "proveedor_nombre": "HORMIGONES DEL SUR", "numero_albaran": "A-1"}
    envelope = {"data": {"cabecera": cabecera, "lineas": []}}

    final = sellar_origen_datos(envelope, lectura=_LECTURA, correo=CORREO, obras_conocidas=_OBRAS)

    assert final["data"]["cabecera"] == {**cabecera, "obra_codigo": "0945"}
    assert cabecera["obra_codigo"] == "0937"  # no muta la entrada


def test_f048_r19_sin_cabecera_el_correo_la_crea_con_la_obra():
    final = sellar_origen_datos(
        {"data": {"lineas": []}}, lectura=_LECTURA, correo=CORREO, obras_conocidas=_OBRAS,
    )

    assert final["data"]["cabecera"] == {"obra_codigo": "0945"}


# ---------------------------------------------------------------- #
# Mutantes 3 y 4 · encolar_extraccion.py:57 y :88 (R42).
# ---------------------------------------------------------------- #
class _Almacen:
    def __init__(self) -> None:
        self.blobs: dict = {}

    def put_json(self, contenedor, nombre, objeto):
        self.blobs[(contenedor, nombre)] = objeto


class _Publicador:
    def __init__(self) -> None:
        self.publicados: list = []

    def publicar(self, cola, mensaje):
        self.publicados.append((cola, mensaje))


@pytest.fixture
def entorno(monkeypatch):
    almacen, publicador = _Almacen(), _Publicador()
    monkeypatch.setattr(encolar_extraccion, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(encolar_extraccion, "construir_publicador", lambda **k: publicador)
    monkeypatch.setattr(encolar_extraccion, "construir_almacen_desde_entorno", lambda: almacen)
    return almacen, publicador


def test_f048_r42_una_captura_sin_asunto_para_con_error_de_uso(entorno, tmp_path, capsys):
    """Mutante 3: la guarda exige ``asunto`` Y ``cuerpo``; sin asunto no llega a ``datos['asunto']``."""
    almacen, publicador = entorno
    ruta = tmp_path / "sin_asunto.json"
    ruta.write_text(json.dumps({"cuerpo": f"Obra 0945 {CENTINELA}"}), encoding="utf-8")

    with pytest.raises(ValueError, match="faltan 'asunto' y 'cuerpo'"):
        encolar_extraccion.leer_captura(ruta)
    with pytest.raises(SystemExit) as salida:
        encolar_extraccion.main(["DOC-4", "--correo", str(ruta)])

    assert salida.value.code == 2
    assert publicador.publicados == [] and almacen.blobs == {}
    assert CENTINELA not in capsys.readouterr().err


def test_f048_r42_por_pantalla_la_huella_abreviada_son_ocho_caracteres(entorno, tmp_path, capsys):
    """Mutante 4: la huella abreviada es la MISMA en sv1, sv2 y los scripts: 8 hex."""
    ruta = tmp_path / "caso.json"
    ruta.write_text(json.dumps({"asunto": "Obra 0945", "cuerpo": "Os paso los albaranes."}), encoding="utf-8")
    ctx = construir_contexto_correo("Obra 0945", "Os paso los albaranes.")

    encolar_extraccion.main(["DOC-5", "--correo", str(ruta)])

    assert f"(sha={ctx.sha256[:8]} caracteres={ctx.caracteres_originales} " in capsys.readouterr().out
