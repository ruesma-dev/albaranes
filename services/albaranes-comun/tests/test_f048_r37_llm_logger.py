# tests/test_f048_r37_llm_logger.py
"""F-048 · R37 · ``LlmCallLogger`` no escribe el texto del correo a disco.

Con ``LLM_CALL_LOG_DIR`` puesto, el logger guarda ``instructions`` y
``user_text`` ENTEROS: el bloque del correo iria tal cual a un fichero. El
logger aplica ``redactar_correo`` a TODO texto que escribe, a cualquier
profundidad, antes de escribir: la peticion, la RESPUESTA (el ``Response``
de la API Responses de OpenAI repite ``instructions``) y el ERROR. Queda el
resumen (sha256, caracteres) y desaparece el cuerpo.

Escribe en ``tmp_path`` y busca el centinela ``CENTINELA-F048`` en TODO lo
que queda escrito ahi. Sin red.
"""
from __future__ import annotations

import copy
import json

from pydantic import BaseModel
from ruesma_comun.correo import construir_contexto_correo, render_bloque_correo
from ruesma_comun.correo.prompt import ADVERTENCIA_DATO
from ruesma_comun.llm.llm_call_logger import LlmCallLogger

CENTINELA = "CENTINELA-F048"


class _RespuestaSdk(BaseModel):
    """Doble del ``Response`` de OpenAI: como el de verdad, repite ``instructions``."""

    id: str = "resp_1"
    instructions: str
    output_text: str = "{}"


class _Opaco:
    """Objeto que no es JSON: ``json.dumps`` lo escribe con su ``str``."""

    __slots__ = ("texto",)

    def __init__(self, texto: str) -> None:
        self.texto = texto

    def __str__(self) -> str:
        return self.texto


def _todo_lo_escrito(tmp_path) -> str:
    return "".join(
        f.read_text(encoding="utf-8") for f in tmp_path.rglob("*") if f.is_file()
    )


def _bloque():
    ctx = construir_contexto_correo("Albaran obra 1234", f"Obra 1234. {CENTINELA}")
    return ctx, render_bloque_correo(ctx)


def _escribir(tmp_path, request_summary):
    ruta = LlmCallLogger(tmp_path).log_call(
        provider="claude",
        model="modelo-de-prueba",
        request_summary=request_summary,
        response_payload={"ok": True},
        document_id="doc-1",
    )
    assert ruta is not None and ruta.exists()
    return ruta, ruta.read_text(encoding="utf-8")


def test_f048_r37_instructions_y_user_text_sin_el_cuerpo(tmp_path):
    ctx, bloque = _bloque()
    _, texto = _escribir(
        tmp_path,
        {
            "instructions": f"Lee el albaran.\n{bloque}\nDevuelve JSON.",
            "user_text": f"Fase 2. Prompt de fase 1:\n{bloque}",
        },
    )
    assert CENTINELA not in texto
    datos = json.loads(texto)["request"]
    assert datos["instructions"].startswith("Lee el albaran.\n")
    assert f"[correo omitido: sha256={ctx.sha256}, caracteres=" in datos["instructions"]
    assert datos["instructions"].endswith("]\nDevuelve JSON.")
    assert f"sha256={ctx.sha256}" in datos["user_text"]


def test_f048_r37_redacta_a_cualquier_profundidad(tmp_path):
    _, bloque = _bloque()
    _, texto = _escribir(
        tmp_path,
        {
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": bloque}]},
            ],
            "tupla": (bloque, 1),
            "anidado": {"a": {"b": [bloque]}},
        },
    )
    assert CENTINELA not in texto
    assert texto.count("[correo omitido: sha256=") == 3


def test_f048_r37_lo_que_no_es_correo_queda_igual(tmp_path):
    attachment = {"kind": "pdf", "size_bytes": 12, "sha256": "a" * 64}
    resumen = {
        "instructions": "Sin correo. << a >>",
        "temperature": 0.0,
        "max_tokens": 4096,
        "stream": False,
        "nada": None,
        "attachment": attachment,
        "lista": ["x", 2],
    }
    _, texto = _escribir(tmp_path, resumen)
    assert json.loads(texto)["request"] == resumen


def test_f048_r37_no_muta_el_request_summary_del_llamador(tmp_path):
    _, bloque = _bloque()
    resumen = {"instructions": bloque, "lista": [bloque, {"t": bloque}]}
    copia = copy.deepcopy(resumen)
    _escribir(tmp_path, resumen)
    assert resumen == copia


def test_f048_r37_deshabilitado_no_escribe_nada(tmp_path):
    _, bloque = _bloque()
    logger = LlmCallLogger(None)
    assert logger.log_call(
        provider="claude", model="m", request_summary={"instructions": bloque}
    ) is None
    assert list(tmp_path.iterdir()) == []


# ------------------------------------------------------------------ #
# R37 · tambien la respuesta y el error (review del bloque A, pasada 1)
# ------------------------------------------------------------------ #
def test_f048_r37_respuesta_pydantic_con_instructions_sin_el_cuerpo(tmp_path):
    ctx, bloque = _bloque()
    ruta = LlmCallLogger(tmp_path).log_call(
        provider="openai",
        model="modelo-de-prueba",
        request_summary={"instructions": "sin correo"},
        response_payload=_RespuestaSdk(instructions=f"Lee el albaran.\n{bloque}"),
        document_id="doc-1",
    )
    assert ruta is not None
    assert CENTINELA not in _todo_lo_escrito(tmp_path)
    respuesta = json.loads(ruta.read_text(encoding="utf-8"))["response"]
    assert respuesta["id"] == "resp_1"
    assert respuesta["output_text"] == "{}"
    assert respuesta["instructions"].startswith("Lee el albaran.\n")
    assert f"[correo omitido: sha256={ctx.sha256}, caracteres=" in respuesta["instructions"]


def test_f048_r37_bloque_anidado_en_la_respuesta_sin_el_cuerpo(tmp_path):
    ctx, bloque = _bloque()
    ruta = LlmCallLogger(tmp_path).log_call(
        provider="openai",
        model="modelo-de-prueba",
        request_summary={},
        response_payload={
            "raw_sdk_response": {
                "output": [{"content": [{"type": "output_text", "text": bloque}]}],
            },
            "tupla": (bloque, 1),
            "clave": {bloque: 1},
        },
        document_id="doc-1",
    )
    assert ruta is not None
    texto = _todo_lo_escrito(tmp_path)
    assert CENTINELA not in texto
    assert texto.count(f"[correo omitido: sha256={ctx.sha256}, caracteres=") == 3
    respuesta = json.loads(texto)["response"]
    assert respuesta["tupla"][1] == 1
    assert respuesta["raw_sdk_response"]["output"][0]["content"][0]["type"] == "output_text"


def test_f048_r37_error_con_el_bloque_sin_el_cuerpo(tmp_path):
    ctx, bloque = _bloque()
    ruta = LlmCallLogger(tmp_path).log_call(
        provider="openai",
        model="modelo-de-prueba",
        request_summary={},
        error=f"ValueError: no se pudo parsear: {bloque}",
        document_id="doc-1",
    )
    assert ruta is not None
    assert CENTINELA not in _todo_lo_escrito(tmp_path)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["status"] == "error"
    assert datos["error"].startswith(
        f"ValueError: no se pudo parsear: {ADVERTENCIA_DATO}\n[correo omitido: "
    )
    assert f"sha256={ctx.sha256}" in datos["error"]


def test_f048_r37_objeto_no_json_se_escribe_sin_el_cuerpo(tmp_path):
    """Lo que no es JSON sale por su ``str``: tambien pasa por la redaccion."""
    ctx, bloque = _bloque()
    ruta = LlmCallLogger(tmp_path).log_call(
        provider="claude",
        model="modelo-de-prueba",
        request_summary={"objeto": _Opaco(f"previo {bloque}")},
        document_id="doc-1",
    )
    assert ruta is not None
    assert CENTINELA not in _todo_lo_escrito(tmp_path)
    objeto = json.loads(ruta.read_text(encoding="utf-8"))["request"]["objeto"]
    assert objeto.startswith(f"previo {ADVERTENCIA_DATO}\n[correo omitido: ")
    assert f"sha256={ctx.sha256}" in objeto
