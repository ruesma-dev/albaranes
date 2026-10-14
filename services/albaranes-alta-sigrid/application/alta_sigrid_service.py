# application/alta_sigrid_service.py
"""``AltaSigridService.procesar``: el flujo de sv9 (F-053, design §5).

Única clase que conoce el modo (``simulacion`` | ``real``). Pasos:

1. ``reclamar`` (R5–R8) en una transacción con el merge ``FOR UPDATE``. Una
   excepción AQUÍ se propaga: el worker deja el mensaje en la cola (reintento).
2. Según la decisión: ``ignorar`` / ``a_incierto`` (ya resueltos al reclamar),
   ``verificar_anulacion`` (R28), ``solo_adjunto`` (R23) o ``procesar``.
3. ``procesar``: todo dentro de ``try/finally`` (R9). Una petición nueva lleva
   el ``usu`` de quien aprobó o el Respaldo (v8, R47–R48:
   ``_resolver_usuario``). Tras dejar el alta en
   ``en_curso``, ninguna salida —tampoco una excepción— la deja ahí: queda
   ``incierto`` si la grabación estaba en vuelo y ``error`` si no. Las
   excepciones de esta fase NO se propagan (el mensaje se confirma).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta

from domain.models.alta_models import (
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    DatosAlta,
    Decision,
    ErrorAlta,
    EstadoAlta,
    ModoAlta,
    Motivo,
    PeticionAlbaran,
    RespuestaAlta,
    ResultadoAdjunto,
    ResultadoAlta,
)
from domain.ports.alta_repository import AltaRepository
from domain.ports.pdf_port import PdfAlbaranPort
from domain.ports.sigrid_alta_port import SigridAltaPort
from domain.services.clasificador import clasificar, motivos_de_error
from domain.services.comparador_previa import comparar
from domain.services.usuario_sigrid import candidato_usuario
from domain.services.validador_alta import (
    PREFIJO_REFERENCIA,
    ConfigAlta,
    estado_de_motivos,
    importes_por_referencia,
    lineas_de_otro_contrato,
    validar_y_construir,
)

logger = logging.getLogger(__name__)

_LOG = "[sv9-alta]"

#: Motivo que acompaña a un adjunto que no se pudo colgar (R23, R29).
MOTIVO_ADJUNTO = "adjunto_no_colgado"
#: R48: sin ``usu`` no se sigue (lectura de ``dbo.usu`` caída o Respaldo vacío).
MOTIVO_USUARIO = "usuario_no_resuelto"

#: Motivos de la última verificación de anulación (R28): se sustituyen, no se acumulan.
_MOTIVOS_VERIFICACION = frozenset({"sigue_en_sigrid", "verificacion_fallida"})


def _ahora_utc() -> datetime:
    return datetime.now(UTC)


def hoy_en_madrid(instante: datetime) -> date:
    """Fecha de hoy en Europe/Madrid (R39). Sin base de zonas horarias en el
    sistema, la hora local del contenedor (``TZ=Europe/Madrid`` en el Dockerfile)."""
    try:
        from zoneinfo import ZoneInfo

        return instante.astimezone(ZoneInfo("Europe/Madrid")).date()
    except Exception:  # noqa: BLE001 — sin tzdata: hora local del sistema
        return instante.astimezone().date()


def _avisar_lineas_de_otro_contrato(document_id: str, datos: DatosAlta) -> None:
    """R46 (D2): una línea casada con OTRO contrato es una anomalía aguas arriba.
    Se deja en el log siempre que se valida (también si R10 manda a
    ``no_admitido``), sin precios ni importes."""
    contrato = datos.cabecera.contrato_codigo or "sin contrato"
    for linea in lineas_de_otro_contrato(datos):
        logger.warning(
            "%s ANOMALIA document_id=%s linea=%s casada con una línea del contrato %s y la "
            "valoración es de %s (R46: fallo aguas arriba en sv5/sv6 o conciliación manual en sv4)",
            _LOG, document_id, linea.referencia_linea, linea.contrato_linea, contrato,
        )


@dataclass(frozen=True)
class ResultadoProceso:
    """Qué pasó con un mensaje (para el log del worker y los tests)."""

    decision: Decision
    estado: EstadoAlta | None = None
    motivo: str = ""


@dataclass
class _Paso:
    """Estado de un ``procesar`` en marcha, para el ``finally`` de R9."""

    en_vuelo: bool = False
    cerrado: bool = False
    estado: EstadoAlta | None = None
    peticion: dict | None = None


class UsuarioNoResuelto(Exception):
    """R48: no hay ``usu`` con el que pedir el alta (o colgar el adjunto)."""


class AltaSigridService:
    def __init__(
        self,
        *,
        repo: AltaRepository,
        sigrid: SigridAltaPort,
        pdf: PdfAlbaranPort,
        config: ConfigAlta,
        usuario_respaldo: str,
        modo: ModoAlta,
        desde: datetime | None,
        espera: timedelta,
        tolerancia_eur: float,
        avisos_bloqueantes: frozenset[str],
        reloj: Callable[[], datetime] = _ahora_utc,
    ) -> None:
        self._repo = repo
        self._sigrid = sigrid
        self._pdf = pdf
        self._config = config
        self._respaldo = (usuario_respaldo or "").strip()
        self._modo = ModoAlta(modo)
        self._desde = desde
        self._espera = espera
        self._tolerancia = tolerancia_eur
        self._bloqueantes = frozenset(avisos_bloqueantes)
        self._reloj = reloj

    @property
    def modo(self) -> ModoAlta:
        return self._modo

    # ------------------------------------------------------------------ #
    # Entrada
    # ------------------------------------------------------------------ #
    def procesar(
        self, document_id: str, accion: AccionAlta | str = AccionAlta.ALTA,
    ) -> ResultadoProceso:
        accion = AccionAlta(accion)
        if self._desde is None:
            logger.info("%s document_id=%s ignorado: ALTA_SIGRID_DESDE_UTC vacía",
                        _LOG, document_id)
            return ResultadoProceso(Decision.IGNORAR, None, "DESDE vacía")

        reclamacion = self._repo.reclamar(
            document_id, accion=accion, ahora=self._reloj(), desde=self._desde,
            espera=self._espera, modo=self._modo.value,
        )
        decision = reclamacion.decision
        logger.info(
            "%s document_id=%s accion=%s decision=%s %s",
            _LOG, document_id, accion.value, decision.value, reclamacion.motivo,
        )
        if decision is Decision.IGNORAR:
            return ResultadoProceso(decision, None, reclamacion.motivo)
        if decision is Decision.A_INCIERTO:
            return ResultadoProceso(decision, EstadoAlta.INCIERTO, reclamacion.motivo)
        if decision is Decision.VERIFICAR_ANULACION:
            return self._verificar_anulacion(document_id, reclamacion.alta)
        if decision is Decision.SOLO_ADJUNTO:
            return self._solo_adjunto(document_id, reclamacion.alta)
        return self._procesar_alta(document_id, reclamacion.alta, reclamacion.approved_by)

    # ------------------------------------------------------------------ #
    # procesar (R9)
    # ------------------------------------------------------------------ #
    def _procesar_alta(
        self, document_id: str, previa: AltaActual | None, approved_by: str | None,
    ) -> ResultadoProceso:
        paso = _Paso()
        try:
            self._flujo(document_id, previa, approved_by, paso)
        except Exception as exc:
            logger.exception("%s document_id=%s fallo inesperado", _LOG, document_id)
            self._cerrar_por_excepcion(document_id, paso, exc)
        finally:
            if not paso.cerrado:
                self._cerrar_por_excepcion(document_id, paso, None)
        return ResultadoProceso(Decision.PROCESAR, paso.estado)

    def _cerrar_por_excepcion(
        self, document_id: str, paso: _Paso, exc: Exception | None,
    ) -> None:
        if paso.cerrado:
            return
        estado = EstadoAlta.INCIERTO if paso.en_vuelo else EstadoAlta.ERROR
        detalle = type(exc).__name__ if exc is not None else "salida sin estado final"
        paso.estado = estado
        try:
            self._guardar(document_id, paso, ResultadoAlta(
                estado=estado, modo=self._modo.value,
                motivos=(Motivo("excepcion", detalle),), peticion=paso.peticion,
            ))
        except Exception:
            logger.exception(
                "%s document_id=%s no se pudo guardar %s: queda en_curso (R8 lo pasará "
                "a incierto tras la Espera)", _LOG, document_id, estado.value,
            )

    def _guardar(self, document_id: str, paso: _Paso, resultado: ResultadoAlta) -> None:
        self._repo.guardar(document_id, resultado, ahora=self._reloj())
        if resultado.estado is not EstadoAlta.EN_CURSO:
            paso.cerrado = True
            paso.estado = resultado.estado
            logger.info(
                "%s document_id=%s estado=%s modo=%s cod=%s motivos=%s",
                _LOG, document_id, resultado.estado.value, resultado.modo,
                resultado.sigrid_cod, [m.codigo for m in resultado.motivos],
            )

    def _resultado(self, estado: EstadoAlta, paso: _Paso, **campos) -> ResultadoAlta:
        return ResultadoAlta(estado=estado, modo=self._modo.value, peticion=paso.peticion, **campos)

    def _resolver_usuario(self, document_id: str, approved_by: str | None) -> str:
        """R47–R48: el ``usu`` de una petición nueva. ÚNICO punto que lo decide.

        El ``cod`` de ``dbo.usu`` para la parte local del correo ``@ruesma.es``
        de quien aprobó; si no es correo de Ruesma o no casa, el Respaldo
        (``ALTA_SIGRID_USUARIO_RESPALDO``). Lanza :class:`UsuarioNoResuelto` si
        la lectura cae tras sus reintentos o hace falta el Respaldo y está
        vacío. (F-069, la lista de equivalencias correo → login, entrará aquí,
        antes de la parte local.)"""
        candidato = candidato_usuario(approved_by)
        if candidato is not None:
            try:
                cod = self._sigrid.buscar_usuario(candidato)
            except Exception as exc:  # noqa: BLE001 — R48: sin comprobar, no se atribuye
                raise UsuarioNoResuelto(
                    f"no se pudo leer dbo.usu: {type(exc).__name__}",
                ) from exc
            if cod:
                logger.info("%s document_id=%s usu=%s (quien aprobó)", _LOG, document_id, cod)
                return cod
        if not self._respaldo:
            raise UsuarioNoResuelto(
                "quien aprobó no casa con un login de Sigrid y "
                "ALTA_SIGRID_USUARIO_RESPALDO está vacío",
            )
        logger.info("%s document_id=%s usu=%s (respaldo)", _LOG, document_id, self._respaldo)
        return self._respaldo

    def _flujo(
        self, document_id: str, previa: AltaActual | None, approved_by: str | None,
        paso: _Paso,
    ) -> None:
        datos = self._repo.leer_datos(document_id)

        # 1. Petición: la guardada si se retoma un incierto (R15, con su usu), o
        #    una nueva con el usu de quien aprobó (R47–R48; solo lee dbo.usu) y
        #    validada en local (R10–R13, R39; sin llamar a nadie más).
        peticion = _peticion_retomada(previa)
        if peticion is None:
            try:
                usu = self._resolver_usuario(document_id, approved_by)
            except UsuarioNoResuelto as exc:
                self._guardar(document_id, paso, self._resultado(
                    EstadoAlta.ERROR, paso, motivos=(Motivo(MOTIVO_USUARIO, str(exc)),),
                ))
                return
            _avisar_lineas_de_otro_contrato(document_id, datos)
            validada = validar_y_construir(
                datos, self._config, hoy_en_madrid(self._reloj()), usu,
            )
            if isinstance(validada, list):
                self._guardar(document_id, paso, self._resultado(
                    estado_de_motivos(validada), paso, motivos=tuple(validada),
                ))
                return
            peticion = validada
        paso.peticion = peticion.a_dict()
        self._guardar(document_id, paso, self._resultado(EstadoAlta.EN_CURSO, paso))

        # 2. Alta a mano del mismo albarán en Sigrid (R14).
        encontrados = self._sigrid.buscar_albaranes(
            peticion.cif_proveedor, peticion.su_referencia, peticion.referencia_externa,
        )
        if encontrados:
            primero = encontrados[0]
            self._guardar(document_id, paso, self._resultado(
                EstadoAlta.YA_EN_SIGRID, paso,
                sigrid_con_ide=primero.ide, sigrid_cod=primero.cod,
                motivos=tuple(
                    Motivo("alta_a_mano", f"{a.cod} (con.ide {a.ide})") for a in encontrados
                ),
            ))
            return

        # 3. Previa (en los dos modos).
        importes = _importes(datos, peticion)
        respuesta = self._sigrid.alta_albaran(peticion, commit=False)
        estado = clasificar(respuesta, grabacion=False)
        if isinstance(respuesta, ErrorAlta):
            self._guardar_error(document_id, paso, estado, respuesta)
            return
        if estado is EstadoAlta.REGISTRADO:
            self._registrar(document_id, paso, peticion, respuesta, importes, datos)
            return
        if estado is not None:
            self._guardar_inesperada(document_id, paso, estado, respuesta)
            return
        motivos = comparar(peticion, respuesta, importes, self._tolerancia, self._bloqueantes)
        if motivos:
            self._guardar(document_id, paso, self._resultado(
                EstadoAlta.REVISAR, paso, motivos=tuple(motivos), avisos=_avisos(respuesta),
                respuesta=respuesta.a_dict(),
            ))
            return

        # 4. Simulación: aquí termina; nunca commit=true (R19).
        if self._modo is ModoAlta.SIMULACION:
            self._guardar(document_id, paso, self._resultado(
                EstadoAlta.SIMULADO, paso, sigrid_cod=respuesta.cod,
                avisos=_avisos(respuesta), respuesta=respuesta.a_dict(),
            ))
            return
        # 5. Real: la MISMA petición con commit=true, una sola vez (R20). Desde
        #    aquí, una excepción deja el alta en incierto (R9).
        paso.en_vuelo = True
        grabada = self._sigrid.alta_albaran(peticion, commit=True)
        estado = clasificar(grabada, grabacion=True)
        if isinstance(grabada, ErrorAlta):
            self._guardar_error(document_id, paso, estado, grabada)
            return
        if estado is EstadoAlta.REGISTRADO:
            self._registrar(document_id, paso, peticion, grabada, importes, datos)
            return
        self._guardar_inesperada(document_id, paso, estado, grabada)

    def _guardar_error(
        self, document_id: str, paso: _Paso, estado: EstadoAlta, error: ErrorAlta,
    ) -> None:
        """400/5xx/tiempo agotado: estado de la tabla y sus motivos (R18, R21)."""
        self._guardar(document_id, paso, self._resultado(
            estado, paso, motivos=tuple(motivos_de_error(error)), respuesta=error.a_dict(),
        ))

    def _guardar_inesperada(
        self, document_id: str, paso: _Paso, estado: EstadoAlta, respuesta: RespuestaAlta,
    ) -> None:
        """Un 200 con un ``estado`` que no toca en ese paso."""
        self._guardar(document_id, paso, self._resultado(
            estado, paso, motivos=(Motivo("respuesta_inesperada", respuesta.estado),),
            respuesta=respuesta.a_dict(),
        ))

    def _registrar(
        self, document_id: str, paso: _Paso, peticion: PeticionAlbaran,
        respuesta: RespuestaAlta, importes: dict[str, float], datos: DatosAlta,
    ) -> None:
        """``creado`` o ``idempotente`` ⇒ ``registrado`` (R15, R20).

        Lo registrado se compara con lo pedido como en ``idempotente``: si
        difiere, el motivo es ``registrado_distinto`` (se corrige anulando, R28)."""
        motivos = comparar(
            peticion, replace(respuesta, estado="idempotente"), importes,
            self._tolerancia, self._bloqueantes,
        )
        resultado = self._resultado(
            EstadoAlta.REGISTRADO, paso,
            sigrid_con_ide=respuesta.con_ide, sigrid_cod=respuesta.cod,
            motivos=tuple(motivos), avisos=_avisos(respuesta), respuesta=respuesta.a_dict(),
        )
        self._guardar(document_id, paso, resultado)
        paso.en_vuelo = False
        # 6. Adjunto, solo en real (R22).
        if self._modo is ModoAlta.REAL:
            self._adjuntar(document_id, datos, resultado)

    def _adjuntar(self, document_id: str, datos: DatosAlta, resultado: ResultadoAlta) -> None:
        """Cuelga el PDF; si falla, el alta sigue ``registrado`` con el adjunto
        en error (R23). Nunca lanza."""
        motivos = tuple(m for m in resultado.motivos if m.codigo != MOTIVO_ADJUNTO)
        nombre = f"{PREFIJO_REFERENCIA}{document_id}.pdf"
        # R22 (v8): a nombre del usu de la petición, también en solo_adjunto.
        usu = str((resultado.peticion or {}).get("usu") or "").strip()
        try:
            if not usu:
                raise UsuarioNoResuelto("la petición guardada no lleva usu")
            contenido = self._pdf.descargar(datos)
            adjunto = self._sigrid.adjuntar_pdf(
                resultado.sigrid_con_ide, nombre, contenido, usu=usu,
            )
        except UsuarioNoResuelto as exc:
            logger.warning("%s document_id=%s adjunto sin usu", _LOG, document_id)
            adjunto = ResultadoAdjunto(False, codigo=MOTIVO_USUARIO, mensaje=str(exc))
        except Exception as exc:  # noqa: BLE001 — el adjunto nunca tumba el alta
            logger.warning("%s document_id=%s adjunto fallido: %s", _LOG, document_id,
                           type(exc).__name__)
            adjunto = ResultadoAdjunto(False, codigo=type(exc).__name__, mensaje=str(exc)[:200])
        if adjunto.colgado:
            nuevo = replace(resultado, adjunto_estado=AdjuntoEstado.COLGADO,
                            sigrid_gra_ide=adjunto.gra_ide, motivos=motivos)
        else:
            detalle = f"{adjunto.codigo or ''}: {adjunto.mensaje}".strip(": ")
            nuevo = replace(resultado, adjunto_estado=AdjuntoEstado.ERROR,
                            motivos=(*motivos, Motivo(MOTIVO_ADJUNTO, detalle)))
        self._repo.guardar(document_id, nuevo, ahora=self._reloj())
        logger.info("%s document_id=%s adjunto=%s", _LOG, document_id, nuevo.adjunto_estado)

    # ------------------------------------------------------------------ #
    # Otras decisiones
    # ------------------------------------------------------------------ #
    def _verificar_anulacion(self, document_id: str, alta: AltaActual | None) -> ResultadoProceso:
        """R28: ``anulado`` solo si ``sql/read`` ya no encuentra el ``con.ide``.

        Si sigue, o no se puede comprobar, el alta se queda ``registrado`` (y
        bloqueada en sv4) con un motivo que lo explica."""
        if alta is None:
            return ResultadoProceso(Decision.VERIFICAR_ANULACION, None)
        motivos = tuple(m for m in alta.motivos if m.codigo not in _MOTIVOS_VERIFICACION)
        if alta.sigrid_con_ide is None:
            nuevo = alta.a_resultado(motivos=(*motivos, Motivo(
                "verificacion_fallida", "el alta registrada no tiene con.ide")))
        else:
            try:
                existe = self._sigrid.existe_concepto(alta.sigrid_con_ide)
            except Exception as exc:  # noqa: BLE001 — sin comprobar, no se anula
                logger.warning("%s document_id=%s no se pudo comprobar la anulación: %s",
                               _LOG, document_id, type(exc).__name__)
                nuevo = alta.a_resultado(motivos=(*motivos, Motivo(
                    "verificacion_fallida", "no se pudo consultar Sigrid; vuelve a pulsar")))
            else:
                if existe:
                    nuevo = alta.a_resultado(motivos=(*motivos, Motivo(
                        "sigue_en_sigrid", f"{alta.sigrid_cod} sigue en Sigrid")))
                else:
                    nuevo = alta.a_resultado(estado=EstadoAlta.ANULADO, motivos=())
        self._repo.guardar(document_id, nuevo, ahora=self._reloj())
        logger.info("%s document_id=%s verificar_anulacion -> %s", _LOG, document_id,
                    nuevo.estado.value)
        return ResultadoProceso(Decision.VERIFICAR_ANULACION, nuevo.estado)

    def _solo_adjunto(self, document_id: str, alta: AltaActual | None) -> ResultadoProceso:
        """R23: un alta ``registrado`` sin adjunto colgado solo reintenta el adjunto,
        y solo en real (R22)."""
        if self._modo is not ModoAlta.REAL or alta is None:
            logger.info("%s document_id=%s registrado sin adjunto: en simulación no se adjunta",
                        _LOG, document_id)
            return ResultadoProceso(Decision.SOLO_ADJUNTO, alta.estado if alta else None)
        datos = self._repo.leer_datos(document_id)
        self._adjuntar(document_id, datos, alta.a_resultado())
        return ResultadoProceso(Decision.SOLO_ADJUNTO, EstadoAlta.REGISTRADO)


# ---------------------------------------------------------------------- #
# Ayudas puras
# ---------------------------------------------------------------------- #
def _peticion_retomada(previa: AltaActual | None) -> PeticionAlbaran | None:
    """La petición ya mandada de un ``incierto`` que se retoma (R15)."""
    if previa is None or previa.estado is not EstadoAlta.INCIERTO or not previa.peticion:
        return None
    return PeticionAlbaran.desde_dict(previa.peticion)


def _importes(datos: DatosAlta, peticion: PeticionAlbaran) -> dict[str, float]:
    """Importe aprobado por ``referencia_linea``; si una línea pedida ya no está
    en los datos (petición retomada), el que implica la propia petición."""
    importes = importes_por_referencia(datos)
    for linea in peticion.lineas:
        importes.setdefault(linea.referencia_linea, round(linea.cantidad * linea.precio, 2))
    return importes


def _avisos(respuesta: RespuestaAlta) -> tuple[dict, ...]:
    """Avisos de cabecera y de línea (estos con su ``referencia_linea``)."""
    avisos = [dict(a) for a in respuesta.avisos]
    for linea in respuesta.lineas:
        for aviso in linea.get("avisos") or ():
            avisos.append({**aviso, "referencia_linea": linea.get("referencia_linea")})
    return tuple(avisos)
