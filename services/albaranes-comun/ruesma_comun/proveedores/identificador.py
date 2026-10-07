# ruesma_comun/proveedores/identificador.py
"""Identificador fiscal español: normalización y carácter de control.

F-062 (R1, R2). Lo usa sv3 en la red de proveedor: un CIF leído con el
control inválido es, casi seguro, una lectura errónea de la IA (los tres
casos medidos el 2026-10-07 lo eran), y solo un candidato de Sigrid con
identificador válido puede aplicarse sin que lo confirme el revisor.

Puro y sin dependencias: sv4 (al elegir proveedor) y F-055 (al verificar
la elección de IA2) pueden importarlo tal cual.
"""
from __future__ import annotations

import re

#: Caracteres que sobreviven a la normalización.
_ALFANUMERICOS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

#: Prefijo de país que se quita cuando deja un identificador de 9.
_PREFIJO_PAIS = "ES"
_LONGITUD_CON_PREFIJO = 11

#: CIF: letra de tipo + 7 dígitos + carácter de control.
_RE_CIF = re.compile(r"[ABCDEFGHJNPQRSUVW][0-9]{7}[0-9A-J]")
#: Tipos de CIF cuyo control es SIEMPRE un dígito.
_CIF_CONTROL_DIGITO = frozenset("ABEH")
#: Tipos de CIF cuyo control es SIEMPRE una letra.
_CIF_CONTROL_LETRA = frozenset("NPQRSW")
#: Letra de control del CIF, indexada por el dígito de control.
_LETRAS_CONTROL_CIF = "JABCDEFGHI"

#: NIF: 8 dígitos + letra; NIE: X/Y/Z + 7 dígitos + letra.
_RE_NIF = re.compile(r"[0-9]{8}[A-Z]")
_RE_NIE = re.compile(r"[XYZ][0-9]{7}[A-Z]")
_VALOR_PREFIJO_NIE = {"X": "0", "Y": "1", "Z": "2"}
#: Letra del NIF/NIE, indexada por el resto entre 23.
_LETRAS_NIF = "TRWAGMYFPDXBNJZSQVHLCKE"

#: NIF especial (K, L, M): solo se comprueba el formato.
_RE_NIF_ESPECIAL = re.compile(r"[KLM][0-9]{7}[A-Z]")


def normalizar_cif(valor: str | None) -> str | None:
    """Mayúsculas, solo ``[A-Z0-9]`` y sin el prefijo ``ES`` de país.

    El prefijo solo se quita cuando el resultado tiene 11 caracteres y
    empieza por ``ES`` (``ESB66056201`` → ``B66056201``); un CIF de tipo
    ``E`` conserva su letra. Vacío o ``None`` ⇒ ``None``.
    """
    limpio = "".join(c for c in (valor or "").upper() if c in _ALFANUMERICOS)
    if len(limpio) == _LONGITUD_CON_PREFIJO and limpio.startswith(_PREFIJO_PAIS):
        limpio = limpio[len(_PREFIJO_PAIS):]
    return limpio or None


def _digito_control_cif(cuerpo: str) -> int:
    """Dígito de control de los 7 dígitos de un CIF.

    Las posiciones impares (1.ª, 3.ª, 5.ª y 7.ª) se doblan y se suman sus
    cifras; las pares se suman tal cual. Control = ``(10 - suma % 10) % 10``.
    """
    suma = 0
    for posicion, caracter in enumerate(cuerpo):
        cifra = int(caracter)
        if posicion % 2 == 0:
            doble = cifra * 2
            suma += doble // 10 + doble % 10
        else:
            suma += cifra
    return (10 - suma % 10) % 10


def _cif_valido(cif: str) -> bool:
    control = _digito_control_cif(cif[1:8])
    final = cif[8]
    digito_ok = final == str(control)
    letra_ok = final == _LETRAS_CONTROL_CIF[control]
    tipo = cif[0]
    if tipo in _CIF_CONTROL_DIGITO:
        return digito_ok
    if tipo in _CIF_CONTROL_LETRA:
        return letra_ok
    return digito_ok or letra_ok


def _letra_nif_valida(numero: str, letra: str) -> bool:
    return _LETRAS_NIF[int(numero) % 23] == letra


def identificador_fiscal_valido(valor: str | None) -> bool:
    """``True`` solo para un CIF, NIF o NIE español con el control correcto,
    o un NIF especial (``K``, ``L``, ``M``) con formato correcto.

    Normaliza antes (``normalizar_cif``). Un identificador extranjero
    (``FR…``, ``PT…``) no es válido aquí.
    """
    ident = normalizar_cif(valor)
    if ident is None:
        return False
    if _RE_CIF.fullmatch(ident):
        return _cif_valido(ident)
    if _RE_NIF.fullmatch(ident):
        return _letra_nif_valida(ident[:8], ident[8])
    if _RE_NIE.fullmatch(ident):
        return _letra_nif_valida(_VALOR_PREFIJO_NIE[ident[0]] + ident[1:8], ident[8])
    return bool(_RE_NIF_ESPECIAL.fullmatch(ident))
