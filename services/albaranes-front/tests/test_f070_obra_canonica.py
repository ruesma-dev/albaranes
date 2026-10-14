# tests/test_f070_obra_canonica.py
"""F-070 · sv4 consulta y guarda la obra canónica (R10–R13).

Regla del humano: todo código de obra lleva el 0 inicial salvo VAR y POSTV2.
Caso real (HERMANOS SAN JUAN): merge con ``686`` ⇒ sv4 preguntaba a
sigrid-api por ``686`` y los combos salían vacíos (con ``0686``: 115
proveedores, 117 contratos, 2412 partidas).

- R10/R11: ``SigridLookupClient`` canoniza en las tres consultas por obra;
  lo que no encaja va tal cual (recortado) y el vacío no consulta.
- R12: al guardar la cabecera se guarda la obra canonizada.
- R13: el estado de la búsqueda de contratos compara con la misma regla.

Sin red (``httpx.MockTransport``) ni BBDD real (SQLite de los tests de sv4).
"""
from __future__ import annotations

import json

import httpx
import pytest

from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient


# ================================================================ #
# R10, R11 — las tres consultas a Sigrid por obra
# ================================================================ #
class _SigridApiFalsa:
    """``/api/sql/read`` falso: registra los parámetros de cada SQL."""

    def __init__(self) -> None:
        self.parametros: list[tuple[str, list]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        cuerpo = json.loads(request.content)
        sql = cuerpo["sql"]
        if sql == modulo._SQL_PROVEEDORES_POR_OBRA:
            nombre, columnas, filas = "proveedores", ["cif", "nombre"], [["B1", "P"]]
        elif sql == modulo._SQL_CONTRATOS_POR_OBRA:
            nombre = "contratos"
            columnas = ["codigo", "nombre", "cif", "nombre_proveedor"]
            filas = [["CTSU24/0524", "C", "B1", "P"]]
        elif sql == modulo._SQL_PARTIDAS_POR_OBRA:
            nombre = "partidas"
            columnas, filas = ["ide", "padide", "cod", "res"], [[1, 0, "01", "CAP"]]
        else:  # pragma: no cover - F-070 no toca otras SQL
            return httpx.Response(400, json={"ok": False})
        self.parametros.append((nombre, cuerpo["parameters"]))
        return httpx.Response(200, json={
            "ok": True, "columns": columnas, "rows": filas, "truncated": False,
        })


@pytest.fixture
def sigrid_api(monkeypatch) -> _SigridApiFalsa:
    falsa = _SigridApiFalsa()
    monkeypatch.setattr(
        modulo.httpx, "HTTPTransport", lambda *a, **k: httpx.MockTransport(falsa),
    )
    return falsa


def _cliente() -> SigridLookupClient:
    return SigridLookupClient(
        base_url="https://sigrid.invalid", function_key="clave-de-test", database="db-test",
    )


def _consultar(consulta: str, codigo_obra):
    cliente = _cliente()
    if consulta == "proveedores":
        return cliente.fetch_proveedores_por_obra(codigo_obra=codigo_obra)
    if consulta == "contratos":
        return cliente.fetch_contratos(codigo_obra=codigo_obra)
    return cliente.fetch_partidas_por_obra(codigo_obra=codigo_obra)


_CONSULTAS = ["proveedores", "contratos", "partidas"]


@pytest.mark.parametrize("consulta", _CONSULTAS)
@pytest.mark.parametrize(
    ("en_merge", "preguntado"),
    [
        ("686", "0686"),
        (" 686 ", "0686"),
        ("0686", "0686"),
        (" var ", "VAR"),
        ("Postv2", "POSTV2"),
    ],
)
def test_f070_r10_consulta_con_la_obra_canonica(sigrid_api, consulta, en_merge, preguntado):
    filas = _consultar(consulta, en_merge)
    assert sigrid_api.parametros == [(consulta, [preguntado])]
    assert len(filas) == 1


@pytest.mark.parametrize("consulta", _CONSULTAS)
@pytest.mark.parametrize(
    ("en_merge", "preguntado"),
    [("GG", "GG"), (" GG ", "GG"), ("gg", "gg"), ("1234", "1234"), (" 0578-B", "0578-B")],
)
def test_f070_r11_lo_que_no_encaja_va_tal_cual_recortado(
    sigrid_api, consulta, en_merge, preguntado,
):
    _consultar(consulta, en_merge)
    assert sigrid_api.parametros == [(consulta, [preguntado])]


@pytest.mark.parametrize("consulta", _CONSULTAS)
@pytest.mark.parametrize("vacio", ["", "   ", None])
def test_f070_r11_sin_obra_no_consulta(sigrid_api, consulta, vacio):
    assert _consultar(consulta, vacio) == []
    assert sigrid_api.parametros == []


# ================================================================ #
# R12 — guardar la cabecera guarda la obra canonizada
# ================================================================ #
def _obra_guardada(monkeypatch, obra_codigo):
    from f065_bbdd import DOC, construir, repositorio
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    from domain.models.review_models import MergeDocumentUpdatePayload

    motor = construir()
    repo = repositorio(motor)
    monkeypatch.setattr(repo, "get_document_detail", lambda document_id: "detalle")
    repo.update_document_y_transicion(
        document_id=DOC,
        payload=MergeDocumentUpdatePayload(obra_codigo=obra_codigo, numero_albaran="A-1"),
    )
    with Session(motor) as sesion:
        return sesion.execute(
            text("SELECT obra_codigo FROM albaran_documents_merge WHERE id = :id"),
            {"id": DOC},
        ).scalar_one()


@pytest.mark.parametrize(
    ("enviado", "guardado"),
    [
        ("686", "0686"),
        (" 686 ", "0686"),
        ("0686", "0686"),
        ("var", "VAR"),
        (" Postv2 ", "POSTV2"),
        (" GG ", "GG"),       # no encaja: recortado, como hoy
        ("1234", "1234"),
        ("   ", None),
        (None, None),
    ],
)
def test_f070_r12_guardar_cabecera_guarda_la_obra_canonica(monkeypatch, enviado, guardado):
    assert _obra_guardada(monkeypatch, enviado) == guardado


# ================================================================ #
# R13 — el estado de la búsqueda de contratos compara con la misma regla
# ================================================================ #
def _estado(obra_actual, rastro_obra, resultado="encontrados"):
    from application.services.busqueda_contratos import (
        debe_relanzar_busqueda,
        estado_busqueda,
    )
    from domain.models.review_models import RastroBusquedaContratos

    vista = estado_busqueda(
        "B82899550", obra_actual,
        RastroBusquedaContratos(
            cif=None if resultado == "sin_datos" else "B82899550",
            obra=rastro_obra, resultado=resultado, at_utc="2026-10-14T10:00:00+00:00",
        ),
    )
    return vista.estado, debe_relanzar_busqueda(vista)


@pytest.mark.parametrize(
    ("obra_actual", "rastro_obra"),
    [
        ("VAR", "VAR"),
        (" var ", "VAR"),
        ("POSTV2", "POSTV2"),
        ("686", "0686"),
        ("0686", "0686"),
    ],
)
def test_f070_r13_merge_y_rastro_canonicos_coinciden(obra_actual, rastro_obra):
    assert _estado(obra_actual, rastro_obra) == ("vigente", False)


def test_f070_r13_rastro_viejo_sin_obra_frente_a_var_esta_desfasado():
    """Antes de F-070 sv3 sellaba ``sin_datos`` con obra nula para un merge
    ``VAR``: ahora el merge ``VAR`` es buscable y «Guardar» relanza (D4-A)."""
    assert _estado("VAR", None, resultado="sin_datos") == ("desfasada", True)


@pytest.mark.parametrize(
    ("obra_actual", "rastro_obra"),
    [("VAR", "POSTV2"), ("686", "0687"), ("GG", "GG")],
)
def test_f070_r13_obras_distintas_o_no_canonicas_no_coinciden(obra_actual, rastro_obra):
    estado, _ = _estado(obra_actual, rastro_obra)
    assert estado == "desfasada"
