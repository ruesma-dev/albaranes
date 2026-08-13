# evals/comparador.py
"""Compara el ground truth con lo que el sistema produjo.

Manda el ground truth: solo se comparan los campos que el libro declara. Lo que
el sistema devuelva de más no se evalúa —no está en el banco de casos— y lo que
devuelva de menos cuenta como `null`.

Los dos sentinelas del contrato de datos se resuelven aquí:

- `NO_COMPARAR` (celda `?`) salta el campo, por encima de la criticidad.
- `ESPERA_REVISION` (literal `REVISIÓN`) se cumple cuando el sistema **no
  inventó** el valor: lo dejó sin resolver o marcado para revisión humana. Si
  el sistema puso un precio o una partida concreta donde el ground truth
  esperaba revisión, eso es un fallo, y de los importantes.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from evals.criticidad import Criticidad
from evals.modelos import ESPERA_REVISION, NO_COMPARAR, Discrepancia

#: Tolerancia al comparar dos números. Los importes se calculan con float en
#: varios sitios del pipeline; exigir igualdad binaria daría rojos falsos.
TOLERANCIA_RELATIVA = 1e-6
TOLERANCIA_ABSOLUTA = 1e-6

#: Textos que significan «sí» y «no» en los libros que rellena el humano.
_AFIRMATIVOS = frozenset({"SI", "SÍ", "TRUE", "VERDADERO", "1", "X"})
_NEGATIVOS = frozenset({"NO", "FALSE", "FALSO", "0"})

#: Textos con los que el sistema dice «esto lo dejo para revisión humana».
_MARCAS_DE_REVISION = frozenset({"REVISION", "REVISIÓN", "REVIEW", "PENDIENTE"})


def _es_escalar(valor: object) -> bool:
    return not isinstance(valor, (Mapping, list, tuple))


def _es_hoja(valor: object) -> bool:
    """Un valor que se compara como campo: un escalar o una lista de escalares."""
    if _es_escalar(valor):
        return True
    if isinstance(valor, (list, tuple)):
        return all(_es_escalar(elemento) for elemento in valor)
    return False


def _texto(valor: object) -> str:
    return str(valor).strip().upper()


def _a_numero(valor: object) -> float | None:
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    try:
        return float(str(valor).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def _a_booleano(valor: object) -> bool | None:
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return None
    texto = _texto(valor)
    if texto in _AFIRMATIVOS:
        return True
    if texto in _NEGATIVOS:
        return False
    return None


def dejado_a_revision(obtenido: object) -> bool:
    """¿El sistema dejó este valor a revisión en vez de inventárselo?"""
    if obtenido is None:
        return True
    if isinstance(obtenido, bool):
        return obtenido
    return _texto(obtenido) in _MARCAS_DE_REVISION


def equivalentes(esperado: object, obtenido: object) -> bool:
    """¿Son el mismo valor, con la tolerancia razonable de cada tipo?"""
    if esperado is None or obtenido is None:
        return esperado is None and obtenido is None

    numero_esperado = _a_numero(esperado)
    numero_obtenido = _a_numero(obtenido)
    if numero_esperado is not None and numero_obtenido is not None:
        return math.isclose(
            numero_esperado,
            numero_obtenido,
            rel_tol=TOLERANCIA_RELATIVA,
            abs_tol=TOLERANCIA_ABSOLUTA,
        )

    if isinstance(esperado, bool) or isinstance(obtenido, bool):
        return _a_booleano(esperado) == _a_booleano(obtenido)

    return _texto(esperado) == _texto(obtenido)


def _discrepancia(
    campo: str,
    esperado: object,
    obtenido: object,
    criticidad: Criticidad,
    motivo: str = "",
) -> Discrepancia:
    return Discrepancia(
        campo=campo,
        esperado=esperado,
        obtenido=obtenido,
        severidad=criticidad.severidad(campo),
        motivo=motivo,
    )


def comparar(
    esperado: object,
    obtenido: object,
    criticidad: Criticidad,
    prefijo: str = "",
) -> list[Discrepancia]:
    """Compara recursivamente y devuelve las diferencias con su severidad."""
    if isinstance(esperado, Mapping):
        if not isinstance(obtenido, Mapping):
            obtenido = {}
        discrepancias: list[Discrepancia] = []
        for campo, valor in esperado.items():
            camino = f"{prefijo}.{campo}" if prefijo else campo
            discrepancias.extend(
                comparar(valor, obtenido.get(campo), criticidad, camino)
            )
        return discrepancias

    if isinstance(esperado, (list, tuple)):
        if not isinstance(obtenido, Sequence) or isinstance(obtenido, (str, bytes)):
            return [
                _discrepancia(
                    prefijo, esperado, obtenido, criticidad, "se esperaba una lista"
                )
            ]
        if len(esperado) != len(obtenido):
            return [
                _discrepancia(
                    prefijo,
                    esperado,
                    obtenido,
                    criticidad,
                    f"se esperaban {len(esperado)} elemento(s) y hay {len(obtenido)}",
                )
            ]
        discrepancias = []
        for indice, elemento in enumerate(esperado):
            discrepancias.extend(
                comparar(
                    elemento, obtenido[indice], criticidad, f"{prefijo}[{indice}]"
                )
            )
        return discrepancias

    if esperado == NO_COMPARAR:
        return []

    if esperado == ESPERA_REVISION:
        if dejado_a_revision(obtenido):
            return []
        return [
            _discrepancia(
                prefijo,
                "REVISIÓN",
                obtenido,
                criticidad,
                "se esperaba que quedara a revisión humana y el sistema resolvió "
                "un valor",
            )
        ]

    if equivalentes(esperado, obtenido):
        return []
    return [_discrepancia(prefijo, esperado, obtenido, criticidad)]


def _clave_de_fila(fila: Mapping, claves: Sequence[str]) -> tuple:
    return tuple(
        None if fila.get(clave) is None else _texto(fila.get(clave)) for clave in claves
    )


def podar(fila: Mapping, observables: Sequence[str] | None) -> dict:
    """Deja de una fila esperada solo los campos que la corrida puede observar.

    No es una relajación encubierta: los campos podados se listan aparte y
    salen en el informe como «no observables en esta corrida», con lo que se
    ve qué parte del ground truth no está evaluando nadie.
    """
    if observables is None:
        return dict(fila)
    return {campo: valor for campo, valor in fila.items() if campo in observables}


def comparar_tablas(
    esperadas: Sequence[Mapping],
    obtenidas: Sequence[Mapping],
    criticidad: Criticidad,
    *,
    claves: Sequence[str],
    prefijo: str,
    observables: Sequence[str] | None = None,
    severidad_sobrantes: str = "aviso",
) -> list[Discrepancia]:
    """Compara dos tablas emparejando sus filas por `claves`, no por posición.

    Emparejar por posición sería frágil: sv6 inyecta líneas sintéticas
    deterministas y el orden del ground truth no tiene por qué coincidir.
    """
    pendientes = list(enumerate(obtenidas))
    discrepancias: list[Discrepancia] = []

    for fila_esperada in esperadas:
        buscada = _clave_de_fila(fila_esperada, claves)
        pareja = None
        for posicion, (_, fila_obtenida) in enumerate(pendientes):
            if _clave_de_fila(fila_obtenida, claves) == buscada:
                pareja = pendientes.pop(posicion)[1]
                break

        etiqueta = f"{prefijo}[{'/'.join(str(v) for v in buscada)}]"
        if pareja is None:
            discrepancias.append(
                Discrepancia(
                    campo=etiqueta,
                    esperado=podar(fila_esperada, observables),
                    obtenido=None,
                    severidad="fallo",
                    motivo="fila del ground truth que el sistema no ha producido",
                )
            )
            continue
        discrepancias.extend(
            comparar(
                podar(fila_esperada, observables), pareja, criticidad, etiqueta
            )
        )

    for _, sobrante in pendientes:
        discrepancias.append(
            Discrepancia(
                campo=f"{prefijo}[+]",
                esperado=None,
                obtenido=dict(sobrante),
                severidad=severidad_sobrantes,  # type: ignore[arg-type]
                motivo="fila producida por el sistema que el ground truth no declara",
            )
        )
    return discrepancias


def campos_no_observables(
    esperadas: Sequence[Mapping], observables: Sequence[str]
) -> list[str]:
    """Campos del ground truth que esta corrida no puede mirar."""
    vistos: list[str] = []
    for fila in esperadas:
        for campo in fila:
            if campo not in observables and campo not in vistos:
                vistos.append(campo)
    return vistos


def campos_sin_clasificar(
    esperado: object, criticidad: Criticidad, prefijo: str = ""
) -> list[str]:
    """Campos del ground truth que la criticidad no clasifica (R8).

    No relajan nada —se tratan como críticos— pero constan en el informe: una
    entrada olvidada en `criticidad.json` tiene que verse, no pasar de largo.
    """
    encontrados: list[str] = []

    if isinstance(esperado, Mapping):
        for campo, valor in esperado.items():
            camino = f"{prefijo}.{campo}" if prefijo else campo
            if _es_hoja(valor) and not criticidad.clasificar(camino).clasificado:
                encontrados.append(campo)
            encontrados.extend(campos_sin_clasificar(valor, criticidad, camino))
    elif isinstance(esperado, (list, tuple)):
        for indice, elemento in enumerate(esperado):
            encontrados.extend(
                campos_sin_clasificar(elemento, criticidad, f"{prefijo}[{indice}]")
            )

    vistos: list[str] = []
    for campo in encontrados:
        if campo not in vistos:
            vistos.append(campo)
    return vistos
