# tests/test_f048_t34_supervivientes.py
"""F-048 · T34: los supervivientes de la campaña de mutación que eran huecos reales (comun).

Cada test nombra el mutante que mata (numeración de
``progress/mutacion_F-048.md``) y el requisito que lo pide. El análisis de
los 26 está en ``progress/impl_F-048_T34_supervivientes.md``. Sin red.
"""
from __future__ import annotations

import json

from ruesma_comun.correo import construir_contexto_correo
from ruesma_comun.llm.llm_call_logger import LlmCallLogger


# ---------------------------------------------------------------- #
# Mutante 5 · correo/contexto.py:105 (``<= 0`` -> ``<= 1``). R1: el máximo
# es configurable y solo se rechaza lo que no es positivo; 1 es positivo.
# ---------------------------------------------------------------- #
def test_f048_r1_un_maximo_de_un_caracter_es_valido():
    ctx = construir_contexto_correo("Asunto", "0945 y lo demas", max_caracteres=1)

    assert ctx.cuerpo == "0"
    assert ctx.truncado is True
    assert ctx.caracteres_originales == len("0945 y lo demas")


# ---------------------------------------------------------------- #
# Mutantes 6 y 7 · llm/llm_call_logger.py:120-121 (``ensure_ascii`` e
# ``indent``). R37: el fichero es para que lo lea una persona, en UTF-8
# legible —un «Albarán» no sale como ``á``— y con la sangría de 2 de
# todo JSON del repositorio. Con ``ensure_ascii=True`` un texto no ASCII del
# correo que se colara saldría escapado y una búsqueda del texto literal en
# el fichero no lo vería.
# ---------------------------------------------------------------- #
def test_f048_r37_el_fichero_del_logger_es_json_utf8_legible_con_sangria_2(tmp_path):
    ruta = LlmCallLogger(tmp_path).log_call(
        provider="claude",
        model="modelo-de-prueba",
        request_summary={"instructions": "Extrae el albarán de la obra nº 0945"},
        response_payload={"texto": "Hormigón HA-25, camión grúa"},
        document_id="doc-1",
    )

    assert ruta is not None
    texto = ruta.read_text(encoding="utf-8")
    assert "Extrae el albarán de la obra nº 0945" in texto
    assert "Hormigón HA-25, camión grúa" in texto
    assert "\\u00" not in texto
    assert texto == json.dumps(json.loads(texto), ensure_ascii=False, indent=2)
