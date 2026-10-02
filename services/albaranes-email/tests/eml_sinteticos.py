# tests/eml_sinteticos.py
"""Correos RFC 822 sinteticos para la suite de sv1 (F-054, T1).

Todo se construye en memoria: ningun ``.eml`` en disco, ninguna direccion,
nombre, PDF ni foto reales. Las direcciones son ``@ejemplo.test`` y los
textos, inventados. El asunto, el remitente y el cuerpo de los correos
interiores llevan el centinela ``CENTINELA-F054`` para que los tests de
logs (R25) puedan buscarlo.

  - ``pdf_bytes(paginas)``: un PDF valido de N paginas en blanco (pypdf).
  - ``png_bytes()`` / ``jpeg_bytes()``: cabecera magica y relleno (sv1 no
    decodifica imagenes: solo las pasa).
  - ``Fichero``: un adjunto de fichero con disposicion configurable
    (``attachment``, ``inline`` con ``Content-ID`` o ``ninguna``).
  - ``correo(...)``: un ``EmailMessage`` con cuerpo opcional y adjuntos; un
    adjunto que sea ``EmailMessage`` (o ``Anidado``) va como parte
    ``message/rfc822``.
  - ``envolver(interior, niveles)``: mete ``interior`` en ``niveles`` correos.
  - ``a_bytes(msg)``: los bytes RFC 822 que devolveria Graph en ``$value``.

Patron tomado de ``partes`` (F-020), escrito de nuevo: nada se importa de alli.
"""
from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage, MIMEPart
from email.policy import SMTP
from io import BytesIO

from pypdf import PdfWriter

CENTINELA_F054 = "CENTINELA-F054"
FECHA_INTERIOR = "Wed, 30 Sep 2026 08:16:00 +0200"

DISPOSICIONES = ("attachment", "inline", "ninguna")


def pdf_bytes(paginas: int = 1) -> bytes:
    """PDF valido con ``paginas`` paginas en blanco."""
    escritor = PdfWriter()
    for _ in range(paginas):
        escritor.add_blank_page(width=200, height=200)
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def png_bytes(relleno: bytes = b"PNG-F054") -> bytes:
    """Bytes con la cabecera magica de PNG y un relleno distinguible."""
    return b"\x89PNG\r\n\x1a\n" + relleno


def jpeg_bytes(relleno: bytes = b"JPEG-F054") -> bytes:
    """Bytes con la cabecera magica de JPEG y un relleno distinguible."""
    return b"\xff\xd8\xff\xe0" + relleno + b"\xff\xd9"


@dataclass(frozen=True)
class Fichero:
    """Adjunto de fichero de un correo sintetico."""

    datos: bytes
    maintype: str = "application"
    subtype: str = "pdf"
    nombre: str | None = "albaran.pdf"
    disposicion: str = "attachment"
    cte: str = "base64"


@dataclass(frozen=True)
class Anidado:
    """Correo adjuntado como parte ``message/rfc822``, con nombre opcional."""

    mensaje: EmailMessage
    nombre: str | None = None


def fichero_pdf(
    nombre: str | None = "albaran.pdf",
    paginas: int = 1,
    *,
    cte: str = "base64",
    disposicion: str = "attachment",
) -> Fichero:
    return Fichero(datos=pdf_bytes(paginas), nombre=nombre, cte=cte, disposicion=disposicion)


def fichero_png(
    nombre: str | None = "foto.png",
    *,
    disposicion: str = "attachment",
    datos: bytes | None = None,
) -> Fichero:
    return Fichero(
        datos=datos if datos is not None else png_bytes(),
        maintype="image",
        subtype="png",
        nombre=nombre,
        disposicion=disposicion,
    )


def fichero_jpeg(
    nombre: str | None = "foto.jpg",
    *,
    disposicion: str = "attachment",
    datos: bytes | None = None,
) -> Fichero:
    return Fichero(
        datos=datos if datos is not None else jpeg_bytes(),
        maintype="image",
        subtype="jpeg",
        nombre=nombre,
        disposicion=disposicion,
    )


def fichero_texto(nombre: str | None = "nota.txt") -> Fichero:
    return Fichero(
        datos=f"texto inventado {CENTINELA_F054}".encode(),
        maintype="text",
        subtype="plain",
        nombre=nombre,
    )


def fichero_msg(nombre: str = "reenviado.msg") -> Fichero:
    """Un ``.msg`` de Outlook falso: sv1 no lo abre (DH4)."""
    return Fichero(
        datos=b"\xd0\xcf\x11\xe0MSG-FALSO",
        maintype="application",
        subtype="vnd.ms-outlook",
        nombre=nombre,
    )


def _parte_sin_disposicion(fichero: Fichero) -> MIMEPart:
    """Parte sin ``Content-Disposition``; el nombre viaja en ``name=``."""
    parte = MIMEPart()
    params = {"name": fichero.nombre} if fichero.nombre is not None else None
    parte.set_content(
        fichero.datos,
        maintype=fichero.maintype,
        subtype=fichero.subtype,
        cte=fichero.cte,
        params=params,
    )
    return parte


def _adjuntar_fichero(msg: EmailMessage, fichero: Fichero, orden: int) -> None:
    if fichero.disposicion not in DISPOSICIONES:
        raise ValueError(f"disposicion desconocida: {fichero.disposicion}")
    if fichero.disposicion == "ninguna":
        if not msg.is_multipart():
            msg.make_mixed()
        msg.attach(_parte_sin_disposicion(fichero))
        return
    kwargs: dict = {
        "maintype": fichero.maintype,
        "subtype": fichero.subtype,
        "cte": fichero.cte,
        "disposition": fichero.disposicion,
    }
    if fichero.nombre is not None:
        kwargs["filename"] = fichero.nombre
    if fichero.disposicion == "inline":
        kwargs["cid"] = f"<parte{orden}@ejemplo.test>"
    msg.add_attachment(fichero.datos, **kwargs)


def correo(
    *,
    subject: str | None = f"Albaran del proveedor {CENTINELA_F054}",
    sender: str | None = f'"Proveedor {CENTINELA_F054}" <proveedor@ejemplo.test>',
    date: str | None = FECHA_INTERIOR,
    cuerpo: str | None = f"Adjunto el albaran de la obra. {CENTINELA_F054}",
    adjuntos: list[Fichero | EmailMessage | Anidado] | None = None,
) -> EmailMessage:
    """Un correo con los adjuntos dados, en orden."""
    msg = EmailMessage()
    if subject is not None:
        msg["Subject"] = subject
    if sender is not None:
        msg["From"] = sender
    msg["To"] = "albaranes@ejemplo.test"
    if date is not None:
        msg["Date"] = date
    if cuerpo is not None:
        msg.set_content(cuerpo)
    for orden, adjunto in enumerate(adjuntos or [], start=1):
        if isinstance(adjunto, Fichero):
            _adjuntar_fichero(msg, adjunto, orden)
            continue
        anidado = adjunto if isinstance(adjunto, Anidado) else Anidado(mensaje=adjunto)
        if anidado.nombre is not None:
            msg.add_attachment(anidado.mensaje, filename=anidado.nombre)
        else:
            msg.add_attachment(anidado.mensaje)
    return msg


def envolver(interior: EmailMessage, niveles: int) -> EmailMessage:
    """Mete ``interior`` en ``niveles`` correos, del interior al exterior.

    ``envolver(x, 0)`` es ``x``. El correo devuelto es el nivel 1 e
    ``interior`` queda en el nivel ``niveles + 1``.
    """
    actual = interior
    for n in range(niveles, 0, -1):
        actual = correo(
            subject=f"Nivel {n} {CENTINELA_F054}",
            sender=f"nivel{n}@ejemplo.test",
            adjuntos=[Anidado(actual, nombre=f"nivel{n + 1}.eml")],
        )
    return actual


def a_bytes(msg: EmailMessage) -> bytes:
    """Los bytes RFC 822 del correo (lo que devuelve Graph en ``$value``)."""
    return msg.as_bytes(policy=SMTP)
