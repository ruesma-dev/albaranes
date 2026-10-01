# tests/test_f052_doble_sigrid_api.py
"""F-052 T2 · humo del doble de sigrid-api y ``transport`` inyectable.

El doble (``doble_sigrid_api.py``) es la base de todos los tests de
F-052: si el fixture no es el que dice ser, los demás tests prueban
otra cosa. Aquí se fija el fixture, la semántica de ``max_rows`` /
``truncated`` / ``OFFSET`` y que el cliente de sv3 acepta un
``transport`` sin cambiar su comportamiento por defecto.
"""
from __future__ import annotations

from collections import Counter

import httpx
from doble_sigrid_api import (
    CIF_GRANDE_0668,
    CIF_SALMEDINA,
    CONTRATO_SALMEDINA,
    RAZ_SALMEDINA,
    TOTAL_PROVEEDORES_GLOBAL,
    DobleSigridApi,
    fixture_por_defecto,
)
from infrastructure.sigrid import sigrid_api_contrato_client as modulo_cliente

_SQL_ANTIGUA = (
    "SELECT prv.cif AS cif, prv.raz AS nombre, con_ctr.cod AS codigo_contrato, "
    "con_ctr.res AS nombre_contrato, ctrpro.res AS descripcion_linea, "
    "con_pro.cod AS codigo_producto FROM ctr WHERE con_obr.cod = ? AND con_ctr.emp = 1"
)


def _post(doble: DobleSigridApi, sql: str, params: list, max_rows: int | None = None):
    payload = {"database": "ruesma", "sql": sql, "parameters": params}
    if max_rows is not None:
        payload["max_rows"] = max_rows
    with httpx.Client(transport=doble.transport, base_url="https://x") as c:
        return c.post("/api/sql/read", json=payload)


# ------------------------------------------------------------------ #
# El fixture es el que dice ser
# ------------------------------------------------------------------ #
def test_f052_doble_fixture_0691_tiene_2083_filas_y_81_proveedores():
    lineas = fixture_por_defecto().de_obra("0691")
    assert len(lineas) == 2083
    assert len({ln.cif for ln in lineas}) == 81
    assert len({(ln.cif, ln.cod_ctr) for ln in lineas}) == 84


def test_f052_doble_salmedina_llega_despues_de_la_fila_1000():
    lineas = fixture_por_defecto().de_obra("0691")
    posiciones = [i for i, ln in enumerate(lineas) if ln.cif == CIF_SALMEDINA]
    assert len(posiciones) == 5
    assert min(posiciones) >= 1000
    assert {ln.cod_ctr for ln in lineas if ln.cif == CIF_SALMEDINA} == {CONTRATO_SALMEDINA}


def test_f052_doble_fixture_trae_repetidos_espacios_vacios_y_null():
    lineas = fixture_por_defecto().de_obra("0691")
    descripciones = [ln.res_lin for ln in lineas]
    assert None in descripciones
    assert "" in descripciones
    assert any(d and d.strip() == "" for d in descripciones)
    assert any(d and d != d.strip() and d.strip() for d in descripciones)
    repetidas = Counter(d for d in descripciones if d and d.strip())
    assert max(repetidas.values()) > 1
    assert any(ln.line_ide is None for ln in lineas)  # contrato sin líneas


def test_f052_doble_lista_global_y_obra_grande():
    fx = fixture_por_defecto()
    assert len(fx.proveedores_global) == TOTAL_PROVEEDORES_GLOBAL
    assert len(set(fx.proveedores_global)) == TOTAL_PROVEEDORES_GLOBAL
    grande = [ln for ln in fx.de_obra("0668") if ln.cif == CIF_GRANDE_0668]
    assert len(grande) == 1200


# ------------------------------------------------------------------ #
# max_rows, truncated, OFFSET y modos
# ------------------------------------------------------------------ #
def test_f052_doble_consulta_antigua_se_trunca_en_max_rows_sin_salmedina():
    doble = DobleSigridApi()
    body = _post(doble, _SQL_ANTIGUA, ["0691"], max_rows=1000).json()
    assert body["ok"] is True
    assert body["truncated"] is True
    assert body["row_count"] == 1000
    assert CIF_SALMEDINA not in {fila[0] for fila in body["rows"]}


def test_f052_doble_max_rows_por_defecto_200_y_alcanzarlo_es_truncar():
    doble = DobleSigridApi()
    assert _post(doble, _SQL_ANTIGUA, ["0691"]).json()["row_count"] == 200
    exacto = _post(doble, _SQL_ANTIGUA, ["0691"], max_rows=2083).json()
    assert exacto["truncated"] is True
    holgado = _post(doble, _SQL_ANTIGUA, ["0691"], max_rows=2084).json()
    assert (holgado["truncated"], holgado["row_count"]) == (False, 2083)


def test_f052_doble_agregada_una_fila_por_proveedor_y_error_xml():
    sql = "WITH base AS (...) SELECT ... FOR XML PATH('') ..."
    body = _post(DobleSigridApi(), sql, ["0691"], max_rows=1000).json()
    assert body["row_count"] == 81
    assert body["truncated"] is False
    fila = next(f for f in body["rows"] if f[0] == CIF_SALMEDINA)
    assert fila[1] == RAZ_SALMEDINA
    assert fila[2] == CONTRATO_SALMEDINA
    assert "CONTENEDOR 6 M3 RCD" in fila[3]
    r = _post(DobleSigridApi(error_xml=True), sql, ["0691"], max_rows=1000)
    assert r.status_code == 400
    assert r.json()["ok"] is False
    assert "FOR XML could not serialize" in r.json()["error"]


def test_f052_doble_offset_fetch_pagina_y_exige_order_by():
    doble = DobleSigridApi()
    base = "SELECT DISTINCT prv.cif AS cif, prv.raz AS nombre FROM ctr WHERE prv.cif IS NOT NULL AND con.emp = 1"
    pagina = _post(doble, base + " ORDER BY prv.cif, prv.raz OFFSET ? ROWS FETCH NEXT ? ROWS ONLY",
                   [10, 5], max_rows=6).json()
    esperado = sorted(fixture_por_defecto().proveedores_global)[10:15]
    assert [tuple(f) for f in pagina["rows"]] == esperado
    assert pagina["truncated"] is False
    sin_orden = _post(doble, base + " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY", [0, 5])
    assert sin_orden.status_code == 400


def test_f052_doble_forzar_truncado_y_sql_desconocida():
    doble = DobleSigridApi(forzar_truncado=True)
    assert _post(doble, _SQL_ANTIGUA, ["0691"], max_rows=5000).json()["truncated"] is True
    assert _post(doble, "SELECT 1", []).status_code == 400
    assert len(doble.peticiones) == 2


# ------------------------------------------------------------------ #
# transport inyectable en el cliente, sin cambio de comportamiento
# ------------------------------------------------------------------ #
def test_f052_doble_cliente_con_transport_inyectado_habla_con_el_doble():
    doble = DobleSigridApi()
    cliente = doble.cliente()
    assert cliente.fetch_proveedor_by_cif(cif=" b82899550 ") == (CIF_SALMEDINA, RAZ_SALMEDINA)
    assert doble.peticiones[-1]["parameters"] == [CIF_SALMEDINA]
    assert cliente.fetch_proveedor_by_cif(cif="X0000000") is None


def test_f052_doble_sin_transport_usa_httptransport_con_un_reintento(monkeypatch):
    """Por defecto, igual que antes de F-052: un ``HTTPTransport(retries=1)``
    nuevo por petición."""
    doble = DobleSigridApi()
    creados: list[dict] = []

    def _falso_http_transport(**kwargs):
        creados.append(kwargs)
        return doble.transport

    monkeypatch.setattr(modulo_cliente.httpx, "HTTPTransport", _falso_http_transport)
    cliente = modulo_cliente.SigridApiContratoClient(
        base_url="https://x", function_key="k", database="ruesma",
    )
    cliente.fetch_proveedor_by_cif(cif=CIF_SALMEDINA)
    cliente.fetch_proveedor_by_cif(cif=CIF_SALMEDINA)
    assert creados == [{"retries": 1}, {"retries": 1}]
    assert len(doble.peticiones) == 2
