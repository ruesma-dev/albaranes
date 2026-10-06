# infrastructure/sigrid/sigrid_api_alta_client.py
"""Cliente HTTP de sigrid-api para sv9 (F-053; contrato F-009 v8.2, ``13fd99d``).

Solo tres rutas (R33): ``POST /api/sql/read`` (altas a mano y anulación),
``POST /api/sigrid/albaran`` en modo extendido (previa y grabación) y
``POST /api/sigrid/concepto-grafico`` (adjunto). Nunca la escritura genérica de
SQL, ni el modo clásico, ni el alta directa.

Reintentos (R24) con tenacity y espera exponencial ante fallos transitorios
(5xx, tiempo agotado, conexión) en lecturas, previa y adjunto. La GRABACIÓN
(``commit=true``) va una sola vez, sin reintento, con un cliente de 240 s de
timeout (> 230 s del balanceador de sigrid-api): si no hay respuesta, el alta
queda ``incierto`` y se retoma tras la Espera con la misma petición.

Sin secretos en el log (R35): ni la clave (cabecera ``x-functions-key``), ni
el PDF, ni los cuerpos de las respuestas; solo ruta, estado HTTP y códigos.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
from typing import Any

import httpx
from ruesma_comun.sigrid import PoliticaTruncado, comprobar_truncado
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from domain.models.alta_models import (
    AlbaranSigrid,
    ErrorAlta,
    PeticionAlbaran,
    RespuestaAlta,
    ResultadoAdjunto,
    TipoFallo,
)
from domain.ports.sigrid_alta_port import SigridAltaPort

logger = logging.getLogger(__name__)

_LOG = "[sv9-alta][sigrid-api]"

RUTA_SQL_READ = "/api/sql/read"
RUTA_ALBARAN = "/api/sigrid/albaran"
RUTA_CONCEPTO_GRAFICO = "/api/sigrid/concepto-grafico"

#: R14: albaranes de compra con el mismo CIF y número del proveedor y otra
#: referencia externa (altas a mano). Design §6.
SQL_BUSCAR_ALBARANES = (
    "SELECT c.ide, c.cod, c.fec FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
    "WHERE c.tip = 14 AND d.entcif = ? AND d.entref = ? AND ISNULL(d.synckey, '') <> ?"
)
#: R28: ¿sigue en Sigrid el albarán de compra?
SQL_EXISTE_CONCEPTO = "SELECT ide FROM dbo.con WHERE ide = ? AND tip = 14"

#: Timeout de la grabación: por encima del corte de 230 s del balanceador.
TIMEOUT_GRABACION_S = 240.0
#: ``contip`` de un albarán de compra y clase de gráfico «sin clase».
CONTIP_ALBARAN_COMPRA = 14
GRATIPIDE_SIN_CLASE = 0
MAX_RES = 48
MAX_NOM = 255
MAX_FILAS_BUSQUEDA = 50


class _Transitorio(Exception):
    """5xx: se reintenta (salvo en la grabación)."""

    def __init__(self, respuesta: httpx.Response) -> None:
        super().__init__(f"HTTP {respuesta.status_code}")
        self.respuesta = respuesta


class SigridLecturaError(RuntimeError):
    """Una lectura (``sql/read``) que no se pudo hacer."""


_EXCEPCIONES_TRANSITORIAS = (_Transitorio, httpx.TimeoutException, httpx.TransportError)


class SigridApiAltaClient(SigridAltaPort):
    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        usuario: str,
        timeout_s: float = 60.0,
        timeout_grabacion_s: float = TIMEOUT_GRABACION_S,
        intentos: int = 3,
        espera_base_s: float = 1.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url:
            raise ValueError("SigridApiAltaClient requiere base_url")
        if not function_key:
            raise ValueError("SigridApiAltaClient requiere la clave de sigrid-api")
        if not database:
            raise ValueError("SigridApiAltaClient requiere database")
        self._base_url = base_url.rstrip("/")
        self._clave = function_key
        self._database = database
        self._usuario = usuario
        self._timeout = float(timeout_s)
        self._timeout_grabacion = float(timeout_grabacion_s)
        self._intentos = max(1, int(intentos))
        self._espera_base = float(espera_base_s)
        self._transport = transport
        logger.info(
            "%s base_url=%s database=%s timeout=%ss grabacion=%ss intentos=%s",
            _LOG, self._base_url, database, self._timeout, self._timeout_grabacion,
            self._intentos,
        )

    def __repr__(self) -> str:  # sin la clave
        return f"SigridApiAltaClient(base_url={self._base_url!r}, database={self._database!r})"

    # ------------------------------------------------------------------ #
    # HTTP
    # ------------------------------------------------------------------ #
    def _post(self, ruta: str, cuerpo: dict[str, Any], timeout: float) -> httpx.Response:
        cabeceras = {"x-functions-key": self._clave, "Content-Type": "application/json"}
        with httpx.Client(timeout=timeout, transport=self._transport) as cliente:
            respuesta = cliente.post(f"{self._base_url}{ruta}", json=cuerpo, headers=cabeceras)
        logger.info("%s POST %s -> %s", _LOG, ruta, respuesta.status_code)
        return respuesta

    def _post_con_reintentos(self, ruta: str, cuerpo: dict[str, Any]) -> httpx.Response:
        """POST con reintentos ante 5xx, tiempo agotado y conexión (R24).

        Agotados, relanza la última excepción transitoria."""

        def intento() -> httpx.Response:
            respuesta = self._post(ruta, cuerpo, self._timeout)
            if respuesta.status_code >= 500:
                raise _Transitorio(respuesta)
            return respuesta

        reintentos = Retrying(
            stop=stop_after_attempt(self._intentos),
            wait=wait_exponential(multiplier=self._espera_base, max=30),
            retry=retry_if_exception_type(_EXCEPCIONES_TRANSITORIAS),
            before_sleep=lambda estado: logger.warning(
                "%s %s intento %s fallido (%s); reintento", _LOG, ruta,
                estado.attempt_number, type(estado.outcome.exception()).__name__,
            ),
            reraise=True,
        )
        return reintentos(intento)

    # ------------------------------------------------------------------ #
    # sql/read
    # ------------------------------------------------------------------ #
    def _leer(self, sql: str, parametros: list[Any], etiqueta: str, max_filas: int) -> list[dict]:
        cuerpo = {
            "database": self._database, "sql": sql, "parameters": parametros,
            "timeout_seconds": int(self._timeout), "max_rows": max_filas,
        }
        try:
            respuesta = self._post_con_reintentos(RUTA_SQL_READ, cuerpo)
        except _EXCEPCIONES_TRANSITORIAS as exc:
            raise SigridLecturaError(f"sql/read [{etiqueta}] sin respuesta: {exc!r}") from exc
        if respuesta.status_code != 200:
            raise SigridLecturaError(f"sql/read [{etiqueta}] HTTP {respuesta.status_code}")
        datos = _json_o_none(respuesta)
        if not isinstance(datos, dict) or datos.get("ok") is not True:
            raise SigridLecturaError(f"sql/read [{etiqueta}] respuesta no válida")
        comprobar_truncado(datos, politica=PoliticaTruncado.NO_TOLERA, etiqueta=etiqueta,
                           logger=logger)
        columnas = [str(c).lower() for c in datos.get("columns") or []]
        return [dict(zip(columnas, fila, strict=False)) for fila in datos.get("rows") or []]

    def buscar_albaranes(
        self, cif: str, referencia: str, referencia_externa: str,
    ) -> list[AlbaranSigrid]:
        filas = self._leer(
            SQL_BUSCAR_ALBARANES, [cif, referencia, referencia_externa],
            "f053-altas-a-mano", MAX_FILAS_BUSQUEDA,
        )
        return [
            AlbaranSigrid(
                ide=int(f["ide"]), cod=str(f.get("cod") or ""),
                fec=None if f.get("fec") is None else int(f["fec"]),
            )
            for f in filas
        ]

    def existe_concepto(self, ide: int) -> bool:
        return bool(self._leer(SQL_EXISTE_CONCEPTO, [int(ide)], "f053-anulacion", 2))

    # ------------------------------------------------------------------ #
    # sigrid/albaran
    # ------------------------------------------------------------------ #
    def alta_albaran(self, peticion: PeticionAlbaran, commit: bool) -> RespuestaAlta | ErrorAlta:
        cuerpo = {"database": self._database, **peticion.a_dict(), "commit": bool(commit)}
        try:
            if commit:
                # Grabación: UNA vez, sin reintento (R20, R24).
                respuesta = self._post(RUTA_ALBARAN, cuerpo, self._timeout_grabacion)
            else:
                respuesta = self._post_con_reintentos(RUTA_ALBARAN, cuerpo)
        except _Transitorio as exc:
            respuesta = exc.respuesta
        except httpx.TimeoutException:
            return ErrorAlta(tipo=TipoFallo.TIEMPO_AGOTADO, mensaje="tiempo agotado")
        except httpx.TransportError as exc:
            return ErrorAlta(tipo=TipoFallo.CONEXION, mensaje=type(exc).__name__)
        resultado = _respuesta_alta(respuesta)
        if isinstance(resultado, ErrorAlta):
            logger.info("%s sigrid/albaran commit=%s fallo=%s codigo=%s", _LOG, commit,
                        resultado.tipo.value, resultado.codigo)
        else:
            logger.info("%s sigrid/albaran commit=%s estado=%s cod=%s", _LOG, commit,
                        resultado.estado, resultado.cod)
        return resultado

    # ------------------------------------------------------------------ #
    # concepto-grafico
    # ------------------------------------------------------------------ #
    def adjuntar_pdf(self, con_ide: int, nombre: str, contenido: bytes) -> ResultadoAdjunto:
        cuerpo = {
            "database": self._database,
            "conide": int(con_ide),
            "contip": CONTIP_ALBARAN_COMPRA,
            "gratipide": GRATIPIDE_SIN_CLASE,
            "res": nombre[:MAX_RES],
            "nom": nombre[:MAX_NOM],
            "usu": self._usuario,
            "contenido_base64": base64.b64encode(contenido).decode("ascii"),
            "sha256": hashlib.sha256(contenido).hexdigest(),
            "commit": True,
        }
        try:
            respuesta = self._post_con_reintentos(RUTA_CONCEPTO_GRAFICO, cuerpo)
        except _Transitorio as exc:
            return ResultadoAdjunto(False, codigo=f"http_{exc.respuesta.status_code}")
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            return ResultadoAdjunto(False, codigo=type(exc).__name__)
        datos = _json_o_none(respuesta)
        datos = datos if isinstance(datos, dict) else {}
        if respuesta.status_code != 200:
            detalles = datos.get("details") if isinstance(datos.get("details"), dict) else {}
            return ResultadoAdjunto(
                False, codigo=detalles.get("codigo") or f"http_{respuesta.status_code}",
                mensaje=str(datos.get("error") or "")[:200],
            )
        colgado = datos.get("ok") is True and bool(datos.get("committed") or datos.get("idempotente"))
        grafico = datos.get("grafico") if isinstance(datos.get("grafico"), dict) else {}
        gra_ide = grafico.get("ide")
        logger.info("%s concepto-grafico colgado=%s", _LOG, colgado)
        return ResultadoAdjunto(
            colgado, gra_ide=None if gra_ide is None else int(gra_ide),
            codigo=None if colgado else "no_escrito",
        )


# ---------------------------------------------------------------------- #
# Traducción de respuestas
# ---------------------------------------------------------------------- #
def _json_o_none(respuesta: httpx.Response) -> Any:
    try:
        return respuesta.json()
    except (json.JSONDecodeError, ValueError):
        return None


def _respuesta_alta(respuesta: httpx.Response) -> RespuestaAlta | ErrorAlta:
    status = respuesta.status_code
    datos = _json_o_none(respuesta)
    if status == 200:
        if not isinstance(datos, dict) or datos.get("ok") is not True:
            return ErrorAlta(tipo=TipoFallo.RESPUESTA_INVALIDA, status=200,
                             mensaje="200 sin JSON válido u ok=false")
        return RespuestaAlta.desde_cuerpo(datos)
    if status >= 500:
        return ErrorAlta(tipo=TipoFallo.SERVIDOR, status=status, mensaje=f"HTTP {status}")
    datos = datos if isinstance(datos, dict) else {}
    if status == 400:
        detalles = datos.get("details") if isinstance(datos.get("details"), dict) else {}
        lineas = detalles.get("lineas") if isinstance(detalles.get("lineas"), list) else []
        return ErrorAlta(
            tipo=TipoFallo.RECHAZO, status=400,
            codigo=detalles.get("codigo") or None,
            lineas=tuple(l for l in lineas if isinstance(l, dict)),
            mensaje=str(datos.get("error") or "")[:500],
        )
    tipo = TipoFallo.AUTORIZACION if status in (401, 403) else TipoFallo.CLIENTE
    return ErrorAlta(tipo=tipo, status=status, mensaje=f"HTTP {status}")


def construir_desde_settings(settings: Any, *, transport: httpx.BaseTransport | None = None,
                             ) -> SigridApiAltaClient:
    """El cliente con la configuración de sv9 (``config.settings.Settings``)."""
    return SigridApiAltaClient(
        base_url=settings.sigrid_api_base_url,
        function_key=settings.sigrid_api_function_key,
        database=settings.sigrid_api_database,
        usuario=settings.usuario,
        timeout_s=settings.sigrid_api_timeout_s,
        transport=transport,
    )
