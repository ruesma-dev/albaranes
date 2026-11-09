# tests/test_f112_render_prompt.py
"""F-112 · R6–R11 y R17 (parte de código): la referencia llega a IA1 y a IA2.

- ``_render_task_fase_1`` sustituye ``{fecha_recepcion}`` ANTES que el correo
  (un correo que escriba el literal lo conserva) y, sin marcador, no añade
  nada (la variante ``base`` del comparador sale byte a byte como hoy).
- ``extract_phase_1`` y ``review_phase_2`` aceptan ``fecha_recepcion``: el
  task de IA1 y el ``{prompt_fase_1}`` de IA2 llevan el MISMO bloque.
- ``{revision_fecha}`` se rellena en la pasada única de fase 2 (F-048 R14).
- Los logs de las dos fases dicen ``fecha_recepcion=AAAA-MM-DD`` o ``=NO``.
- sv2 no toca la ``cabecera.fecha`` que devuelve la IA.

Sin red ni LLM: el cliente de visión es un doble que captura las
instructions y devuelve una respuesta fija.
"""
from __future__ import annotations

from datetime import date

import pytest
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
from domain.models.revision_models import RevisionAlbaranFase2
from domain.ports.prompt_repository import PromptRepository, PromptSpec
from ruesma_comun.correo import construir_contexto_correo, render_bloque_correo

FECHA = date(2026, 10, 28)
CLAVE_FASE_1 = "fase1"
CLAVE_FASE_2 = "fase2"
TASK_F1 = "## Cabecera\n\n- fecha: del papel.\n\n  {fecha_recepcion}\n\n## Correo\n\n{contexto_correo}\n\nfin"
TASK_F1_SIN_MARCADOR = "## Cabecera\n\n- fecha: la del albarán.\n\n## Correo\n\n{contexto_correo}\n\nfin"
TASK_F2 = (
    "PROMPT1:\n{prompt_fase_1}\n\nREGLAS:\n{revision_rules}\n\n"
    "## Fecha del albarán (revisión obligatoria)\n\n{revision_fecha}\n\n"
    "JSON:\n{json_fase_1}\n\nSIGRID:\n{sigrid_context}\nFIN"
)
CORREO = construir_contexto_correo("Albarán", "Cuerpo del correo sin trampas.")
FECHA_IA = "2019-03-07"  # a más de un año de la referencia: sv2 no la toca (R11)


class ClienteEspia:
    """Doble de ``LlmVisionClient``: guarda las instructions y responde fijo."""

    def __init__(self) -> None:
        self.instructions: list[str] = []

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        self.instructions.append(instructions)
        documento = {"cabecera": {"fecha": FECHA_IA}, "lineas": []}
        if response_model is RevisionAlbaranFase2:
            return RevisionAlbaranFase2.model_validate(
                {"review_status": "ok", "documento_revisado": documento, "razonamientos": []}
            )
        return DocumentoAlbaran.model_validate(documento)


class RepoFake(PromptRepository):
    def __init__(self, task_f1: str = TASK_F1, task_f2: str = TASK_F2) -> None:
        self._specs = {
            CLAVE_FASE_1: PromptSpec(system="S1", task=task_f1, schema_hint="H1", schema="documento_albaran"),
            CLAVE_FASE_2: PromptSpec(system="S2", task=task_f2, schema_hint="H2", schema="revision_albaran_fase2"),
        }

    def get(self, prompt_key: str) -> PromptSpec:
        return self._specs[prompt_key]

    def has(self, prompt_key: str) -> bool:
        return prompt_key in self._specs


class _ReglasFake:
    count = 1
    rule_ids: tuple[str, ...] = ("r1",)

    def render_for_prompt(self) -> str:
        return "REGLAS-FAKE"


def _servicio(cliente: ClienteEspia, repo: RepoFake | None = None) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente)],
        prompt_repo=repo or RepoFake(),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=_ReglasFake(),
        prompt_key_phase_1=CLAVE_FASE_1,
        empresas_cliente=(),
    )


def _render(task: str, correo=None, fecha=None) -> str:
    renderizado, _obras = _servicio(ClienteEspia())._render_task_fase_1(task, correo, fecha)
    return renderizado


def _fase1(fecha=None, correo=None, repo=None):
    cliente = ClienteEspia()
    resultado = _servicio(cliente, repo).extract_phase_1(
        attachments=[], provider="gemini", prompt_key=CLAVE_FASE_1,
        contexto_correo=correo, fecha_recepcion=fecha,
    )
    return cliente.instructions[-1], resultado


def _fase2(fecha=None, correo=None, repo=None, phase_1_json=None):
    cliente = ClienteEspia()
    resultado = _servicio(cliente, repo).review_phase_2(
        attachments=[], provider="gemini", prompt_key=CLAVE_FASE_2,
        phase_1_json=phase_1_json or {"cabecera": {"fecha": FECHA_IA}, "lineas": []},
        contexto_correo=correo, fecha_recepcion=fecha,
    )
    return cliente.instructions[-1], resultado


# ---------------------------------------------------------------- #
# R6 · el marcador se sustituye en su sitio.
# ---------------------------------------------------------------- #
def test_f112_r6_con_fecha_el_marcador_se_sustituye_por_el_bloque():
    renderizado = _render(TASK_F1, fecha=FECHA)

    assert "{fecha_recepcion}" not in renderizado
    assert render_fecha_recepcion(FECHA) in renderizado
    assert renderizado.index("- fecha:") < renderizado.index("FECHA DE RECEPCIÓN") < renderizado.index("## Correo")


def test_f112_r6_sin_fecha_el_marcador_se_sustituye_por_la_nota():
    renderizado = _render(TASK_F1, fecha=None)

    assert "{fecha_recepcion}" not in renderizado
    assert NOTA_SIN_RECEPCION in renderizado
    assert "FECHA DE RECEPCIÓN" not in renderizado


# ---------------------------------------------------------------- #
# R7 · antes que el correo: el literal del correo queda intacto.
# ---------------------------------------------------------------- #
def test_f112_r7_un_correo_con_el_literal_lo_conserva():
    tramposo = construir_contexto_correo("Albarán", "Texto con {fecha_recepcion} dentro.")

    renderizado = _render(TASK_F1, correo=tramposo, fecha=FECHA)

    assert render_bloque_correo(tramposo) in renderizado
    assert "Texto con {fecha_recepcion} dentro." in renderizado
    assert renderizado.count("FECHA DE RECEPCIÓN DEL CORREO") == 1


# ---------------------------------------------------------------- #
# R8 · sin marcador no se añade nada.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("correo", [None, CORREO], ids=["sin_correo", "con_correo"])
def test_f112_r8_sin_marcador_el_task_sale_identico(correo):
    con_fecha = _render(TASK_F1_SIN_MARCADOR, correo=correo, fecha=FECHA)
    sin_fecha = _render(TASK_F1_SIN_MARCADOR, correo=correo, fecha=None)

    assert con_fecha == sin_fecha
    assert "FECHA DE RECEPCIÓN" not in con_fecha and NOTA_SIN_RECEPCION not in con_fecha


def test_f112_r8_el_argumento_es_opcional():
    """Sin pasar la fecha, como hoy: los llamantes de antes siguen valiendo."""
    servicio = _servicio(ClienteEspia())
    renderizado, _ = servicio._render_task_fase_1(TASK_F1, None)
    assert NOTA_SIN_RECEPCION in renderizado


# ---------------------------------------------------------------- #
# R9 · el MISMO bloque en IA1 y dentro de {prompt_fase_1} de IA2.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("fecha", [FECHA, None], ids=["con_fecha", "sin_fecha"])
def test_f112_r9_ia1_e_ia2_reciben_el_mismo_bloque(fecha):
    ia1, _ = _fase1(fecha=fecha, correo=CORREO)
    ia2, _ = _fase2(fecha=fecha, correo=CORREO)

    bloque = render_fecha_recepcion(fecha)
    assert bloque in ia1
    assert bloque in ia2
    # {prompt_fase_1} lleva el task de IA1 tal cual lo vio IA1.
    prompt_fase_1 = ia2[ia2.index("PROMPT1:\n") + len("PROMPT1:\n"): ia2.index("\n\nREGLAS:")]
    assert prompt_fase_1 == ia1


def test_f112_r9_con_fecha_distinta_ia2_lleva_la_suya():
    ia2, _ = _fase2(fecha=date(2027, 1, 3))
    assert "FECHA DE RECEPCIÓN DEL CORREO: 2027-01-03." in ia2
    assert "2026-10-28" not in ia2


# ---------------------------------------------------------------- #
# R17 (código) · {revision_fecha} en la pasada única de fase 2.
# ---------------------------------------------------------------- #
def test_f112_r17_con_fecha_revision_fecha_lleva_el_bloque_de_revision():
    ia2, _ = _fase2(fecha=FECHA)

    assert "{revision_fecha}" not in ia2
    seccion = ia2[ia2.index("(revisión obligatoria)"): ia2.index("JSON:")]
    assert render_revision_fecha(FECHA) in seccion


def test_f112_r17_sin_fecha_revision_fecha_lleva_la_nota():
    ia2, _ = _fase2(fecha=None)

    assert "{revision_fecha}" not in ia2
    seccion = ia2[ia2.index("(revisión obligatoria)"): ia2.index("JSON:")]
    assert NOTA_REVISION_SIN_RECEPCION in seccion


def test_f112_r17_lo_insertado_no_se_vuelve_a_recorrer():
    """Un JSON de fase 1 o un correo que escriban el marcador no reciben el bloque."""
    tramposo = construir_contexto_correo("Albarán", "Correo con {revision_fecha}.")
    json_tramposo = {"cabecera": {"fecha": FECHA_IA, "notas": "{revision_fecha}"}, "lineas": []}

    ia2, _ = _fase2(fecha=FECHA, correo=tramposo, phase_1_json=json_tramposo)

    assert "Correo con {revision_fecha}." in ia2
    assert '"notas": "{revision_fecha}"' in ia2
    assert ia2.count("Revisa SIEMPRE cabecera.fecha") == 1


def test_f112_r17_sin_marcador_en_fase_2_no_se_anade_nada():
    repo = RepoFake(task_f2="PROMPT1:\n{prompt_fase_1}\n\nREGLAS:\n{revision_rules}\n\nJSON:\n{json_fase_1}\nFIN")
    ia2, _ = _fase2(fecha=FECHA, repo=repo)
    assert "Revisa SIEMPRE cabecera.fecha" not in ia2
    assert NOTA_REVISION_SIN_RECEPCION not in ia2


# ---------------------------------------------------------------- #
# R10 · logs de las dos fases.
# ---------------------------------------------------------------- #
def test_f112_r10_los_logs_dicen_la_fecha_o_no(caplog):
    with caplog.at_level("INFO"):
        _fase1(fecha=FECHA)
        _fase1(fecha=None)
        _fase2(fecha=FECHA)
        _fase2(fecha=None)

    fase1 = [r.getMessage() for r in caplog.records if "FASE 1" in r.getMessage()]
    fase2 = [r.getMessage() for r in caplog.records if "FASE 2" in r.getMessage()]
    assert "fecha_recepcion=2026-10-28" in fase1[0]
    assert "fecha_recepcion=NO" in fase1[1]
    assert "fecha_recepcion=2026-10-28" in fase2[0]
    assert "fecha_recepcion=NO" in fase2[1]


# ---------------------------------------------------------------- #
# R11 · sv2 no toca la fecha que devuelve la IA.
# ---------------------------------------------------------------- #
def test_f112_r11_la_fecha_de_la_ia_pasa_tal_cual():
    _, r1 = _fase1(fecha=FECHA)
    _, r2 = _fase2(fecha=FECHA)

    assert r1.parsed.model_dump()["cabecera"]["fecha"] == FECHA_IA
    assert r2.parsed.model_dump()["documento_revisado"]["cabecera"]["fecha"] == FECHA_IA
