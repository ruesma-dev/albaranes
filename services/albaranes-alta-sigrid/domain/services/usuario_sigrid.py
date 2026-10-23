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
- Los códigos ``AVISO_*`` de los Avisos de resolución y
  :func:`clasificar_empleados_correo` (R10, R11), que importa también el
  script de medición (R25).
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from domain.models.alta_models import AvisoResolucion, EmpleadoSigrid

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


# ---------------------------------------------------------------------- #
# Avisos de resolución y Empleados del correo (F-069 R6, R9–R13)
# ---------------------------------------------------------------------- #
#: La Entrada con ``usu`` no casa con ``dbo.usu`` (R6).
AVISO_USUARIO_LISTA_NO_EXISTE = "usuario_lista_no_existe"
#: La Entrada con ``empide`` no es un Empleado de alta (R9).
AVISO_EMPLEADO_LISTA_NO_VALIDO = "empleado_lista_no_valido"
#: Dos o más Empleados del correo de alta (R11).
AVISO_EMPLEADO_CORREO_AMBIGUO = "empleado_correo_ambiguo"
#: Todos los Empleados del correo están de baja (R11).
AVISO_EMPLEADO_CORREO_DE_BAJA = "empleado_correo_de_baja"
#: Ningún empleado con ese correo (R11).
AVISO_EMPLEADO_CORREO_SIN_EMPLEADO = "empleado_correo_sin_empleado"
#: Quien aprobó no tiene Correo de Ruesma: ``dbo.emp`` ni se lee (R11).
AVISO_EMPLEADO_SIN_CORREO = "empleado_sin_correo"
#: Último escalón: ``empide`` nulo y sigrid-api pone el suyo (R12).
AVISO_DEFECTO_SIGRID_API = "defecto_sigrid_api"
#: Una lectura de ``dbo.emp`` falló tras los reintentos (R13).
AVISO_EMPLEADO_LECTURA_FALLIDA = "empleado_lectura_fallida"

#: Todos los códigos de Aviso de resolución (sv4 los contrasta, R24).
AVISOS_RESOLUCION = frozenset({
    AVISO_USUARIO_LISTA_NO_EXISTE, AVISO_EMPLEADO_LISTA_NO_VALIDO,
    AVISO_EMPLEADO_CORREO_AMBIGUO, AVISO_EMPLEADO_CORREO_DE_BAJA,
    AVISO_EMPLEADO_CORREO_SIN_EMPLEADO, AVISO_EMPLEADO_SIN_CORREO,
    AVISO_DEFECTO_SIGRID_API, AVISO_EMPLEADO_LECTURA_FALLIDA,
})

#: Desde cuántos empleados de alta el detalle dice «N o más»: la consulta del
#: correo trae como mucho tres filas (``TOP (3)``, design §7).
TOPE_EMPLEADOS_CORREO = 3


def clasificar_empleados_correo(
    empleados: list[EmpleadoSigrid],
) -> tuple[int | None, AvisoResolucion | None]:
    """Los Empleados del correo ⇒ ``(ide, None)`` si hay exactamente uno de
    alta (R10); si no, ``(None, aviso)`` (R11): ambiguo con cuántos (sin sus
    ``ide``), solo de baja o ninguno. Los de baja no cuentan (E7)."""
    de_alta = [e for e in empleados if e.de_alta]
    if len(de_alta) == 1:
        return de_alta[0].ide, None
    if len(de_alta) >= 2:
        cuantos = (f"{TOPE_EMPLEADOS_CORREO} o más" if len(de_alta) >= TOPE_EMPLEADOS_CORREO
                   else str(len(de_alta)))
        return None, AvisoResolucion(
            AVISO_EMPLEADO_CORREO_AMBIGUO,
            f"{cuantos} empleados de alta con el correo de quien aprobó",
        )
    if empleados:
        return None, AvisoResolucion(
            AVISO_EMPLEADO_CORREO_DE_BAJA,
            "los empleados con el correo de quien aprobó están de baja",
        )
    return None, AvisoResolucion(
        AVISO_EMPLEADO_CORREO_SIN_EMPLEADO,
        "ningún empleado de Sigrid tiene el correo de quien aprobó",
    )
