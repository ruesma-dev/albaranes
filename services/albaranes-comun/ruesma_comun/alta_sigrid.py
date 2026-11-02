# ruesma_comun/alta_sigrid.py
"""Producto genérico de Sigrid de las líneas sin vincular (F-053, R38-R44).

Decisión del humano (2026-10-05): una línea que no casa con el contrato se da
de alta en Sigrid con un producto genérico de la lista blanca de sigrid-api,
**por línea** y según su familia: alquiler de maquinaria → ``QA9999``, medios
auxiliares → ``XA9999``, el resto → ``MA9999``. El administrativo lo cambia
en sv4 antes de aprobar (``albaran_line_valuations.producto_sigrid``; nulo =
por defecto).

El por defecto **no se guarda**: se calcula al leer, en sv4 al pintar y en sv9
al construir la petición, con esta misma función y el mismo mapeo
(``ALTA_SIGRID_PRODUCTO_POR_DEFECTO``, con el mismo valor en los dos).

Funciones puras, sin E/S.
"""
from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

from ruesma_comun.contratos.familias import familia_efectiva
from ruesma_comun.importes import (
    clasificar_descuento,
    difieren,
    importe_de_linea,
    unitario_despejado,
)

#: Estados del alta (``albaran_altas_sigrid.estado``) que bloquean el documento:
#: sv4 no deja tocarlo (R25) y sv3 no lo borra al reingresar su PDF (R45). Son
#: los ``ESTADOS_BLOQUEANTES`` de sv9, que un test de sv9 ata a estos.
ESTADOS_ALTA_BLOQUEANTES: frozenset[str] = frozenset({"en_curso", "incierto", "registrado"})

#: Estados desde los que un alta se puede repetir: sv9 la reprocesa (R5) y sv4
#: ofrece «Solicitar alta en Sigrid» (R30). Los ``_REPETIBLES`` de sv9.
ESTADOS_ALTA_REPETIBLES: frozenset[str] = frozenset({
    "no_admitido", "revisar", "error", "simulado", "anulado",
})

#: Por debajo de esto un importe cuenta como cero (glosario: «línea a registrar»).
_EPSILON = 1e-9

#: Clave comodín del mapeo: la familia que no tenga clave propia (o ninguna).
CLAVE_COMODIN = "*"

#: Mapeo por defecto (design §7). Sus valores deben estar en la lista blanca
#: ``SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO`` de sigrid-api.
MAPEO_PRODUCTO_POR_DEFECTO: dict[str, str] = {
    "alquiler_maquinaria": "QA9999",
    "medios_auxiliares": "XA9999",
    CLAVE_COMODIN: "MA9999",
}

#: El mismo mapeo como texto, para el defecto de los ``settings``.
MAPEO_PRODUCTO_POR_DEFECTO_TEXTO = json.dumps(MAPEO_PRODUCTO_POR_DEFECTO)

#: Nombre legible de cada genérico (para sv4). Sin nombre, se enseña el código.
NOMBRES_PRODUCTO: dict[str, str] = {
    "MA9999": "Suministro de materiales",
    "QA9999": "Alquiler de maquinaria",
    "XA9999": "Alquiler de medios auxiliares",
}


def leer_mapeo(texto: str) -> dict[str, str]:
    """Lee ``ALTA_SIGRID_PRODUCTO_POR_DEFECTO`` (R44).

    Debe ser un objeto JSON cuyos valores sean textos no vacíos y que tenga
    la clave ``*``. Si no, ``ValueError`` con el motivo: sv4 y sv9 no deben
    arrancar con un mapeo roto (un producto vacío acabaría en un 400 de
    sigrid-api en cada alta).
    """
    if not isinstance(texto, str):
        # ValueError y no TypeError a propósito (R44): los validadores de
        # pydantic-settings solo convierten ValueError en error de arranque.
        raise ValueError("ALTA_SIGRID_PRODUCTO_POR_DEFECTO debe ser un texto JSON")  # noqa: TRY004
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"ALTA_SIGRID_PRODUCTO_POR_DEFECTO no es JSON válido: {exc}"
        ) from exc
    if not isinstance(datos, dict):
        raise ValueError("ALTA_SIGRID_PRODUCTO_POR_DEFECTO debe ser un objeto JSON")  # noqa: TRY004
    for clave, valor in datos.items():
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(
                f"ALTA_SIGRID_PRODUCTO_POR_DEFECTO: el producto de {clave!r} "
                "debe ser un texto no vacío"
            )
    if CLAVE_COMODIN not in datos:
        raise ValueError(
            f"ALTA_SIGRID_PRODUCTO_POR_DEFECTO debe tener la clave {CLAVE_COMODIN!r}"
        )
    return dict(datos)


def leer_instante_utc(texto: str | None) -> datetime | None:
    """``ALTA_SIGRID_DESDE_UTC`` (ISO 8601) a instante UTC, igual en sv4 y sv9.

    Vacío = ``None`` (feature apagada); sin zona = UTC. Ilegible:
    ``ValueError`` (los ``settings`` no arrancan)."""
    limpio = (texto or "").strip()
    if not limpio:
        return None
    instante = datetime.fromisoformat(limpio.replace("Z", "+00:00"))
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)
    return instante.astimezone(UTC)


def espera_pasada(
    ultimo_intento: datetime | None, ahora: datetime, espera: timedelta,
) -> bool:
    """¿Pasó la Espera desde el último intento? (R7, R8, R30). Sin último
    intento conocido, se da por pasada. sv9 decide con esto si retoma un
    ``en_curso``/``incierto``, y sv4 si ofrece «Solicitar alta»."""
    if ultimo_intento is None:
        return True
    return ahora - ultimo_intento >= espera


def es_linea_vinculada(
    *,
    matched_contrato_line_id: int | None,
    derived_contrato_line_id: int | None,
    sigrid_ide: int | None,
    contrato_linea: str | None,
    contrato_valoracion: str | None,
) -> bool:
    """Vinculada (glosario): casa con una línea del contrato de la valoración
    que tiene ``sigrid_ide``, sin línea derivada. Lo demás es sin vincular.

    sv9 manda la vinculada por ``ctrpro_ide`` (R12, R43) y sv4 solo deja
    elegir producto en las sin vincular (R40, R41): las dos puntas deciden
    con esta función."""
    contrato = (contrato_valoracion or "").strip()
    return (
        matched_contrato_line_id is not None
        and derived_contrato_line_id is None
        and sigrid_ide is not None
        and bool(contrato)
        and (contrato_linea or "").strip() == contrato
    )


def es_linea_a_registrar(importe_calculado: float | None) -> bool:
    """Línea a registrar (glosario): ``importe_calculado`` no nulo y ≠ 0
    (positivo o negativo). Las demás no van en la petición (R13)."""
    return importe_calculado is not None and abs(float(importe_calculado)) > _EPSILON


#: (F-110 R5, R14) Único valor de ``ALTA_SIGRID_ENVIAR_DTO`` que enciende la
#: guarda del descuento por línea (como ``ALTA_SIGRID_COMMIT``).
LITERAL_ENVIAR_DTO = "true"


def enviar_dto_activo(valor: str | None) -> bool:
    """(F-110 R5, R14) ¿Encendida la guarda? Solo con el literal ``true``: sin
    ``strip`` ni mayúsculas. sv4 y sv9 la leen con esta función."""
    return valor == LITERAL_ENVIAR_DTO


class LineaASigrid(tuple):
    """(F-110 R1) Cantidad, precio y ``dto`` que sv9 pone en la línea.

    Es la tupla ``(cantidad, precio)`` de F-106 (se desempaqueta y se compara
    igual) con el atributo ``dto`` (``None`` = sin descuento). Con ``dto``, solo
    es igual a otra ``LineaASigrid`` con el mismo ``dto``: nunca a la tupla de
    F-106. Inmutable.
    """

    __slots__ = ()

    def __new__(cls, cantidad: float, precio: float, dto: float | None = None) -> LineaASigrid:
        return super().__new__(cls, (cantidad, precio, dto))

    # La tupla guarda los tres; se ve (y se desempaqueta) como la de F-106.
    def __len__(self) -> int:
        return 2

    def __iter__(self):  # type: ignore[override]
        return iter((self.cantidad, self.precio))

    def __getitem__(self, indice):  # type: ignore[override]
        return (self.cantidad, self.precio)[indice]

    @property
    def cantidad(self) -> float:
        return tuple.__getitem__(self, 0)

    @property
    def precio(self) -> float:
        return tuple.__getitem__(self, 1)

    @property
    def dto(self) -> float | None:
        return tuple.__getitem__(self, 2)

    def _clave(self) -> tuple[float, float, float | None]:
        return (self.cantidad, self.precio, self.dto)

    def __eq__(self, otro: object) -> bool:
        if isinstance(otro, LineaASigrid):
            return self._clave() == otro._clave()
        if isinstance(otro, tuple):
            return self.dto is None and (self.cantidad, self.precio) == otro
        return NotImplemented

    def __ne__(self, otro: object) -> bool:
        igual = self.__eq__(otro)
        return igual if igual is NotImplemented else not igual

    def __hash__(self) -> int:
        if self.dto is None:
            return hash((self.cantidad, self.precio))
        return hash(self._clave())

    def __repr__(self) -> str:
        return f"LineaASigrid(cantidad={self.cantidad!r}, precio={self.precio!r}, dto={self.dto!r})"


def _finito(valor: object) -> float | None:
    """``float`` finito o ``None`` (nulo, booleano, ilegible, NaN o infinito)."""
    if valor is None or isinstance(valor, bool):
        return None
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) else None


def _dto_a_sigrid(descuento: object) -> float | None:
    """(F-110 R3, D6) ``round(d, 2)`` si el descuento es aplicable y no se
    queda en 0 al redondear; si no, ``None`` (la línea va como hoy)."""
    estado, valor = clasificar_descuento(descuento)
    if estado != "aplicable" or valor is None:
        return None
    dto = round(valor, 2)
    return dto if dto > 0 else None


def linea_a_sigrid(
    *,
    vinculada: bool,
    cantidad_albaran: float | None,
    cantidad_convertida: float | None,
    importe: float | None,
    precio: object = None,
    descuento: object = None,
    con_descuento: bool = False,
) -> LineaASigrid | None:
    """(F-106 R2, F-110 R1–R4) La línea que sv9 pone en la petición.

    La cantidad es la convertida si la línea va vinculada (``ctrpro_ide``, en
    la unidad del contrato) y la del albarán si no, con el signo del importe.

    - Sin ``con_descuento`` (la guarda apagada) o sin descuento aplicable: el
      precio es ``|importe| / |cantidad|`` a 6 decimales (neto, H14) y ``dto``
      nulo: lo de F-106.
    - Con ``con_descuento`` y descuento aplicable: ``dto = round(d, 2)`` y el
      precio es ``round(P, 6)`` si con ese ``dto`` y la cantidad a Sigrid da el
      importe al céntimo (``importes.difieren``); si no, el bruto despejado
      (``importes.unitario_despejado``).

    ``None`` sin cantidad (nula o 0), sin importe legible o con un precio que
    no se puede despejar (100 %). Nunca lanza. Es la ÚNICA definición de «a
    Sigrid»: sv9 la manda y sv4 la enseña.
    """
    cantidad = cantidad_convertida if vinculada else cantidad_albaran
    if cantidad is None or importe is None:
        return None
    try:
        cantidad_num = abs(float(cantidad))
        importe_num = float(importe)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(cantidad_num) and math.isfinite(importe_num)):
        return None
    if cantidad_num <= _EPSILON:
        return None
    con_signo = -cantidad_num if importe_num < 0 else cantidad_num
    importe_abs = abs(importe_num)
    dto = _dto_a_sigrid(descuento) if con_descuento else None
    if dto is None:
        return LineaASigrid(con_signo, round(importe_abs / cantidad_num, 6))
    precio_num = _finito(precio)
    if precio_num is not None:
        precio_p = round(precio_num, 6)
        calculado = importe_de_linea(
            cantidad=cantidad_num, precio_unitario=precio_p, descuento_pct=dto,
        )
        if calculado is not None and not difieren(calculado, importe_abs):
            return LineaASigrid(con_signo, precio_p, dto)
    despejado = unitario_despejado(importe=importe_abs, cantidad=cantidad_num, descuento_pct=dto)
    if despejado is None:
        return None
    return LineaASigrid(con_signo, despejado, dto)


def clasificacion_documento(
    tipologia: str | None, tipologia_mixta: bool | None,
) -> dict[str, object] | None:
    """Clasificación del documento para ``producto_efectivo`` desde las
    columnas del merge (``tipologia``, ``tipologia_mixta``): ``None`` sin
    familia (documento anterior a F-043). La usan sv9 al construir la
    petición y sv4 al pintar el producto (R38, R40)."""
    familia = (tipologia or "").strip()
    if not familia:
        return None
    return {"familia": familia, "mixto": bool(tipologia_mixta)}


def productos_admitidos(mapeo: Mapping[str, str]) -> frozenset[str]:
    """Productos que se pueden elegir o mandar: los valores del mapeo."""
    return frozenset(mapeo.values())


def producto_efectivo(
    elegido: str | None,
    tipo_familia_linea: str | None,
    clasificacion: object,
    mapeo: Mapping[str, str],
) -> str:
    """Producto con el que se da de alta una línea sin vincular (R38, R40).

    El elegido en sv4 si lo hay; si no, el del mapeo para la familia efectiva
    de la línea (``familia_efectiva``: la de la línea; si no, la del documento
    salvo mixto), o el de ``*`` si esa familia no tiene clave o no hay
    familia. ``clasificacion`` es la del documento (objeto o diccionario con
    ``familia`` y ``mixto``) o ``None``.
    """
    if elegido is not None and elegido.strip():
        return elegido.strip()
    familia = familia_efectiva(tipo_familia_linea, clasificacion)
    if familia is not None and familia in mapeo:
        return mapeo[familia]
    return mapeo[CLAVE_COMODIN]


def nombre_producto(codigo: str) -> str:
    """Nombre legible del producto o, si no se conoce, el propio código."""
    return NOMBRES_PRODUCTO.get(codigo, codigo)
