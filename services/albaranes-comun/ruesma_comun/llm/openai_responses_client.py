# ruesma_comun/llm/openai_responses_client.py
from __future__ import annotations

import base64
import logging

from ruesma_comun.llm.json_coercion import sanear_para_modelo
import re
import time
import traceback
from typing import Any, Optional, Sequence, Type

from openai import OpenAI
from pydantic import BaseModel

from ruesma_comun.llm.llm_attachment import LlmAttachment
from ruesma_comun.llm.llm_client import LlmVisionClient, normalizar_adjuntos
from ruesma_comun.llm.llm_call_logger import LlmCallLogger
from ruesma_comun.llm.openai_sdk_compat import patch_openai_pydantic_compat
from ruesma_comun.llm.retry_policy import RetryPolicy, run_with_retry

logger = logging.getLogger(__name__)


class OpenAIResponsesVisionClient(LlmVisionClient):
    def __init__(
        self,
        api_key: str,
        *,
        retry_policy: RetryPolicy | None = None,
        call_logger: LlmCallLogger | None = None,
    ) -> None:
        patch_openai_pydantic_compat()
        self._client = OpenAI(api_key=api_key)
        self._retry_policy = retry_policy or RetryPolicy()
        # Logger best-effort (puede ser None si IA_LOGGING_ENABLED=false).
        self._call_logger = call_logger

    @staticmethod
    def _to_data_url(mime_type: str, data: bytes) -> str:
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def _safe_filename(filename: str, fallback: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("_")
        return cleaned or fallback

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
            "OpenAI call. model=%s kind=%s n_adjuntos=%s filename=%s "
            "mime=%s size_total=%s schema=%s",
            model,
            att_kind,
            len(adjuntos),
            att_filename,
            att_mime,
            att_size,
            response_model.__name__,
        )

        # (jul 2026) Acepta N adjuntos: una imagen por página rinde
        # mucho mejor que la tira apilada. Orden: adjuntos primero y
        # el input_text al final.
        content: list[dict[str, Any]] = []
        for i, att in enumerate(adjuntos, start=1):
            if att.kind == "pdf":
                safe_name = self._safe_filename(
                    att.filename,
                    f"document_{i}.pdf",
                )
                content.append(
                    {
                        "type": "input_file",
                        "filename": safe_name,
                        "file_data": self._to_data_url(
                            "application/pdf",
                            att.data,
                        ),
                    }
                )
            else:
                content.append(
                    {
                        "type": "input_image",
                        "image_url": self._to_data_url(
                            att.mime_type,
                            att.data,
                        ),
                    }
                )
        content.append(
            {
                "type": "input_text",
                "text": user_text,
            }
        )

        # Resumen del request (sin bytes binarios) para el call_logger.
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
            "response_format": "responses.parse + text_format=Pydantic",
        }

        response = None
        error_str: str | None = None
        t0 = time.time()
        try:
            response = run_with_retry(
                provider="openai",
                operation=lambda: self._client.responses.parse(
                    model=model,
                    instructions=instructions,
                    input=[{"role": "user", "content": content}],
                    text_format=response_model,
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
                provider="openai",
                model=model,
                request_summary=request_summary,
                response_payload=response_payload,
                error=error,
            )
        except Exception:
            logger.warning(
                "OpenAIResponsesVisionClient: error guardando call log; "
                "se continúa.",
                exc_info=True,
            )

    @staticmethod
    def _parse_response(
        response: Any,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        if response.output_parsed is not None:
            return response.output_parsed

        # Red de seguridad: si el SDK no pudo tipar la salida, intentamos
        # con el texto crudo + coercion (algunos modelos devuelven listas
        # como STRING con JSON dentro).
        raw_text = getattr(response, "output_text", None)
        if isinstance(raw_text, str) and raw_text.strip():
            import json as _json

            try:
                datos = _json.loads(raw_text)
            except (ValueError, TypeError):
                datos = None
            if datos is not None:
                return response_model.model_validate(
                    sanear_para_modelo(datos, response_model)
                )
        if getattr(response, "output_text", None):
            return response_model.model_validate_json(response.output_text)
        raise ValueError("OpenAI no devolvió output_parsed ni output_text.")
