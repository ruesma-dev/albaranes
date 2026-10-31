# tests/test_f113_mime_real.py
"""F-113 · sv1 deja en ``input/`` el MIME real y un nombre coherente (R11–R16).

Buzón, intake, repositorio y publicador son dobles (``dobles_sv1``); el
almacén de blobs es un doble propio que registra ``content_type`` y
``metadata`` (R12). Los bytes son cabeceras sintéticas o PDF en blanco: ni
fotos reales ni correos reales.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

from dobles_sv1 import (
    ID_ERRORES,
    ID_PROCESADOS,
    BuzonDoble,
    IntakeDoble,
    PublicadorDoble,
    RepositorioDoble,
    adjunto,
    construir_pipeline,
    ejecutar_ciclo,
    mensaje,
    pdf_de_paginas,
)
from domain.models.email_models import DocumentoInterior, ExtraccionCorreoAdjunto
from infrastructure.colas.intake_cola_adapter import IntakeColaClient
from ruesma_comun.blobs.conexion import CONTENEDOR_INPUT

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00" + b"\x00" * 32
WHATSAPP = "WhatsApp Image 2026-10-30 at 11.59.10 CENTINELA-F113.jpeg"
OCTET = "application/octet-stream"
RFC822 = "message/rfc822"


def _sha(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


@dataclass(frozen=True)
class BlobSubido:
    contenedor: str
    nombre: str
    datos: bytes
    content_type: str | None
    metadata: dict | None


class AlmacenCaptura:
    """Almacén con la forma de ``AlmacenBlobs`` que guarda los kwargs de ``put_bytes``."""

    def __init__(self) -> None:
        self.subidos: list[BlobSubido] = []
        self.json: dict[tuple[str, str], object] = {}

    def put_bytes(self, contenedor: str, nombre: str, datos: bytes, *, content_type=None, metadata=None) -> None:
        self.subidos.append(BlobSubido(contenedor, nombre, datos, content_type, metadata))

    def put_json(self, contenedor: str, nombre: str, objeto: object) -> None:
        # El blob lateral del contexto de correo (F-048 R7): no es de F-113.
        self.json[(contenedor, nombre)] = objeto


class ExtractorFijo:
    """Extractor de correos adjuntos que devuelve los documentos que se le dan."""

    nivel_maximo = 5

    def __init__(self, *documentos: DocumentoInterior) -> None:
        self._documentos = documentos

    def extraer(self, *, raw_mime: bytes) -> ExtraccionCorreoAdjunto:
        return ExtraccionCorreoAdjunto(documentos=self._documentos, tope_excedido=False, partes_ignoradas=0)


def _ciclo(adjuntos, ficheros, intake=None, **opciones):
    buzon = BuzonDoble(mensajes=[mensaje("msg-1")], adjuntos={"msg-1": adjuntos}, ficheros=ficheros)
    intake = intake or IntakeDoble()
    ejecutar_ciclo(construir_pipeline(buzon, intake, **opciones))
    return buzon, intake


def _intake_por_colas():
    llamadas: list = []
    almacen = AlmacenCaptura()
    repo = RepositorioDoble(llamadas)
    publicador = PublicadorDoble(llamadas)
    return IntakeColaClient(repositorio=repo, almacen=almacen, publicador=publicador), almacen, repo, publicador


# --------------------------------------------------------------------- #
# R11 / R12 · el caso del 2026-10-30: JPEG de WhatsApp declarado octet-stream
# --------------------------------------------------------------------- #
def test_f113_r12_whatsapp_octet_stream_sube_como_image_jpeg():
    intake, almacen, repo, publicador = _intake_por_colas()
    buzon, _ = _ciclo([adjunto("a", WHATSAPP, content_type=OCTET)], {"a": JPEG}, intake=intake)

    [blob] = almacen.subidos
    [(_, msg_cola)] = publicador.publicados
    assert blob.contenedor == CONTENEDOR_INPUT
    assert blob.nombre == f"{msg_cola.document_id}.pdf"
    assert blob.content_type == "image/jpeg"
    assert blob.metadata["filename"].endswith(".jpeg")
    assert blob.datos == JPEG
    import json

    [payload] = repo.payloads
    meta = json.loads(payload)
    assert meta["attachment_content_type"] == "image/jpeg"
    assert meta["attachment_content_type_declarado"] == OCTET
    assert meta["attachment_filename"] == WHATSAPP
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f113_r11_el_troceo_y_el_intake_reciben_mime_y_nombre_reales():
    _, intake = _ciclo([adjunto("a", WHATSAPP, content_type=OCTET)], {"a": JPEG})
    [envio] = intake.envios
    assert envio.content_type == "image/jpeg"
    assert envio.filename == WHATSAPP
    assert envio.meta["attachment_content_type"] == "image/jpeg"


def test_f113_r11_pdf_multipagina_sin_extension_y_generico_se_trocea():
    pdf = pdf_de_paginas(3)
    buzon, intake = _ciclo([adjunto("a", "escaneo", content_type=OCTET)], {"a": pdf})
    assert [e.meta["page_number"] for e in intake.envios] == [1, 2, 3]
    assert {e.content_type for e in intake.envios} == {"application/pdf"}
    assert [e.filename for e in intake.envios] == [
        "escaneo__page_001_of_003.pdf",
        "escaneo__page_002_of_003.pdf",
        "escaneo__page_003_of_003.pdf",
    ]
    assert {e.meta["attachment_content_type_declarado"] for e in intake.envios} == {OCTET}
    assert {e.meta["attachment_sha256"] for e in intake.envios} == {_sha(pdf)}
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f113_r11_documento_interior_de_correo_adjunto():
    extractor = ExtractorFijo(DocumentoInterior("albaran.pdf", "application/pdf", JPEG, 1))
    buzon, intake = _ciclo(
        [adjunto("c", "Asunto interior", content_type=RFC822)],
        {"c": b"MIME del correo (no se lee: extractor fijo)"},
        extractor_correo=extractor,
    )
    [envio] = intake.envios
    assert envio.content_type == "image/jpeg"
    assert envio.filename == "albaran.jpg"
    assert envio.meta["correo_adjunto_id"] == "c"
    assert envio.meta["correo_adjunto_nivel"] == 1
    assert envio.meta["attachment_content_type_declarado"] == "application/pdf"
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


# --------------------------------------------------------------------- #
# R13 · JPEG con nombre .pdf: no se trocea como PDF
# --------------------------------------------------------------------- #
def test_f113_r13_jpeg_con_nombre_pdf_va_como_imagen():
    buzon, intake = _ciclo([adjunto("a", "albaran.pdf", content_type="application/pdf")], {"a": JPEG})
    [envio] = intake.envios
    assert envio.filename == "albaran.jpg"
    assert envio.content_type == "image/jpeg"
    assert envio.meta["attachment_filename"] == "albaran.jpg"
    assert (envio.meta["page_number"], envio.meta["total_pages"]) == (1, 1)
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f113_r13_jpeg_declarado_jpeg_con_nombre_pdf_tampoco_se_trocea():
    buzon, intake = _ciclo([adjunto("a", "foto.pdf", content_type="image/jpeg")], {"a": JPEG})
    [envio] = intake.envios
    assert envio.filename == "foto.jpg"
    assert envio.content_type == "image/jpeg"
    # R15: el MIME coincide, así que no hay declarado en el meta.
    assert "attachment_content_type_declarado" not in envio.meta
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


# --------------------------------------------------------------------- #
# R14 · WARNING con ids, declarado y real; nunca el nombre
# --------------------------------------------------------------------- #
def test_f113_r14_warning_sin_nombre(caplog):
    caplog.set_level(logging.DEBUG)
    _ciclo([adjunto("att-9", WHATSAPP, content_type=OCTET)], {"att-9": JPEG})
    avisos = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "mime corregido" in r.getMessage()
    ]
    assert len(avisos) == 1
    texto = avisos[0].getMessage()
    assert "msg=msg-1" in texto
    assert "att=att-9" in texto
    assert f"declarado={OCTET}" in texto
    assert "real=image/jpeg" in texto
    assert "CENTINELA" not in texto
    assert "WhatsApp" not in texto


def test_f113_r14_nombre_corregido_avisa_sin_nombre(caplog):
    caplog.set_level(logging.DEBUG)
    _ciclo([adjunto("att-9", "CENTINELA-F113.pdf", content_type="image/jpeg")], {"att-9": JPEG})
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING and "att=att-9" in r.getMessage()]
    assert len(avisos) == 1
    assert "nombre corregido" in avisos[0].getMessage()
    assert "CENTINELA" not in avisos[0].getMessage()


# --------------------------------------------------------------------- #
# R15 · MIME coherente: meta y flujo de siempre
# --------------------------------------------------------------------- #
def test_f113_r15_pdf_bien_declarado_sin_declarado_en_el_meta():
    pdf = pdf_de_paginas(1)
    intake, almacen, repo, publicador = _intake_por_colas()
    buzon, _ = _ciclo([adjunto("a", "albaran.pdf")], {"a": pdf}, intake=intake)

    import json

    [payload] = repo.payloads
    meta = json.loads(payload)
    assert "attachment_content_type_declarado" not in meta
    assert meta["attachment_content_type"] == "application/pdf"
    [(_, msg_cola)] = publicador.publicados
    assert msg_cola.correlation_key == f"email:msg-1:{_sha(pdf)}"
    [blob] = almacen.subidos
    assert blob.nombre == f"{msg_cola.document_id}.pdf"
    assert blob.content_type == "application/pdf"
    assert blob.metadata == {"filename": "albaran.pdf"}
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f113_r15_declarado_con_mayusculas_y_parametros_se_conserva_tal_cual():
    _, intake = _ciclo([adjunto("a", "foto.png", content_type="Image/PNG; name=foto.png")], {"a": b"\x89PNG\r\n\x1a\n" + b"\x00" * 16})
    [envio] = intake.envios
    assert envio.content_type == "Image/PNG; name=foto.png"
    assert "attachment_content_type_declarado" not in envio.meta


def test_f113_r15_imagen_bien_declarada_sin_aviso(caplog):
    caplog.set_level(logging.DEBUG)
    _, intake = _ciclo([adjunto("a", "foto.jpg", content_type="image/jpeg")], {"a": JPEG})
    [envio] = intake.envios
    assert "attachment_content_type_declarado" not in envio.meta
    assert envio.content_type == "image/jpeg"
    assert not [r for r in caplog.records if "corregido" in r.getMessage()]


def test_f113_r15_pdf_roto_sigue_yendo_a_errores():
    # Bytes con firma PDF pero ilegibles: el troceo falla como hoy.
    buzon, intake = _ciclo([adjunto("a", "roto", content_type=OCTET)], {"a": b"%PDF-1.4 roto"})
    assert intake.envios == []
    assert buzon.movidos == [("msg-1", ID_ERRORES)]


# --------------------------------------------------------------------- #
# R16 · ni imagen ni PDF: entra con su MIME declarado (D-3)
# --------------------------------------------------------------------- #
def test_f113_r16_adjunto_de_texto_entra_con_su_declarado():
    _, intake = _ciclo([adjunto("a", "notas.txt", content_type="text/plain")], {"a": b"texto inventado"})
    [envio] = intake.envios
    assert envio.content_type == "text/plain"
    assert envio.filename == "notas.txt"
    assert "attachment_content_type_declarado" not in envio.meta


def test_f113_r16_generico_sin_firma_ni_extension_conocida_sigue_igual():
    _, intake = _ciclo([adjunto("a", "hoja.xlsx", content_type=OCTET)], {"a": b"PK\x03\x04 inventado"})
    [envio] = intake.envios
    assert envio.content_type == OCTET
    assert envio.filename == "hoja.xlsx"
    assert "attachment_content_type_declarado" not in envio.meta
