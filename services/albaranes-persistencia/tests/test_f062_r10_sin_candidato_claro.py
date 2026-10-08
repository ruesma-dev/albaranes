# tests/test_f062_r10_sin_candidato_claro.py
"""F-062 · R10, R11 — sin candidato claro, la red se comporta como hoy.

Ningún elegible, varios sin margen, sin obra, sin nombre o con la consulta
fallida o truncada: no se escribe CIF ni nombre, motivo
``proveedor_cif_no_casa:<leído>`` y nota ``[AVISO] Proveedor`` con o sin
propuesta (F-002 R9–R10, F-052 R15–R19). Lo único nuevo (R11): si el CIF
leído no es un identificador válido, la nota lo dice.
"""
from __future__ import annotations

import pytest
from doble_sigrid_api import (
    CIF_HORMIGONERA_EMPATE,
    CIF_HORMIGONES_MAT,
    CIF_LEIDO_19407,
    DobleSigridApi,
    fixture_f062,
)
from f062_dobles import RepoRed, pasada
from ruesma_comun.sigrid import SigridRespuestaTruncada

from application.services.header_resolver_service import (
    _NOTA_PROVEEDOR_PREFIX,
    _distancia_edicion,
)
from domain.models.header_resolution_models import ProveedorObraResumen

FRASE_CONTROL = (
    f"El carácter de control del CIF leído {CIF_LEIDO_19407} no es válido: "
    "es una lectura errónea."
)


class _Cliente:
    def __init__(self, resumenes=(), *, error: Exception | None = None) -> None:
        self._resumenes = list(resumenes)
        self._error = error

    def fetch_proveedor_by_cif(self, *, cif):
        return None

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra):
        if self._error is not None:
            raise self._error
        return list(self._resumenes)


def _r(cif, nombre):
    return ProveedorObraResumen(cif=cif, nombre=nombre, codigos_contratos=("C",), texto="")


def _marca_unica(repo: RepoRed) -> str:
    assert repo.aplicadas == []
    assert repo.cif == CIF_LEIDO_19407
    [(motivo, nota, prefijo)] = repo.marcas
    assert motivo == f"proveedor_cif_no_casa:{CIF_LEIDO_19407}"
    assert prefijo == _NOTA_PROVEEDOR_PREFIX
    assert nota.startswith(f"{_NOTA_PROVEEDOR_PREFIX} el CIF leido {CIF_LEIDO_19407} no existe en Sigrid")
    return nota


# ------------------------------------------------------------------ #
# R10 · cada forma de «no hay candidato claro»
# ------------------------------------------------------------------ #
def test_f062_r10_empate_sin_margen_propone_como_hoy():
    """Dos hormigoneras con CIF válido y nombre completo, sin margen de
    distancia al leído: se propone la primera, no se aplica nada."""
    a = _r("B66056201", "HORMIGONES MAT, S.L.U.")
    b = _r("B66056219", "HORMIGONES MAT DEL NORTE, S.L.")
    repo = RepoRed(cif="B66056291", nombre="Hormigones Mat SL", obra="0720")
    # 1 frente a 2: margen 1 < 2.
    pasada(_Cliente([a, b]), repo)
    assert repo.aplicadas == []
    [(motivo, nota, _)] = repo.marcas
    assert motivo == "proveedor_cif_no_casa:B66056291"
    assert "PROPUESTA: B66056201" in nota


@pytest.mark.parametrize(
    ("resumenes", "propuesta"),
    [
        pytest.param([], None, id="obra-sin-proveedores"),
        pytest.param([_r("B11111119", "ARIDOS DEL SUR, S.L.")], None, id="nadie-casa"),
        pytest.param([_r("B66056291", "HORMIGONES MAT, S.L.U.")], "B66056291", id="candidato-con-control-invalido"),
        pytest.param([_r(CIF_HORMIGONES_MAT, "HORMIGONES DEL VALLE")], CIF_HORMIGONES_MAT, id="nombre-a-medias"),
        pytest.param([_r("PT123456789", "HORMIGONES MAT")], "PT123456789", id="extranjero"),
    ],
)
def test_f062_r10_sin_elegibles_no_se_aplica(resumenes, propuesta):
    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720")
    pasada(_Cliente(resumenes), repo)
    nota = _marca_unica(repo)
    if propuesta:
        assert f"PROPUESTA: {propuesta}" in nota
    else:
        assert "PROPUESTA" not in nota


@pytest.mark.parametrize(
    ("header", "cliente", "trozo"),
    [
        pytest.param({"obra": None}, _Cliente([_r(CIF_HORMIGONES_MAT, "HORMIGONES MAT")]),
                     "y no hay obra válida con la que buscar candidatos", id="sin-obra"),
        pytest.param({"nombre": None}, _Cliente([_r(CIF_HORMIGONES_MAT, "HORMIGONES MAT")]),
                     "y no se leyó nombre de proveedor con el que comparar", id="sin-nombre"),
        pytest.param({}, _Cliente(error=RuntimeError("sigrid-api 500")),
                     "no se pudo consultar la lista de proveedores de la obra 0720", id="consulta-fallida"),
        pytest.param({}, _Cliente(error=SigridRespuestaTruncada("contratos_resumen_obra_0720", 1000)),
                     "no se pudo consultar la lista de proveedores de la obra 0720", id="truncada"),
    ],
)
def test_f062_r10_sin_obra_sin_nombre_o_consulta_fallida(header, cliente, trozo):
    datos = {"cif": CIF_LEIDO_19407, "nombre": "Hormigones Mat SL", "obra": "0720"}
    datos.update(header)
    repo = RepoRed(**datos)
    pasada(cliente, repo)
    assert trozo in _marca_unica(repo)


def test_f062_r10_con_el_doble_y_el_empate_de_la_0720_sin_margen():
    """Con el fixture real: un leído equidistante de las dos hormigoneras
    elegibles no tiene candidato claro."""
    doble = DobleSigridApi(fixture_f062())
    # Dista 4 de HORMIGONES MAT y 5 de la otra hormigonera: margen 1 < 2.
    leido = "B66053453"
    assert _distancia_edicion(leido, CIF_HORMIGONES_MAT) == 4
    assert _distancia_edicion(leido, CIF_HORMIGONERA_EMPATE) == 5
    repo = RepoRed(cif=leido, nombre="Hormigones Mat SL", obra="0720")
    pasada(doble.cliente(), repo)
    assert repo.aplicadas == []
    [(motivo, nota, _)] = repo.marcas
    assert motivo == f"proveedor_cif_no_casa:{leido}"
    # La propuesta de F-052, como hoy: la primera con el mejor nombre.
    assert f"PROPUESTA: {CIF_HORMIGONERA_EMPATE} —" in nota


# ------------------------------------------------------------------ #
# R11 · el control inválido del leído se dice en la nota
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "cliente",
    [
        pytest.param(_Cliente([]), id="sin-propuesta"),
        pytest.param(_Cliente([_r("B66056291", "HORMIGONES MAT, S.L.U.")]), id="con-propuesta"),
        pytest.param(_Cliente(error=RuntimeError("x")), id="consulta-fallida"),
    ],
)
def test_f062_r11_control_invalido_se_anade_a_la_nota(cliente):
    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720")
    pasada(cliente, repo)
    nota = _marca_unica(repo)
    assert nota.endswith(FRASE_CONTROL)


def test_f062_r11_la_frase_no_rompe_la_consulta_de_vigilancia_de_propuestas():
    """Las consultas A.1/A.2 del humano buscan «no existe en Sigrid.
    PROPUESTA:» tal cual: la frase del control va al final."""
    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720")
    pasada(_Cliente([_r("B66056291", "HORMIGONES MAT, S.L.U.")]), repo)
    assert "no existe en Sigrid. PROPUESTA: B66056291 —" in _marca_unica(repo)


def test_f062_r11_con_control_valido_no_se_anade_nada():
    leido_valido = "B66056219"
    repo = RepoRed(cif=leido_valido, nombre="TRANSPORTES MACOTRAN", obra="0720")
    pasada(_Cliente([]), repo)
    [(_, nota, _)] = repo.marcas
    assert "carácter de control" not in nota
    assert nota.endswith("Revisa el proveedor en el portal.")
