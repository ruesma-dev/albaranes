# tests/test_f062_r3_candidato_claro.py
"""F-062 · R3, R4, R5 — qué es un «candidato claro» de la obra.

Elegibles: candidatos con contrato en la obra, identificador fiscal válido
y nombre completo (``score >= 1,0`` por defecto), agrupados por CIF
normalizado. Uno solo ⇒ claro. Varios ⇒ gana el de CIF más cercano al
leído si saca al siguiente un margen de distancia (2 por defecto). La
distancia solo desempata; el control del CIF leído no cambia la regla.

T4 al principio: la consulta de candidatos de la obra se hace UNA vez por
pasada (``_candidatos_puntuados``) y la propuesta de F-052 sale de ahí.
"""
from __future__ import annotations

import pytest
from application.services.header_resolver_service import HeaderResolverService
from domain.models.header_resolution_models import ProveedorObraResumen

from doble_sigrid_api import CIF_HORMIGONES_MAT


class _Obras:
    def search_obras(self):
        return []


class _Cliente:
    def __init__(self, resumenes=None, *, error: Exception | None = None) -> None:
        self._resumenes = list(resumenes or [])
        self._error = error
        self.consultas: list[str] = []

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra: str):
        self.consultas.append(codigo_obra)
        if self._error is not None:
            raise self._error
        return list(self._resumenes)


def _r(cif: str, nombre: str | None) -> ProveedorObraResumen:
    return ProveedorObraResumen(cif=cif, nombre=nombre, codigos_contratos=("C1",), texto="")


def _resolver(cliente, **kwargs) -> HeaderResolverService:
    return HeaderResolverService(
        obra_client=_Obras(), proveedor_client=cliente, repository=None, **kwargs,
    )


# ------------------------------------------------------------------ #
# T4 · una sola consulta de candidatos por pasada
# ------------------------------------------------------------------ #
def test_f062_t4_candidatos_puntuados_una_consulta_y_todos_con_score():
    cliente = _Cliente([_r(CIF_HORMIGONES_MAT, "HORMIGONES MAT, S.L.U."), _r("B1", "GRUAS, S.L.")])
    puntuados, motivo = _resolver(cliente)._candidatos_puntuados(
        proveedor_nombre="Hormigones Mat SL", obra="0720",
    )
    assert cliente.consultas == ["0720"]
    assert motivo == "propuesta"
    assert [(r.cif, s) for r, s in puntuados] == [(CIF_HORMIGONES_MAT, 1.0), ("B1", 0.0)]


@pytest.mark.parametrize(
    ("nombre", "obra", "cliente", "motivo"),
    [
        ("X", None, _Cliente(), "sin_obra"),
        (None, None, _Cliente(), "sin_obra"),
        ("  ", "0720", _Cliente(), "sin_nombre"),
        ("X", "0720", _Cliente(error=RuntimeError("500")), "consulta_fallida"),
        ("TRANSPORTES MACOTRAN", "0720", _Cliente([_r("B1", "GRUAS, S.L.")]), "nadie_casa"),
    ],
)
def test_f062_t4_candidatos_puntuados_motivos_de_f052(nombre, obra, cliente, motivo):
    puntuados, obtenido = _resolver(cliente)._candidatos_puntuados(
        proveedor_nombre=nombre, obra=obra,
    )
    assert obtenido == motivo
    if motivo != "nadie_casa":
        assert puntuados == []


def test_f062_t4_el_umbral_de_la_propuesta_es_inclusivo():
    cliente = _Cliente([_r("B66000666", "EBRO CANTERAS")])
    _, motivo = _resolver(cliente)._candidatos_puntuados(
        proveedor_nombre="HORMIGONES DEL EBRO", obra="0720",
    )
    assert motivo == "propuesta"  # 0,5 >= 0,5
