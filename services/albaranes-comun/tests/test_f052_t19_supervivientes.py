# tests/test_f052_t19_supervivientes.py
"""F-052 T19 · supervivientes de la campaña de mutación en ``ruesma_comun``.

Cada test fija un borde o un texto que la campaña
(``progress/mutacion_F-052.md``) demostró que ningún test leía: los
límites inferiores de ``pagina`` y ``max_paginas`` (1 es válido) y el
número de página 1-based que llevan los mensajes de error.
"""
from __future__ import annotations

import logging

import pytest
from ruesma_comun.sigrid import (
    PAGINA_MAXIMA,
    PoliticaTruncado,
    SigridRespuestaTruncada,
    leer_paginado,
)

_LOG = logging.getLogger("test_f052_t19_supervivientes")


class _Paginas:
    """Sirve ``total`` filas por páginas; marca ``truncated`` en la
    llamada número ``truncar_en`` (1-based) y, si ``de_mas_en`` coincide,
    sirve en esa llamada una fila más de las pedidas."""

    def __init__(self, total: int, *, truncar_en: int | None = None,
                 de_mas_en: int | None = None):
        self.filas = [[i] for i in range(total)]
        self.llamadas: list[tuple[int, int]] = []
        self.truncar_en = truncar_en
        self.de_mas_en = de_mas_en

    def __call__(self, offset: int, tamano: int):
        self.llamadas.append((offset, tamano))
        n = len(self.llamadas)
        extra = 1 if n == self.de_mas_en else 0
        trozo = self.filas[offset:offset + tamano + extra]
        return ["n"], trozo, n == self.truncar_en


def _leer(fuente, *, pagina=10, max_paginas=5, politica=PoliticaTruncado.NO_TOLERA):
    return leer_paginado(
        fuente,
        pagina=pagina,
        max_paginas=max_paginas,
        etiqueta="header_and_lines",
        politica=politica,
        logger=_LOG,
    )


def test_f052_t19_pagina_de_una_fila_es_valida():
    """``pagina=1`` es el mínimo válido (R14): una fila por petición."""
    fuente = _Paginas(2)
    _, filas = _leer(fuente, pagina=1)
    assert filas == [[0], [1]]
    assert fuente.llamadas == [(0, 1), (1, 1), (2, 1)]


def test_f052_t19_una_sola_pagina_como_tope_es_valida():
    """``max_paginas=1`` es el mínimo válido: una lectura, sin encadenar."""
    fuente = _Paginas(3)
    _, filas = _leer(fuente, max_paginas=1)
    assert len(filas) == 3
    assert fuente.llamadas == [(0, 10)]


def test_f052_t19_pagina_por_encima_del_tope_dice_el_max_rows_que_pediria():
    with pytest.raises(ValueError) as info:
        _leer(_Paginas(1), pagina=PAGINA_MAXIMA + 1)
    assert f"max_rows={PAGINA_MAXIMA + 2}," in str(info.value)


def test_f052_t19_pagina_de_mas_dice_su_numero_1_based():
    """La segunda página es la «página 2» del mensaje, no la 1 ni la 3."""
    fuente = _Paginas(30, de_mas_en=2)
    with pytest.raises(RuntimeError) as info:
        _leer(fuente)
    assert "página 2, 11 filas" in str(info.value)


def test_f052_t19_pagina_marcada_truncada_dice_su_numero_1_based():
    fuente = _Paginas(15, truncar_en=2)
    with pytest.raises(SigridRespuestaTruncada) as info:
        _leer(fuente)
    assert "(página 2 marcada truncated)" in str(info.value)
