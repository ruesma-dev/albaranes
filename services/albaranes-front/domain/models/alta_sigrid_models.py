# domain/models/alta_sigrid_models.py
"""Alta en Sigrid vista desde sv4 (F-053, R1–R4, R25–R31, R37, R40–R41).

sv4 **lee** ``albaran_altas_sigrid`` (la escribe solo sv9, R34) para:

- bloquear el documento mientras el alta sea bloqueante (R25, R26): las
  operaciones que escriben lanzan :class:`AlbaranBloqueadoError` dentro de su
  transacción, con el merge bloqueado, y el portal lo traduce a 409 o a un
  aviso, sin cambiar nada;
- no aprobar lo no valorado (R37, :class:`AlbaranSinValorarError`);
- pintar el panel del alta, el estado en el listado y el producto de cada
  línea (R29–R31, R40).

La configuración (:class:`ConfigAltaSigrid`) lleva DESDE, la Espera y el mapeo
de productos con el MISMO valor que sv9 (design §7). DESDE vacía = feature
apagada: sv4 se comporta como antes de F-053 (R3), salvo R37, que vale siempre.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field, computed_field
from ruesma_comun.alta_sigrid import (
    ESTADOS_ALTA_BLOQUEANTES,
    MAPEO_PRODUCTO_POR_DEFECTO,
    nombre_producto,
    productos_admitidos,
)

#: R37: aviso al intentar aprobar un albarán no valorado.
AVISO_SIN_VALORAR = "No se puede aprobar un albarán sin valorar"

#: R4: la aprobación se mantiene, pero el alta no se pidió.
AVISO_ALTA_NO_PEDIDA = (
    "el alta en Sigrid no se pudo pedir: pulsa «Solicitar alta en Sigrid» en la ficha"
)


#: R29, R31: cómo se lee cada estado del alta en el portal.
ETIQUETAS_ESTADO_ALTA: dict[str, str] = {
    "en_curso": "En curso",
    "no_admitido": "No admitido",
    "ya_en_sigrid": "Ya estaba en Sigrid",
    "simulado": "Simulado (no grabado)",
    "revisar": "A revisar",
    "error": "Error",
    "incierto": "Incierto (pendiente de confirmar)",
    "registrado": "Registrado en Sigrid",
    "anulado": "Anulado",
}


#: F-077 R17: estados del alta que la ficha pinta como error (un rechazo de sv9
#: o de Sigrid). ``incierto`` no lo es: es una grabación sin confirmar que sv9
#: retoma tras la Espera (aviso de bloqueo, como antes).
ESTADOS_ALTA_ERROR: frozenset[str] = frozenset({"no_admitido", "revisar", "error"})


#: F-077 R26, R27: texto legible de cada código de motivo que sv9 escribe en
#: ``motivos_json`` (Anexo A de ``progress/spec_F-077.md``). El panel enseña el
#: texto y deja el código en el ``title``. Un test lee las fuentes de sv9 como
#: texto y falla si aparece un código sin entrada aquí.
TEXTOS_MOTIVO_ALTA: dict[str, str] = {
    # Validación local de sv9 (validador_alta.py).
    "falta_obra": "Falta la obra",
    "falta_cif": "Falta el CIF del proveedor",
    "cif_no_valido": "El CIF del proveedor no es válido",
    "falta_numero_albaran": "Falta el número de albarán",
    "fecha_ilegible": "La fecha del albarán no se entiende",
    "fecha_no_plausible": "La fecha del albarán no es plausible (futura o demasiado antigua)",
    "no_valorado": "El albarán no está valorado",
    "sin_lineas": "No hay líneas que dar de alta",
    "campo_demasiado_largo": "Un campo es demasiado largo para Sigrid",
    "falta_descripcion": "La línea no tiene descripción",
    "cantidad_no_valida": "La línea no tiene cantidad (o es 0)",
    "cantidad_sin_convertir": "La línea no tiene la cantidad en la unidad del contrato",
    "producto_no_admitido": "Producto de Sigrid no admitido",
    "signo_incoherente": "La cantidad y el importe tienen signos distintos",
    "linea_de_otro_contrato": "La línea es de otro contrato",
    # Comparación con la previa (comparador_previa.py).
    "lineas_distintas": "Las líneas no coinciden con lo que devolvió Sigrid",
    "importe_distinto": "El importe no coincide con el que calcula Sigrid",
    "registrado_distinto": "Lo registrado en Sigrid no coincide con lo aprobado",
    "partida_distinta": "Sigrid devolvió otra partida",
    "aviso_bloqueante": "Sigrid dio un aviso que impide el alta",
    # Servicio de sv9 (alta_sigrid_service.py).
    "alta_a_mano": "Ya hay un alta a mano en Sigrid para este albarán",
    "respuesta_inesperada": "Sigrid devolvió una respuesta inesperada",
    "excepcion": "Fallo interno al dar de alta (sv9)",
    "adjunto_no_colgado": "No se pudo colgar el PDF del albarán en Sigrid",
    # F-069 R24: vale para el alta (sv9 lo pone sin petición, R8) y para el PDF.
    "usuario_no_resuelto": "No se pudo saber con qué usuario de Sigrid dar de alta el albarán ni colgar su PDF",
    "verificacion_fallida": "No se pudo comprobar en Sigrid si el albarán está anulado",
    "sigue_en_sigrid": "El albarán sigue en Sigrid: anúlalo allí antes de pulsar «Ya lo he anulado»",
    # Códigos de cabecera de sigrid-api (clasificador.py).
    "obra_no_encontrada": "La obra no existe en Sigrid",
    "obra_ambigua": "La obra es ambigua en Sigrid",
    "contrato_no_encontrado": "El contrato no existe en Sigrid",
    "contrato_ambiguo": "El contrato es ambiguo en Sigrid",
    # Retirado en la v8.3; el texto se queda siempre: las altas antiguas lo
    # llevan en motivos_json (F-104 R10).
    "proveedor_sin_albaran_previo": "El proveedor no tiene ningún albarán previo en Sigrid",
    # Contrato v8.3 (F-015 de sigrid-api; F-104).
    "proveedor_no_encontrado": "El proveedor no existe en Sigrid en la empresa de la obra",
    "proveedor_ambiguo": "Hay varios proveedores en Sigrid con ese CIF",
    "retencion_no_soportada": "La retención del contrato no la admite el alta automática: alta a mano",
    "almacen_de_obra_no_resuelto": "Sigrid no encuentra el almacén de la obra",
    "demasiadas_lineas": "El albarán tiene más líneas de las que admite Sigrid",
    "referencia_en_conflicto": "Otro albarán de Sigrid ya lleva este número",
    "escritura_albaranes_deshabilitada": "La escritura de albaranes está deshabilitada en sigrid-api",
    "base_de_datos_no_permitida": "sigrid-api no permite escribir en esa base de datos",
    "referencia_no_permitida": "sigrid-api no admite el prefijo de la referencia del albarán",
    "obra_de_empresa_no_permitida": "La obra es de una empresa en la que no se puede dar de alta",
    "usuario_no_valido": "El usuario de Sigrid no es válido",
    "estado_inicial_no_encontrado": "Sigrid no encuentra el estado inicial del albarán",
    "peticion_mixta": "Petición no válida: mezcla los dos modos de alta de sigrid-api",
    "colision_de_clave": "Colisión de clave en Sigrid: vuelve a solicitar el alta",
    "filas_afectadas_inesperadas": "Sigrid escribió un número de filas inesperado",
    "lineas_no_validas": "Sigrid rechazó alguna línea",
    # Códigos de línea de sigrid-api (clasificador.py).
    "linea_no_es_del_contrato": "La línea no es del contrato",
    "partida_no_encontrada": "La partida no existe en la obra en Sigrid",
    "partida_ambigua": "La partida es ambigua en la obra",
    "partida_no_imputable": "La partida no admite imputaciones",
    "paride_no_valido": "Identificador de partida no válido",
    "analitica_no_resuelta": "Sigrid no encuentra la analítica de la obra",
    "producto_no_permitido": "Producto no permitido en Sigrid",
    "producto_no_encontrado": "El producto no existe en Sigrid",
    "naturaleza_no_valida": "Naturaleza no válida (configuración de sigrid-api)",
    "precio_negativo": "Precio negativo",
    # Avisos de cabecera de sigrid-api (v8.3): no son motivos ni bloquean;
    # el panel los pinta en «Avisos de Sigrid» con su mensaje (F-104 R8).
    "retencion_del_contrato": "Sigrid aplicó la retención del contrato",
    "cabecera_sin_dato": "Sigrid dejó vacío algún dato de pago de la cabecera",
    # Tipo de fallo sin código ni HTTP (TipoFallo, alta_models.py).
    "rechazo": "Sigrid rechazó el alta",
    "autorizacion": "sigrid-api no autorizó la petición",
    "cliente": "Petición no válida para sigrid-api",
    "servidor": "Error del servidor de sigrid-api",
    "tiempo_agotado": "sigrid-api no respondió a tiempo",
    "conexion": "No se pudo conectar con sigrid-api",
    "respuesta_invalida": "Respuesta no válida de sigrid-api",
}

_HTTP = re.compile(r"http_(\d{3})")


#: F-069 R16: clave de ``peticion_json`` con el rastro de la resolución de
#: ``usu`` y ``empide`` (la escribe sv9; sv4 no importa sv9 y un test contrasta
#: el valor con ``CLAVE_RESOLUCION`` de sv9, R24).
CLAVE_RESOLUCION = "resolucion"
#: F-069 R23: Origen del usuario que se marca «(respaldo)» (``OrigenUsuario`` de sv9).
ORIGEN_RESPALDO = "respaldo"

#: F-069 R22, R24: texto legible de cada Aviso de resolución de sv9
#: (``AVISO_*`` de ``usuario_sigrid.py``). Son avisos: nunca bloquean el alta.
TEXTOS_AVISO_RESOLUCION: dict[str, str] = {
    "usuario_lista_no_existe": "El usuario de la lista de equivalencias no existe en Sigrid",
    "empleado_lista_no_valido": "El empleado de la lista de equivalencias no existe o está de baja",
    "empleado_correo_ambiguo": "Varios empleados de Sigrid tienen el correo de quien aprobó",
    "empleado_correo_de_baja": "Los empleados de Sigrid con el correo de quien aprobó están de baja",
    "empleado_correo_sin_empleado": "Ningún empleado de Sigrid tiene el correo de quien aprobó",
    "empleado_sin_correo": "Quien aprobó no tiene correo de Ruesma: no se buscó su empleado",
    "defecto_sigrid_api": "Se usó el empleado por defecto de sigrid-api",
    "empleado_lectura_fallida": "No se pudo leer el empleado en Sigrid",
}


def texto_motivo_alta(codigo: str | None) -> str:
    """F-077 R26: el texto legible de un código de motivo del alta.

    ``http_<NNN>`` => «sigrid-api respondió con HTTP <NNN>»; un código que no
    está en la tabla se enseña tal cual (nunca se pierde el motivo)."""
    texto = "" if codigo is None else str(codigo)
    if texto in TEXTOS_MOTIVO_ALTA:
        return TEXTOS_MOTIVO_ALTA[texto]
    http = _HTTP.fullmatch(texto)
    if http:
        return f"sigrid-api respondió con HTTP {http.group(1)}"
    return texto


def _con_texto(motivo: dict[str, Any]) -> dict[str, Any]:
    """El motivo tal cual, con su ``texto`` legible (R26)."""
    return {**motivo, "texto": texto_motivo_alta(motivo.get("codigo"))}


def etiqueta_estado_alta(estado: str | None) -> str | None:
    """Texto del estado; uno desconocido se enseña tal cual."""
    if estado is None:
        return None
    return ETIQUETAS_ESTADO_ALTA.get(estado, estado)


def aviso_bloqueo(cod: str | None) -> str:
    """R25: «Registrado en Sigrid como {cod}: corrígelo en Sigrid y pulsa
    "Ya lo he anulado en Sigrid"» (sin ``cod`` si no lo hay)."""
    limpio = (cod or "").strip()
    sujeto = f"Registrado en Sigrid como {limpio}" if limpio else "Registrado en Sigrid"
    return f'{sujeto}: corrígelo en Sigrid y pulsa "Ya lo he anulado en Sigrid"'


class AlbaranBloqueadoError(Exception):
    """R25/R26: el documento tiene un alta bloqueante; no se cambia nada."""

    def __init__(self, document_id: str, estado: str, cod: str | None) -> None:
        self.document_id = document_id
        self.estado = estado
        self.cod = cod
        super().__init__(aviso_bloqueo(cod))

    @property
    def aviso(self) -> str:
        return aviso_bloqueo(self.cod)


class AlbaranSinValorarError(Exception):
    """R37: no se aprueba un albarán no valorado; no se cambia nada."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(AVISO_SIN_VALORAR)

    @property
    def aviso(self) -> str:
        return AVISO_SIN_VALORAR


@dataclass(frozen=True)
class ConfigAltaSigrid:
    """DESDE, Espera y mapeo de productos (los mismos valores que sv9)."""

    desde: datetime | None = None
    espera: timedelta = timedelta(minutes=15)
    mapeo: Mapping[str, str] = field(
        default_factory=lambda: dict(MAPEO_PRODUCTO_POR_DEFECTO),
    )

    @property
    def activa(self) -> bool:
        """DESDE no vacía (R3)."""
        return self.desde is not None

    @property
    def admitidos(self) -> frozenset[str]:
        """Productos que se pueden elegir en una sin vincular (R41)."""
        return productos_admitidos(self.mapeo)


@dataclass(frozen=True)
class ResultadoAprobacion:
    """Lo que pasó al aprobar (R1–R4).

    ``paso_a_aprobado``: el documento no estaba aprobado y ahora sí.
    ``alta_pedida``: ``None`` si no tocaba pedirla (ya estaba aprobado o DESDE
    vacía); ``True``/``False`` si se publicó o no en ``q-feedback``.
    """

    paso_a_aprobado: bool
    alta_pedida: bool | None = None

    @property
    def aviso(self) -> str | None:
        """R4: aviso cuando el alta tocaba y no se pudo pedir."""
        return AVISO_ALTA_NO_PEDIDA if self.alta_pedida is False else None


class ProductoOpcion(BaseModel):
    """Una opción del selector de producto (R40)."""

    codigo: str
    nombre: str


class ProductoLinea(BaseModel):
    """Producto Sigrid de una línea valorada (R40, R41, R43).

    Vinculada: el producto de su línea de contrato, sin selector. Sin
    vincular a registrar: el elegido o, si no hay, el por defecto según la
    familia (``producto_efectivo`` de comun), con selector. Sin vincular sin
    importe: no se registra, sin selector (R13).
    """

    valuation_line_id: int
    vinculada: bool
    a_registrar: bool
    elegido: str | None = None
    codigo: str | None = None
    #: El que llevaría sin elegir nada (familia + mapeo); ``None`` en vinculadas.
    defecto: str | None = None
    por_defecto: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nombre(self) -> str | None:
        return nombre_producto(self.codigo) if self.codigo else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def seleccionable(self) -> bool:
        return not self.vinculada and self.a_registrar


class AltaSigridVista(BaseModel):
    """Una fila de ``albaran_altas_sigrid``, para pintarla (R29)."""

    estado: str
    modo: str | None = None
    sigrid_con_ide: int | None = None
    sigrid_cod: str | None = None
    adjunto_estado: str | None = None
    motivos: list[dict[str, Any]] = Field(default_factory=list)
    avisos: list[dict[str, Any]] = Field(default_factory=list)
    peticion: dict[str, Any] | None = None
    respuesta: dict[str, Any] | None = None
    intentos: int = 0
    approved_at_utc: str | None = None
    #: Quien aprobó, tal como lo guardó sv9 al reclamar (R5); de ahí el ``usu`` (R47).
    approved_by: str | None = None
    ultimo_intento_at_utc: str | None = None
    actualizado_at_utc: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def usu(self) -> str | None:
        """R29 (v8): el usuario de Sigrid con el que se pidió el alta (el de la
        petición guardada); sin petición, ``None``."""
        valor = (self.peticion or {}).get("usu")
        texto = "" if valor is None else str(valor).strip()
        return texto or None

    def _resolucion(self) -> dict[str, Any] | None:
        """``peticion.resolucion`` si es un objeto (F-069 R16); si no, ``None``."""
        valor = (self.peticion or {}).get(CLAVE_RESOLUCION)
        return valor if isinstance(valor, dict) else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def empide(self) -> int | None:
        """F-069 R21: el empleado de Sigrid de la petición guardada; ``None`` si
        es nulo (sigrid-api puso el suyo) o no hay petición."""
        valor = (self.peticion or {}).get("empide")
        return valor if isinstance(valor, int) and not isinstance(valor, bool) else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def avisos_resolucion(self) -> list[dict[str, Any]]:
        """F-069 R22: los Avisos de resolución con su texto legible; un código
        sin texto, tal cual. Son avisos, no motivos: no cambian nada."""
        avisos = (self._resolucion() or {}).get("avisos")
        if not isinstance(avisos, list):
            return []
        return [
            {"codigo": str(a.get("codigo") or ""),
             "texto": TEXTOS_AVISO_RESOLUCION.get(str(a.get("codigo") or ""),
                                                  str(a.get("codigo") or "")),
             "detalle": str(a.get("detalle") or "")}
            for a in avisos if isinstance(a, dict)
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def avisos_sigrid(self) -> list[dict[str, Any]]:
        """F-104 R8 (D2): los avisos de Sigrid con su ``texto`` de
        :data:`TEXTOS_MOTIVO_ALTA` (``None`` si no lo tiene: se pintan como
        antes), su ``mensaje`` y su línea. Son avisos: no cambian nada (R9)."""
        return [
            {"codigo": a.get("codigo"),
             "texto": TEXTOS_MOTIVO_ALTA.get(str(a.get("codigo") or "")),
             "mensaje": a.get("mensaje"),
             "referencia_linea": a.get("referencia_linea")}
            for a in self.avisos if isinstance(a, dict)
        ]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def usu_respaldo(self) -> bool:
        """F-069 R23: el ``usu`` salió del Respaldo de sv9 según la
        ``resolucion`` guardada. Sin ella (altas anteriores a F-069), la regla
        de R29 (v8): el ``usu`` no es la parte local del correo de quien aprobó
        (sin distinguir mayúsculas)."""
        if self.usu is None:
            return False
        origen = (self._resolucion() or {}).get("usu")
        if isinstance(origen, str):
            return origen == ORIGEN_RESPALDO
        texto = (self.approved_by or "").strip()
        parte_local = texto.split("@")[0] if "@" in texto else ""
        return self.usu.casefold() != parte_local.casefold()

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bloqueante(self) -> bool:
        return self.estado in ESTADOS_ALTA_BLOQUEANTES

    @computed_field  # type: ignore[prop-decorator]
    @property
    def es_error(self) -> bool:
        """F-077 R17: el panel lo pinta como error (``ESTADOS_ALTA_ERROR``)."""
        return self.estado in ESTADOS_ALTA_ERROR

    @computed_field  # type: ignore[prop-decorator]
    @property
    def estado_texto(self) -> str:
        return etiqueta_estado_alta(self.estado) or self.estado

    @computed_field  # type: ignore[prop-decorator]
    @property
    def aviso(self) -> str | None:
        """R25: el aviso del bloqueo, si lo es."""
        return aviso_bloqueo(self.sigrid_cod) if self.bloqueante else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def simulacion(self) -> bool:
        return self.modo == "simulacion"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def lineas(self) -> list[dict[str, Any]]:
        """Líneas de la petición con lo que devolvió la previa (por
        ``referencia_linea``): producto, partida, cantidad, precio y total."""
        pedidas = (self.peticion or {}).get("lineas") or []
        devueltas = {
            str(linea.get("referencia_linea")): linea
            for linea in ((self.respuesta or {}).get("lineas") or [])
            if isinstance(linea, dict)
        }
        filas: list[dict[str, Any]] = []
        for pedida in pedidas:
            if not isinstance(pedida, dict):
                continue
            referencia = str(pedida.get("referencia_linea"))
            devuelta = devueltas.get(referencia, {})
            filas.append({
                "referencia_linea": referencia,
                "producto": pedida.get("producto"),
                "ctrpro_ide": pedida.get("ctrpro_ide"),
                "descripcion": pedida.get("descripcion") or devuelta.get("descripcion"),
                "partida": pedida.get("partida"),
                "cantidad": pedida.get("cantidad"),
                "precio": pedida.get("precio"),
                "total": devuelta.get("total"),
                "motivos": [
                    _con_texto(m) for m in self.motivos
                    if str(m.get("referencia_linea")) == referencia
                ],
            })
        return filas

    def _total(self, clave: str) -> float | None:
        totales = (self.respuesta or {}).get("totales")
        valor = totales.get(clave) if isinstance(totales, dict) else None
        return float(valor) if isinstance(valor, (int, float)) else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_previa(self) -> float | None:
        """Base imponible de la previa (``totales.totbas``, contrato §2)."""
        return self._total("totbas")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_documento(self) -> float | None:
        """Total con IVA de la previa (``totales.totdoc``)."""
        return self._total("totdoc")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def motivos_documento(self) -> list[dict[str, Any]]:
        """Motivos que no son de una línea concreta, con su texto (F-077 R26)."""
        return [_con_texto(m) for m in self.motivos if not m.get("referencia_linea")]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def motivos_linea_sueltos(self) -> list[dict[str, Any]]:
        """F-077 R24: motivos de línea cuya ``referencia_linea`` no está en la
        tabla de líneas del panel (``lineas``, que sale de la petición): p. ej.
        un rechazo local de sv9 sin petición. Con su texto (R26)."""
        en_tabla = {fila["referencia_linea"] for fila in self.lineas}
        return [
            _con_texto(m) for m in self.motivos
            if m.get("referencia_linea") and str(m.get("referencia_linea")) not in en_tabla
        ]
