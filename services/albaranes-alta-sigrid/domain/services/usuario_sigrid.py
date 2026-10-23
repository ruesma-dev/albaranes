# domain/services/usuario_sigrid.py
"""Usuario y empleado de Sigrid a partir de quien aprobó (F-053 v8 R47; F-069).

Puro: ni red ni BBDD. ``dbo.usu`` no tiene el correo (``ele`` vacío en todos,
T0c), así que se casa la parte antes de la @ del UPN de Easy Auth con
``dbo.usu.cod``, igual que valida sigrid-api. Quien lo comprueba en Sigrid y
decide el Respaldo es el servicio (``AltaSigridService._resolver_usuario``).

F-069 añade aquí lo puro de la resolución:

- :func:`correo_ruesma`: el Correo de Ruesma (recortado y en minúsculas) o
  ``None``; :func:`candidato_usuario` se apoya en él sin cambiar su resultado.
- La **Lista** de excepciones (``ALTA_SIGRID_EQUIVALENCIAS_USUARIO``):
  :func:`leer_equivalencias` (R1, R2) y :func:`entrada_de` (por Login).
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

#: Longitud máxima de ``dbo.usu.cod`` que admite el contrato (``usu``, H6).
MAX_LOGIN = 24

#: Dominio de los correos de Ruesma (sin distinguir mayúsculas).
DOMINIO_RUESMA = "ruesma.es"

#: Variable de sv9 con la Lista (R1); va en los mensajes de error (R2).
VARIABLE_LISTA = "ALTA_SIGRID_EQUIVALENCIAS_USUARIO"
#: Únicas claves admitidas en el valor de una Entrada (R2).
CLAVES_ENTRADA = frozenset({"usu", "empide"})


def correo_ruesma(approved_by: str | None) -> str | None:
    """El Correo de Ruesma de quien aprobó: sin espacios alrededor y en
    minúsculas, si tiene una sola @, el dominio ``ruesma.es`` y la parte local
    no está vacía ni pasa de :data:`MAX_LOGIN`; si no, ``None`` (texto libre,
    ``DEFAULT_REVIEWER``, invitado ``#EXT#``, otro dominio o nada). Es el
    parámetro que se compara con ``dbo.emp.traele`` (F-069 R10)."""
    texto = (approved_by or "").strip().lower()
    if texto.count("@") != 1:
        return None
    local, dominio = texto.split("@")
    if dominio != DOMINIO_RUESMA:
        return None
    if not local or len(local) > MAX_LOGIN:
        return None
    return texto


def candidato_usuario(approved_by: str | None) -> str | None:
    """La parte antes de la @ si quien aprobó tiene Correo de Ruesma
    (:func:`correo_ruesma`); si no, ``None`` (y sv9 usará el Respaldo). La
    parte local va tal cual se escribió: el ``cod`` que se manda es el que
    devuelve Sigrid."""
    if correo_ruesma(approved_by) is None:
        return None
    return (approved_by or "").strip().split("@")[0]


# ---------------------------------------------------------------------- #
# La Lista de excepciones (F-069 R1, R2)
# ---------------------------------------------------------------------- #
@dataclass(frozen=True)
class Equivalencia:
    """Una Entrada de la Lista: el ``usu`` de ``dbo.usu`` y/o el ``ide`` de
    ``dbo.emp`` que corresponden a un Login (al menos uno de los dos)."""

    usu: str | None
    empide: int | None


class _Pares(list):
    """Un objeto JSON como lista de pares, para ver las claves repetidas."""


def _error(motivo: str) -> ValueError:
    # ValueError (no TypeError): pydantic-settings solo convierte ValueError
    # en error de arranque, como en R44.
    return ValueError(f"{VARIABLE_LISTA}: {motivo}")


def _repetida(pares: _Pares, *, sin_mayusculas: bool) -> str | None:
    """La primera clave que ya había salido antes (o ``None``)."""
    vistas: set[str] = set()
    for clave, _ in pares:
        normal = clave.casefold() if sin_mayusculas else clave
        if normal in vistas:
            return clave
        vistas.add(normal)
    return None


def _clave_valida(clave: str) -> None:
    if not clave:
        raise _error(f"la clave {clave!r} está vacía")
    if "@" in clave:
        raise _error(f"la clave {clave!r} lleva @: va el Login, no el correo")
    if any(c.isspace() for c in clave):
        raise _error(f"la clave {clave!r} lleva espacios")
    if len(clave) > MAX_LOGIN:
        raise _error(f"la clave {clave!r} pasa de {MAX_LOGIN} caracteres")


def _usu_valido(clave: str, valor: Any) -> str:
    limpio = valor.strip() if isinstance(valor, str) else ""
    if not limpio or len(limpio) > MAX_LOGIN:
        raise _error(
            f"el usu de {clave!r} debe ser un texto no vacío de hasta {MAX_LOGIN} caracteres",
        )
    return limpio


def _empide_valido(clave: str, valor: Any) -> int:
    # bool es int en Python: se rechaza explícitamente (R2).
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
        raise _error(f"el empide de {clave!r} debe ser un entero JSON mayor o igual que 1")
    return valor


def _entrada(clave: str, valor: Any) -> Equivalencia:
    if not isinstance(valor, _Pares):
        raise _error(f"el valor de {clave!r} debe ser un objeto con usu y/o empide")
    repetida = _repetida(valor, sin_mayusculas=False)
    if repetida is not None:
        raise _error(f"el valor de {clave!r} tiene la clave {repetida!r} repetida")
    campos = dict(valor)
    desconocidas = sorted(set(campos) - CLAVES_ENTRADA)
    if desconocidas:
        raise _error(f"el valor de {clave!r} tiene claves no admitidas: {desconocidas}")
    if not campos:
        raise _error(f"el valor de {clave!r} debe tener al menos usu o empide")
    return Equivalencia(
        usu=_usu_valido(clave, campos["usu"]) if "usu" in campos else None,
        empide=_empide_valido(clave, campos["empide"]) if "empide" in campos else None,
    )


def leer_equivalencias(texto: str | None) -> dict[str, Equivalencia]:
    """La Lista: Login (en minúsculas) → :class:`Equivalencia`.

    Ausente o vacía es ``{}`` (R1, lo normal). Cualquier caso de R2 es un
    ``ValueError`` con el motivo y la clave: sv9 no arranca."""
    if texto is None:
        return {}
    if not isinstance(texto, str):
        raise _error("debe ser un texto JSON")
    if not texto.strip():
        return {}
    try:
        datos = json.loads(texto, object_pairs_hook=_Pares)
    except json.JSONDecodeError as exc:
        raise _error(f"no es JSON válido: {exc}") from exc
    if not isinstance(datos, _Pares):
        raise _error("debe ser un objeto JSON (Login → {usu, empide})")
    repetida = _repetida(datos, sin_mayusculas=True)
    if repetida is not None:
        raise _error(f"la clave {repetida!r} está repetida (sin distinguir mayúsculas)")
    lista: dict[str, Equivalencia] = {}
    for clave, valor in datos:
        _clave_valida(clave)
        lista[clave.casefold()] = _entrada(clave, valor)
    return lista


def entrada_de(
    approved_by: str | None, equivalencias: Mapping[str, Equivalencia],
) -> Equivalencia | None:
    """La Entrada de quien aprobó: la de su Login, sin distinguir mayúsculas.
    Sin Correo de Ruesma no hay Entrada."""
    correo = correo_ruesma(approved_by)
    if correo is None:
        return None
    return equivalencias.get(correo.split("@")[0].casefold())
