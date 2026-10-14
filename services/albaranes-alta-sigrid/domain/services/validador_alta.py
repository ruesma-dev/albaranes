# domain/services/validador_alta.py
"""Validación local y construcción de la petición (F-053, R10–R13, R39, R43).

Puro: ni red ni BBDD. Si hay motivos, sv9 NO llama a sigrid-api:

- Motivos de R10 ⇒ ``no_admitido`` (se corrige en sv4 y «Solicitar alta»).
- Si no los hay, los de R39 (fecha no plausible, signos opuestos) y R46
  (línea casada con una línea de OTRO contrato, decisión D2 del humano) ⇒
  ``revisar``. No se evalúan si hay motivos de R10.

Sin motivos, devuelve la :class:`PeticionAlbaran` del modo extendido de
``POST /api/sigrid/albaran`` (contrato §2, v8 de F-009):

- Cabecera: ``cod_obra``, CIF normalizado (H21), ``cod_contrato`` de la
  valoración si lo tiene (también sin vinculadas, H31), ``referencia_externa``
  ``ALB-{document_id}``, ``su_referencia`` = número recortado, ``usu`` (H1; v8:
  el de quien aprobó o el Respaldo, R47, lo resuelve el servicio y llega aquí),
  ``fecha_albaran`` ``AAAAMMDD`` y ``empide``. Nunca ``lineas_recibidas`` ni
  ``naturaleza`` (H34).
- Una línea por cada línea con importe ≠ 0 (R13), por ``line_index`` y las que
  no lo tienen al final por ``id`` (H26). **Vinculada** (casa con una línea del
  contrato de la valoración con ``sigrid_ide`` y sin derivada): ``ctrpro_ide``
  y la cantidad convertida, sin ``unidad`` ni ``descripcion`` (H7) e ignorando
  ``producto_sigrid`` (R43). **Sin vincular**: producto efectivo (elegido o por
  familia, ``ruesma_comun.alta_sigrid``), descripción a 128 y unidad a 8.
  ``partida`` solo si ``codigo_partida_final`` no está vacío: sin partida =
  almacén (F-051 v4; no existe campo ``almacen``, H5). Sin ``paride`` (H17).
- ``precio`` = |importe| / |cantidad| a 6 decimales (neto, H14) y la cantidad
  con el signo del importe: ``cantidad · precio`` = importe.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from ruesma_comun.alta_sigrid import (
    es_linea_a_registrar,
    es_linea_vinculada,
    producto_efectivo,
    productos_admitidos,
)
from ruesma_comun.valoracion import esta_valorado

from domain.models.alta_models import (
    DatosAlta,
    EstadoAlta,
    LineaAlta,
    LineaPeticion,
    Motivo,
    PeticionAlbaran,
)

#: Longitudes máximas (contrato §2.1-§2.2; H6).
MAX_CODIGO = 24          # obra, CIF, contrato, partida
MAX_NUMERO = 128         # su_referencia
MAX_DESCRIPCION = 128
MAX_UNIDAD = 8

#: Plausibilidad de la fecha (H19): ni futura ni de hace más de un año.
DIAS_ATRAS_PLAUSIBLES = 365

#: Motivos locales que llevan a ``revisar`` (R39); el resto, a ``no_admitido``.
MOTIVOS_REVISAR_LOCAL = frozenset(
    {"fecha_no_plausible", "signo_incoherente", "linea_de_otro_contrato"},
)

PREFIJO_REFERENCIA = "ALB-"

_RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RE_CIF = re.compile(r"^[A-Z0-9]+$")
_SEPARADORES_CIF = re.compile(r"[\s.\-]")
_EPSILON = 1e-9


@dataclass(frozen=True)
class ConfigAlta:
    """Lo que el validador toma de la configuración (design §3). El ``usu``
    ya no: es por documento (v8, R47) y llega como argumento."""

    empide: int | None
    mapeo: Mapping[str, str]


def normalizar_cif(cif: str | None) -> str:
    """Mayúsculas, sin espacios, guiones ni puntos y sin ``ES`` delante de
    9 caracteres (H21)."""
    limpio = _SEPARADORES_CIF.sub("", (cif or "").upper())
    if len(limpio) == 11 and limpio.startswith("ES"):
        limpio = limpio[2:]
    return limpio


#: R14 (v8, U6): lo que se quita al comparar el número del proveedor con
#: ``dca.entref``. El SQL de la búsqueda quita LOS MISMOS (``REPLACE`` anidados).
SEPARADORES_REFERENCIA = (" ", ".", "-", "/")


def normalizar_referencia(numero: str | None) -> str:
    """Número del proveedor para casarlo con ``dca.entref`` (R14, T0b): en
    mayúsculas y sin espacio, ``.``, ``-`` ni ``/``. ``2.172.946`` y ``2172946``
    dan lo mismo; una errata (``2.2168.320``), no."""
    texto = (numero or "").upper()
    for separador in SEPARADORES_REFERENCIA:
        texto = texto.replace(separador, "")
    return texto


def _texto(valor: str | None) -> str:
    return (valor or "").strip()


def _con_importe(linea: LineaAlta) -> bool:
    return es_linea_a_registrar(linea.importe_calculado)


def es_vinculada(linea: LineaAlta, contrato: str | None) -> bool:
    """Casa con una línea del contrato de la valoración con ``sigrid_ide`` y
    sin línea derivada (glosario). Lo demás es sin vincular. La regla vive en
    ``comun`` (``es_linea_vinculada``): sv4 la usa para el selector de
    producto (R40, R41)."""
    return es_linea_vinculada(
        matched_contrato_line_id=linea.matched_contrato_line_id,
        derived_contrato_line_id=linea.derived_contrato_line_id,
        sigrid_ide=linea.ctrpro_ide,
        contrato_linea=linea.contrato_linea,
        contrato_valoracion=contrato,
    )


def _cantidad(linea: LineaAlta, vinculada: bool) -> float | None:
    return linea.cantidad_convertida if vinculada else linea.cantidad_albaran


def _descripcion(linea: LineaAlta) -> str:
    return _texto(linea.descripcion_linea) or _texto(linea.descripcion_merge)


def _fecha(texto: str | None) -> date | None:
    limpio = _texto(texto)
    if not _RE_FECHA.match(limpio):
        return None
    try:
        return date.fromisoformat(limpio)
    except ValueError:
        return None


def lineas_a_registrar(datos: DatosAlta) -> list[LineaAlta]:
    """Las de importe no nulo y ≠ 0 (R13), en el orden de la petición (H26)."""

    def clave(linea: LineaAlta) -> tuple[int, int, int]:
        if linea.merge_line_id is not None and linea.line_index is not None:
            return (0, linea.line_index, linea.id)
        return (1, linea.id, 0)

    return sorted((l for l in datos.lineas if _con_importe(l)), key=clave)


def importes_por_referencia(datos: DatosAlta) -> dict[str, float]:
    """``importe_calculado`` de cada línea a registrar, por ``referencia_linea``."""
    return {l.referencia_linea: float(l.importe_calculado) for l in lineas_a_registrar(datos)}


def lineas_de_otro_contrato(datos: DatosAlta) -> list[LineaAlta]:
    """R46 (D2): líneas a registrar casadas con una línea de contrato cuyo
    contrato no es el de la valoración (también si la valoración no tiene).
    «No debería ocurrir nunca» (humano, 2026-10-06): es un fallo aguas arriba.
    Sin código de contrato en la línea casada no se puede afirmar: no cuenta."""
    contrato = _texto(datos.cabecera.contrato_codigo)
    return [
        linea for linea in lineas_a_registrar(datos)
        if linea.matched_contrato_line_id is not None
        and _texto(linea.contrato_linea)
        and _texto(linea.contrato_linea) != contrato
    ]


def estado_de_motivos(motivos: list[Motivo]) -> EstadoAlta:
    """``revisar`` si todos son de R39; ``no_admitido`` en otro caso."""
    if motivos and all(m.codigo in MOTIVOS_REVISAR_LOCAL for m in motivos):
        return EstadoAlta.REVISAR
    return EstadoAlta.NO_ADMITIDO


def _motivos_cabecera(datos: DatosAlta) -> list[Motivo]:
    cab = datos.cabecera
    motivos: list[Motivo] = []

    obra = _texto(cab.obra_codigo)
    if not obra:
        motivos.append(Motivo("falta_obra"))
    elif len(obra) > MAX_CODIGO:
        motivos.append(Motivo("campo_demasiado_largo", "cod_obra"))

    if not _texto(cab.proveedor_cif):
        motivos.append(Motivo("falta_cif"))
    else:
        cif = normalizar_cif(cab.proveedor_cif)
        if not _RE_CIF.match(cif):
            motivos.append(Motivo("cif_no_valido", cif))
        elif len(cif) > MAX_CODIGO:
            motivos.append(Motivo("campo_demasiado_largo", "cif_proveedor"))

    numero = _texto(cab.numero_albaran)
    if not numero:
        motivos.append(Motivo("falta_numero_albaran"))
    elif len(numero) > MAX_NUMERO:
        motivos.append(Motivo("campo_demasiado_largo", "su_referencia"))

    if len(_texto(cab.contrato_codigo)) > MAX_CODIGO:
        motivos.append(Motivo("campo_demasiado_largo", "cod_contrato"))

    if _fecha(cab.fecha) is None:
        motivos.append(Motivo("fecha_ilegible", _texto(cab.fecha)))

    if not esta_valorado(cab.valoracion_status, [l.importe_calculado for l in datos.lineas]):
        motivos.append(Motivo("no_valorado", _texto(cab.valoracion_status)))
    return motivos


def _motivos_lineas(datos: DatosAlta, mapeo: Mapping[str, str]) -> list[Motivo]:
    cab = datos.cabecera
    admitidos = productos_admitidos(mapeo)
    lineas = lineas_a_registrar(datos)
    if not lineas:
        return [Motivo("sin_lineas")]

    motivos: list[Motivo] = []
    for linea in lineas:
        ref = linea.referencia_linea
        vinculada = es_vinculada(linea, cab.contrato_codigo)
        cantidad = _cantidad(linea, vinculada)
        if vinculada and cantidad is None:
            motivos.append(Motivo("cantidad_sin_convertir", "", ref))
        elif cantidad is None or abs(cantidad) <= _EPSILON:
            motivos.append(Motivo("cantidad_no_valida", "", ref))
        if not vinculada:
            if not _descripcion(linea):
                motivos.append(Motivo("falta_descripcion", "", ref))
            producto = producto_efectivo(
                linea.producto_sigrid, linea.tipo_familia, cab.clasificacion, mapeo,
            )
            if producto not in admitidos:
                motivos.append(Motivo("producto_no_admitido", producto, ref))
        if len(_texto(linea.codigo_partida_final)) > MAX_CODIGO:
            motivos.append(Motivo("campo_demasiado_largo", "partida", ref))
    return motivos


def _motivos_r39(datos: DatosAlta, hoy: date) -> list[Motivo]:
    cab = datos.cabecera
    motivos: list[Motivo] = []
    fecha = _fecha(cab.fecha)
    if fecha is not None and (fecha > hoy or fecha < hoy - timedelta(days=DIAS_ATRAS_PLAUSIBLES)):
        motivos.append(Motivo("fecha_no_plausible", fecha.isoformat()))
    for linea in lineas_a_registrar(datos):
        cantidad = _cantidad(linea, es_vinculada(linea, cab.contrato_codigo))
        importe = linea.importe_calculado
        if cantidad is None or importe is None:
            continue
        if (cantidad > 0 and importe < 0) or (cantidad < 0 and importe > 0):
            motivos.append(Motivo(
                "signo_incoherente", f"cantidad {cantidad}, importe {importe}",
                linea.referencia_linea,
            ))
    contrato = _texto(cab.contrato_codigo) or "sin contrato"
    for linea in lineas_de_otro_contrato(datos):
        motivos.append(Motivo(
            "linea_de_otro_contrato",
            f"{_texto(linea.contrato_linea)} (valoración: {contrato})",
            linea.referencia_linea,
        ))
    return motivos


def _linea_peticion(linea: LineaAlta, datos: DatosAlta, config: ConfigAlta) -> LineaPeticion:
    cab = datos.cabecera
    vinculada = es_vinculada(linea, cab.contrato_codigo)
    cantidad = abs(float(_cantidad(linea, vinculada)))
    importe = float(linea.importe_calculado)
    con_signo = -cantidad if importe < 0 else cantidad
    precio = round(abs(importe) / cantidad, 6)
    partida = _texto(linea.codigo_partida_final) or None
    if vinculada:
        return LineaPeticion(
            referencia_linea=linea.referencia_linea,
            ctrpro_ide=linea.ctrpro_ide,
            cantidad=con_signo,
            precio=precio,
            partida=partida,
        )
    return LineaPeticion(
        referencia_linea=linea.referencia_linea,
        producto=producto_efectivo(
            linea.producto_sigrid, linea.tipo_familia, cab.clasificacion, config.mapeo,
        ),
        descripcion=_descripcion(linea)[:MAX_DESCRIPCION],
        unidad=_texto(linea.unidad_albaran)[:MAX_UNIDAD] or None,
        cantidad=con_signo,
        precio=precio,
        partida=partida,
    )


def validar_y_construir(
    datos: DatosAlta, config: ConfigAlta, hoy: date, usu: str,
) -> PeticionAlbaran | list[Motivo]:
    """Motivos de R10 (o, si no hay, de R39) o la petición de R12, con ``usu``
    (el login ya resuelto, R47)."""
    motivos = _motivos_cabecera(datos) + _motivos_lineas(datos, config.mapeo)
    if motivos:
        return motivos
    motivos = _motivos_r39(datos, hoy)
    if motivos:
        return motivos

    cab = datos.cabecera
    fecha = _fecha(cab.fecha)
    return PeticionAlbaran(
        cod_obra=_texto(cab.obra_codigo),
        cif_proveedor=normalizar_cif(cab.proveedor_cif),
        cod_contrato=_texto(cab.contrato_codigo) or None,
        referencia_externa=f"{PREFIJO_REFERENCIA}{cab.document_id}",
        su_referencia=_texto(cab.numero_albaran),
        usu=usu,
        fecha_albaran=int(fecha.strftime("%Y%m%d")),
        empide=config.empide,
        lineas=tuple(_linea_peticion(l, datos, config) for l in lineas_a_registrar(datos)),
    )
