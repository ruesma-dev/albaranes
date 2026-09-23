# tests/test_f048_r37_llm_logger.py
"""F-048 · R37 · ``LlmCallLogger`` no escribe el texto del correo a disco.

Con ``LLM_CALL_LOG_DIR`` puesto, el logger guarda ``instructions`` y
``user_text`` ENTEROS: el bloque del correo iria tal cual a un fichero. El
logger aplica ``redactar_correo`` a TODO texto de ``request_summary``, a
cualquier profundidad, antes de escribir: queda el resumen (sha256,
caracteres) y desaparece el cuerpo.

Escribe en ``tmp_path`` y busca el centinela ``CENTINELA-F048`` en el
fichero. Sin red.
"""
from __future__ import annotations

import copy
import json

from ruesma_comun.correo import construir_contexto_correo, render_bloque_correo
from ruesma_comun.llm.llm_call_logger import LlmCallLogger

CENTINELA = "CENTINELA-F048"


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
