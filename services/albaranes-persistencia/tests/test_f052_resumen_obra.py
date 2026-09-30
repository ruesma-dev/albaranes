# tests/test_f052_resumen_obra.py
"""F-052 T5 · candidatos de la obra con UNA consulta agregada (R2, R3, R5).

``fetch_contratos_resumen_por_obra`` deja de traer una fila por línea de
contrato (2.083 en la 0691, cortadas a 1.000 sin aviso) y pide una fila
por proveedor (``WITH`` + ``FOR XML PATH``, design §4). Sobre el doble de
sigrid-api, sin red; el resolver se ejerce con el cliente real.
"""
from __future__ import annotations

import logging

import pytest

from application.services import header_resolver_service as modulo_resolver
from application.services.header_resolver_service import HeaderResolverService
from doble_sigrid_api import (
    CIF_SALMEDINA,
    CONTRATO_SALMEDINA,
    RAZ_SALMEDINA,
    DobleSigridApi,
    Fixture,
    Linea,
    fixture_por_defecto,
)
from ruesma_comun.sigrid import SigridRespuestaTruncada

DOC = "doc-f052"


class _RepoFake:
    """Repositorio mínimo del resolver: líneas del albarán y notas."""

    def __init__(self, conceptos: list[str] | None = None) -> None:
        self._conceptos = conceptos or []
        self.notas: list[str] = []

    def get_merge_lines_for_scoring(self, *, document_id: str) -> list[dict]:
        return [{"codigo": "", "concepto": c, "contexto_linea_json": None} for c in self._conceptos]

    def append_review_note(self, *, document_id: str, nota: str) -> None:
        self.notas.append(nota)

    def remove_review_note_prefix(self, *, document_id: str, prefijo: str) -> None:
        self.notas = [n for n in self.notas if not n.startswith(prefijo)]


class _ObraFake:
    def search_obras(self):
        return []


def _resolver(cliente, repo) -> HeaderResolverService:
    return HeaderResolverService(obra_client=_ObraFake(), proveedor_client=cliente, repository=repo)


def _por_cif(resumenes) -> dict:
    return {r.cif: (r.nombre, r.codigos_contratos, r.texto) for r in resumenes}


# ------------------------------------------------------------------ #
# R3 · una sola llamada, agregada, NO_TOLERA
# ------------------------------------------------------------------ #
def test_f052_r3_una_sola_peticion_con_la_consulta_agregada():
    doble = DobleSigridApi()
    resumenes = doble.cliente().fetch_contratos_resumen_por_obra(codigo_obra=" 0691 ")
    assert len(resumenes) == 81
    [peticion] = doble.peticiones
    sql = peticion["sql"]
    for fragmento in (
        "WITH base AS",
        "CAST(LTRIM(RTRIM(x.v)) AS NVARCHAR(MAX))",
        "ORDER BY c.cod_ctr",
        "ORDER BY t.v",
        "FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)')",
        "WHERE con_obr.cod = ? AND con_ctr.emp = 1",
    ):
        assert fragmento in sql
    assert sql.rstrip().endswith("ORDER BY p.cif, p.raz")
    assert "OFFSET" not in sql
    assert peticion["parameters"] == ["0691"]
    assert doble.respuestas[0]["truncated"] is False


def test_f052_r3_truncado_lanza_y_no_pagina():
    doble = DobleSigridApi(forzar_truncado=True)
    with pytest.raises(SigridRespuestaTruncada) as info:
        doble.cliente().fetch_contratos_resumen_por_obra(codigo_obra="0691")
    assert info.value.etiqueta == "contratos_resumen_obra_0691"
    assert len(doble.peticiones) == 1


def test_f052_r3_sin_obra_no_consulta():
    doble = DobleSigridApi()
    assert doble.cliente().fetch_contratos_resumen_por_obra(codigo_obra="  ") == []
    assert doble.peticiones == []


def test_f052_r3_un_resumen_por_cif_codigos_y_texto():
    """Un CIF con dos razones sociales sale dos veces de la SQL: se queda
    la primera en el orden de la SQL (``cif, raz``). Códigos por ``|``
    sin vacíos; texto ``NULL`` → ``""``; un contrato sin líneas sigue
    siendo candidato."""
    lineas = (
        Linea("0001", "B2", "ZETA, S.L.", 1, "C2/01", "HORMIGON HA-25", 11, 1, "BOMBEO", None),
        Linea("0001", "B2", "ALFA, S.L.", 2, "C1/01", None, 12, 1, "GASOLEO A", "P1"),
        Linea("0001", "B1", "SIN TEXTO, S.A.", 3, "C9/01", "  ", None, None, None, None),
    )
    doble = DobleSigridApi(Fixture(lineas=lineas, proveedores_global=()))
    resumenes = doble.cliente().fetch_contratos_resumen_por_obra(codigo_obra="0001")
    assert [(r.cif, r.nombre, r.codigos_contratos, r.texto) for r in resumenes] == [
        ("B1", "SIN TEXTO, S.A.", ("C9/01",), ""),
        ("B2", "ALFA, S.L.", ("C1/01", "C2/01"), "BOMBEO GASOLEO A HORMIGON HA-25 P1"),
    ]


# ------------------------------------------------------------------ #
# R2 · el resolver ve y puntúa los 81 proveedores de la obra
# ------------------------------------------------------------------ #
def test_f052_r2_el_resumen_trae_los_81_con_salmedina_y_su_texto():
    resumenes = DobleSigridApi().cliente().fetch_contratos_resumen_por_obra(codigo_obra="0691")
    por_cif = _por_cif(resumenes)
    assert set(por_cif) == {ln.cif for ln in fixture_por_defecto().de_obra("0691")}
    nombre, codigos, texto = por_cif[CIF_SALMEDINA]
    assert (nombre, codigos) == (RAZ_SALMEDINA, (CONTRATO_SALMEDINA,))
    assert "CONTENEDOR 6 M3 RCD" in texto
    assert "CANON VERTIDO ESCOMBRO LIMPIO" in texto


def test_f052_r2_paso_obra_familia_puntua_los_81(caplog):
    resolver = _resolver(DobleSigridApi().cliente(), _RepoFake(["CONTENEDOR 6 M3 RCD"]))
    with caplog.at_level(logging.INFO, logger=modulo_resolver.logger.name):
        cif, origen = resolver._resolver_por_obra_y_familia(
            proveedor_nombre="SALMEDINA", obra_codigo="0691", merge_document_id=DOC,
        )
    puntuados = [r for r in caplog.records if "candidato obra=0691" in r.getMessage()]
    assert len(puntuados) == 81
    assert (cif, origen) == (CIF_SALMEDINA, "deterministic")


# ------------------------------------------------------------------ #
# R5 · el orden de llegada no cambia nada
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_f052_r5_barajado_mismo_resumen_y_mismo_orden(semilla):
    referencia = DobleSigridApi().cliente().fetch_contratos_resumen_por_obra(codigo_obra="0691")
    doble = DobleSigridApi(barajar=semilla)
    barajado = doble.cliente().fetch_contratos_resumen_por_obra(codigo_obra="0691")
    llegada = [fila[0] for fila in doble.respuestas[0]["rows"]]
    assert llegada != sorted(llegada)  # el doble de verdad ha barajado
    assert len(barajado) == 81
    assert barajado == referencia


@pytest.mark.parametrize(
    "nombre,conceptos",
    [
        pytest.param("SALMEDINA", ["CONTENEDOR 6 M3 RCD"], id="red-por-nombre"),
        pytest.param(None, ["CONTENEDOR 6 M3 RCD"], id="familia-sin-nombre"),
        pytest.param("PROVEEDOR", ["HORMIGON HA-25"], id="nombre-debil-y-familia"),
    ],
)
def test_f052_r5_mismo_ganador_y_misma_nota_con_tres_barajados(nombre, conceptos):
    resultados = []
    for semilla in (None, 11, 22, 33):
        repo = _RepoFake(conceptos)
        resolver = _resolver(DobleSigridApi(barajar=semilla).cliente(), repo)
        decision = resolver._resolver_por_obra_y_familia(
            proveedor_nombre=nombre, obra_codigo="0691", merge_document_id=DOC,
        )
        resultados.append((decision, tuple(repo.notas)))
    assert len(set(resultados)) == 1
