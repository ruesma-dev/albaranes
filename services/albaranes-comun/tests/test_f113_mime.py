# tests/test_f113_mime.py
"""F-113 · ``ruesma_comun.mime``: el MIME real manda sobre el declarado (R1–R6).

Los bytes son cabeceras sintéticas de 16–32 bytes con relleno: ninguna foto
real de albarán entra al repositorio.
"""
from __future__ import annotations

import pytest

from ruesma_comun.mime import (
    MIME_GENERICO,
    MIME_PDF,
    detectar_mime,
    es_mime_generico,
    nombre_coherente,
)

RELLENO = b"\x00" * 24

JPEG = b"\xff\xd8\xff\xe0" + RELLENO
PNG = b"\x89PNG\r\n\x1a\n" + RELLENO
GIF87 = b"GIF87a" + RELLENO
GIF89 = b"GIF89a" + RELLENO
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + RELLENO
TIFF_II = b"II*\x00" + RELLENO
TIFF_MM = b"MM\x00*" + RELLENO
PDF = b"%PDF-1.7\n" + RELLENO
PDF_CON_BASURA = b"\r\n" * 100 + b"%PDF-1.4\n" + RELLENO
TEXTO = b"Hola, esto es texto plano sin firma." + RELLENO


def _heif(marca: bytes) -> bytes:
    return b"\x00\x00\x00\x18ftyp" + marca + b"\x00\x00\x00\x00" + RELLENO


# --------------------------------------------------------------------- #
# R1 · orden de decisión: firma > declarado específico > extensión > genérico
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("datos", "esperado"),
    [
        (JPEG, "image/jpeg"),
        (PNG, "image/png"),
        (GIF87, "image/gif"),
        (GIF89, "image/gif"),
        (WEBP, "image/webp"),
        (TIFF_II, "image/tiff"),
        (TIFF_MM, "image/tiff"),
        (_heif(b"heic"), "image/heic"),
        (_heif(b"heix"), "image/heic"),
        (_heif(b"hevc"), "image/heic"),
        (_heif(b"hevx"), "image/heic"),
        (_heif(b"mif1"), "image/heif"),
        (_heif(b"msf1"), "image/heif"),
        (PDF, MIME_PDF),
        (PDF_CON_BASURA, MIME_PDF),
    ],
)
def test_f113_r1_firma_reconocida_con_declarado_generico(datos: bytes, esperado: str) -> None:
    assert detectar_mime(datos, declarado="application/octet-stream", nombre="x.bin") == esperado


def test_f113_r1_firma_sin_declarado_ni_nombre() -> None:
    assert detectar_mime(JPEG) == "image/jpeg"


def test_f113_r1_pdf_fuera_de_los_primeros_1024_bytes_no_cuenta() -> None:
    datos = b" " * 1024 + b"%PDF-1.4" + RELLENO
    assert detectar_mime(datos, declarado=MIME_GENERICO) == MIME_GENERICO


def test_f113_r1_pdf_justo_dentro_de_los_1024_bytes() -> None:
    datos = b" " * (1024 - 5) + b"%PDF-" + RELLENO
    assert detectar_mime(datos) == MIME_PDF


def test_f113_r1_webp_exige_la_marca_en_su_sitio() -> None:
    # RIFF de un WAV: no es WebP.
    wav = b"RIFF\x24\x00\x00\x00WAVEfmt " + RELLENO
    assert detectar_mime(wav, declarado="audio/wav") == "audio/wav"
    assert detectar_mime(wav) == MIME_GENERICO


def test_f113_r1_ftyp_de_video_no_es_heic() -> None:
    mp4 = _heif(b"isom")
    assert detectar_mime(mp4) == MIME_GENERICO


def test_f113_r1_heic_exige_ftyp_en_los_bytes_4_a_8() -> None:
    datos = b"\x00\x00\x00\x18xxxxheic" + RELLENO
    assert detectar_mime(datos) == MIME_GENERICO


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [
        ("foto.jpg", "image/jpeg"),
        ("foto.JPEG", "image/jpeg"),
        ("foto.jpe", "image/jpeg"),
        ("foto.jfif", "image/jpeg"),
        ("a.png", "image/png"),
        ("a.gif", "image/gif"),
        ("a.webp", "image/webp"),
        ("a.tif", "image/tiff"),
        ("a.TIFF", "image/tiff"),
        ("a.heic", "image/heic"),
        ("a.heif", "image/heif"),
        ("a.pdf", MIME_PDF),
    ],
)
def test_f113_r1_sin_firma_y_declarado_generico_manda_la_extension(nombre: str, esperado: str) -> None:
    assert detectar_mime(TEXTO, declarado="application/octet-stream", nombre=nombre) == esperado


@pytest.mark.parametrize("nombre", [None, "", "sin_extension", "a.bmp", "a.docx"])
def test_f113_r1_sin_firma_ni_declarado_ni_extension_conocida_es_octet_stream(nombre: str | None) -> None:
    assert detectar_mime(TEXTO, declarado=None, nombre=nombre) == MIME_GENERICO


def test_f113_r1_constantes() -> None:
    assert MIME_PDF == "application/pdf"
    assert MIME_GENERICO == "application/octet-stream"


# --------------------------------------------------------------------- #
# R2 · la firma manda sobre un declarado específico que la contradice
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("datos", "declarado", "esperado"),
    [
        (JPEG, "application/pdf", "image/jpeg"),
        (PDF, "image/jpeg", MIME_PDF),
        (PNG, "image/jpeg", "image/png"),
    ],
)
def test_f113_r2_firma_contradice_al_declarado(datos: bytes, declarado: str, esperado: str) -> None:
    assert detectar_mime(datos, declarado=declarado, nombre="a.pdf") == esperado


# --------------------------------------------------------------------- #
# R3 · sin firma, el declarado específico normalizado, sin mirar extensión
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("declarado", "esperado"),
    [
        ("text/plain", "text/plain"),
        ("application/zip", "application/zip"),
        ("Text/Plain; charset=UTF-8", "text/plain"),
        ("  APPLICATION/ZIP ; name=a.zip", "application/zip"),
    ],
)
def test_f113_r3_declarado_especifico_sin_firma(declarado: str, esperado: str) -> None:
    assert detectar_mime(TEXTO, declarado=declarado, nombre="foto.jpg") == esperado


# --------------------------------------------------------------------- #
# R4 · datos vacíos o cortos no lanzan
# --------------------------------------------------------------------- #
@pytest.mark.parametrize("datos", [b"", b"\xff", b"\xff\xd8", b"GIF8", b"RIFF", b"%PD", None])
def test_f113_r4_datos_cortos_o_vacios(datos: bytes | None) -> None:
    assert detectar_mime(datos, declarado=MIME_GENERICO, nombre="a.png") == "image/png"
    assert detectar_mime(datos, declarado="text/csv") == "text/csv"
    assert detectar_mime(datos) == MIME_GENERICO


# --------------------------------------------------------------------- #
# Glosario · MIME genérico
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "mime",
    [
        None,
        "",
        "   ",
        "application/octet-stream",
        "APPLICATION/OCTET-STREAM; name=foto.jpeg",
        "binary/octet-stream",
        "application/binary",
        "application/unknown",
        "application/x-unknown",
        "application/download",
        "application/force-download",
    ],
)
def test_f113_glosario_mime_generico(mime: str | None) -> None:
    assert es_mime_generico(mime) is True


@pytest.mark.parametrize("mime", ["image/jpeg", "application/pdf", "text/plain", "application/zip"])
def test_f113_glosario_mime_especifico(mime: str) -> None:
    assert es_mime_generico(mime) is False


@pytest.mark.parametrize(
    "declarado",
    [
        "binary/octet-stream",
        "application/binary",
        "application/unknown",
        "application/x-unknown",
        "application/download",
        "application/force-download",
        "",
    ],
)
def test_f113_r1_todos_los_genericos_caen_a_la_extension(declarado: str) -> None:
    assert detectar_mime(TEXTO, declarado=declarado, nombre="a.pdf") == MIME_PDF


# --------------------------------------------------------------------- #
# R5 · nombre coherente
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("nombre", "mime", "esperado"),
    [
        # Alias aceptados: no se toca.
        ("WhatsApp Image 2026-10-30 at 11.59.10.jpeg", "image/jpeg", "WhatsApp Image 2026-10-30 at 11.59.10.jpeg"),
        ("a.JPG", "image/jpeg", "a.JPG"),
        ("a.jpe", "image/jpeg", "a.jpe"),
        ("a.jfif", "image/jpeg", "a.jfif"),
        ("a.tiff", "image/tiff", "a.tiff"),
        ("a.TIF", "image/tiff", "a.TIF"),
        ("a.heif", "image/heic", "a.heif"),
        ("a.heic", "image/heif", "a.heic"),
        ("a.png", "image/png", "a.png"),
        ("a.gif", "image/gif", "a.gif"),
        ("a.webp", "image/webp", "a.webp"),
        ("a.PDF", MIME_PDF, "a.PDF"),
        # Extensión que no corresponde: se cambia por la canónica.
        ("albaran.pdf", "image/jpeg", "albaran.jpg"),
        ("foto.jpg", MIME_PDF, "foto.pdf"),
        ("foto.bin", "image/png", "foto.png"),
        ("foto.jpg", "image/tiff", "foto.tif"),
        ("foto.jpg", "image/heic", "foto.heic"),
        ("foto.jpg", "image/heif", "foto.heif"),
        ("foto.jpg", "image/gif", "foto.gif"),
        ("foto.jpg", "image/webp", "foto.webp"),
        # Sin extensión: se añade.
        ("foto", "image/jpeg", "foto.jpg"),
        # Nombre vacío: defecto + canónica.
        ("", "image/jpeg", "documento.jpg"),
        (None, MIME_PDF, "documento.pdf"),
        # MIME fuera de la tabla: el nombre tal cual.
        ("hoja.xlsx", "application/zip", "hoja.xlsx"),
        ("raro.pdf", MIME_GENERICO, "raro.pdf"),
        ("", "text/plain", ""),
    ],
)
def test_f113_r5_nombre_coherente(nombre: str | None, mime: str, esperado: str) -> None:
    assert nombre_coherente(nombre, mime) == esperado


def test_f113_r5_defecto_configurable() -> None:
    assert nombre_coherente("", "image/png", defecto="pagina") == "pagina.png"


def test_f113_r5_mime_con_mayusculas_y_parametros() -> None:
    assert nombre_coherente("a.pdf", "IMAGE/JPEG; q=1") == "a.jpg"


def test_f113_r5_respeta_el_tallo_tal_cual() -> None:
    assert nombre_coherente("Fóto ñ  (1).pdf", "image/jpeg") == "Fóto ñ  (1).jpg"


# --------------------------------------------------------------------- #
# R6 · exportaciones (la versión se comprueba en T3)
# --------------------------------------------------------------------- #
def test_f113_r6_exporta_la_api() -> None:
    import ruesma_comun.mime as mod

    for nombre in ("detectar_mime", "nombre_coherente", "es_mime_generico", "MIME_PDF"):
        assert nombre in mod.__all__
