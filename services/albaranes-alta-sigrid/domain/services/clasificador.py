# domain/services/clasificador.py
"""Respuesta de sigrid-api → estado del alta (F-053, design §2; R15, R18, R20, R21).

Puro. La tabla de códigos es un DATO (:data:`CODIGOS_CABECERA`,
:data:`CODIGOS_LINEA`), con los códigos del contrato de F-009 v8.3 (§3.3;
``sigrid-api`` ``871cc0c``, F-104):

- Lo que se corrige en sv4 o se da de alta a mano ⇒ ``no_admitido``.
- ``referencia_en_conflicto`` (otro albarán lleva nuestra referencia) ⇒ ``revisar``.
- Configuración o fallo del servicio, no del revisor ⇒ ``error``; también un
  400 sin código, 401/403, otro 4xx y cualquier código que no esté en la tabla
  (H25). En ``lineas_no_validas``, si alguna línea trae un código de ``error``
  o desconocido, gana ``error``.
- 5xx, tiempo agotado, conexión o respuesta ilegible: ``incierto`` si era la
  grabación (pudo escribir; se retoma tras la Espera por idempotencia) y
  ``error`` si era la previa (R21).
- 200 ``creado`` o ``idempotente`` ⇒ ``registrado``; ``previsto`` en la previa
  ⇒ ``None`` (toca comparar, R17).
"""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from domain.models.alta_models import (
    ErrorAlta,
    EstadoAlta,
    Motivo,
    RespuestaAlta,
    TipoFallo,
)

_NO_ADMITIDO = EstadoAlta.NO_ADMITIDO
_REVISAR = EstadoAlta.REVISAR
_ERROR = EstadoAlta.ERROR

#: ``details.codigo`` de cabecera → estado.
CODIGOS_CABECERA: Mapping[str, EstadoAlta] = MappingProxyType({
    # Se corrige obra o contrato en sv4, o alta a mano en Sigrid.
    "obra_no_encontrada": _NO_ADMITIDO,
    "obra_ambigua": _NO_ADMITIDO,
    "contrato_no_encontrado": _NO_ADMITIDO,
    "contrato_ambiguo": _NO_ADMITIDO,
    # retirado en la v8.3: se quita tras F-104 T7 (T8, tras la verificación M2).
    "proveedor_sin_albaran_previo": _NO_ADMITIDO,
    # Contrato v8.3 (F-015 de sigrid-api).
    "proveedor_no_encontrado": _NO_ADMITIDO,
    "proveedor_ambiguo": _NO_ADMITIDO,
    "retencion_no_soportada": _NO_ADMITIDO,
    "almacen_de_obra_no_resuelto": _NO_ADMITIDO,   # H13
    "demasiadas_lineas": _NO_ADMITIDO,             # H22
    # Otro albarán de Sigrid lleva nuestra referencia: mirarlo.
    "referencia_en_conflicto": _REVISAR,
    # Configuración o servicio: no es del revisor.
    "escritura_albaranes_deshabilitada": _ERROR,
    "base_de_datos_no_permitida": _ERROR,
    "referencia_no_permitida": _ERROR,
    "obra_de_empresa_no_permitida": _ERROR,
    "usuario_no_valido": _ERROR,
    "estado_inicial_no_encontrado": _ERROR,
    "peticion_mixta": _ERROR,
    # ERP intacto: «Solicitar alta» reintenta con la misma referencia.
    "colision_de_clave": _ERROR,
    "filas_afectadas_inesperadas": _ERROR,
})

#: Código de cabecera que trae el detalle por línea.
CODIGO_LINEAS_NO_VALIDAS = "lineas_no_validas"

#: ``details.lineas[].codigo`` → estado.
CODIGOS_LINEA: Mapping[str, EstadoAlta] = MappingProxyType({
    "linea_no_es_del_contrato": _NO_ADMITIDO,
    "partida_no_encontrada": _NO_ADMITIDO,
    "partida_ambigua": _NO_ADMITIDO,       # sin paride hasta F-049 (H17)
    "partida_no_imputable": _NO_ADMITIDO,
    "paride_no_valido": _NO_ADMITIDO,
    "analitica_no_resuelta": _NO_ADMITIDO,  # la obra no tiene <obra>.<sufijo> (H10)
    "producto_no_permitido": _ERROR,
    "producto_no_encontrado": _ERROR,       # H24
    "naturaleza_no_valida": _ERROR,         # configuración de sigrid-api (H34)
    "precio_negativo": _ERROR,              # sv9 nunca lo manda: es un fallo
})

_TRANSITORIOS = frozenset({
    TipoFallo.SERVIDOR, TipoFallo.TIEMPO_AGOTADO, TipoFallo.CONEXION,
    TipoFallo.RESPUESTA_INVALIDA,
})

ESTADOS_200_REGISTRADO = frozenset({"creado", "idempotente"})
ESTADO_PREVISTO = "previsto"


def _clasificar_lineas(error: ErrorAlta) -> EstadoAlta:
    codigos = [str(l.get("codigo") or "") for l in error.lineas]
    if not codigos:
        return _ERROR
    estados = [CODIGOS_LINEA.get(c, _ERROR) for c in codigos]
    return _ERROR if _ERROR in estados else _NO_ADMITIDO


def _clasificar_error(error: ErrorAlta, grabacion: bool) -> EstadoAlta:
    if error.tipo in _TRANSITORIOS:
        return EstadoAlta.INCIERTO if grabacion else _ERROR
    if error.tipo is not TipoFallo.RECHAZO or not error.codigo:
        return _ERROR
    if error.codigo == CODIGO_LINEAS_NO_VALIDAS:
        return _clasificar_lineas(error)
    return CODIGOS_CABECERA.get(error.codigo, _ERROR)


def clasificar(resultado: RespuestaAlta | ErrorAlta, *, grabacion: bool) -> EstadoAlta | None:
    """Estado al que lleva la respuesta, o ``None`` si es una previa que
    hay que comparar (R17)."""
    if isinstance(resultado, ErrorAlta):
        return _clasificar_error(resultado, grabacion)
    if resultado.estado in ESTADOS_200_REGISTRADO:
        return EstadoAlta.REGISTRADO
    if resultado.estado == ESTADO_PREVISTO:
        # En la grabación, «previsto» es que sigrid-api no escribió.
        return _ERROR if grabacion else None
    # Un 200 con un estado que no conocemos: en la grabación no sabemos si
    # escribió (incierto); en la previa, fallo del servicio.
    return EstadoAlta.INCIERTO if grabacion else _ERROR


def motivos_de_error(error: ErrorAlta) -> list[Motivo]:
    """El código de cabecera (o el tipo de fallo) y una línea por cada
    ``details.lineas`` (R18, R29)."""
    if error.codigo:
        cabecera = error.codigo
    elif error.status is not None and error.tipo is not TipoFallo.SERVIDOR:
        cabecera = f"http_{error.status}"
    else:
        cabecera = error.tipo.value
    motivos = [Motivo(cabecera, error.mensaje)]
    for linea in error.lineas:
        referencia = linea.get("referencia_linea")
        motivos.append(Motivo(
            str(linea.get("codigo") or ""),
            str(linea.get("mensaje") or ""),
            None if referencia is None else str(referencia),
        ))
    return motivos
