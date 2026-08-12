# ruesma_comun/llm/claude_messages_client.py
from __future__ import annotations

import base64
import json
import logging

from ruesma_comun.llm.json_coercion import sanear_para_modelo
import re
import time
import traceback
from typing import Any, Optional, Sequence, Type

import anthropic
from pydantic import BaseModel

from ruesma_comun.llm.llm_attachment import LlmAttachment
from ruesma_comun.llm.llm_client import LlmVisionClient, normalizar_adjuntos
from ruesma_comun.llm.llm_call_logger import LlmCallLogger
from ruesma_comun.llm.retry_policy import RetryPolicy, run_with_retry

logger = logging.getLogger(__name__)

# Nombre/descripción del tool forzado. Cada servicio pasa los suyos en
# el constructor (sv2: emit_albaran_extraction · sv5: emit_valuation_result)
# para conservar sus logs y trazas tal cual; estos son solo el defecto.
_TOOL_NAME_POR_DEFECTO = "emit_structured_result"
_TOOL_DESCRIPTION_POR_DEFECTO = (
    "Devuelve el resultado estructurado conforme al esquema exigido. "
    "Debes llamar SIEMPRE a esta herramienta y solo a ella."
)


class ClaudeMessagesVisionClient(LlmVisionClient):
    def __init__(
        self,
        *,
        api_key: str,
        max_tokens: int = 8192,
        timeout_s: int = 120,
        retry_policy: RetryPolicy | None = None,
        call_logger: LlmCallLogger | None = None,
        tool_name: str = _TOOL_NAME_POR_DEFECTO,
        tool_description: str = _TOOL_DESCRIPTION_POR_DEFECTO,
    ) -> None:
        self._tool_name = tool_name
        self._tool_description = tool_description
        self._client = anthropic.Anthropic(
            api_key=api_key,
            timeout=float(timeout_s),
        )
        self._max_tokens = int(max_tokens)
        self._retry_policy = retry_policy or RetryPolicy()
        # Logger best-effort (puede ser None si IA_LOGGING_ENABLED=false).
        self._call_logger = call_logger

    @staticmethod
    def _sanitize_schema(schema: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(schema, dict):
            return schema
        cleaned = {k: v for k, v in schema.items() if k != "title"}
        if "properties" in cleaned and isinstance(cleaned["properties"], dict):
            cleaned["properties"] = {
                key: ClaudeMessagesVisionClient._sanitize_schema(value)
                for key, value in cleaned["properties"].items()
            }
        if "$defs" in cleaned and isinstance(cleaned["$defs"], dict):
            cleaned["$defs"] = {
                key: ClaudeMessagesVisionClient._sanitize_schema(value)
                for key, value in cleaned["$defs"].items()
            }
        if "items" in cleaned and isinstance(cleaned["items"], dict):
            cleaned["items"] = ClaudeMessagesVisionClient._sanitize_schema(
                cleaned["items"]
            )
        return cleaned

    @staticmethod
    def _b64(data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    @staticmethod
    def _safe_filename(filename: str, fallback: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename or "").strip("_")
        return cleaned or fallback

    def _build_content_block(
        self,
        *,
        adjuntos: Sequence[LlmAttachment],
        user_text: str,
    ) -> list[dict[str, Any]]:
        # Modo texto puro (sin adjuntos): p. ej. valoración sin PDF de
        # contrato (solo fase 1a sobre la tabla del ERP).
        # (jul 2026) Acepta N adjuntos: una imagen por página rinde
        # mucho mejor que la tira apilada. Orden: adjuntos y al final
        # el texto (mismo orden relativo que siempre).
        blocks: list[dict[str, Any]] = []
        for att in adjuntos:
            if att.kind == "pdf":
                blocks.append({
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": self._b64(att.data),
                    },
                })
            else:
                blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": att.mime_type or "image/jpeg",
                        "data": self._b64(att.data),
                    },
                })
        blocks.append({"type": "text", "text": user_text})
        return blocks

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
        adjuntos = normalizar_adjuntos(attachment, attachments)
        att_kind = adjuntos[0].kind if adjuntos else "text_only"
        att_filename = adjuntos[0].filename if adjuntos else "n/a"
        att_mime = adjuntos[0].mime_type if adjuntos else "n/a"
        att_size = sum(len(a.data) for a in adjuntos)
        logger.info(
            "Claude call. model=%s kind=%s n_adjuntos=%s filename=%s "
            "mime=%s size_total=%s schema=%s",
            model,
            att_kind,
            len(adjuntos),
            att_filename,
            att_mime,
            att_size,
            response_model.__name__,
        )

        raw_schema = response_model.model_json_schema()
        input_schema = self._sanitize_schema(raw_schema)

        tool_spec = {
            "name": self._tool_name,
            "description": self._tool_description,
            "input_schema": input_schema,
        }

        content = self._build_content_block(
            adjuntos=adjuntos,
            user_text=user_text,
        )

        # Resumen del request (sin bytes binarios) para call_logger.
        if not adjuntos:
            attachment_summary: Any = {"kind": "text_only"}
        else:
            resumenes = [
                LlmCallLogger.attachment_summary(
                    kind=a.kind,
                    filename=a.filename,
                    mime_type=a.mime_type,
                    data=a.data,
                )
                for a in adjuntos
            ]
            attachment_summary = (
                resumenes[0] if len(resumenes) == 1 else resumenes
            )
        request_summary = {
            "model": model,
            "instructions": instructions,
            "user_text": user_text,
            "attachment": attachment_summary,
            "schema_name": response_model.__name__,
            "tool_name": self._tool_name,
            "max_tokens": self._max_tokens,
            "response_format": "tool_use forced",
        }

        response = None
        error_str: str | None = None
        t0 = time.time()
        try:
            response = run_with_retry(
                provider="claude",
                operation=lambda: self._client.messages.create(
                    model=model,
                    max_tokens=self._max_tokens,
                    system=instructions,
                    tools=[tool_spec],
                    tool_choice={"type": "tool", "name": self._tool_name},
                    messages=[{"role": "user", "content": content}],
                ),
                policy=self._retry_policy,
            )
        except Exception as exc:
            error_str = (
                f"{type(exc).__name__}: {exc}\n"
                f"{traceback.format_exc(limit=3)}"
            )
            self._safe_log_call(
                model=model,
                request_summary=request_summary,
                response_payload=None,
                error=error_str,
                duration_ms=int((time.time() - t0) * 1000),
            )
            raise

        duration_ms = int((time.time() - t0) * 1000)

        try:
            parsed_obj = self._parse_response(response, response_model)
        except Exception as exc:
            error_str = f"PARSE ERROR: {type(exc).__name__}: {exc}"
            self._safe_log_call(
                model=model,
                request_summary=request_summary,
                response_payload=response,
                error=error_str,
                duration_ms=duration_ms,
            )
            raise

        self._safe_log_call(
            model=model,
            request_summary=request_summary,
            response_payload={
                "raw_sdk_response": response,
                "parsed_pydantic": (
                    parsed_obj.model_dump(mode="json")
                    if isinstance(parsed_obj, BaseModel) else None
                ),
                "duration_ms": duration_ms,
            },
            error=None,
            duration_ms=duration_ms,
        )
        return parsed_obj

    # ------------------------------------------------------------ #
    # Helpers internos.
    # ------------------------------------------------------------ #
    def _safe_log_call(
        self,
        *,
        model: str,
        request_summary: dict,
        response_payload: Any,
        error: str | None,
        duration_ms: int,
    ) -> None:
        if self._call_logger is None:
            return
        try:
            request_summary["duration_ms"] = duration_ms
            self._call_logger.log_call(
                provider="claude",
                model=model,
                request_summary=request_summary,
                response_payload=response_payload,
                error=error,
            )
        except Exception:
            logger.warning(
                "ClaudeMessagesVisionClient: error guardando call log; "
                "se continúa.",
                exc_info=True,
            )

    def _parse_response(
        self,
        response: Any,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        for block in response.content or []:
            block_type = getattr(block, "type", None)
            if block_type != "tool_use":
                continue
            tool_name = getattr(block, "name", None)
            if tool_name != self._tool_name:
                continue
            tool_input = getattr(block, "input", None)
            if isinstance(tool_input, dict):
                # Coercion defensiva: algunos modelos devuelven listas u
                # objetos como STRING con JSON dentro -> Pydantic falla.
                return response_model.model_validate(
                    sanear_para_modelo(tool_input, response_model)
                )
            if isinstance(tool_input, str):
                import json as _json

                try:
                    return response_model.model_validate(
                        sanear_para_modelo(_json.loads(tool_input), response_model)
                    )
                except (ValueError, TypeError):
                    return response_model.model_validate_json(tool_input)

        # Fallback: por si el modelo devolvió texto JSON sin usar el tool.
        text_parts: list[str] = []
        for block in response.content or []:
            if getattr(block, "type", None) == "text":
                text_value = getattr(block, "text", None)
                if isinstance(text_value, str) and text_value.strip():
                    text_parts.append(text_value)
        if text_parts:
            joined = "\n".join(text_parts).strip()
            try:
                payload = json.loads(cls._strip_code_fences(joined))
                if isinstance(payload, dict):
                    return response_model.model_validate(payload)
            except Exception as exc:
                logger.debug(
                    "Claude devolvió texto no parseable como JSON: %s", exc
                )

        raise ValueError(
            "Claude no devolvió tool_use ni JSON válido en la respuesta."
        )

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        return cleaned
