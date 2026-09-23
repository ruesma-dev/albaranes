# application/services/origen_datos_resolver.py
"""Sella ``origen_datos``: de donde sale la OBRA del albaran (F-048, R17–R25).

IA1 hace dos lecturas independientes (D3): la del CORREO
(``lectura_correo.obra_codigos``) y la del PAPEL (``cabecera.obra_codigo``).
Este modulo las cruza y aplica la precedencia que decidio el humano el
2026-09-23 («el codigo indicado en el correo manda sobre lo que elija la IA
[...] pero si no cuadra se marcara para revision»), con la tabla de D5:

1. Se normaliza todo con ``normalizar_codigo`` (D9) y se descarta lo que no
   esta en la lista de TODAS las obras con contrato (``obras_conocidas``):
   un pedido o un telefono no son obras y no cuentan. Sin lista (``None``)
   cuentan todos, con ``validada = None``.
2. Ninguno cuenta ⇒ manda la IA con lo del papel (``correo_sin_dato``,
   ``ia_sin_lectura_correo`` o ``correo_fuera_de_lista``).
3. Cuenta UNO ⇒ manda el correo: la cabecera se escribe con el codigo COMO
   FIGURA EN LA LISTA (``945`` ⇒ ``0945``, para que la red de sv3 lo
   encuentre, R28); si el papel traia otro, ``discrepancia = true``.
4. Cuentan VARIOS ⇒ la cabecera no se toca: si el del papel es uno de
   ellos, ``correo_confirma_papel``; si no, ``correo_ambiguo`` (sv3 lo manda
   a revision).

Lo que este modulo NO hace, a proposito:

- **No mira el texto del correo** (D3, F-043): solo las listas que devolvio
  IA1. Del ``ContextoCorreo`` solo toma la huella y si se recorto.
- **No se fia de la IA para el sello** (R23): ``origen_datos`` lo escribe
  aqui y pisa lo que hubiera; ``lectura_correo`` sale del ``data``.
- **No elige la ``lectura`` ni el documento**: el worker le pasa la lectura
  del correo de FASE 1 (la de IA2 se ignora, D3) y el envelope FINAL, cuya
  cabecera es la de fase 2 (R25).
- **No muta** el envelope de entrada: devuelve uno nuevo.

Funcion PURA: sin I/O, sin red, sin BBDD, sin log.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ruesma_comun.contratos.origen_datos import (
    FUENTE_CORREO,
    FUENTE_PAPEL,
    MOTIVO_CORREO_AMBIGUO,
    MOTIVO_CORREO_CONFIRMA_PAPEL,
    MOTIVO_CORREO_FUERA_DE_LISTA,
    MOTIVO_CORREO_SIN_DATO,
    MOTIVO_CORREO_UNICO,
    MOTIVO_IA_SIN_LECTURA_CORREO,
    MOTIVO_SIN_CORREO,
    OrigenCampo,
    OrigenDatos,
    normalizar_codigo,
)

if TYPE_CHECKING:
    from ruesma_comun.correo import ContextoCorreo

CAMPO_LECTURA = "lectura_correo"
CAMPO_ORIGEN = "origen_datos"


def _campo(bloque: Any, nombre: str) -> Any:
    """Lee un campo venga la lectura como dict o como modelo validado."""
    if isinstance(bloque, Mapping):
        return bloque.get(nombre)
    return getattr(bloque, nombre, None)


def _leidos(lectura: Any) -> dict[str, str]:
    """Codigos leidos en el correo: normalizado -> como lo leyo IA1.

    Sin repetir (dos formas del mismo codigo cuentan como uno; se queda la
    primera) y sin los que normalizan a vacio, en el orden de la IA.
    """
    leidos: dict[str, str] = {}
    for codigo in _campo(lectura, "obra_codigos") or []:
        if codigo is None:
            continue
        clave = normalizar_codigo(str(codigo))
        if clave is not None:
            leidos.setdefault(clave, str(codigo))
    return leidos


def _resolver_obra(
    *,
    correo: ContextoCorreo | None,
    lectura: Any,
    papel: str | None,
    obras_conocidas: Mapping[str, str] | None,
) -> OrigenCampo:
    """La tabla de D5 para la obra."""
    base = {"fuente": FUENTE_PAPEL, "valor_final": papel, "valor_papel": papel}
    if correo is None:
        return OrigenCampo(motivo=MOTIVO_SIN_CORREO, **base)
    if lectura is None:
        return OrigenCampo(motivo=MOTIVO_IA_SIN_LECTURA_CORREO, **base)

    leidos = _leidos(lectura)
    if not leidos:
        return OrigenCampo(motivo=MOTIVO_CORREO_SIN_DATO, **base)

    if obras_conocidas is None:
        validada = None
        cuentan = dict(leidos)
    else:
        cuentan = {c: obras_conocidas[c] for c in leidos if c in obras_conocidas}
        validada = bool(cuentan)
    if not cuentan:
        return OrigenCampo(
            motivo=MOTIVO_CORREO_FUERA_DE_LISTA,
            candidatos_correo=list(leidos.values()),
            validada=validada,
            **base,
        )

    clave_papel = normalizar_codigo(papel)
    candidatos = list(cuentan.values())
    if len(cuentan) == 1:
        clave, codigo = next(iter(cuentan.items()))
        return OrigenCampo(
            fuente=FUENTE_CORREO,
            motivo=MOTIVO_CORREO_UNICO,
            valor_final=codigo,
            valor_correo=codigo,
            candidatos_correo=candidatos,
            valor_papel=papel,
            discrepancia=clave_papel is not None and clave_papel != clave,
            validada=validada,
        )

    motivo = MOTIVO_CORREO_CONFIRMA_PAPEL if clave_papel in cuentan else MOTIVO_CORREO_AMBIGUO
    return OrigenCampo(motivo=motivo, candidatos_correo=candidatos, validada=validada, **base)


def sellar_origen_datos(
    envelope: Mapping[str, Any],
    *,
    lectura: Any,
    correo: ContextoCorreo | None,
    obras_conocidas: Mapping[str, str] | None,
) -> dict:
    """Devuelve una copia del envelope con ``data.origen_datos`` sellado.

    ``lectura``: la ``lectura_correo`` de FASE 1 (dict, modelo o ``None``).
    ``correo``: el contexto que llego con el mensaje, o ``None``.
    ``obras_conocidas``: normalizado -> codigo de la lista, o ``None`` si no
    hay lista.
    """
    data = dict(envelope.get("data") or {})
    data.pop(CAMPO_LECTURA, None)
    cabecera = data.get("cabecera")
    papel = _campo(cabecera, "obra_codigo") if cabecera is not None else None

    obra = _resolver_obra(
        correo=correo, lectura=lectura, papel=papel, obras_conocidas=obras_conocidas,
    )
    if obra.valor_final != papel:
        data["cabecera"] = {**(cabecera or {}), "obra_codigo": obra.valor_final}

    origen = OrigenDatos(
        correo_presente=correo is not None,
        correo_sha256=correo.sha256 if correo is not None else None,
        correo_truncado=correo.truncado if correo is not None else False,
        evidencia=_campo(lectura, "evidencia") if correo is not None and lectura is not None else None,
        obra=obra,
    )
    data[CAMPO_ORIGEN] = origen.model_dump(mode="json")
    return {**envelope, "data": data}
