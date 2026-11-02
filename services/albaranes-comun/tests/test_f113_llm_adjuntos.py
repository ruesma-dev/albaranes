# tests/test_f113_llm_adjuntos.py
"""F-113 · ``normalizar_adjuntos`` corrige el MIME de cada adjunto (R7–R10).

Defensa en profundidad: lo heredan OpenAI, Gemini, Claude, Document AI y
Document Intelligence sin tocar sus bloques. El SDK de OpenAI se sustituye
por un doble que registra la petición: ninguna llamada de red.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from ruesma_comun.llm.llm_attachment import LlmAttachment
from ruesma_comun.llm.llm_client import normalizar_adjuntos
from ruesma_comun.llm.openai_responses_client import OpenAIResponsesVisionClient
from ruesma_comun.llm.retry_policy import RetryPolicy

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 24
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
PDF = b"%PDF-1.7\n" + b"\x00" * 24
TEXTO = b"no es ni imagen ni pdf" + b"\x00" * 8
NOMBRE_SECRETO = "WhatsApp Image NOMBRE-CENTINELA-F113.jpeg"


def _adj(kind: str, mime: str, data: bytes, nombre: str = NOMBRE_SECRETO) -> LlmAttachment:
    return LlmAttachment(kind=kind, filename=nombre, mime_type=mime, data=data)


# --------------------------------------------------------------------- #
# R7 · copia con MIME real y kind coherente
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("kind", "declarado", "datos", "mime_esperado", "kind_esperado"),
    [
        ("pdf", "application/octet-stream", JPEG, "image/jpeg", "image"),
        ("image", "application/octet-stream", JPEG, "image/jpeg", "image"),
        ("image", "application/pdf", JPEG, "image/jpeg", "image"),
        ("image", "application/octet-stream", PDF, "application/pdf", "pdf"),
        ("pdf", "image/jpeg", PNG, "image/png", "image"),
        ("image", "image/JPEG", JPEG, "image/jpeg", "image"),
    ],
)
def test_f113_r7_corrige_mime_y_kind(
    kind: str, declarado: str, datos: bytes, mime_esperado: str, kind_esperado: str
) -> None:
    original = _adj(kind, declarado, datos)
    [corregido] = normalizar_adjuntos(original, None)
    assert corregido is not original
    assert corregido.mime_type == mime_esperado
    assert corregido.kind == kind_esperado
    assert corregido.data is original.data
    assert corregido.filename == original.filename


@pytest.mark.parametrize("kind", ["image", "pdf"])
def test_f113_r7_mime_real_ni_imagen_ni_pdf_conserva_el_kind(kind: str) -> None:
    original = _adj(kind, "Text/Plain; charset=utf-8", TEXTO)
    [corregido] = normalizar_adjuntos(original, None)
    assert corregido.mime_type == "text/plain"
    assert corregido.kind == kind


def test_f113_r7_se_aplica_a_la_lista_de_adjuntos() -> None:
    bueno = _adj("image", "image/png", PNG)
    malo = _adj("image", "application/octet-stream", JPEG)
    resultado = normalizar_adjuntos(None, [bueno, None, malo])
    assert resultado[0] is bueno
    assert [a.mime_type for a in resultado] == ["image/png", "image/jpeg"]


# --------------------------------------------------------------------- #
# R8 · WARNING con declarado y real, nunca el nombre ni los bytes
# --------------------------------------------------------------------- #
def test_f113_r8_warning_sin_nombre(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="ruesma_comun.llm.llm_client")
    normalizar_adjuntos(_adj("image", "application/octet-stream", JPEG), None)
    avisos = [r for r in caplog.records if r.name == "ruesma_comun.llm.llm_client"]
    assert len(avisos) == 1
    assert avisos[0].levelno == logging.WARNING
    texto = avisos[0].getMessage()
    assert "declarado=application/octet-stream" in texto
    assert "real=image/jpeg" in texto
    assert "CENTINELA" not in caplog.text
    assert repr(JPEG[:4]) not in caplog.text


def test_f113_r8_sin_correccion_no_hay_warning(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="ruesma_comun.llm.llm_client")
    normalizar_adjuntos(_adj("image", "image/jpeg", JPEG), None)
    assert not [r for r in caplog.records if r.name == "ruesma_comun.llm.llm_client"]


# --------------------------------------------------------------------- #
# R9 · identidad y regla attachment/attachments de siempre
# --------------------------------------------------------------------- #
def test_f113_r9_identidad_si_el_declarado_ya_es_el_real() -> None:
    a = _adj("image", "image/jpeg", JPEG)
    b = _adj("pdf", "application/pdf", PDF)
    [ra] = normalizar_adjuntos(a, None)
    [rb] = normalizar_adjuntos(None, [b])
    assert ra is a
    assert rb is b


def test_f113_r9_regla_de_attachment_y_attachments() -> None:
    a = _adj("image", "image/jpeg", JPEG)
    b = _adj("pdf", "application/pdf", PDF)
    assert normalizar_adjuntos(None, None) == []
    assert normalizar_adjuntos(None, []) == []
    assert normalizar_adjuntos(a, None) == [a]
    assert normalizar_adjuntos(a, []) == [a]
    # attachments manda sobre attachment.
    assert normalizar_adjuntos(a, [b]) == [b]
    assert normalizar_adjuntos(None, [None]) == []


# --------------------------------------------------------------------- #
# R10 · OpenAI con un JPEG declarado octet-stream (caso del 2026-10-30)
# --------------------------------------------------------------------- #
class _Salida(BaseModel):
    ok: bool


class _RespuestasDobles:
    def __init__(self) -> None:
        self.peticiones: list[dict] = []

    def parse(self, **kwargs: object) -> SimpleNamespace:
        self.peticiones.append(kwargs)
        return SimpleNamespace(output_parsed=_Salida(ok=True), output_text=None)


def _cliente_openai() -> tuple[OpenAIResponsesVisionClient, _RespuestasDobles]:
    cliente = OpenAIResponsesVisionClient("clave-de-prueba", retry_policy=RetryPolicy(max_retries=0))
    respuestas = _RespuestasDobles()
    cliente._client = SimpleNamespace(responses=respuestas)
    return cliente, respuestas


def _contenido(respuestas: _RespuestasDobles) -> list[dict]:
    [peticion] = respuestas.peticiones
    return peticion["input"][0]["content"]


def test_f113_r10_openai_jpeg_octet_stream_va_como_image_jpeg() -> None:
    cliente, respuestas = _cliente_openai()
    adjunto = _adj("image", "application/octet-stream", JPEG)
    resultado = cliente.extract_document(
        model="modelo-de-prueba",
        instructions="i",
        user_text="u",
        attachments=[adjunto],
        response_model=_Salida,
    )
    assert resultado.ok is True
    bloque = _contenido(respuestas)[0]
    assert bloque["type"] == "input_image"
    assert bloque["image_url"].startswith("data:image/jpeg;base64,")


def test_f113_r10_openai_jpeg_declarado_pdf_no_va_como_input_file() -> None:
    cliente, respuestas = _cliente_openai()
    adjunto = _adj("pdf", "application/pdf", JPEG, nombre="albaran.pdf")
    cliente.extract_document(
        model="modelo-de-prueba",
        instructions="i",
        user_text="u",
        attachment=adjunto,
        response_model=_Salida,
    )
    bloque = _contenido(respuestas)[0]
    assert bloque["type"] == "input_image"
    assert bloque["image_url"].startswith("data:image/jpeg;base64,")
