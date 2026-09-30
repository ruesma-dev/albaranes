# tests/test_f052_nota_proveedor.py
"""F-052 T7 · la nota de la red de proveedor dice la verdad (R1, R5, R15–R19).

Cuando el CIF leído no existe en Sigrid, la red de F-002 busca un candidato
por nombre entre los proveedores con contrato en la obra. Hasta F-052 una
consulta fallida, una obra ausente o un nombre sin leer acababan todos en la
misma nota: «ningún proveedor con contrato en la obra casa». Ahora
``_mejor_candidato_por_nombre`` devuelve ``(candidato, motivo, n)`` y la
nota se redacta por motivo (design §6).

Sin red ni BBDD: el cliente es el real sobre el doble de sigrid-api, o un
fake cuando lo que se prueba es el tipo de fallo.
"""
from __future__ import annotations

import httpx
import pytest
from doble_sigrid_api import CIF_SALMEDINA, RAZ_SALMEDINA, DobleSigridApi
from ruesma_comun.sigrid import SigridRespuestaTruncada

from application.services.header_resolver_service import (
    _NOTA_PROVEEDOR_PREFIX,
    HeaderResolverService,
)
from domain.models.header_resolution_models import (
    MergeHeaderForResolution,
    ProveedorObraResumen,
)

DOC = "doc-f052-nota"
#: El CIF mal leído por IA1 en SS-0026122 (no existe en Sigrid).
CIF_MAL_LEIDO = "B82890580"
MOTIVO = f"proveedor_cif_no_casa:{CIF_MAL_LEIDO}"


class _Repo:
    """Repositorio del resolver: cabecera fija; registra marcas y notas."""

    def __init__(self, header: MergeHeaderForResolution) -> None:
        self._header = header
        self.marcas: list[tuple[str, str, str]] = []
        self.notas: list[str] = []
        self.resoluciones: list[tuple[str | None, str | None, str]] = []

    def get_merge_header_for_resolution(self, *, document_id: str):
        return self._header

    def update_merge_resolved_header(
        self, *, document_id, obra_codigo_det, proveedor_cif_det,
        proveedor_origen="deterministic",
    ) -> None:
        self.resoluciones.append((obra_codigo_det, proveedor_cif_det, proveedor_origen))

    def get_merge_lines_for_scoring(self, *, document_id: str) -> list[dict]:
        return []

    def append_review_note(self, *, document_id: str, nota: str) -> None:
        self.notas.append(nota)

    def remove_review_note_prefix(self, *, document_id: str, prefijo: str) -> None:
        self.notas = [n for n in self.notas if not n.startswith(prefijo)]

    def set_merge_proveedor_nombre_canonico(self, *, document_id: str, nombre: str) -> None:
        raise AssertionError("un CIF inexistente no canoniza nada")

    def marcar_revision_cabecera(
        self, *, document_id: str, motivo: str, nota: str, nota_prefijo: str,
    ) -> None:
        self.marcas.append((motivo, nota, nota_prefijo))


class _Obras:
    def search_obras(self):
        return []


class _ClienteQueFalla:
    """CIF inexistente y consulta de la obra que lanza ``error``."""

    def __init__(self, error: Exception) -> None:
        self._error = error
        self.consultas_obra: list[str] = []

    def fetch_proveedor_by_cif(self, *, cif: str):
        return None

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra: str):
        self.consultas_obra.append(codigo_obra)
        raise self._error

    def search_proveedores(self):  # pragma: no cover - con CIF no se llega
        raise AssertionError("con CIF leído no hay fallback global")


class _ClienteCon:
    """CIF inexistente y una lista fija de proveedores de la obra."""

    def __init__(self, resumenes: list[ProveedorObraResumen]) -> None:
        self._resumenes = resumenes

    def fetch_proveedor_by_cif(self, *, cif: str):
        return None

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra: str):
        return list(self._resumenes)


def _header(*, nombre: str | None = "SALMEDINA", obra: str | None = "0691") -> MergeHeaderForResolution:
    return MergeHeaderForResolution(
        obra_codigo=obra, obra_nombre=None, obra_direccion=None,
        proveedor_cif=CIF_MAL_LEIDO, proveedor_nombre=nombre,
    )


def _resolver(cliente, repo) -> HeaderResolverService:
    return HeaderResolverService(obra_client=_Obras(), proveedor_client=cliente, repository=repo)


def _nota_tras_resolver(cliente, **header) -> str:
    repo = _Repo(_header(**header))
    _resolver(cliente, repo).resolve_merge_document(merge_document_id=DOC)
    [(motivo, nota, prefijo)] = repo.marcas
    assert motivo == MOTIVO
    assert prefijo == _NOTA_PROVEEDOR_PREFIX
    return nota


def _resumen(cif: str, nombre: str) -> ProveedorObraResumen:
    return ProveedorObraResumen(cif=cif, nombre=nombre, codigos_contratos=("C1",), texto="")


# ------------------------------------------------------------------ #
# R1 · regresión SS-0026122: el bueno estaba más allá de la fila 1.000
# ------------------------------------------------------------------ #
def test_f052_r1_la_red_por_nombre_propone_salmedina_con_el_cliente_real():
    doble = DobleSigridApi()
    nota = _nota_tras_resolver(doble.cliente())
    assert f"PROPUESTA: {CIF_SALMEDINA} — {RAZ_SALMEDINA}" in nota
    assert "obra 0691" in nota
    # Una consulta del CIF y UNA de la obra (la agregada), sin paginar.
    assert len(doble.peticiones_con("SELECT TOP 1 prv.cif")) == 1
    assert len(doble.peticiones_con("FOR XML PATH")) == 1
    assert len(doble.peticiones) == 2


def test_f052_r1_mejor_candidato_devuelve_candidato_motivo_y_n():
    resolver = _resolver(DobleSigridApi().cliente(), _Repo(_header()))
    candidato, motivo, n = resolver._mejor_candidato_por_nombre(
        proveedor_nombre="SALMEDINA", obra_codigo_efectiva="0691",
    )
    assert (candidato.cif, motivo, n) == (CIF_SALMEDINA, "propuesta", 81)


@pytest.mark.parametrize("semilla", [11, 22, 33])
def test_f052_r5_la_red_por_nombre_no_depende_del_orden_de_llegada(semilla):
    referencia = _nota_tras_resolver(DobleSigridApi().cliente())
    assert _nota_tras_resolver(DobleSigridApi(barajar=semilla).cliente()) == referencia


# ------------------------------------------------------------------ #
# R6 / R15 · consulta fallida: «no se pudo consultar», nunca «nadie casa»
# ------------------------------------------------------------------ #
def test_f052_r6_error_xml_la_nota_dice_que_no_se_pudo_consultar():
    doble = DobleSigridApi(error_xml=True)
    nota = _nota_tras_resolver(doble.cliente())
    assert (
        "no se pudo consultar la lista de proveedores de la obra 0691 "
        "(fallo al consultar Sigrid): no hay propuesta"
    ) in nota
    assert "casa con el nombre" not in nota
    assert "PROPUESTA" not in nota
    assert doble.respuestas[-1]["ok"] is False  # de verdad falló la agregada


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(SigridRespuestaTruncada("contratos_resumen_obra_0691", 1000), id="truncado"),
        pytest.param(RuntimeError("sigrid-api HTTP 500"), id="http-u-ok-false"),
        pytest.param(httpx.ConnectError("sin red"), id="red"),
    ],
)
def test_f052_r15_cualquier_fallo_de_la_consulta_es_consulta_fallida(error):
    cliente = _ClienteQueFalla(error)
    nota = _nota_tras_resolver(cliente)
    assert "no se pudo consultar la lista de proveedores de la obra 0691" in nota
    assert "casa con el nombre" not in nota
    assert cliente.consultas_obra == ["0691"]


def test_f052_r15_mejor_candidato_consulta_fallida_con_n_cero():
    resolver = _resolver(_ClienteQueFalla(RuntimeError("x")), _Repo(_header()))
    assert resolver._mejor_candidato_por_nombre(
        proveedor_nombre="SALMEDINA", obra_codigo_efectiva="0691",
    ) == (None, "consulta_fallida", 0)


# ------------------------------------------------------------------ #
# R16 · sin obra válida · R17 · sin nombre leído
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("obra", [None, "", "OBRA-X", "12345"])
def test_f052_r16_sin_obra_valida_la_nota_lo_dice(obra):
    doble = DobleSigridApi()
    nota = _nota_tras_resolver(doble.cliente(), obra=obra)
    assert "y no hay obra válida con la que buscar candidatos" in nota
    assert "casa con el nombre" not in nota
    assert doble.peticiones_con("FOR XML PATH") == []  # sin obra no se consulta


@pytest.mark.parametrize("nombre", [None, "", "   "])
def test_f052_r17_sin_nombre_leido_la_nota_lo_dice(nombre):
    doble = DobleSigridApi()
    nota = _nota_tras_resolver(doble.cliente(), nombre=nombre)
    assert "y no se leyó nombre de proveedor con el que comparar" in nota
    assert "casa con el nombre" not in nota
    assert "None" not in nota
    assert doble.peticiones_con("FOR XML PATH") == []


def test_f052_r16_sin_obra_ni_nombre_manda_la_obra():
    """Sin obra no hay lista de candidatos que comparar: ese es el motivo
    primero, aunque tampoco haya nombre."""
    resolver = _resolver(DobleSigridApi().cliente(), _Repo(_header()))
    assert resolver._mejor_candidato_por_nombre(
        proveedor_nombre=None, obra_codigo_efectiva=None,
    ) == (None, "sin_obra", 0)
    assert resolver._mejor_candidato_por_nombre(
        proveedor_nombre="  ", obra_codigo_efectiva="0691",
    ) == (None, "sin_nombre", 0)


# ------------------------------------------------------------------ #
# R18 · la consulta funcionó y nadie casa: N real
# ------------------------------------------------------------------ #
def test_f052_r18_nadie_casa_con_los_81_de_la_obra():
    doble = DobleSigridApi()
    nota = _nota_tras_resolver(doble.cliente(), nombre="TRANSPORTES MACOTRAN")
    assert (
        "y ninguno de los 81 proveedores con contrato en la obra 0691 casa "
        "con el nombre leído ('TRANSPORTES MACOTRAN')"
    ) in nota
    assert "PROPUESTA" not in nota


@pytest.mark.parametrize("n", [0, 1, 3])
def test_f052_r18_n_es_el_numero_de_proveedores_devueltos(n):
    resumenes = [_resumen(f"B0000000{i}", f"ARIDOS {i}, S.A.") for i in range(n)]
    nota = _nota_tras_resolver(_ClienteCon(resumenes), nombre="TRANSPORTES MACOTRAN")
    assert f"ninguno de los {n} proveedores con contrato en la obra 0691" in nota


def test_f052_r18_mejor_candidato_nadie_casa_con_n():
    resolver = _resolver(_ClienteCon([_resumen("B1", "ARIDOS, S.A."), _resumen("B2", "GRUAS, S.L.")]),
                         _Repo(_header()))
    assert resolver._mejor_candidato_por_nombre(
        proveedor_nombre="TRANSPORTES MACOTRAN", obra_codigo_efectiva="0691",
    ) == (None, "nadie_casa", 2)


# ------------------------------------------------------------------ #
# R19 · mismo motivo y mismo prefijo en todos los casos
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "cliente,header",
    [
        pytest.param(lambda: DobleSigridApi().cliente(), {}, id="propuesta"),
        pytest.param(lambda: DobleSigridApi(error_xml=True).cliente(), {}, id="consulta_fallida"),
        pytest.param(lambda: DobleSigridApi().cliente(), {"obra": None}, id="sin_obra"),
        pytest.param(lambda: DobleSigridApi().cliente(), {"nombre": None}, id="sin_nombre"),
        pytest.param(lambda: DobleSigridApi().cliente(), {"nombre": "MACOTRAN"}, id="nadie_casa"),
    ],
)
def test_f052_r19_motivo_y_prefijo_de_siempre(cliente, header):
    nota = _nota_tras_resolver(cliente(), **header)  # comprueba motivo y prefijo
    assert nota.startswith(
        f"{_NOTA_PROVEEDOR_PREFIX} el CIF leido {CIF_MAL_LEIDO} no existe en Sigrid",
    )
