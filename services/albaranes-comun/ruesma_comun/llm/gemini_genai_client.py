# ruesma_comun/llm/gemini_genai_client.py
from __future__ import annotations

import json
import logging

from ruesma_comun.llm.json_coercion import sanear_para_modelo
import time
import traceback
from typing import Any, Optional, Sequence, Type

from google import genai
from google.genai import types
from pydantic import BaseModel

from ruesma_comun.llm.llm_attachment import LlmAttachment
from ruesma_comun.llm.llm_client import LlmVisionClient, normalizar_adjuntos
from ruesma_comun.llm.llm_call_logger import LlmCallLogger
from ruesma_comun.llm.retry_policy import RetryPolicy, run_with_retry

logger = logging.getLogger(__name__)


class GeminiGenAiVisionClient(LlmVisionClient):
    def __init__(
        self,
        api_key: str,
        *,
        retry_policy: RetryPolicy | None = None,
        call_logger: LlmCallLogger | None = None,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._retry_policy = retry_policy or RetryPolicy()
        # Logger best-effort (puede ser None si IA_LOGGING_ENABLED=false).
        self._call_logger = call_logger

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
            "Gemini call. model=%s kind=%s n_adjuntos=%s filename=%s "
            "mime=%s size_total=%s schema=%s",
            model,
            att_kind,
            len(adjuntos),
            att_filename,
            att_mime,
            att_size,
            response_model.__name__,
        )

        response_schema = response_model.model_json_schema()

        # Construcción de contents según haya o no adjunto. Antes el
        # llamante inventaba un PDF dummy cuando no había PDF real y
        # Gemini lo rechazaba con 400 INVALID_ARGUMENT ("The document
        # has no pages."). Si attachment es None, solo texto puro.
        # (jul 2026) Acepta N adjuntos: una Part por página rinde
        # mucho mejor que la tira apilada.
        contents: list[Any] = []
        for att in adjuntos:
            contents.append(
                types.Part.from_bytes(
                    data=att.data,
                    mime_type=att.mime_type,
                )
            )
        contents.append(user_text)

        # ----- Captura del request para el call_logger ----- #
        request_summary = self._build_request_summary(
            model=model,
            instructions=instructions,
            user_text=user_text,
            adjuntos=adjuntos,
            schema_name=response_model.__name__,
            response_schema=response_schema,
        )

        response = None
        error_str: str | None = None
        t0 = time.time()
        try:
            response = run_with_retry(
                provider="gemini",
                operation=lambda: self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=instructions,
                        response_mime_type="application/json",
                        response_json_schema=response_schema,
                    ),
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

        # Intentamos parsear ANTES de loguear, para que el log refleje
        # el resultado real (parsed exitoso o no). Si el parseo falla,
        # también lo logueamos.
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

        # Log OK con response del SDK + objeto parseado (lo más útil).
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
        """Llama a call_logger.log_call() ignorando cualquier error."""
        if self._call_logger is None:
            return
        try:
            request_summary["duration_ms"] = duration_ms
            self._call_logger.log_call(
                provider="gemini",
                model=model,
                request_summary=request_summary,
                response_payload=response_payload,
                error=error,
            )
        except Exception:
            logger.warning(
                "GeminiGenAiVisionClient: error guardando call log; "
                "se continúa.",
                exc_info=True,
            )

    @staticmethod
    def _build_request_summary(
        *,
        model: str,
        instructions: str,
        user_text: str,
        adjuntos: Sequence[LlmAttachment],
        schema_name: str,
        response_schema: dict,
    ) -> dict:
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
        return {
            "model": model,
            "instructions": instructions,
            "user_text": user_text,
            "attachment": attachment_summary,
            "schema_name": schema_name,
            "response_format": "json_schema",
            "response_schema_keys": list((response_schema or {}).keys()),
        }

    def _parse_response(
        self,
        response: Any,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, response_model):
            return parsed
        if isinstance(parsed, BaseModel):
            return response_model.model_validate(parsed.model_dump())
        if isinstance(parsed, dict):
            return response_model.model_validate(sanear_para_modelo(parsed, response_model))

        response_text = getattr(response, "text", None)
        if isinstance(response_text, str) and response_text.strip():
            return response_model.model_validate_json(
                self._sanitize_json_text(response_text)
            )

        parsed_from_candidates = self._extract_json_dict(response)
        if parsed_from_candidates is not None:
            return response_model.model_validate(sanear_para_modelo(parsed_from_candidates, response_model))

        raise ValueError("Gemini no devolvió parsed ni text JSON válido.")

    @staticmethod
    def _sanitize_json_text(text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 2:
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        return cleaned

    @classmethod
    def _extract_json_dict(cls, response: Any) -> dict[str, Any] | None:
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                text = getattr(part, "text", None)
                if isinstance(text, str) and text.strip():
                    try:
                        loaded = json.loads(cls._sanitize_json_text(text))
                    except Exception:
                        continue
                    if isinstance(loaded, dict):
                        return loaded
        return None
