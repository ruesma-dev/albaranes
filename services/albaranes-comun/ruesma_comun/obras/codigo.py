# ruesma_comun/obras/codigo.py
"""Normalización del código de obra al formato canónico de Ruesma.

Movida aquí desde sv3 (``application/services/obra_code_normalizer.py``)
en F-052 CR-C1, con la semántica de sv3 intacta: sv4 tenía otra copia
(1 a 4 dígitos + ``zfill``) que no coincidía y, al comparar el rastro que
sella sv3, tomaba por «desfasada» una búsqueda que sv3 había descartado.

No confundir con ``ruesma_comun.contratos.origen_datos.normalizar_codigo``
(F-048): aquella es una forma de COMPARACIÓN (sin ceros a la izquierda ni
separadores); esta es el código que se envía a Sigrid y se sella.

F-070: regla del humano, «es crucial que añada el 0 inicial si no es VAR ni
POSTV2». VAR y POSTV2 son códigos de obra válidos en Sigrid (``con.cod``) y
se devuelven tal cual, en mayúsculas; viven SOLO aquí
(``CODIGOS_OBRA_SIN_CERO``). ``canonizar_codigo_obra`` es lo que usan quienes
sellan, consultan o dan de alta la obra (sv3, sv4 y sv9): el canónico si lo
hay y, si no, el valor recortado tal cual.
"""
from __future__ import annotations

#: Códigos de obra válidos SIN el 0 inicial (regla del humano, F-070). Único
#: sitio del repositorio donde se escriben estos literales.
CODIGOS_OBRA_SIN_CERO: frozenset[str] = frozenset({"VAR", "POSTV2"})


def normalizar_codigo_obra(valor: str | None) -> str | None:
    """Código de obra canónico, o ``None`` si no es válido.

    Reglas:
      - 4 dígitos, el primero siempre ``0``.
      - Con 3 dígitos se antepone ``0`` (``695`` → ``0695``).
      - ``VAR`` y ``POSTV2`` (F-070), en cualquier combinación de mayúsculas,
        se devuelven en mayúsculas (``var`` → ``VAR``).
      - Cualquier otro patrón (``12``, ``1234``, ``12345``, ``abc``, vacío)
        devuelve ``None`` y el llamador no consulta Sigrid.

    Ejemplos:
        >>> normalizar_codigo_obra("0695")
        '0695'
        >>> normalizar_codigo_obra("  695  ")
        '0695'
        >>> normalizar_codigo_obra("1234")   # no empieza por 0
        >>> normalizar_codigo_obra(None)
    """
    if valor is None:
        return None
    limpio = str(valor).strip()
    if limpio.upper() in CODIGOS_OBRA_SIN_CERO:
        return limpio.upper()
    if not limpio or not limpio.isdigit():
        return None
    if len(limpio) == 3:
        return "0" + limpio
    if len(limpio) == 4 and limpio.startswith("0"):
        return limpio
    return None


def canonizar_codigo_obra(valor: str | None) -> str | None:
    """Código canónico si lo hay; si no, el valor recortado (F-070, R4).

    ``None`` si el valor es ``None`` o queda vacío. Idempotente.

    Ejemplos:
        >>> canonizar_codigo_obra(" 686 ")
        '0686'
        >>> canonizar_codigo_obra("var")
        'VAR'
        >>> canonizar_codigo_obra(" GG ")   # no encaja: tal cual, recortado
        'GG'
        >>> canonizar_codigo_obra("   ")
    """
    canonico = normalizar_codigo_obra(valor)
    if canonico is not None:
        return canonico
    if valor is None:
        return None
    return str(valor).strip() or None
