# domain/services/fecha_albaran.py
"""F-108 · A · Cómo lee sv4 la fecha y el número de albarán que escribe una persona.

La ficha enseña la fecha en ``dd/mm/aaaa`` y la guarda en ``AAAA-MM-DD``: es
lo que sella sv3 y lo único que entiende sv9 (``_RE_FECHA`` de
``validador_alta.py``; si no, ``fecha_ilegible``). La regla es estricta (lo
que no entiende, lo rechaza con un aviso): es entrada humana, y la de sv3
(``AlbaranNormalizer``), que es tolerante con lo que lee la IA, es otra
responsabilidad (D7).

Formatos admitidos: ``d/m/aaaa``, ``d-m-aaaa``, ``d.m.aaaa`` (día y mes de 1
o 2 cifras; año de 2 cifras ⇒ ``20aa``) y ``aaaa-mm-dd``; espacios alrededor
ignorados. Siempre día antes que mes salvo en ``aaaa-mm-dd``. Sin
``strptime`` (depende de la configuración regional) ni plausibilidad (es de
sv9, D6). La función de la ficha (``parseFechaEs`` de ``static/app.js``) da
lo mismo en la tabla común de los tests (R20).
"""
from __future__ import annotations

import re
from datetime import date

from domain.models.review_models import (
    FechaAlbaranNoValidaError,
    NumeroAlbaranNoValidoError,
)

#: (R3) Aviso de una fecha escrita que no se admite; ``{texto}`` es lo escrito.
AVISO_FECHA_NO_VALIDA = ("Fecha del albarán no válida: «{texto}». Escríbela como dd/mm/aaaa "
                         "(p. ej. 28/10/2026) o elígela en el calendario.")

#: (R9) ``String(128)`` de ``albaran_documents_merge.numero_albaran``.
MAX_NUMERO_ALBARAN = 128

#: (R9) Aviso de un número de albarán que no cabe en la columna.
AVISO_NUMERO_LARGO = (
    f"El número de albarán no puede pasar de {MAX_NUMERO_ALBARAN} caracteres"
)

# ASCII: sin él, ``\d`` admitiría cifras de otros alfabetos (y la de JS no).
_RE_DIA_MES_ANO = re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2}|\d{4})", re.ASCII)
_RE_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})", re.ASCII)


def _fecha_real(ano: int, mes: int, dia: int) -> date | None:
    """La fecha, o ``None`` si no existe en el calendario (``31/02``, año 0)."""
    try:
        return date(ano, mes, dia)
    except ValueError:
        return None


def _leer(limpio: str) -> date | None:
    """La fecha de ``limpio`` (ya recortado) o ``None`` si no se admite."""
    iso = _RE_ISO.fullmatch(limpio)
    if iso:
        return _fecha_real(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
    dma = _RE_DIA_MES_ANO.fullmatch(limpio)
    if dma:
        ano = int(dma.group(3))
        if len(dma.group(3)) == 2:
            ano += 2000
        return _fecha_real(ano, int(dma.group(2)), int(dma.group(1)))
    return None


def normalizar_fecha_albaran(texto: str | None) -> str | None:
    """(R1–R3) La fecha escrita en ``AAAA-MM-DD``; ``None`` si está vacía.

    Lanza :class:`FechaAlbaranNoValidaError` (con el aviso de R3) si no está
    en un formato admitido o no existe en el calendario."""
    limpio = (texto or "").strip()
    if not limpio:
        return None
    fecha = _leer(limpio)
    if fecha is None:
        raise FechaAlbaranNoValidaError(limpio, AVISO_FECHA_NO_VALIDA.format(texto=limpio))
    return fecha.isoformat()


def es_fecha_guardada_valida(valor: str | None) -> bool:
    """(R11) ¿La fecha guardada es ``AAAA-MM-DD`` y existe? (lo que sv9 admite)."""
    iso = _RE_ISO.fullmatch(valor or "")
    return bool(iso) and _fecha_real(
        int(iso.group(1)), int(iso.group(2)), int(iso.group(3)),
    ) is not None


def fecha_para_ver(valor: str | None) -> str:
    """(R4) La fecha guardada en ``dd/mm/aaaa``; tal cual si no se entiende
    (para que se vea y se corrija) y vacía si es nula. Nunca lanza."""
    limpio = (valor or "").strip()
    if not limpio:
        return ""
    fecha = _leer(limpio)
    if fecha is None:
        return valor or ""
    return f"{fecha.day:02d}/{fecha.month:02d}/{fecha.year:04d}"


def normalizar_numero_albaran(texto: str | None) -> str | None:
    """(R8, R9) El número recortado de espacios, sin otro cambio (la
    comparación normalizada es de sv9, F-053 R14); ``None`` si queda vacío.

    Lanza :class:`NumeroAlbaranNoValidoError` si pasa de
    :data:`MAX_NUMERO_ALBARAN` caracteres (no cabría en la columna)."""
    limpio = (texto or "").strip()
    if not limpio:
        return None
    if len(limpio) > MAX_NUMERO_ALBARAN:
        raise NumeroAlbaranNoValidoError(AVISO_NUMERO_LARGO)
    return limpio
