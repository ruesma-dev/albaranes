# ruesma_comun/obras/codigo.py
"""Normalización del código de obra al formato canónico de Ruesma.

Movida aquí desde sv3 (``application/services/obra_code_normalizer.py``)
en F-052 CR-C1, con la semántica de sv3 intacta: sv4 tenía otra copia
(``^\d{1,4}$`` + ``zfill``) que no coincidía y, al comparar el rastro que
sella sv3, tomaba por «desfasada» una búsqueda que sv3 había descartado.

No confundir con ``ruesma_comun.contratos.origen_datos.normalizar_codigo``
(F-048): aquella es una forma de COMPARACIÓN (sin ceros a la izquierda ni
separadores); esta es el código que se envía a Sigrid y se sella.
"""
from __future__ import annotations


def normalizar_codigo_obra(valor: str | None) -> str | None:
    """Código de obra canónico, o ``None`` si no es válido.

    Reglas:
      - 4 dígitos, el primero siempre ``0``.
      - Con 3 dígitos se antepone ``0`` (``695`` → ``0695``).
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
    if not limpio or not limpio.isdigit():
        return None
    if len(limpio) == 3:
        return "0" + limpio
    if len(limpio) == 4 and limpio.startswith("0"):
        return limpio
    return None
