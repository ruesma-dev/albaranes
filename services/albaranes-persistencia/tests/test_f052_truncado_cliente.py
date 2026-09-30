# tests/test_f052_truncado_cliente.py
"""F-052 T3 · el cliente de contratos de sv3 nunca ignora ``truncated``
(R7–R10). Sobre el doble de sigrid-api, sin red.

Cada consulta declara su política (design §3): las que alimentan
decisiones (candidatos, contratos, validación de CIF) no toleran una
respuesta incompleta; las de documentos del contrato (PDF best-effort)
la toleran con WARNING.
"""
from __future__ import annotations

import inspect
import logging

import pytest

from doble_sigrid_api import CIF_SALMEDINA, DobleSigridApi
from infrastructure.sigrid import sigrid_api_contrato_client as modulo_cliente
from ruesma_comun.sigrid import PoliticaTruncado, SigridRespuestaTruncada

_SQL_TOP1 = "SELECT TOP 1 prv.cif AS cif, prv.raz AS nombre FROM prv WHERE REPLACE(UPPER(prv.cif), ' ', '') = ?"
_LOGGER = modulo_cliente.logger.name


def _leer(cliente, **kwargs):
    base = dict(sql=_SQL_TOP1, parameters=[CIF_SALMEDINA], database="ruesma", label="prueba")
    base.update(kwargs)
    return cliente._post_sql_read(**base)


# ------------------------------------------------------------------ #
# R7 · la política es obligatoria; max_rows opcional
# ------------------------------------------------------------------ #
def test_f052_r7_politica_es_obligatoria_y_sin_valor_por_defecto():
    firma = inspect.signature(modulo_cliente.SigridApiContratoClient._post_sql_read)
    politica = firma.parameters["politica"]
    assert politica.kind is inspect.Parameter.KEYWORD_ONLY
    assert politica.default is inspect.Parameter.empty
    with pytest.raises(TypeError):
        _leer(DobleSigridApi().cliente())


def test_f052_r7_max_rows_opcional_por_llamada():
    doble = DobleSigridApi()
    cliente = doble.cliente(max_rows=321)
    _leer(cliente, politica=PoliticaTruncado.NO_TOLERA)
    _leer(cliente, politica=PoliticaTruncado.NO_TOLERA, max_rows=4321)
    assert [p["max_rows"] for p in doble.peticiones] == [321, 4321]


# ------------------------------------------------------------------ #
# R8 / R9 · la política decide
# ------------------------------------------------------------------ #
def test_f052_r8_truncado_no_tolera_lanza_con_etiqueta_y_filas():
    cliente = DobleSigridApi(forzar_truncado=True).cliente()
    with pytest.raises(SigridRespuestaTruncada) as info:
        _leer(cliente, politica=PoliticaTruncado.NO_TOLERA, label="etiqueta_x")
    assert info.value.etiqueta == "etiqueta_x"
    assert info.value.filas == 1


def test_f052_r9_truncado_tolera_devuelve_filas_y_warning(caplog):
    cliente = DobleSigridApi(forzar_truncado=True).cliente()
    with caplog.at_level(logging.WARNING, logger=_LOGGER):
        columnas, filas = _leer(cliente, politica=PoliticaTruncado.TOLERA, label="etiqueta_y")
    assert columnas == ["cif", "nombre"]
    assert filas == [[CIF_SALMEDINA, "SALMEDINA, S.L."]]
    assert any("etiqueta_y" in r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)


def test_f052_r8_sin_truncado_no_lanza():
    columnas, filas = _leer(DobleSigridApi().cliente(), politica=PoliticaTruncado.NO_TOLERA)
    assert len(filas) == 1


# ------------------------------------------------------------------ #
# R10 · política de cada consulta (design §3)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "llamada",
    [
        pytest.param(lambda c: c.fetch_contratos(cif_proveedor=CIF_SALMEDINA, codigo_obra_normalizado="0691"),
                     id="1-header_and_lines"),
        pytest.param(lambda c: c.search_proveedores(), id="2-search_proveedores"),
        pytest.param(lambda c: c.fetch_proveedor_by_cif(cif=CIF_SALMEDINA), id="3-fetch_proveedor_by_cif"),
        pytest.param(lambda c: c.fetch_proveedores_por_obra(codigo_obra="0691"), id="4-proveedores_por_obra"),
        pytest.param(lambda c: c.fetch_contratos_resumen_por_obra(codigo_obra="0691"), id="5-resumen_obra"),
    ],
)
def test_f052_r10_consultas_no_tolera_lanzan_si_truncado(llamada):
    doble = DobleSigridApi(forzar_truncado=True)
    with pytest.raises(SigridRespuestaTruncada):
        llamada(doble.cliente())
    assert len(doble.peticiones) == 1  # falla en la primera respuesta, sin seguir


def test_f052_r10_documentos_del_contrato_toleran_con_warning(caplog):
    """Filas 6 y 7 de design §3: ``rcg_gra_for_ctr_*`` y
    ``gra_rep_for_cod_*`` usan las filas y avisan."""
    doble = DobleSigridApi(forzar_truncado=True)
    cliente = doble.cliente()
    with caplog.at_level(logging.WARNING, logger=_LOGGER):
        gra_rep_ide = cliente._fetch_gra_rep_ide(contrato_ide=2405748)
    assert gra_rep_ide == 2405749
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert any("rcg_gra_for_ctr_2405748" in m for m in avisos)
    assert any("gra_rep_for_cod_G2405748" in m for m in avisos)
    assert [p["database"] for p in doble.peticiones] == ["ruesma", "ruesma_rep"]


def test_f052_r10_sin_truncado_las_consultas_simples_funcionan():
    doble = DobleSigridApi()
    cliente = doble.cliente()
    assert cliente.fetch_proveedor_by_cif(cif=CIF_SALMEDINA)[0] == CIF_SALMEDINA
    assert len(cliente.fetch_proveedores_por_obra(codigo_obra="0691")) == 81
    assert cliente._fetch_gra_rep_ide(contrato_ide=2405748) == 2405749


def test_f052_r10_docstring_sin_el_falso_tope_de_10000():
    doc = modulo_cliente.SigridApiContratoClient.fetch_contratos_resumen_por_obra.__doc__ or ""
    assert "10.000" not in doc
