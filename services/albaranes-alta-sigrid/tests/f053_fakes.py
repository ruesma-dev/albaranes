# tests/f053_fakes.py
"""Dobles de los tres puertos de sv9 (F-053). Sin red ni BBDD.

- :class:`RepoFalso`: la BBDD en memoria. ``reclamar`` usa la MISMA decisión
  pura que el repositorio SQL (``domain.services.reclamacion.decidir``) y aplica
  sus efectos (``en_curso`` con ``intentos + 1``, o ``incierto``).
- :class:`SigridFalso`: respuestas programadas y registro de cada llamada.
- :class:`PdfFalso`: bytes de un PDF de mentira.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta

from domain.models.alta_models import (
    AccionAlta,
    AlbaranSigrid,
    AltaActual,
    DatosAlta,
    Decision,
    ErrorAlta,
    EstadoAlta,
    EstadoDocumento,
    PeticionAlbaran,
    Reclamacion,
    RespuestaAlta,
    ResultadoAdjunto,
    ResultadoAlta,
)
from domain.ports.alta_repository import AltaRepository
from domain.ports.pdf_port import PdfAlbaranPort, PdfNoDisponibleError
from domain.ports.sigrid_alta_port import SigridAltaPort
from domain.services.reclamacion import decidir

AHORA = datetime(2026, 10, 6, 9, 0, tzinfo=UTC)
DESDE = datetime(2026, 10, 1, tzinfo=UTC)
APROBADO = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


class Explota(RuntimeError):
    """Fallo inesperado provocado por un test."""


@dataclass
class RepoFalso(AltaRepository):
    documentos: dict[str, EstadoDocumento] = field(default_factory=dict)
    datos: dict[str, DatosAlta] = field(default_factory=dict)
    altas: dict[str, AltaActual] = field(default_factory=dict)
    guardados: list[tuple[str, ResultadoAlta]] = field(default_factory=list)
    reclamaciones: list[tuple[str, Decision]] = field(default_factory=list)
    tras_reclamar: dict[str, AltaActual] = field(default_factory=dict)
    fallar_en: set[str] = field(default_factory=set)
    fallar_al_guardar: set[EstadoAlta] = field(default_factory=set)

    def anadir(self, datos: DatosAlta, *, aprobado: bool = True, activo: bool = True,
               approved_at: datetime | None = APROBADO, alta: AltaActual | None = None) -> str:
        document_id = datos.cabecera.document_id
        self.documentos[document_id] = EstadoDocumento(
            activo=activo, aprobado=aprobado, approved_at_utc=approved_at, approved_by="ana",
        )
        self.datos[document_id] = datos
        if alta is not None:
            self.altas[document_id] = alta
        return document_id

    def reclamar(self, document_id, *, accion, ahora, desde, espera, modo) -> Reclamacion:
        if "reclamar" in self.fallar_en:
            raise Explota("BBDD caída al reclamar")
        documento = self.documentos.get(document_id)
        previa = self.altas.get(document_id)
        reclamacion = decidir(documento, previa, accion=AccionAlta(accion), ahora=ahora,
                              desde=desde, espera=espera)
        if reclamacion.decision is Decision.PROCESAR:
            base = previa or AltaActual(estado=EstadoAlta.EN_CURSO)
            self.altas[document_id] = replace(
                base, estado=EstadoAlta.EN_CURSO, modo=modo, intentos=base.intentos + 1,
                ultimo_intento_at_utc=ahora,
            )
            self.tras_reclamar[document_id] = self.altas[document_id]
        elif reclamacion.decision is Decision.A_INCIERTO:
            self.altas[document_id] = replace(previa, estado=EstadoAlta.INCIERTO)
        self.reclamaciones.append((document_id, reclamacion.decision))
        return reclamacion

    def leer_datos(self, document_id) -> DatosAlta:
        if "leer_datos" in self.fallar_en:
            raise Explota("BBDD caída al leer")
        return self.datos[document_id]

    def guardar(self, document_id, resultado, *, ahora) -> None:
        if resultado.estado in self.fallar_al_guardar:
            raise Explota(f"BBDD caída al guardar {resultado.estado}")
        self.guardados.append((document_id, resultado))
        previa = self.altas.get(document_id) or AltaActual(estado=resultado.estado)
        self.altas[document_id] = AltaActual(
            estado=resultado.estado, modo=resultado.modo,
            sigrid_con_ide=resultado.sigrid_con_ide, sigrid_cod=resultado.sigrid_cod,
            adjunto_estado=resultado.adjunto_estado, sigrid_gra_ide=resultado.sigrid_gra_ide,
            motivos=resultado.motivos, avisos=resultado.avisos, peticion=resultado.peticion,
            respuesta=resultado.respuesta, intentos=previa.intentos,
            ultimo_intento_at_utc=previa.ultimo_intento_at_utc,
        )

    def leer_alta(self, document_id) -> AltaActual | None:
        return self.altas.get(document_id)

    # ayudas de los tests
    def estado(self, document_id) -> EstadoAlta | None:
        alta = self.altas.get(document_id)
        return None if alta is None else alta.estado

    def ultimo(self, document_id) -> ResultadoAlta:
        return [r for d, r in self.guardados if d == document_id][-1]


@dataclass
class SigridFalso(SigridAltaPort):
    encontrados: list[AlbaranSigrid] = field(default_factory=list)
    previa: RespuestaAlta | ErrorAlta | None = None
    grabacion: RespuestaAlta | ErrorAlta | None = None
    existe: bool = True
    adjunto: ResultadoAdjunto = field(default_factory=lambda: ResultadoAdjunto(True, gra_ide=555))
    llamadas: list[tuple] = field(default_factory=list)
    fallar_en: set[str] = field(default_factory=set)

    def buscar_albaranes(self, cif, referencia, referencia_externa):
        self.llamadas.append(("buscar_albaranes", cif, referencia, referencia_externa))
        if "buscar_albaranes" in self.fallar_en:
            raise Explota("sql/read caído")
        return list(self.encontrados)

    def existe_concepto(self, ide):
        self.llamadas.append(("existe_concepto", ide))
        if "existe_concepto" in self.fallar_en:
            raise Explota("sql/read caído")
        return self.existe

    def alta_albaran(self, peticion: PeticionAlbaran, commit: bool):
        self.llamadas.append(("alta_albaran", peticion, commit))
        if ("grabacion" if commit else "previa") in self.fallar_en:
            raise Explota("fallo inesperado en la llamada")
        return self.grabacion if commit else self.previa

    def adjuntar_pdf(self, con_ide, nombre, contenido):
        self.llamadas.append(("adjuntar_pdf", con_ide, nombre, contenido))
        if "adjuntar_pdf" in self.fallar_en:
            raise Explota("concepto-grafico caído")
        return self.adjunto

    # ayudas de los tests
    def operaciones(self) -> list[str]:
        return [c[0] for c in self.llamadas]

    def commits(self) -> list[bool]:
        return [c[2] for c in self.llamadas if c[0] == "alta_albaran"]


@dataclass
class PdfFalso(PdfAlbaranPort):
    contenido: bytes = b"%PDF-1.4 albaran de mentira"
    sin_ruta: bool = False
    descargas: int = 0

    def descargar(self, datos):
        self.descargas += 1
        if self.sin_ruta:
            raise PdfNoDisponibleError("sin ruta de SharePoint")
        return self.contenido


def previa_ok(peticion_o_lineas, *, estado: str = "previsto", cod: str = "AC26/16001",
              con_ide: int = 9123457, totales: dict[str, float] | None = None,
              partidas: dict[str, str | None] | None = None, avisos=()) -> RespuestaAlta:
    """Respuesta 200 que devuelve exactamente lo pedido (salvo lo cambiado)."""
    lineas = peticion_o_lineas.lineas if hasattr(peticion_o_lineas, "lineas") else peticion_o_lineas
    totales = totales or {}
    partidas = partidas or {}
    return RespuestaAlta(
        estado=estado, con_ide=con_ide, cod=cod, avisos=tuple(avisos),
        lineas=tuple({
            "referencia_linea": l.referencia_linea,
            "total": totales.get(l.referencia_linea, round(l.cantidad * l.precio, 2)),
            "partida": partidas.get(l.referencia_linea, l.partida),
            "avisos": [],
        } for l in lineas),
        totales={"n_lineas": len(lineas)},
    )


ESPERA = timedelta(minutes=15)
