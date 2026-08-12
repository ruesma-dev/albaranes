# ruesma_comun/llm/llm_client.py
"""Port abstracto para clientes LLM con capacidad de procesar
documentos (PDFs/imágenes) y devolver respuestas estructuradas
según un schema Pydantic.

Soporta dos modos de operación:

1. **Modo documento** (attachment != None):
   El PDF/imagen se envía al LLM como parte del input. Útil para
   valoración de albaranes con PDF de contrato adjunto.

2. **Modo multi-adjunto** (attachments != None, jul 2026):
   Lista de adjuntos: p. ej. UNA IMAGEN POR PAGINA de un albarán
   escaneado (del preprocesado de ruesma_comun.imaging). Mandar
   páginas sueltas rinde mucho mejor que una tira apilada porque las
   APIs de visión reescalan las imágenes grandes hacia abajo. Si se
   pasa ``attachments``, tiene prioridad sobre ``attachment``.

3. **Modo texto puro** (attachment y attachments = None):
   Solo se envía texto. Útil cuando:
     - El contrato no tiene PDF asociado en SharePoint y la IA
       solo puede hacer fase 1a (matching contra la tabla del
       contrato persistida en BBDD desde el ERP).
     - Análisis de información de texto pre-procesado (ej. dossier
       económico extraído del PDF previamente con pdfplumber).

Antes de esta tanda (abr 2026) el ``attachment`` era obligatorio. El
servicio inventaba un PDF dummy de 1 byte cuando no había PDF real,
lo cual funcionaba con Anthropic/OpenAI pero Gemini lo rechazaba con
``400 INVALID_ARGUMENT: The document has no pages.`` Al hacer
``attachment`` opcional, los 3 proveedores manejan el caso de forma
limpia y nativa.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence, Type

from pydantic import BaseModel

from ruesma_comun.llm.llm_attachment import LlmAttachment


def normalizar_adjuntos(
    attachment: Optional[LlmAttachment],
    attachments: Optional[Sequence[LlmAttachment]],
) -> list[LlmAttachment]:
    """Lista efectiva de adjuntos para una llamada.

    ``attachments`` manda si viene informado; si no, ``attachment``;
    si nada, lista vacía (modo texto puro). Utilidad compartida por
    todas las implementaciones del port.
    """
    if attachments:
        return [a for a in attachments if a is not None]
    return [attachment] if attachment is not None else []


class LlmVisionClient(ABC):
    """Cliente abstracto para llamadas LLM con/sin adjunto(s)."""

    @abstractmethod
    def extract_document(
        self,
        *,
        model: str,
        instructions: str,
        user_text: str,
        attachment: Optional[LlmAttachment] = None,
        attachments: Optional[Sequence[LlmAttachment]] = None,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        """Llama al LLM y devuelve el resultado validado.

        :param model: id del modelo a usar.
        :param instructions: system prompt.
        :param user_text: contenido del mensaje del usuario.
        :param attachment: PDF o imagen adjunta. Si None, solo texto.
        :param attachments: lista de adjuntos (p. ej. una imagen por
            página); si viene informada tiene prioridad sobre
            ``attachment``.
        :param response_model: clase Pydantic para validar la respuesta.
        :return: instancia validada de response_model.
        :raises: ValueError si el LLM no devuelve un resultado parseable.
        """
        raise NotImplementedError
