# infrastructure/llm/claude_messages_client.py
"""Reexport — la implementación canónica vive en ruesma-albaranes-comun.

Este módulo se conserva como reexport para que TODOS los imports del
servicio sigan funcionando sin tocar más ficheros, eliminando a la vez
la copia local divergente. Requiere: pip install -e ../comun

(F-086) Aquí vive también la herramienta que sv5 pide a Claude: el cliente
de comun es compartido con sv2 y cada servicio fija la suya. Es la única
definición: la usan el wiring (``interface_adapters/api/app.py``) y el
banco de evals (``evals/procesos/sv5_valoracion.py``), para que se mida el
mismo cliente que va a producción. Con ``tool_choice`` ``auto``
(``ANTHROPIC_FORZAR_HERRAMIENTA=false``) es esta descripción la que pide al
modelo llamar a la herramienta.
"""
from ruesma_comun.llm.claude_messages_client import ClaudeMessagesVisionClient

TOOL_NAME_VALORACION = "emit_valuation_result"
TOOL_DESCRIPTION_VALORACION = (
    "Devuelve la valoración estructurada de las líneas del albarán "
    "conforme al esquema exigido. Llama SIEMPRE y SOLO a esta herramienta."
)

__all__ = [
    "ClaudeMessagesVisionClient",
    "TOOL_NAME_VALORACION",
    "TOOL_DESCRIPTION_VALORACION",
]
