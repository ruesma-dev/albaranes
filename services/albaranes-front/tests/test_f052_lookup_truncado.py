# tests/test_f052_lookup_truncado.py
"""F-052 R28 · el lookup de sv4 no usa en silencio una respuesta truncada.

``SigridLookupClient`` alimenta los desplegables de cabecera del portal.
sigrid-api marca ``truncated=true`` cuando corta en ``max_rows`` y hasta
F-052 nadie lo miraba. Ahora cada consulta declara su política
(``ruesma_comun.sigrid``):

- proveedores de la obra: ``NO_TOLERA`` ⇒ ``SigridRespuestaTruncada``
  (el endpoint la convierte en ``ok=false`` y el front mantiene la entrada
  manual: mejor eso que una lista a la que le falta el proveedor bueno);
- obras, contratos y partidas: ``TOLERA`` ⇒ filas tal cual + WARNING.

La SQL no cambia ni se comparte con sv3 (D2).

Sin red: ``httpx.MockTransport`` en lugar del transporte real.
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
    """Responde a ``/api/sql/read`` con las filas que le toque a cada SQL."""

    def __init__(self, *, truncated: bool):
        self.truncated = truncated
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        cuerpo = json.loads(request.content)
        self.peticiones.append(cuerpo)
        sql = cuerpo["sql"]
        if sql == modulo._SQL_PROVEEDORES_POR_OBRA:
            columnas, filas = ["cif", "nombre"], [["B82899550", "SALMEDINA"]]
        elif sql == modulo._SQL_OBRAS:
            columnas, filas = ["codigo", "nombre"], [["0691", "OBRA 691"]]
        elif sql == modulo._SQL_CONTRATOS_POR_OBRA:
            columnas = ["codigo", "nombre", "cif", "nombre_proveedor"]
            filas = [["CTSU24/0402", "ÁRIDOS", "B82899550", "SALMEDINA"]]
        elif sql == modulo._SQL_PARTIDAS_POR_OBRA:
            columnas = ["ide", "padide", "cod", "res"]
            filas = [[1, 0, "01", "CAP"], [2, 1, "01.01", "HORMIGÓN"]]
        else:  # pragma: no cover - una SQL nueva sería un cambio de R28
            return httpx.Response(400, json={"ok": False})
        return httpx.Response(200, json={
            "ok": True, "columns": columnas, "rows": filas,
            "truncated": self.truncated,
        })


@pytest.fixture
def sigrid_api(monkeypatch):
    """Cambia el transporte HTTP del cliente por la API falsa."""

    def _instalar(*, truncated: bool) -> _SigridApiFalsa:
        falsa = _SigridApiFalsa(truncated=truncated)
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


def test_f052_r28_proveedores_truncados_lanzan(sigrid_api):
    sigrid_api(truncated=True)
    with pytest.raises(SigridRespuestaTruncada) as exc:
        _cliente().fetch_proveedores_por_obra(codigo_obra="0691")
    assert exc.value.etiqueta == "proveedores_obra_0691"
    assert exc.value.filas == 1


@pytest.mark.parametrize(
    ("llamada", "etiqueta", "n"),
    [
        (lambda c: c.fetch_obras(), "obras", 1),
        (lambda c: c.fetch_contratos(codigo_obra="0691"), "contratos_obra_0691", 1),
        (lambda c: c.fetch_partidas_por_obra(codigo_obra="0691"),
         "partidas_obra_0691", 1),
    ],
    ids=["obras", "contratos", "partidas"],
)
def test_f052_r28_obras_contratos_y_partidas_toleran_con_warning(
    sigrid_api, caplog, llamada, etiqueta, n,
):
    sigrid_api(truncated=True)
    with caplog.at_level(logging.WARNING):
        resultado = llamada(_cliente())
    assert len(resultado) == n
    avisos = [r.getMessage() for r in caplog.records
              if r.levelno == logging.WARNING]
    assert any("truncada" in a and etiqueta in a for a in avisos), avisos


@pytest.mark.parametrize(
    "llamada",
    [
        lambda c: c.fetch_proveedores_por_obra(codigo_obra="0691"),
        lambda c: c.fetch_obras(),
        lambda c: c.fetch_contratos(codigo_obra="0691"),
        lambda c: c.fetch_partidas_por_obra(codigo_obra="0691"),
    ],
    ids=["proveedores", "obras", "contratos", "partidas"],
)
def test_f052_r28_sin_truncado_ni_lanza_ni_avisa(sigrid_api, caplog, llamada):
    sigrid_api(truncated=False)
    with caplog.at_level(logging.WARNING):
        assert llamada(_cliente())
    assert not [r for r in caplog.records if "truncada" in r.getMessage()]


def test_f052_r28_la_sql_y_el_max_rows_no_cambian(sigrid_api):
    """D2: la SQL del lookup es la de siempre; solo se mira ``truncated``."""
    falsa = sigrid_api(truncated=False)
    cliente = _cliente()
    cliente.fetch_proveedores_por_obra(codigo_obra="0691")
    cliente.fetch_obras()
    cliente.fetch_contratos(codigo_obra="0691")
    cliente.fetch_partidas_por_obra(codigo_obra="0691")
    assert [p["sql"] for p in falsa.peticiones] == [
        modulo._SQL_PROVEEDORES_POR_OBRA,
        modulo._SQL_OBRAS,
        modulo._SQL_CONTRATOS_POR_OBRA,
        modulo._SQL_PARTIDAS_POR_OBRA,
    ]
    assert {p["max_rows"] for p in falsa.peticiones} == {5000}
    assert "ORDER BY prv.raz" in modulo._SQL_PROVEEDORES_POR_OBRA


def test_f052_r28_post_sql_read_exige_politica(sigrid_api):
    """Sin valor por defecto: una consulta nueva no puede olvidarla."""
    sigrid_api(truncated=False)
    with pytest.raises(TypeError):
        _cliente()._post_sql_read(sql=modulo._SQL_OBRAS, parameters=[],
                                  label="obras")
