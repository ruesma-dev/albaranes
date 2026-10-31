# tests/test_f114_cliente.py
"""F-114 · búsqueda global de proveedores en el cliente de Sigrid de sv4.

``SigridLookupClient.buscar_proveedores`` lee los proveedores VIVOS de Sigrid
(``prv`` + ``con`` con ``tip = 5``, ``emp = 1`` y ``fecbaj = 0``, la misma
definición que el alta sin contrato de sigrid-api) cuyo nombre o CIF contienen
el texto. Sin red: ``httpx.MockTransport`` en lugar del transporte real (patrón
de ``test_f052_lookup_truncado.py``). Nombres y CIF de los tests, inventados.
"""
from __future__ import annotations

import json
import logging

import httpx
import pytest
from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient
from ruesma_comun.sigrid import SigridRespuestaTruncada


class _SigridApiFalsa:
    """Responde a ``/api/sql/read`` con las filas fijadas y apunta lo pedido."""

    def __init__(self, *, columnas, filas, truncated=False):
        self.columnas = columnas
        self.filas = filas
        self.truncated = truncated
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(json.loads(request.content))
        return httpx.Response(200, json={
            "ok": True, "columns": self.columnas, "rows": self.filas,
            "truncated": self.truncated,
        })


_COLUMNAS = ["cif", "nombre", "fichas"]


@pytest.fixture
def sigrid_api(monkeypatch):
    def _instalar(filas=(), *, columnas=_COLUMNAS, truncated=False):
        falsa = _SigridApiFalsa(columnas=columnas, filas=list(filas), truncated=truncated)
        monkeypatch.setattr(
            modulo.httpx, "HTTPTransport",
            lambda *a, **k: httpx.MockTransport(falsa),
        )
        return falsa

    return _instalar


def _cliente() -> SigridLookupClient:
    return SigridLookupClient(
        base_url="https://sigrid.invalid", function_key="clave-de-test",
        database="db-test",
    )


# ------------------------------------------------------------------ #
# R15 · todo por parámetro ``?``
# ------------------------------------------------------------------ #
def test_f114_r15_la_sql_lleva_todo_por_parametro(sigrid_api):
    falsa = sigrid_api()
    _cliente().buscar_proveedores(texto="cera")
    (peticion,) = falsa.peticiones
    assert peticion["sql"] == modulo._SQL_PROVEEDORES_TODOS
    assert peticion["parameters"] == [51, 5, 1, 0, "%cera%", "%CERA%"]
    sql = modulo._SQL_PROVEEDORES_TODOS
    # Ningún valor concatenado: el texto no aparece y TOP va por parámetro.
    assert "cera" not in sql.lower()
    assert "TOP (?)" in sql
    assert "c.tip = ?" in sql and "c.emp = ?" in sql and "c.fecbaj = ?" in sql
    assert sql.count("LIKE ? ESCAPE '!'") == 2
    assert "COLLATE Latin1_General_CI_AI" in sql
    assert "GROUP BY v.cif" in sql
    assert "ORDER BY MIN(v.raz), v.cif" in sql


def test_f114_r15_constantes():
    assert modulo.MINIMO_BUSQUEDA_PROVEEDOR == 3
    assert modulo.LIMITE_BUSQUEDA_PROVEEDOR == 50
    assert modulo.TIP_PROVEEDOR == 5
    assert modulo.EMPRESA_RUESMA == 1


# ------------------------------------------------------------------ #
# R16 · patrones y escape
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("texto", "patron"),
    [
        ("cera", "%cera%"),
        ("50%", "%50!%%"),
        ("a_b", "%a!_b%"),
        ("[x]", "%![x]%"),
        ("¡hola!", "%¡hola!!%"),
        ("!%_[", "%!!!%!_![%"),
    ],
)
def test_f114_r16_patron_like_escapa_comodines(texto, patron):
    assert modulo._patron_like(texto) == patron


def test_f114_r16_cif_sin_espacios_ni_guiones_y_en_mayusculas(sigrid_api):
    falsa = sigrid_api()
    _cliente().buscar_proveedores(texto="  b-12 34 x  ")
    patron_nombre, patron_cif = falsa.peticiones[0]["parameters"][4:]
    assert patron_nombre == "%b-12 34 x%"
    assert patron_cif == "%B1234X%"


def test_f114_r16_comodines_del_texto_escapados_en_ambos_patrones(sigrid_api):
    falsa = sigrid_api()
    _cliente().buscar_proveedores(texto="a_b%")
    assert falsa.peticiones[0]["parameters"][4:] == ["%a!_b!%%", "%A!_B!%%"]


# ------------------------------------------------------------------ #
# R17 · uno por CIF, ordenado, dedupe por CIF normalizado
# ------------------------------------------------------------------ #
def test_f114_r17_un_proveedor_por_cif_con_sus_fichas(sigrid_api):
    sigrid_api([
        ["B00000001", "ALFA SL", 1],
        ["B00000002", "BETA SA", 3],
    ])
    resultado = _cliente().buscar_proveedores(texto="sl sa")
    assert [(p.cif, p.nombre, p.fichas) for p in resultado.items] == [
        ("B00000001", "ALFA SL", 1),
        ("B00000002", "BETA SA", 3),
    ]
    assert resultado.mas is False


def test_f114_r17_dos_grafias_del_mismo_cif_se_suman(sigrid_api):
    sigrid_api([
        ["B00000001", "ALFA SL", 2],
        ["B00000002", "BETA SA", 1],
        ["b-0000000 1", "ALFA SOCIEDAD", 1],
    ])
    resultado = _cliente().buscar_proveedores(texto="alfa")
    assert [(p.cif, p.nombre, p.fichas) for p in resultado.items] == [
        ("B00000001", "ALFA SL", 3),
        ("B00000002", "BETA SA", 1),
    ]


def test_f114_r17_fichas_ausentes_cuentan_como_una(sigrid_api):
    sigrid_api([
        ["B00000001", "ALFA SL", None],
        ["B 00000001", "ALFA SL", None],
    ])
    (unico,) = _cliente().buscar_proveedores(texto="alfa").items
    assert unico.fichas == 2


# ------------------------------------------------------------------ #
# R18 · límite + 1 y ``mas``
# ------------------------------------------------------------------ #
def _filas(n):
    return [[f"B{i:08d}", f"PROVEEDOR {i:03d}", 1] for i in range(n)]


def test_f114_r18_con_la_fila_de_mas_corta_y_avisa(sigrid_api):
    sigrid_api(_filas(51))
    resultado = _cliente().buscar_proveedores(texto="proveedor")
    assert len(resultado.items) == 50
    assert resultado.items[-1].cif == "B00000049"
    assert resultado.mas is True


def test_f114_r18_justo_el_limite_no_hay_mas(sigrid_api):
    sigrid_api(_filas(50))
    resultado = _cliente().buscar_proveedores(texto="proveedor")
    assert len(resultado.items) == 50
    assert resultado.mas is False


def test_f114_r18_mas_cuenta_filas_sql_no_las_que_quedan(sigrid_api):
    """51 filas de SQL con un duplicado: quedan 50 tras deduplicar, pero hay más."""
    filas = _filas(50) + [["B 00000000", "PROVEEDOR 000", 1]]
    sigrid_api(filas)
    resultado = _cliente().buscar_proveedores(texto="proveedor")
    assert len(resultado.items) == 50
    assert resultado.mas is True


# ------------------------------------------------------------------ #
# R19 · propios y sin CIF fuera
# ------------------------------------------------------------------ #
def test_f114_r19_fuera_cif_propio_y_filas_sin_cif(sigrid_api):
    sigrid_api([
        ["A81873903", "PROPIA", 1],
        ["a-81873903", "PROPIA OTRA", 1],
        [None, "SIN CIF", 1],
        ["   ", "BLANCO", 1],
        ["B00000001", "ALFA SL", 1],
    ])
    resultado = _cliente().buscar_proveedores(texto="xxx")
    assert [p.cif for p in resultado.items] == ["B00000001"]


# ------------------------------------------------------------------ #
# R20 · NO_TOLERA y log
# ------------------------------------------------------------------ #
def test_f114_r20_truncado_lanza(sigrid_api):
    sigrid_api(_filas(3), truncated=True)
    with pytest.raises(SigridRespuestaTruncada) as exc:
        _cliente().buscar_proveedores(texto="proveedor")
    assert exc.value.etiqueta == "proveedores_todos"


def test_f114_r20_log_con_etiqueta_numero_y_mas_sin_clave(sigrid_api, caplog):
    sigrid_api(_filas(51))
    with caplog.at_level(logging.INFO, logger=modulo.__name__):
        _cliente().buscar_proveedores(texto="proveedor")
    mensajes = [r.getMessage() for r in caplog.records]
    assert any(
        "proveedores_todos" in m and "-> 50 proveedores" in m and "mas=True" in m
        for m in mensajes
    ), mensajes
    assert not any("clave-de-test" in m for m in mensajes)


def test_f114_r20_max_rows_del_cliente(sigrid_api):
    falsa = sigrid_api()
    _cliente().buscar_proveedores(texto="proveedor")
    assert falsa.peticiones[0]["max_rows"] == 5000


# ------------------------------------------------------------------ #
# Mínimo (defensa del cliente, R13)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("texto", ["", "ab", "  ab  ", "   "])
def test_f114_r13_bajo_el_minimo_no_llama(sigrid_api, texto):
    falsa = sigrid_api(_filas(3))
    resultado = _cliente().buscar_proveedores(texto=texto)
    assert resultado.items == [] and resultado.mas is False
    assert falsa.peticiones == []


def test_f114_r13_justo_el_minimo_llama(sigrid_api):
    falsa = sigrid_api()
    _cliente().buscar_proveedores(texto=" abc ")
    assert falsa.peticiones[0]["parameters"][4] == "%abc%"


# ------------------------------------------------------------------ #
# R21 · la lista de la obra no cambia
# ------------------------------------------------------------------ #
_SQL_PROVEEDORES_POR_OBRA_DE_SIEMPRE = """\
SELECT DISTINCT
    prv.cif AS cif,
    prv.raz AS nombre
FROM ctr
JOIN con AS con_ctr ON ctr.ide    = con_ctr.ide
JOIN con AS con_obr ON ctr.obride = con_obr.ide
JOIN prv            ON ctr.entide = prv.ide
WHERE con_obr.cod = ?
  AND con_ctr.emp = 1
ORDER BY prv.raz
"""


def test_f114_r21_proveedores_por_obra_intacto(sigrid_api):
    assert modulo._SQL_PROVEEDORES_POR_OBRA == _SQL_PROVEEDORES_POR_OBRA_DE_SIEMPRE
    falsa = sigrid_api(
        [["B00000001", "ALFA SL"], ["B00000001", "ALFA SL"]],
        columnas=["cif", "nombre"],
    )
    resultado = _cliente().fetch_proveedores_por_obra(codigo_obra="686")
    (peticion,) = falsa.peticiones
    assert peticion["sql"] == _SQL_PROVEEDORES_POR_OBRA_DE_SIEMPRE
    assert peticion["parameters"] == ["0686"]
    assert [p.model_dump(exclude_none=True) for p in resultado] == [
        {"cif": "B00000001", "nombre": "ALFA SL"}
    ]
