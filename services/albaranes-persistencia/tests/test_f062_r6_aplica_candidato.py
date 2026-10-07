# tests/test_f062_r6_aplica_candidato.py
"""F-062 · R6, R7, R9, R12, R13 — la red de proveedor APLICA el candidato
claro antes de buscar contratos.

Con el CIF leído inexistente en Sigrid y un candidato claro en la obra,
sv3 escribe en el merge el CIF y la razón social de Sigrid (origen
``deterministic``), manda a revisión con el motivo
``proveedor_cif_corregido:<leído>><aplicado>`` y deja una nota con prefijo
PROPIO ``[CORREGIDO] Proveedor``. Lo leído no se pierde. Con el
interruptor apagado o con un CIF fijado por el revisor, como antes.

Cliente real de sv3 sobre el doble de sigrid-api (fixture de F-062).
"""
from __future__ import annotations

import pytest
from application.services.header_resolver_service import _NOTA_PROVEEDOR_PREFIX
from domain.models.header_resolution_models import NOTA_PROVEEDOR_CORREGIDO_PREFIJO

from doble_sigrid_api import (
    CIF_ARIDOS_ANFERSA,
    CIF_HORMIGONES_MAT,
    CIF_LEIDO_19394,
    CIF_LEIDO_19407,
    CIF_LEIDO_1790636816,
    RAZ_ARIDOS_ANFERSA,
    RAZ_HORMIGONES_MAT,
    DobleSigridApi,
    fixture_f062,
)
from f062_dobles import RepoRed, pasada

CASOS = [
    pytest.param(CIF_LEIDO_19407, "Hormigones Mat SL", "0720", CIF_HORMIGONES_MAT,
                 RAZ_HORMIGONES_MAT, "CIF más cercano al leído", id="19407"),
    pytest.param(CIF_LEIDO_19394, "Hormigones Mat SL", "0720", CIF_HORMIGONES_MAT,
                 RAZ_HORMIGONES_MAT, "CIF más cercano al leído", id="19394"),
    pytest.param(CIF_LEIDO_1790636816, "ARIDOS ANFERSA SL", "0678", CIF_ARIDOS_ANFERSA,
                 RAZ_ARIDOS_ANFERSA, "único candidato", id="1790636816"),
]


def _doble() -> DobleSigridApi:
    return DobleSigridApi(fixture_f062())


# ------------------------------------------------------------------ #
# R6 · se aplica CIF, razón social y origen
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(("leido", "nombre", "obra", "real", "raz", "por_que"), CASOS)
def test_f062_r6_aplica_cif_y_razon_social_de_sigrid(leido, nombre, obra, real, raz, por_que):
    repo = RepoRed(cif=leido, nombre=nombre, obra=obra)

    pasada(_doble().cliente(), repo)

    [aplicada] = repo.aplicadas
    assert (aplicada["cif"], aplicada["nombre"]) == (real, raz)
    assert (repo.cif, repo.nombre, repo.origen) == (real, raz, "deterministic")
    assert repo.marcas == []  # sin proveedor_cif_no_casa (R7)
    # El resolver no reescribe nada más: el CIF aplicado ya está en el merge.
    assert repo.resoluciones == [(None, None, "deterministic")]


def test_f062_r6_aplica_el_cif_normalizado_del_candidato():
    from domain.models.header_resolution_models import ProveedorObraResumen

    class _Cliente:
        def fetch_proveedor_by_cif(self, *, cif):
            return None

        def fetch_contratos_resumen_por_obra(self, *, codigo_obra):
            return [ProveedorObraResumen(
                cif=" b-66056201", nombre="  HORMIGONES MAT, S.L.U. ",
                codigos_contratos=("C",), texto="",
            )]

    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720")
    pasada(_Cliente(), repo)
    [aplicada] = repo.aplicadas
    assert (aplicada["cif"], aplicada["nombre"]) == (CIF_HORMIGONES_MAT, "HORMIGONES MAT, S.L.U.")


def test_f062_r6_una_sola_consulta_de_la_obra_por_pasada():
    doble = _doble()
    pasada(doble.cliente(), RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720"))
    assert len(doble.peticiones_con("FOR XML PATH")) == 1
    assert len(doble.peticiones_con("SELECT TOP 1 prv.cif")) == 1


# ------------------------------------------------------------------ #
# R7 · revisión, motivo y nota con prefijo propio
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(("leido", "nombre", "obra", "real", "raz", "por_que"), CASOS)
def test_f062_r7_motivo_y_nota_de_la_correccion(leido, nombre, obra, real, raz, por_que):
    repo = RepoRed(cif=leido, nombre=nombre, obra=obra)

    pasada(_doble().cliente(), repo)

    [aplicada] = repo.aplicadas
    assert aplicada["motivo"] == f"proveedor_cif_corregido:{leido}>{real}"
    nota = aplicada["nota"]
    assert nota.startswith(f"{NOTA_PROVEEDOR_CORREGIDO_PREFIJO}: leído {leido} → {real} ({raz}).")
    for trozo in (
        f"Nombre leído: '{nombre}'",
        raz,  # razón social aplicada
        "carácter de control del CIF leído no es válido",  # los tres lo tienen inválido
        f"obra {obra}",
        por_que,
        "«Elegir proveedor»",
    ):
        assert trozo in nota, trozo
    assert not nota.startswith(_NOTA_PROVEEDOR_PREFIX)
    assert repo.review_required is True
    assert repo.lista_motivos() == [aplicada["motivo"]]


def test_f062_r7_con_control_valido_la_nota_no_habla_de_lectura_erronea():
    """Q4: un leído con el control válido que no existe se corrige igual;
    la nota no dice que el control esté mal."""
    leido_valido = "B66056219"
    repo = RepoRed(cif=leido_valido, nombre="Hormigones Mat SL", obra="0720")

    pasada(_doble().cliente(), repo)

    [aplicada] = repo.aplicadas
    assert aplicada["cif"] == CIF_HORMIGONES_MAT
    assert "carácter de control" not in aplicada["nota"]


def test_f062_r7_la_nota_no_escupe_none():
    from domain.models.header_resolution_models import ProveedorObraResumen

    class _Cliente:
        def fetch_proveedor_by_cif(self, *, cif):
            return None

        def fetch_contratos_resumen_por_obra(self, *, codigo_obra):
            return [ProveedorObraResumen(
                cif=CIF_HORMIGONES_MAT, nombre=RAZ_HORMIGONES_MAT, codigos_contratos=("C",), texto="",
            )]

    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="HORMIGONES MAT", obra="0720")
    pasada(_Cliente(), repo)
    assert "None" not in repo.aplicadas[0]["nota"]


# ------------------------------------------------------------------ #
# R9 · lo leído no se pierde
# ------------------------------------------------------------------ #
def test_f062_r9_lo_leido_queda_en_motivo_y_nota():
    repo = RepoRed(cif=CIF_LEIDO_19394, nombre="Hormigones Mat SL", obra="0720")
    pasada(_doble().cliente(), repo)
    [aplicada] = repo.aplicadas
    assert CIF_LEIDO_19394 in aplicada["motivo"]
    assert CIF_LEIDO_19394 in aplicada["nota"]
    assert "Hormigones Mat SL" in aplicada["nota"]


def test_f062_r9_el_repositorio_solo_toca_el_merge():
    """``aplicar_correccion_proveedor`` pide la fila del MERGE y nada más:
    la fila cruda de ``albaran_documents`` no se toca."""
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm
    from test_f062_r14_repasadas_y_motivos import _documento, _repo

    repo, sesion = _repo(_documento())
    pedidas: list[type] = []
    original = sesion.get

    def _get(orm, document_id):
        pedidas.append(orm)
        return original(orm, document_id)

    sesion.get = _get
    repo.aplicar_correccion_proveedor(
        document_id="doc-f062", cif=CIF_HORMIGONES_MAT, nombre=RAZ_HORMIGONES_MAT,
        motivo="m", nota="[CORREGIDO] Proveedor: x",
    )
    assert pedidas == [AlbaranDocumentMergeOrm]


# ------------------------------------------------------------------ #
# R12 · interruptores
# ------------------------------------------------------------------ #
def test_f062_r12_con_la_correccion_apagada_solo_propone_como_antes():
    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720")

    pasada(_doble().cliente(), repo, correccion_enabled=False)

    assert repo.aplicadas == []
    assert repo.retiradas == []
    [(motivo, nota, prefijo)] = repo.marcas
    assert motivo == f"proveedor_cif_no_casa:{CIF_LEIDO_19407}"
    assert prefijo == _NOTA_PROVEEDOR_PREFIX
    assert "PROPUESTA:" in nota
    # Exactamente como antes: ni la frase del control (R11) es nueva aquí.
    assert "carácter de control" not in nota
    assert (repo.cif, repo.nombre) == (CIF_LEIDO_19407, "Hormigones Mat SL")


def test_f062_r12_con_la_red_de_cif_apagada_no_consulta_ni_corrige():
    doble = _doble()
    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720")

    pasada(doble.cliente(), repo, cif_enabled=False)

    assert doble.peticiones == []
    assert (repo.aplicadas, repo.marcas, repo.retiradas) == ([], [], [])


def test_f062_r12_con_cif_existente_y_correccion_apagada_no_retira_motivos():
    repo = RepoRed(cif=CIF_HORMIGONES_MAT, nombre="Hormigones Mat SL", obra="0720")
    pasada(_doble().cliente(), repo, correccion_enabled=False)
    assert repo.retiradas == []
    assert repo.canonizados == [RAZ_HORMIGONES_MAT]


# ------------------------------------------------------------------ #
# R13 · no se pisa al revisor
# ------------------------------------------------------------------ #
def test_f062_r13_origen_manual_no_se_aplica_y_se_marca_como_hoy():
    repo = RepoRed(cif=CIF_LEIDO_1790636816, nombre="ARIDOS ANFERSA SL", obra="0678", origen="manual")

    pasada(_doble().cliente(), repo)

    assert repo.aplicadas == []
    [(motivo, nota, _)] = repo.marcas
    assert motivo == f"proveedor_cif_no_casa:{CIF_LEIDO_1790636816}"
    assert f"PROPUESTA: {CIF_ARIDOS_ANFERSA}" in nota
    assert (repo.cif, repo.origen) == (CIF_LEIDO_1790636816, "manual")


def test_f062_r13_un_cif_que_existe_en_prv_nunca_se_sustituye():
    """El CIF que elige el revisor en sv4 siempre existe: la red lo
    canoniza y no busca candidatos."""
    doble = _doble()
    repo = RepoRed(cif=CIF_HORMIGONES_MAT.lower(), nombre="otro nombre", obra="0720")

    pasada(doble.cliente(), repo)

    assert repo.aplicadas == []
    assert repo.marcas == []
    assert repo.canonizados == [RAZ_HORMIGONES_MAT]
    assert doble.peticiones_con("FOR XML PATH") == []


# ------------------------------------------------------------------ #
# Best-effort: si aplicar falla, queda como hoy (motivo y nota de aviso)
# ------------------------------------------------------------------ #
def test_f062_r6_si_aplicar_falla_se_marca_como_hoy_y_no_rompe():
    repo = RepoRed(cif=CIF_LEIDO_1790636816, nombre="ARIDOS ANFERSA SL", obra="0678", falla_aplicar=True)

    pasada(_doble().cliente(), repo)

    [(motivo, nota, _)] = repo.marcas
    assert motivo == f"proveedor_cif_no_casa:{CIF_LEIDO_1790636816}"
    assert f"PROPUESTA: {CIF_ARIDOS_ANFERSA}" in nota
    assert repo.resoluciones == [(None, None, "deterministic")]


# ------------------------------------------------------------------ #
# R12 · settings y cableado en los DOS puntos de composición
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("campo", "alias", "defecto"),
    [
        ("red_proveedor_correccion_enabled", "RED_PROVEEDOR_CORRECCION_ENABLED", True),
        ("red_proveedor_correccion_score_min", "RED_PROVEEDOR_CORRECCION_SCORE_MIN", 1.0),
        ("red_proveedor_correccion_margen_distancia", "RED_PROVEEDOR_CORRECCION_MARGEN_DISTANCIA", 2),
    ],
)
def test_f062_r12_settings_con_su_alias_y_su_defecto(campo, alias, defecto):
    from config.settings import Settings

    campo_settings = Settings.model_fields[campo]
    assert campo_settings.alias == alias
    assert campo_settings.default == defecto


def test_f062_r12_el_interruptor_se_lee_del_entorno(monkeypatch):
    from config.settings import Settings

    for obligatoria in ("GRAPH_KEY", "PG_PASSWORD", "PG_ADMIN_PASSWORD", "SHAREPOINT_DRIVE_ID"):
        monkeypatch.setenv(obligatoria, "no-es-un-secreto")
    monkeypatch.setenv("RED_PROVEEDOR_CORRECCION_ENABLED", "false")
    monkeypatch.setenv("RED_PROVEEDOR_CORRECCION_SCORE_MIN", "0.8")
    monkeypatch.setenv("RED_PROVEEDOR_CORRECCION_MARGEN_DISTANCIA", "3")
    ajustes = Settings(_env_file=None)
    assert ajustes.red_proveedor_correccion_enabled is False
    assert ajustes.red_proveedor_correccion_score_min == 0.8
    assert ajustes.red_proveedor_correccion_margen_distancia == 3


@pytest.mark.parametrize("modulo", ["interface_adapters/composition.py", "interface_adapters/api/app.py"])
def test_f062_r12_los_dos_puntos_de_composicion_cablean_la_correccion(modulo):
    from pathlib import Path

    fuente = " ".join((Path(__file__).resolve().parents[1] / modulo).read_text(encoding="utf-8").split())
    for cable in (
        "correccion_enabled=settings.red_proveedor_correccion_enabled",
        "correccion_score_min=settings.red_proveedor_correccion_score_min",
        "correccion_margen_distancia=( settings.red_proveedor_correccion_margen_distancia )",
    ):
        assert cable in fuente, cable


def test_f062_r12_el_resolver_usa_los_umbrales_que_recibe():
    """Lo cableado llega a la regla: con margen 10, el empate de la 0720
    deja de ser claro y vuelve la propuesta."""
    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720")
    pasada(_doble().cliente(), repo, correccion_margen_distancia=10)
    assert repo.aplicadas == []
    assert repo.marcas[0][0] == f"proveedor_cif_no_casa:{CIF_LEIDO_19407}"
