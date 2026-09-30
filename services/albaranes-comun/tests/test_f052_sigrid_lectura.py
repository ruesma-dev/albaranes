# tests/test_f052_sigrid_lectura.py
"""F-052 · lectura de sigrid-api sin truncados silenciosos (R8, R9, R14).

``ruesma_comun.sigrid.lectura`` es puro: sin HTTP, sin BBDD. Decide qué
hacer cuando sigrid-api marca ``truncated=true`` (según la política de
la consulta) y encadena páginas ``OFFSET/FETCH`` hasta una incompleta.
Lo usan sv3 (cliente de contratos) y sv4 (lookup).
"""
from __future__ import annotations

import logging

import pytest
from ruesma_comun.sigrid import (
    PoliticaTruncado,
    SigridRespuestaTruncada,
    comprobar_truncado,
    con_paginacion,
    leer_paginado,
)

_LOG = logging.getLogger("test_f052_sigrid_lectura")


def _body(filas: int, truncated) -> dict:
    body = {"ok": True, "columns": ["a"], "rows": [[i] for i in range(filas)]}
    if truncated is not None:
        body["truncated"] = truncated
    return body


# ------------------------------------------------------------------ #
# R8 · NO_TOLERA: truncado → excepción con etiqueta y filas
# ------------------------------------------------------------------ #
def test_f052_r8_no_tolera_truncado_lanza_con_etiqueta_y_filas():
    with pytest.raises(SigridRespuestaTruncada) as info:
        comprobar_truncado(
            _body(1000, True),
            politica=PoliticaTruncado.NO_TOLERA,
            etiqueta="contratos_resumen_obra_0691",
            logger=_LOG,
        )
    exc = info.value
    assert exc.etiqueta == "contratos_resumen_obra_0691"
    assert exc.filas == 1000
    assert "contratos_resumen_obra_0691" in str(exc)
    assert "1000" in str(exc)


def test_f052_r8_la_excepcion_es_un_runtimeerror():
    """Los ``except Exception`` / ``RuntimeError`` de hoy la tratan como
    fallo de consulta (design §5): se quiere así."""
    assert issubclass(SigridRespuestaTruncada, RuntimeError)


@pytest.mark.parametrize("truncated", [False, None])
def test_f052_r8_no_tolera_sin_truncado_no_lanza(truncated):
    comprobar_truncado(
        _body(5, truncated),
        politica=PoliticaTruncado.NO_TOLERA,
        etiqueta="x",
        logger=_LOG,
    )


def test_f052_r8_no_tolera_truncado_sin_rows_cuenta_cero():
    with pytest.raises(SigridRespuestaTruncada) as info:
        comprobar_truncado(
            {"ok": True, "truncated": True},
            politica=PoliticaTruncado.NO_TOLERA,
            etiqueta="x",
            logger=_LOG,
        )
    assert info.value.filas == 0


# ------------------------------------------------------------------ #
# R9 · TOLERA: truncado → WARNING con la etiqueta, sin excepción
# ------------------------------------------------------------------ #
def test_f052_r9_tolera_truncado_registra_warning(caplog):
    with caplog.at_level(logging.DEBUG, logger=_LOG.name):
        comprobar_truncado(
            _body(1000, True),
            politica=PoliticaTruncado.TOLERA,
            etiqueta="rcg_gra_for_ctr_42",
            logger=_LOG,
        )
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    assert "rcg_gra_for_ctr_42" in avisos[0].getMessage()
    assert "1000" in avisos[0].getMessage()


def test_f052_r9_tolera_sin_truncado_no_registra_nada(caplog):
    with caplog.at_level(logging.DEBUG, logger=_LOG.name):
        comprobar_truncado(
            _body(3, False),
            politica=PoliticaTruncado.TOLERA,
            etiqueta="x",
            logger=_LOG,
        )
    assert caplog.records == []


@pytest.mark.parametrize("politica", [None, "NO_TOLERA", True])
def test_f052_r7_politica_invalida_se_rechaza_aunque_no_trunque(politica):
    """La política es obligatoria y tipada: un valor que no sea
    ``PoliticaTruncado`` falla siempre, no solo el día que trunque."""
    with pytest.raises(TypeError):
        comprobar_truncado(
            _body(1, False), politica=politica, etiqueta="x", logger=_LOG,
        )


# ------------------------------------------------------------------ #
# R14 · con_paginacion
# ------------------------------------------------------------------ #
def test_f052_r14_con_paginacion_anade_offset_fetch_al_final():
    sql = "SELECT a FROM t\nORDER BY a\n"
    out = con_paginacion(sql)
    assert out.startswith("SELECT a FROM t\nORDER BY a")
    assert out.rstrip().endswith("OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")
    assert out.count("?") == 2


def test_f052_r14_con_paginacion_acepta_order_by_en_minusculas_y_saltos():
    out = con_paginacion("select a from t order\n   by a")
    assert out.endswith("OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT a FROM t",
        "SELECT a FROM t WHERE b = 'ORDER'",
        "SELECT border_by FROM t",
        "",
    ],
)
def test_f052_r14_con_paginacion_sin_order_by_da_valueerror(sql):
    with pytest.raises(ValueError):
        con_paginacion(sql)


# ------------------------------------------------------------------ #
# R14 · leer_paginado
# ------------------------------------------------------------------ #
class _Paginas:
    """Simula sigrid-api sobre ``total`` filas: sirve cada página y
    anota las llamadas ``(offset, tamano)``."""

    def __init__(self, total: int, *, truncar_en: int | None = None):
        self.filas = [[i] for i in range(total)]
        self.llamadas: list[tuple[int, int]] = []
        self.truncar_en = truncar_en

    def __call__(self, offset: int, tamano: int):
        self.llamadas.append((offset, tamano))
        trozo = self.filas[offset:offset + tamano]
        truncated = self.truncar_en is not None and len(self.llamadas) == self.truncar_en
        return ["n"], trozo, truncated


def _leer(fuente, *, pagina=10, max_paginas=5, politica=PoliticaTruncado.NO_TOLERA):
    return leer_paginado(
        fuente,
        pagina=pagina,
        max_paginas=max_paginas,
        etiqueta="header_and_lines",
        politica=politica,
        logger=_LOG,
    )


def test_f052_r14_leer_paginado_encadena_hasta_pagina_incompleta():
    fuente = _Paginas(23)
    columnas, filas = _leer(fuente)
    assert columnas == ["n"]
    assert filas == [[i] for i in range(23)]
    assert fuente.llamadas == [(0, 10), (10, 10), (20, 10)]


def test_f052_r14_leer_paginado_una_sola_llamada_si_cabe():
    fuente = _Paginas(9)
    _, filas = _leer(fuente)
    assert len(filas) == 9
    assert fuente.llamadas == [(0, 10)]


def test_f052_r14_leer_paginado_multiplo_exacto_pide_una_pagina_vacia():
    fuente = _Paginas(20)
    _, filas = _leer(fuente)
    assert len(filas) == 20
    assert fuente.llamadas == [(0, 10), (10, 10), (20, 10)]


def test_f052_r14_leer_paginado_sin_filas():
    fuente = _Paginas(0)
    columnas, filas = _leer(fuente)
    assert (columnas, filas) == (["n"], [])
    assert fuente.llamadas == [(0, 10)]


def test_f052_r13_leer_paginado_tope_de_paginas_lanza():
    fuente = _Paginas(100)
    with pytest.raises(SigridRespuestaTruncada) as info:
        _leer(fuente, pagina=10, max_paginas=3)
    assert info.value.etiqueta == "header_and_lines"
    assert info.value.filas == 30
    assert len(fuente.llamadas) == 3


def test_f052_r13_leer_paginado_justo_en_el_tope_sin_pagina_llena_no_lanza():
    fuente = _Paginas(29)
    _, filas = _leer(fuente, pagina=10, max_paginas=3)
    assert len(filas) == 29


def test_f052_r13_leer_paginado_tope_tolera_devuelve_lo_leido_con_warning(caplog):
    fuente = _Paginas(100)
    with caplog.at_level(logging.DEBUG, logger=_LOG.name):
        _, filas = _leer(
            fuente, pagina=10, max_paginas=2, politica=PoliticaTruncado.TOLERA,
        )
    assert len(filas) == 20
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    assert "header_and_lines" in avisos[0].getMessage()


def test_f052_r8_leer_paginado_pagina_marcada_truncada_no_tolera_lanza():
    """Con ``max_rows = pagina + 1`` una página nunca debería venir
    truncada: si llega, es error (design §3)."""
    fuente = _Paginas(15, truncar_en=1)
    with pytest.raises(SigridRespuestaTruncada) as info:
        _leer(fuente)
    assert info.value.filas == 10


def test_f052_r9_leer_paginado_pagina_truncada_tolera_sigue(caplog):
    fuente = _Paginas(15, truncar_en=2)
    with caplog.at_level(logging.DEBUG, logger=_LOG.name):
        _, filas = _leer(fuente, politica=PoliticaTruncado.TOLERA)
    assert len(filas) == 15
    assert any(r.levelno == logging.WARNING for r in caplog.records)


@pytest.mark.parametrize("pagina,max_paginas", [(0, 5), (-1, 5), (10, 0)])
def test_f052_r14_leer_paginado_parametros_invalidos(pagina, max_paginas):
    with pytest.raises(ValueError):
        _leer(_Paginas(3), pagina=pagina, max_paginas=max_paginas)


def test_f052_r7_leer_paginado_politica_invalida():
    with pytest.raises(TypeError):
        _leer(_Paginas(3), politica=None)


class _PaginaDeMas(_Paginas):
    """Fuente rota: ignora el tamaño pedido y sirve ``tamano + 1`` filas
    (FETCH no aplicado, o página truncada con ``max_rows = pagina + 1``)."""

    def __call__(self, offset: int, tamano: int):
        self.llamadas.append((offset, tamano))
        return ["n"], self.filas[offset:offset + tamano + 1], False


@pytest.mark.parametrize("politica", list(PoliticaTruncado))
def test_f052_r14_leer_paginado_pagina_con_filas_de_mas_lanza(politica):
    """CR-A2: una página con más filas que las pedidas rompe el
    encadenado (la siguiente, con ``offset = n * pagina``, repetiría
    filas). Es una anomalía y se lanza siempre, sin aceptar nada."""
    fuente = _PaginaDeMas(25)
    with pytest.raises(RuntimeError) as info:
        _leer(fuente, politica=politica)
    mensaje = str(info.value)
    assert "header_and_lines" in mensaje
    assert "11" in mensaje and "10" in mensaje
    assert fuente.llamadas == [(0, 10)]
