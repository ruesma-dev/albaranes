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

Dos campos se comparan NORMALIZADOS (banco de IA1, 2026-10-22), porque lo
escrito por el humano y lo impreso dicen lo mismo con otra grafía:

- `numero_albaran`: solo dígitos y sin ceros a la izquierda. «SS-0000168» ≡
  «0000168» ≡ «168»; un dígito cambiado sigue siendo un fallo.
- `codigo_imputacion` (la partida que LEE IA1): mayúsculas, sin espacios y sin
  ceros a la izquierda en cada segmento. «CI.04.18» ≡ «CI.4.18». La partida
  valorada (`codigo_partida_final`, `partida_final`) NO se normaliza: ahí se
  exige el código exacto de Sigrid.

Los importes y precios VALORADOS se comparan con una tolerancia de
`TOLERANCIA_IMPORTE_EUR` (F-084 R37, decisión del humano del 2026-10-23): el
libro anota el importe del papel en céntimos y sv6 no redondea cuando INPUTS no
trae el importe de la línea (17,59 ≡ 17,5932). La lectura de IA1 sigue exacta.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal

from evals.criticidad import Criticidad, nombre_de_campo
from evals.modelos import ESPERA_REVISION, NO_COMPARAR, Discrepancia

#: Tolerancia al comparar dos números. Los importes se calculan con float en
#: varios sitios del pipeline; exigir igualdad binaria daría rojos falsos.
TOLERANCIA_RELATIVA = 1e-6
TOLERANCIA_ABSOLUTA = 1e-6

#: (F-084 R37) Euros de diferencia que se toleran en los importes y precios
#: valorados: varios céntimos no cambian la valoración.
TOLERANCIA_IMPORTE_EUR = Decimal("0.05")

#: (F-084 R37) Los campos con esa tolerancia, como (tabla, campo): IA3,
#: RESULTADO_FINAL, sus líneas añadidas y el total del documento. La lectura
#: de IA1 (`lineas.importe`, `lineas.precio_unitario`) no está.
CAMPOS_CON_TOLERANCIA_EUR = frozenset({
    ("lineas_valoradas", "importe_calculado"),
    ("lineas_valoradas", "precio_unitario_final"),
    ("lineas", "importe_final"),
    ("lineas", "precio_unitario_final"),
    ("lineas_anadidas", "importe"),
    ("datos_generales", "total_valorado_esperado"),
})

#: La tabla y el campo de un camino como `FINAL.lineas[1/P5.03.09].importe`.
_TABLA_Y_CAMPO = re.compile(r"([A-Za-z_]+)\[[^\]]*\]\.([A-Za-z_]+)$")

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


def _como_texto(valor: object) -> str:
    """El valor como lo escribiría una persona: 168.0 es «168», no «168.0»."""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)


def normalizar_numero_albaran(valor: object) -> str | None:
    """Solo los dígitos, sin ceros a la izquierda; `None` si no hay ninguno.

    El humano escribe el código sin el prefijo de serie y el papel lo trae con
    él: «0000168» en la tabla, «SS-0000168» impreso. Sin dígitos no hay nada
    que normalizar y se compara el texto tal cual.
    """
    if valor is None or isinstance(valor, bool):
        return None
    digitos = re.sub(r"\D", "", _como_texto(valor))
    if not digitos:
        return None
    return digitos.lstrip("0") or "0"


def normalizar_partida(valor: object) -> str | None:
    """Mayúsculas, sin espacios y sin ceros a la izquierda en cada segmento.

    «CI.04.18» ≡ «CI.4.18» y «CI.03A.7» ≡ «CI.3A.7». Un segmento que no empieza
    por dígito («CI», «P5») se deja como está.
    """
    if valor is None or isinstance(valor, bool):
        return None
    texto = re.sub(r"\s+", "", _como_texto(valor)).upper()
    segmentos = [
        (segmento.lstrip("0") or "0") if segmento[:1].isdigit() else segmento
        for segmento in texto.split(".")
    ]
    return ".".join(segmentos)


#: Campos que se comparan normalizados (ver la cabecera del módulo).
NORMALIZADORES: dict[str, Callable[[object], str | None]] = {
    "numero_albaran": normalizar_numero_albaran,
    "codigo_imputacion": normalizar_partida,
}


def tolera_centimos(campo: str) -> bool:
    """(R37) ¿Es un importe o precio valorado, con la tolerancia en euros?"""
    encontrado = _TABLA_Y_CAMPO.search(campo)
    return bool(encontrado) and encontrado.groups() in CAMPOS_CON_TOLERANCIA_EUR


def equivalentes_en(campo: str, esperado: object, obtenido: object) -> bool:
    """`equivalentes`, pero con la normalización o la tolerancia del campo."""
    if tolera_centimos(campo):
        numero_esperado, numero_obtenido = _a_numero(esperado), _a_numero(obtenido)
        if (
            numero_esperado is not None and numero_obtenido is not None
            and math.isfinite(numero_esperado) and math.isfinite(numero_obtenido)
        ):
            # En Decimal desde la escritura corta del número: en binario,
            # 17,64 − 17,59 no es 0,05.
            diferencia = Decimal(repr(numero_esperado)) - Decimal(repr(numero_obtenido))
            return abs(diferencia) <= TOLERANCIA_IMPORTE_EUR
    normalizar = NORMALIZADORES.get(nombre_de_campo(campo))
    if normalizar is not None:
        normal_esperado, normal_obtenido = normalizar(esperado), normalizar(obtenido)
        if normal_esperado is not None and normal_obtenido is not None:
            return normal_esperado == normal_obtenido
    return equivalentes(esperado, obtenido)


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

    if equivalentes_en(prefijo, esperado, obtenido):
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
