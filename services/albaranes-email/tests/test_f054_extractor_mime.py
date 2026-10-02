# tests/test_f054_extractor_mime.py
"""R6-R12 (F-054, T3): el extractor de documentos de un correo adjunto.

``MimeDocumentoExtractor`` recorre el MIME RFC 822 que Graph devuelve en
``$value`` y saca los PDF y las imagenes validas (``image/*`` con
``Content-Disposition: attachment``). Todos los correos se construyen en
memoria (``eml_sinteticos``): sin red, sin disco y sin datos reales.
"""
from __future__ import annotations

import ast
import importlib
import sys
from email.message import MIMEPart
from email.message import Message as MensajeMime
from pathlib import Path

import pytest
from domain.ports.extractor_correo_adjunto import CorreoAdjuntoIlegible
from eml_sinteticos import (
    CENTINELA_F054,
    Anidado,
    Fichero,
    a_bytes,
    correo,
    envolver,
    fichero_jpeg,
    fichero_msg,
    fichero_pdf,
    fichero_png,
    fichero_texto,
    jpeg_bytes,
    pdf_bytes,
    png_bytes,
)

RUTA_MODULO = "infrastructure.document.mime_documento_extractor"


@pytest.fixture
def modulo():
    return importlib.import_module(RUTA_MODULO)


@pytest.fixture
def extractor(modulo):
    return modulo.MimeDocumentoExtractor()


def _extraer(extractor, msg):
    return extractor.extraer(raw_mime=a_bytes(msg))


def _resumen(resultado):
    return [(d.filename, d.content_type, d.nivel) for d in resultado.documentos]


# --- R6 · recorrido en profundidad y en orden ------------------------------ #
def test_f054_r6_orden_de_aparicion_y_nivel_de_cada_documento(extractor):
    interior = correo(adjuntos=[fichero_pdf("b.pdf"), fichero_png("c.png")])
    msg = correo(adjuntos=[
        fichero_pdf("a.pdf"),
        Anidado(interior, nombre="reenviado.eml"),
        fichero_jpeg("d.jpg"),
    ])

    resultado = _extraer(extractor, msg)

    assert _resumen(resultado) == [
        ("a.pdf", "application/pdf", 1),
        ("b.pdf", "application/pdf", 2),
        ("c.png", "image/png", 2),
        ("d.jpg", "image/jpeg", 1),
    ]
    assert resultado.tope_excedido is False


def test_f054_r6_multipart_anidado_se_recorre_en_el_mismo_nivel(extractor):
    msg = correo(adjuntos=[fichero_pdf("a.pdf")])
    sub = MIMEPart()
    sub.add_attachment(pdf_bytes(1), maintype="application", subtype="pdf", filename="dentro.pdf")
    assert sub.get_content_type() == "multipart/mixed"
    msg.attach(sub)

    resultado = _extraer(extractor, msg)

    assert _resumen(resultado) == [
        ("a.pdf", "application/pdf", 1),
        ("dentro.pdf", "application/pdf", 1),
    ]


# --- R7 · que es un documento interior ------------------------------------ #
def test_f054_r7_pdf_por_tipo_con_sus_bytes_decodificados(extractor):
    datos = pdf_bytes(3)
    msg = correo(adjuntos=[Fichero(datos=datos, nombre="escaneo")])

    resultado = _extraer(extractor, msg)

    assert [d.file_bytes for d in resultado.documentos] == [datos]
    assert _resumen(resultado) == [("escaneo", "application/pdf", 1)]


def test_f054_r7_pdf_por_nombre_en_mayusculas_con_tipo_generico(extractor):
    datos = pdf_bytes(1)
    msg = correo(adjuntos=[Fichero(datos=datos, subtype="octet-stream", nombre="ALBARAN.PDF")])

    resultado = _extraer(extractor, msg)

    assert _resumen(resultado) == [("ALBARAN.PDF", "application/pdf", 1)]
    assert resultado.documentos[0].file_bytes == datos


def test_f054_r7_pdf_en_quoted_printable_se_decodifica(extractor):
    datos = pdf_bytes(1)
    crudo = a_bytes(correo(adjuntos=[Fichero(datos=datos, nombre="qp.pdf", cte="quoted-printable")]))
    assert b"quoted-printable" in crudo

    resultado = extractor.extraer(raw_mime=crudo)

    assert resultado.documentos[0].file_bytes == datos


@pytest.mark.parametrize("disposicion", ["inline", "ninguna"])
def test_f054_r7_un_pdf_entra_sea_cual_sea_su_disposicion(extractor, disposicion):
    msg = correo(adjuntos=[fichero_pdf("a.pdf", disposicion=disposicion)])

    assert _resumen(_extraer(extractor, msg)) == [("a.pdf", "application/pdf", 1)]


def test_f054_r7_png_y_jpeg_con_disposicion_attachment_entran(extractor):
    png, jpeg = png_bytes(b"uno"), jpeg_bytes(b"dos")
    msg = correo(adjuntos=[fichero_png("foto.png", datos=png), fichero_jpeg("foto.jpg", datos=jpeg)])

    resultado = _extraer(extractor, msg)

    assert _resumen(resultado) == [("foto.png", "image/png", 1), ("foto.jpg", "image/jpeg", 1)]
    assert [d.file_bytes for d in resultado.documentos] == [png, jpeg]
    assert resultado.partes_ignoradas == 1  # el cuerpo de texto


def test_f054_r7_imagen_inline_con_content_id_no_entra(extractor):
    msg = correo(adjuntos=[fichero_png("logo.png", disposicion="inline")])
    assert b"Content-ID" in a_bytes(msg)

    resultado = _extraer(extractor, msg)

    assert resultado.documentos == ()
    assert resultado.partes_ignoradas == 2


def test_f054_r7_imagen_sin_content_disposition_no_entra(extractor):
    msg = correo(cuerpo=None, adjuntos=[fichero_png("foto.png", disposicion="ninguna")])
    assert b"Content-Disposition" not in a_bytes(msg)

    resultado = _extraer(extractor, msg)

    assert resultado.documentos == ()
    assert resultado.partes_ignoradas == 1


# --- R8 · lo demas se ignora y se cuenta ---------------------------------- #
def test_f054_r8_texto_msg_inline_y_vacios_se_ignoran_y_se_cuentan(extractor):
    msg = correo(cuerpo="cuerpo inventado", adjuntos=[
        fichero_texto(),
        fichero_msg(),
        fichero_png("logo.png", disposicion="inline"),
        fichero_jpeg("firma.jpg", disposicion="ninguna"),
        Fichero(datos=b"", nombre="vacio.pdf"),
        fichero_png("vacia.png", datos=b""),
        fichero_pdf("bueno.pdf"),
    ])

    resultado = _extraer(extractor, msg)

    assert _resumen(resultado) == [("bueno.pdf", "application/pdf", 1)]
    assert resultado.partes_ignoradas == 7


def test_f054_r8_correo_sin_documentos_devuelve_tupla_vacia(extractor):
    resultado = _extraer(extractor, correo(adjuntos=[fichero_texto()]))

    assert resultado.documentos == ()
    assert resultado.tope_excedido is False
    assert resultado.partes_ignoradas == 2


def test_f054_r8_rfc822_sin_mensaje_dentro_se_ignora(modulo, monkeypatch):
    # Un message/rfc822 sin mensaje no se puede serializar: se inyecta el
    # arbol ya construido en lugar del parser.
    msg = correo(cuerpo=None, adjuntos=[fichero_pdf("a.pdf")])
    vacio = MensajeMime()
    vacio["Content-Type"] = "message/rfc822"
    vacio.set_payload([])
    msg.attach(vacio)
    monkeypatch.setattr(modulo, "message_from_bytes", lambda *a, **k: msg)

    resultado = modulo.MimeDocumentoExtractor().extraer(raw_mime=b"x")

    assert _resumen(resultado) == [("a.pdf", "application/pdf", 1)]
    assert resultado.partes_ignoradas == 1
    assert resultado.tope_excedido is False


# --- R9 · tope de 5 niveles, todo o nada ---------------------------------- #
def test_f054_r9_documentos_en_nivel_5_se_extraen(extractor):
    msg = envolver(correo(adjuntos=[fichero_pdf("hondo.pdf"), fichero_png("hondo.png")]), 4)

    resultado = _extraer(extractor, msg)

    assert resultado.tope_excedido is False
    assert _resumen(resultado) == [("hondo.pdf", "application/pdf", 5), ("hondo.png", "image/png", 5)]


def test_f054_r9_nivel_6_marca_tope_excedido(extractor):
    msg = envolver(correo(adjuntos=[fichero_pdf("demasiado.pdf")]), 5)

    resultado = _extraer(extractor, msg)

    assert resultado.tope_excedido is True
    assert resultado.documentos == ()


@pytest.mark.parametrize("arriba", [fichero_pdf("arriba.pdf"), fichero_png("arriba.png")])
def test_f054_r9_tope_excedido_aunque_haya_documentos_en_niveles_bajos(extractor, arriba):
    hondo = envolver(correo(adjuntos=[fichero_png("hondo.png")]), 5)
    msg = correo(adjuntos=[arriba, hondo])

    resultado = _extraer(extractor, msg)

    assert resultado.tope_excedido is True


def test_f054_r9_la_constante_del_tope_es_5_y_la_usa_el_constructor(modulo):
    assert modulo.NIVEL_MAXIMO_ANIDAMIENTO == 5
    assert modulo.MimeDocumentoExtractor().nivel_maximo == 5
    msg = envolver(correo(adjuntos=[fichero_pdf("x.pdf")]), 5)
    assert _extraer(modulo.MimeDocumentoExtractor(), msg).tope_excedido is True


def test_f054_r9_tope_configurable_en_el_constructor(modulo):
    extractor = modulo.MimeDocumentoExtractor(nivel_maximo=2)
    assert extractor.nivel_maximo == 2

    dos = _extraer(extractor, envolver(correo(adjuntos=[fichero_pdf("x.pdf")]), 1))
    tres = _extraer(extractor, envolver(correo(adjuntos=[fichero_pdf("x.pdf")]), 2))

    assert (dos.tope_excedido, _resumen(dos)) == (False, [("x.pdf", "application/pdf", 2)])
    assert (tres.tope_excedido, tres.documentos) == (True, ())


# --- R10 · nombre del documento interior ---------------------------------- #
@pytest.mark.parametrize("nombre, esperado", [
    ("C:\\escaner\\salida\\albaran.pdf", "albaran.pdf"),
    ("carpeta/sub/albaran.pdf", "albaran.pdf"),
    ("albaran.pdf", "albaran.pdf"),
])
def test_f054_r10_nombre_base_sin_directorios(extractor, nombre, esperado):
    resultado = _extraer(extractor, correo(adjuntos=[fichero_pdf(nombre)]))

    assert resultado.documentos[0].filename == esperado


def test_f054_r10_sin_nombre_documento_n_por_orden_de_pdf_e_imagenes(extractor):
    interior = correo(adjuntos=[fichero_pdf(None)])
    msg = correo(adjuntos=[
        fichero_pdf("uno.pdf"),
        fichero_png(None),
        interior,
        fichero_jpeg(None),
    ])

    resultado = _extraer(extractor, msg)

    assert [d.filename for d in resultado.documentos] == [
        "uno.pdf", "documento_2.png", "documento_3.pdf", "documento_4.jpeg"]


def test_f054_r10_nombre_que_se_queda_vacio_usa_documento_n(extractor):
    resultado = _extraer(extractor, correo(adjuntos=[fichero_pdf("/")]))

    assert resultado.documentos[0].filename == "documento_1.pdf"


def test_f054_r10_nombre_ilegible_usa_documento_n(modulo):
    class ParteRota:
        def get_filename(self):
            raise ValueError("nombre ilegible")

    assert modulo._nombre_fichero(ParteRota()) is None


# --- R11 · bytes ilegibles ------------------------------------------------- #
def test_f054_r11_bytes_vacios_son_ilegibles(extractor):
    with pytest.raises(CorreoAdjuntoIlegible):
        extractor.extraer(raw_mime=b"")


def test_f054_r11_fallo_del_parser_es_ilegible_y_solo_nombra_el_tipo(modulo, monkeypatch):
    def parser_roto(*args, **kwargs):
        raise ValueError(f"texto del correo {CENTINELA_F054}")

    monkeypatch.setattr(modulo, "message_from_bytes", parser_roto)

    with pytest.raises(CorreoAdjuntoIlegible) as error:
        modulo.MimeDocumentoExtractor().extraer(raw_mime=b"no es un correo")

    assert "ValueError" in str(error.value)
    assert CENTINELA_F054 not in str(error.value)


def test_f054_r11_fallo_del_recorrido_es_ilegible(modulo, monkeypatch):
    def recorrido_roto(*args, **kwargs):
        raise KeyError("parte rota")

    monkeypatch.setattr(modulo.MimeDocumentoExtractor, "_recorrer", recorrido_roto)

    with pytest.raises(CorreoAdjuntoIlegible, match="KeyError"):
        modulo.MimeDocumentoExtractor().extraer(raw_mime=a_bytes(correo()))


# --- R12 · extraccion pura ------------------------------------------------- #
def test_f054_r12_solo_importa_biblioteca_estandar_y_dominio(modulo):
    arbol = ast.parse(Path(modulo.__file__).read_text(encoding="utf-8"))
    raices = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            raices.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            raices.add((nodo.module or "").split(".")[0])

    ajenos = {r for r in raices if r not in sys.stdlib_module_names and r != "__future__"}
    assert ajenos <= {"domain"}
    assert not raices & {"socket", "http", "urllib", "httpx", "requests", "os", "shutil", "tempfile", "io"}
    assert "email" in raices


def test_f054_r12_no_lee_cabeceras_del_interior(modulo):
    fuente = Path(modulo.__file__).read_text(encoding="utf-8")

    for cabecera in ('"Subject"', '"From"', '"Date"', "'Subject'", "'From'", "'Date'"):
        assert cabecera not in fuente
