# domain/models/alta_models.py
"""Modelos del alta en Sigrid (F-053, design §3). Sin E/S.

Vocabulario (requirements, glosario):

- **Alta**: la fila de ``albaran_altas_sigrid`` de un documento; solo la escribe
  sv9. Sus estados, :class:`EstadoAlta`; los bloqueantes para sv4,
  :data:`ESTADOS_BLOQUEANTES`.
- **Datos**: lo que sv9 lee de la BBDD para construir la petición
  (:class:`DatosAlta` = :class:`CabeceraAlta` + :class:`LineaAlta`).
- **Petición**: el cuerpo del modo extendido de ``POST /api/sigrid/albaran``
  (contrato §2) sin ``database`` ni ``commit``, que pone el cliente.
- **Respuesta**: de un 200 solo se guarda lo de R16 (``estado``, ``con_ide``,
  ``cod``, ``avisos``, ``lineas``, ``totales``); nunca ``cabecera`` ni
  ``filas`` (H16: podrían llevar datos que no deben salir de Sigrid).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Any

from ruesma_comun.alta_sigrid import clasificacion_documento


class EstadoAlta(StrEnum):
    """Los nueve estados del alta (glosario)."""

    EN_CURSO = "en_curso"
    NO_ADMITIDO = "no_admitido"
    YA_EN_SIGRID = "ya_en_sigrid"
    SIMULADO = "simulado"
    REVISAR = "revisar"
    ERROR = "error"
    INCIERTO = "incierto"
    REGISTRADO = "registrado"
    ANULADO = "anulado"


#: Mientras el alta esté en uno de estos, sv4 no deja tocar el documento (R25).
ESTADOS_BLOQUEANTES: frozenset[EstadoAlta] = frozenset(
    {EstadoAlta.EN_CURSO, EstadoAlta.INCIERTO, EstadoAlta.REGISTRADO},
)


class ModoAlta(StrEnum):
    """``real`` solo con ``ALTA_SIGRID_COMMIT=true``; si no, ``simulacion``."""

    SIMULACION = "simulacion"
    REAL = "real"


class AccionAlta(StrEnum):
    """``MensajeFeedback.accion`` (R32)."""

    ALTA = "alta"
    VERIFICAR_ANULACION = "verificar_anulacion"


class AdjuntoEstado(StrEnum):
    """Estado del PDF adjunto en Sigrid (R22, R23)."""

    COLGADO = "colgado"
    ERROR = "error"


class Decision(StrEnum):
    """Qué hace sv9 con un mensaje tras reclamar el documento (design §5)."""

    IGNORAR = "ignorar"
    SOLO_ADJUNTO = "solo_adjunto"
    A_INCIERTO = "a_incierto"
    PROCESAR = "procesar"
    VERIFICAR_ANULACION = "verificar_anulacion"


class TipoFallo(StrEnum):
    """Por qué no hubo un 200 de sigrid-api."""

    RECHAZO = "rechazo"                  # 400 (con o sin details.codigo)
    AUTORIZACION = "autorizacion"        # 401 / 403
    CLIENTE = "cliente"                  # otro 4xx
    SERVIDOR = "servidor"                # 5xx
    TIEMPO_AGOTADO = "tiempo_agotado"
    CONEXION = "conexion"
    RESPUESTA_INVALIDA = "respuesta_invalida"  # 200 que no es JSON u ok=false


@dataclass(frozen=True)
class Motivo:
    """Motivo de un estado (``no_admitido``, ``revisar``, ``error``...).

    ``referencia_linea`` identifica la línea cuando el motivo es de una línea
    (R39 ``signo_incoherente``, R17, ``details.lineas`` de un 400).
    """

    codigo: str
    detalle: str = ""
    referencia_linea: str | None = None

    def a_dict(self) -> dict[str, Any]:
        datos: dict[str, Any] = {"codigo": self.codigo, "detalle": self.detalle}
        if self.referencia_linea is not None:
            datos["referencia_linea"] = self.referencia_linea
        return datos

    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> Motivo:
        referencia = datos.get("referencia_linea")
        return cls(
            codigo=str(datos.get("codigo") or ""),
            detalle=str(datos.get("detalle") or ""),
            referencia_linea=None if referencia is None else str(referencia),
        )


@dataclass(frozen=True)
class CabeceraAlta:
    """Cabecera del documento, de la valoración y del merge."""

    document_id: str
    obra_codigo: str | None
    proveedor_cif: str | None
    numero_albaran: str | None
    fecha: str | None
    valoracion_status: str | None
    contrato_codigo: str | None
    tipologia: str | None = None
    tipologia_mixta: bool | None = None
    sharepoint_relative_path: str | None = None

    @property
    def clasificacion(self) -> dict[str, Any] | None:
        """Clasificación del documento para ``familia_efectiva`` (o ``None``);
        la regla es la de comun, la misma con la que sv4 pinta el producto."""
        return clasificacion_documento(self.tipologia, self.tipologia_mixta)


@dataclass(frozen=True)
class LineaAlta:
    """Una línea valorada con lo que sv9 necesita de ella.

    ``ctrpro_ide`` es el ``sigrid_ide`` de la línea de contrato casada
    (``matched_contrato_line_id``) y ``contrato_linea`` el contrato de esa
    línea. ``descripcion_merge`` y ``line_index`` son de la línea del merge
    (nulos en las manuales y sintéticas); ``tipo_familia``, de su
    ``contexto_linea_json``.
    """

    id: int
    merge_line_id: int | None
    line_index: int | None
    cantidad_albaran: float | None
    cantidad_convertida: float | None
    unidad_albaran: str | None
    importe_calculado: float | None
    matched_contrato_line_id: int | None
    derived_contrato_line_id: int | None
    ctrpro_ide: int | None
    contrato_linea: str | None
    codigo_partida_final: str | None
    descripcion_linea: str | None
    descripcion_merge: str | None
    tipo_familia: str | None
    producto_sigrid: str | None
    #: (F-106 R17) P (bruto) y d de la fila, para ``linea_no_cuadra``. Nulos =
    #: no comparable (los datos anteriores a F-106 no los traen).
    precio_unitario_final: float | None = None
    descuento_albaran_aplicado: float | None = None

    @property
    def referencia_linea(self) -> str:
        """``str(id)`` de la línea valorada: siempre ≤ 24 caracteres (R12)."""
        return str(self.id)


@dataclass(frozen=True)
class DatosAlta:
    cabecera: CabeceraAlta
    lineas: tuple[LineaAlta, ...] = ()


@dataclass(frozen=True)
class LineaPeticion:
    """Una línea de ``lineas`` (contrato §2.2). Lo nulo no se manda."""

    referencia_linea: str
    cantidad: float
    precio: float
    ctrpro_ide: int | None = None
    producto: str | None = None
    descripcion: str | None = None
    unidad: str | None = None
    partida: str | None = None
    #: (F-110 R7, R10) % de descuento de la línea; con él, ``precio`` es el
    #: bruto. Nulo = sin la clave (las peticiones de antes no la traen).
    dto: float | None = None

    def a_dict(self) -> dict[str, Any]:
        orden = (
            ("referencia_linea", self.referencia_linea),
            ("ctrpro_ide", self.ctrpro_ide),
            ("producto", self.producto),
            ("descripcion", self.descripcion),
            ("unidad", self.unidad),
            ("cantidad", self.cantidad),
            ("precio", self.precio),
            ("dto", self.dto),
            ("partida", self.partida),
        )
        return {clave: valor for clave, valor in orden if valor is not None}


@dataclass(frozen=True)
class PeticionAlbaran:
    """Cuerpo del modo extendido (contrato §2.1) sin ``database`` ni ``commit``.

    Nunca lleva ``lineas_recibidas`` ni ``naturaleza`` (R12, H34).
    """

    cod_obra: str
    cif_proveedor: str
    cod_contrato: str | None
    referencia_externa: str
    su_referencia: str
    usu: str
    fecha_albaran: int
    empide: int | None
    lineas: tuple[LineaPeticion, ...]

    def a_dict(self) -> dict[str, Any]:
        return {
            "cod_obra": self.cod_obra,
            "cif_proveedor": self.cif_proveedor,
            "cod_contrato": self.cod_contrato,
            "referencia_externa": self.referencia_externa,
            "su_referencia": self.su_referencia,
            "usu": self.usu,
            "fecha_albaran": self.fecha_albaran,
            "empide": self.empide,
            "lineas": [linea.a_dict() for linea in self.lineas],
        }

    @classmethod
    def desde_dict(cls, datos: dict[str, Any]) -> PeticionAlbaran:
        """La petición tal como se guardó en ``peticion_json`` (para retomar un
        ``incierto`` con la MISMA petición, R15)."""
        empide = datos.get("empide")
        return cls(
            cod_obra=str(datos["cod_obra"]),
            cif_proveedor=str(datos["cif_proveedor"]),
            cod_contrato=datos.get("cod_contrato"),
            referencia_externa=str(datos["referencia_externa"]),
            su_referencia=str(datos["su_referencia"]),
            usu=str(datos["usu"]),
            fecha_albaran=int(datos["fecha_albaran"]),
            empide=None if empide is None else int(empide),
            lineas=tuple(LineaPeticion(**linea) for linea in datos["lineas"]),
        )


@dataclass(frozen=True)
class RespuestaAlta:
    """200 de ``sigrid/albaran`` reducido a lo que se guarda (R16)."""

    estado: str
    con_ide: int | None = None
    cod: str | None = None
    avisos: tuple[dict[str, Any], ...] = ()
    lineas: tuple[dict[str, Any], ...] = ()
    totales: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def desde_cuerpo(cls, cuerpo: dict[str, Any]) -> RespuestaAlta:
        """Se queda SOLO con los campos de R16; el resto se descarta aquí."""
        con_ide = cuerpo.get("con_ide")
        return cls(
            estado=str(cuerpo.get("estado") or ""),
            con_ide=None if con_ide is None else int(con_ide),
            cod=None if cuerpo.get("cod") is None else str(cuerpo["cod"]),
            avisos=tuple(a for a in (cuerpo.get("avisos") or []) if isinstance(a, dict)),
            lineas=tuple(l for l in (cuerpo.get("lineas") or []) if isinstance(l, dict)),
            totales=dict(cuerpo.get("totales") or {}),
        )

    def a_dict(self) -> dict[str, Any]:
        return {
            "estado": self.estado,
            "con_ide": self.con_ide,
            "cod": self.cod,
            "avisos": list(self.avisos),
            "lineas": list(self.lineas),
            "totales": dict(self.totales),
        }


@dataclass(frozen=True)
class ErrorAlta:
    """Lo que no fue un 200 (400 con ``details``, 5xx, tiempo agotado...)."""

    tipo: TipoFallo
    status: int | None = None
    codigo: str | None = None
    lineas: tuple[dict[str, Any], ...] = ()
    mensaje: str = ""

    def a_dict(self) -> dict[str, Any]:
        return {
            "tipo": self.tipo.value,
            "status": self.status,
            "codigo": self.codigo,
            "lineas": list(self.lineas),
            "error": self.mensaje,
        }


@dataclass(frozen=True)
class AlbaranSigrid:
    """Un albarán de compra de Sigrid hallado por CIF + referencia (R14)."""

    ide: int
    cod: str
    fec: int | None = None


@dataclass(frozen=True)
class ResultadoAdjunto:
    """Resultado de ``concepto-grafico``: colgado = ok y (committed o idempotente)."""

    colgado: bool
    gra_ide: int | None = None
    codigo: str | None = None
    mensaje: str = ""


@dataclass(frozen=True)
class ResultadoAlta:
    """Lo que ``AltaRepository.guardar`` escribe en la fila del alta."""

    estado: EstadoAlta
    modo: str | None = None
    sigrid_con_ide: int | None = None
    sigrid_cod: str | None = None
    adjunto_estado: AdjuntoEstado | None = None
    sigrid_gra_ide: int | None = None
    motivos: tuple[Motivo, ...] = ()
    avisos: tuple[dict[str, Any], ...] = ()
    peticion: dict[str, Any] | None = None
    respuesta: dict[str, Any] | None = None


@dataclass(frozen=True)
class AltaActual:
    """La fila del alta tal como está en la BBDD."""

    estado: EstadoAlta
    modo: str | None = None
    sigrid_con_ide: int | None = None
    sigrid_cod: str | None = None
    adjunto_estado: AdjuntoEstado | None = None
    sigrid_gra_ide: int | None = None
    motivos: tuple[Motivo, ...] = ()
    avisos: tuple[dict[str, Any], ...] = ()
    peticion: dict[str, Any] | None = None
    respuesta: dict[str, Any] | None = None
    intentos: int = 0
    ultimo_intento_at_utc: datetime | None = None

    def a_resultado(self, **cambios: Any) -> ResultadoAlta:
        """Resultado que conserva lo guardado salvo ``cambios``."""
        base = ResultadoAlta(
            estado=self.estado,
            modo=self.modo,
            sigrid_con_ide=self.sigrid_con_ide,
            sigrid_cod=self.sigrid_cod,
            adjunto_estado=self.adjunto_estado,
            sigrid_gra_ide=self.sigrid_gra_ide,
            motivos=self.motivos,
            avisos=self.avisos,
            peticion=self.peticion,
            respuesta=self.respuesta,
        )
        return replace(base, **cambios)


@dataclass(frozen=True)
class EstadoDocumento:
    """Lo que la reclamación lee del merge (R5, R6)."""

    activo: bool
    aprobado: bool
    approved_at_utc: datetime | None
    approved_by: str | None = None


@dataclass(frozen=True)
class Reclamacion:
    """Salida de ``AltaRepository.reclamar``: la decisión y el alta de partida."""

    decision: Decision
    alta: AltaActual | None = None
    motivo: str = ""
    #: ``approved_by`` del merge, leído bajo el cerrojo (R5): fuente del ``usu`` (R47).
    approved_by: str | None = None


# ---------------------------------------------------------------------- #
# F-069 · usuario y empleado de Sigrid de quien aprueba
# ---------------------------------------------------------------------- #
@dataclass(frozen=True)
class EmpleadoSigrid:
    """Una fila de ``dbo.emp`` leída por ``sql/read``: su ``ide`` y si está de
    alta (``fecbaj`` 0 o nulo). Nunca su nombre ni su correo."""

    ide: int
    de_alta: bool


@dataclass(frozen=True)
class AvisoResolucion:
    """Constancia de un escalón de la resolución que no sirvió (F-069). Nunca
    bloquea el alta ni cambia su estado: no es un :class:`Motivo`."""

    codigo: str
    detalle: str = ""

    def a_dict(self) -> dict[str, str]:
        return {"codigo": self.codigo, "detalle": self.detalle}


class OrigenUsuario(StrEnum):
    """De qué escalón salió el ``usu`` de una petición nueva (F-069 R5–R7)."""

    LISTA = "lista"
    CORREO = "correo"
    RESPALDO = "respaldo"


class OrigenEmpleado(StrEnum):
    """De qué escalón salió el ``empide`` (F-069 R9–R12). Con
    ``defecto_sigrid_api`` se manda nulo y sigrid-api pone el suyo."""

    LISTA = "lista"
    CORREO = "correo"
    DEFECTO_SIGRID_API = "defecto_sigrid_api"


#: Clave de ``peticion_json`` con el rastro de la resolución (F-069 R16). Va
#: JUNTO al cuerpo, nunca dentro de lo que se manda a sigrid-api (R17: el
#: contrato es ``extra="forbid"``; se manda siempre ``PeticionAlbaran.a_dict()``).
CLAVE_RESOLUCION = "resolucion"


@dataclass(frozen=True)
class Resolucion:
    """De dónde salieron el ``usu`` y el ``empide`` de una petición nueva y qué
    escalones no sirvieron (F-069 R16)."""

    usu: str
    origen_usu: OrigenUsuario
    empide: int | None
    origen_empide: OrigenEmpleado
    avisos: tuple[AvisoResolucion, ...] = ()

    def a_dict(self) -> dict[str, Any]:
        """Para ``peticion_json``: sin el ``usu`` ni el ``empide``, que ya van en el cuerpo."""
        return {
            "usu": self.origen_usu.value,
            "empide": self.origen_empide.value,
            "avisos": [aviso.a_dict() for aviso in self.avisos],
        }
