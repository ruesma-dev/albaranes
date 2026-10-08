# tests/test_f063_cif_propio.py
"""F-063 — el CIF de Construcciones Ruesma nunca es el proveedor.

Incidencia del 2026-10-08 (logs de Azure): en un albarán de FEYMACO de la
obra 0694 la IA leyó bien el nombre («FERRETERÍA Y MAQUINARIA PARA LA
CONSTRUCCIÓN, S. A.») y como CIF el del CLIENTE impreso en el papel,
A81873903 (Construcciones Ruesma). sv3 lo dio por bueno porque existe en
Sigrid, canonizó el nombre a Ruesma y buscó contratos con ese CIF ⇒ 0.
Sin CIF, el mismo albarán se resolvió bien por nombre dentro de la obra.

Capas: repositorio (sesión doble de F-062), resolver (``RepoRed``) y
pipeline en sus tres rutas con el doble de sigrid-api. Sin red ni BBDD.
"""
from __future__ import annotations

import json

import pytest
from test_f062_r14_repasadas_y_motivos import _documento, _json, _repo

from domain.models.header_resolution_models import (
    MOTIVO_PROVEEDOR_CIF_PROPIO,
    NOTA_CIF_PROPIO_PREFIJO,
)

RUESMA = "A81873903"
FEYMACO = "A28733558"
NOMBRE_LEIDO = "FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A."
MOTIVO = f"{MOTIVO_PROVEEDOR_CIF_PROPIO}{RUESMA}"
NOTA = (
    f"{NOTA_CIF_PROPIO_PREFIJO}: la IA leyó el CIF del cliente ({RUESMA}, "
    "Construcciones Ruesma) como CIF del proveedor; se descarta y el "
    "proveedor se busca por nombre."
)


# ------------------------------------------------------------------ #
# Dominio · prefijos propios (R10)
# ------------------------------------------------------------------ #
def test_f063_r10_prefijos_propios_que_la_red_no_borra():
    assert MOTIVO_PROVEEDOR_CIF_PROPIO == "proveedor_cif_propio:"
    assert NOTA_CIF_PROPIO_PREFIJO == "[AVISO] CIF del cliente"
    assert not NOTA_CIF_PROPIO_PREFIJO.startswith("[AVISO] Proveedor")


# ------------------------------------------------------------------ #
# Repositorio · descartar_cif_propio (R4, R13)
# ------------------------------------------------------------------ #
def _descartar(repo, *, nota=NOTA):
    repo.descartar_cif_propio(document_id="doc-f062", motivo=MOTIVO, nota=nota)


def test_f063_r4_repo_descarta_cif_y_origen_y_marca_revision_sin_tocar_el_nombre():
    doc = _documento(
        proveedor_cif=RUESMA, proveedor_nombre=NOMBRE_LEIDO, proveedor_cif_origen="ia",
        review_reasons_json=_json("obra_no_existe:0937"),
        review_notes="[AVISO] Obra algo\n[AVISO] Proveedor sin CIF ...",
    )
    repo, sesion = _repo(doc)

    _descartar(repo)

    assert (doc.proveedor_cif, doc.proveedor_cif_origen) == (None, None)
    assert doc.proveedor_nombre == NOMBRE_LEIDO
    assert doc.review_required is True
    assert json.loads(doc.review_reasons_json) == ["obra_no_existe:0937", MOTIVO]
    assert doc.review_notes.splitlines() == [
        "[AVISO] Obra algo", "[AVISO] Proveedor sin CIF ...", NOTA,
    ]
    assert sesion.confirmaciones == 1  # una sola transacción


def test_f063_r10_repo_descartar_dos_veces_no_duplica_y_la_nota_se_sustituye():
    doc = _documento(proveedor_cif=RUESMA, proveedor_nombre=NOMBRE_LEIDO)
    repo, _ = _repo(doc)

    _descartar(repo, nota=f"{NOTA_CIF_PROPIO_PREFIJO}: version anterior")
    _descartar(repo)

    assert json.loads(doc.review_reasons_json) == [MOTIVO]
    assert doc.review_notes == NOTA


def test_f063_r4_repo_descartar_sobre_un_merge_que_no_existe_lanza():
    repo, sesion = _repo(None)
    with pytest.raises(KeyError):
        _descartar(repo)
    assert sesion.confirmaciones == 0


# ------------------------------------------------------------------ #
# Resolver · descarte al principio de la resolución del proveedor
# (R3–R8, R10)
# ------------------------------------------------------------------ #
from f062_dobles import DOC, RepoRed, pasada  # noqa: E402

from domain.models.header_resolution_models import (  # noqa: E402
    ProveedorObraResumen,
)
from ruesma_comun.proveedores import cifs_propios  # noqa: E402

OBRA = "0694"
RAZ_FEYMACO = "FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A."
RAZ_RUESMA = "CONSTRUCCIONES RUESMA, S.A."
OTRO = "B11111119"
RAZ_OTRO = "HORMIGONES DEL CENTRO, S.L."


def _resumen(cif, nombre, texto="SUMINISTRO VARIOS") -> ProveedorObraResumen:
    return ProveedorObraResumen(cif=cif, nombre=nombre, codigos_contratos=("CT1",), texto=texto)


class ClienteFalso:
    """Cliente de Sigrid que registra con qué se le pregunta."""

    def __init__(self, *, obra=None, globales=()) -> None:
        self.obra = list(obra if obra is not None else [
            _resumen(FEYMACO, RAZ_FEYMACO), _resumen(OTRO, RAZ_OTRO),
        ])
        self.globales = list(globales)
        self.prv = {RUESMA: RAZ_RUESMA, FEYMACO: RAZ_FEYMACO, OTRO: RAZ_OTRO}
        self.por_cif: list[str] = []
        self.por_obra: list[str] = []

    def fetch_proveedor_by_cif(self, *, cif):
        self.por_cif.append(cif)
        return (cif, self.prv[cif]) if cif in self.prv else None

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra):
        self.por_obra.append(codigo_obra)
        return list(self.obra)

    def search_proveedores(self):
        return list(self.globales)


class RepoF063(RepoRed):
    """``RepoRed`` de F-062 con la escritura del descarte (F-063 · R4)."""

    def __init__(self, *, falla_descartar: bool = False, **kwargs) -> None:
        kwargs.setdefault("nombre", NOMBRE_LEIDO)
        kwargs.setdefault("obra", OBRA)
        super().__init__(**kwargs)
        self.falla_descartar = falla_descartar
        self.descartes: list[tuple[str, str]] = []

    def descartar_cif_propio(self, *, document_id: str, motivo: str, nota: str) -> None:
        assert document_id == DOC
        if self.falla_descartar:
            raise RuntimeError("BBDD caida")
        self.descartes.append((motivo, nota))
        self.cif, self.origen = None, None
        self.review_required = True
        self.motivos = json.dumps(
            [*self.lista_motivos(), motivo] if motivo not in self.lista_motivos()
            else self.lista_motivos()
        )
        lineas = [ln for ln in self.lineas_notas() if not ln.startswith(NOTA_CIF_PROPIO_PREFIJO)]
        self.notas = "\n".join([*lineas, nota])


@pytest.mark.parametrize("leido", [RUESMA, " a-81873903", "ESA81873903"])
def test_f063_r4_r5_resolver_descarta_el_cif_del_cliente_y_resuelve_feymaco_por_nombre(leido):
    cliente = ClienteFalso()
    repo = RepoF063(cif=leido)

    pasada(cliente, repo)

    assert repo.descartes == [(MOTIVO, NOTA)]
    # R4: nunca se consulta prv con el CIF del cliente ni se canoniza a Ruesma.
    assert cliente.por_cif == []
    assert repo.canonizados == []
    # R5: camino «sin CIF», resolución por NOMBRE dentro de la obra.
    assert (repo.cif, repo.origen) == (FEYMACO, "deterministic")
    assert repo.nombre == NOMBRE_LEIDO
    assert repo.review_required is True
    assert repo.lista_motivos() == [MOTIVO]
    assert NOTA in repo.lineas_notas()


def test_f063_r12_resolver_sin_candidato_deja_el_merge_sin_cif_con_nota_y_motivo():
    cliente = ClienteFalso(obra=[_resumen(OTRO, RAZ_OTRO)])
    repo = RepoF063(cif=RUESMA)

    pasada(cliente, repo)

    assert repo.cif is None
    assert repo.lista_motivos() == [MOTIVO]
    assert NOTA in repo.lineas_notas()
    assert cliente.por_cif == []


@pytest.mark.parametrize("origen", ["manual", " manual "])
def test_f063_r6_resolver_respeta_el_cif_propio_elegido_por_el_revisor(origen):
    cliente = ClienteFalso()
    repo = RepoF063(cif=RUESMA, origen=origen)

    pasada(cliente, repo)

    assert repo.descartes == []
    assert cliente.por_cif == [RUESMA]  # la red sigue como antes
    assert repo.cif == RUESMA


def test_f063_r7_resolver_con_la_escritura_fallida_sigue_sin_cif_y_no_canoniza_al_cliente():
    cliente = ClienteFalso()
    repo = RepoF063(cif=RUESMA, falla_descartar=True)

    pasada(cliente, repo)

    assert cliente.por_cif == []
    assert repo.canonizados == []
    assert (repo.cif, repo.origen) == (FEYMACO, "deterministic")


def test_f063_r8_control_negativo_un_cif_normal_sigue_como_antes():
    cliente = ClienteFalso()
    repo = RepoF063(cif=FEYMACO)

    pasada(cliente, repo)

    assert repo.descartes == []
    assert cliente.por_cif == [FEYMACO]
    assert repo.canonizados == [RAZ_FEYMACO]
    assert repo.lista_motivos() == []


def test_f063_r8_sin_cif_no_hay_descarte():
    repo = RepoF063(cif=None)
    pasada(ClienteFalso(), repo)
    assert repo.descartes == []
    assert repo.cif == FEYMACO


def test_f063_r10_resolver_re_pasada_no_duplica_ni_vuelve_a_descartar():
    cliente = ClienteFalso()
    repo = RepoF063(cif=RUESMA)

    pasada(cliente, repo)
    pasada(cliente, repo)

    assert len(repo.descartes) == 1
    assert repo.lista_motivos() == [MOTIVO]
    assert repo.lineas_notas().count(NOTA) == 1
    assert repo.cif == FEYMACO


def test_f063_r3_resolver_usa_la_lista_que_recibe():
    """Un CIF añadido por configuración se descarta, con «CIF propio» en
    la nota; sin configurarlo, es un CIF normal."""
    extra = "B12345674"
    repo = RepoF063(cif=extra)
    pasada(ClienteFalso(), repo, cifs_propios=cifs_propios(extra))
    [(motivo, nota)] = repo.descartes
    assert motivo == f"{MOTIVO_PROVEEDOR_CIF_PROPIO}{extra}"
    assert f"({extra}, CIF propio)" in nota

    otro = RepoF063(cif=extra)
    pasada(ClienteFalso(), otro)
    assert otro.descartes == []


def test_f063_r3_setting_con_su_alias_y_defecto_vacio(monkeypatch):
    from config.settings import Settings

    campo = Settings.model_fields["cifs_propios"]
    assert (campo.alias, campo.default) == ("CIFS_PROPIOS", "")
    for obligatoria in ("GRAPH_KEY", "PG_PASSWORD", "PG_ADMIN_PASSWORD", "SHAREPOINT_DRIVE_ID"):
        monkeypatch.setenv(obligatoria, "no-es-un-secreto")
    monkeypatch.setenv("CIFS_PROPIOS", "B12345674")
    assert Settings(_env_file=None).cifs_propios == "B12345674"


@pytest.mark.parametrize("modulo", ["interface_adapters/composition.py", "interface_adapters/api/app.py"])
def test_f063_r3_los_dos_puntos_de_composicion_cablean_los_cif_propios(modulo):
    from pathlib import Path

    fuente = " ".join((Path(__file__).resolve().parents[1] / modulo).read_text(encoding="utf-8").split())
    assert "cifs_propios=cifs_propios(settings.cifs_propios)" in fuente


# ------------------------------------------------------------------ #
# R9 · un CIF propio nunca es candidato (paso 1, paso 2 y red por CIF)
# ------------------------------------------------------------------ #
NOMBRE_RUESMA_LEIDO = "CONSTRUCCIONES RUESMA, S.A."


def test_f063_r9_candidato_paso1_la_obra_nunca_devuelve_el_cif_propio():
    """Un merge ya canonizado al cliente (el nombre es el de Ruesma): el
    atajo por nombre de la obra lo devolvería si Ruesma estuviera en la
    lista."""
    cliente = ClienteFalso(obra=[_resumen(RUESMA, RAZ_RUESMA), _resumen(OTRO, RAZ_OTRO)])
    repo = RepoF063(cif=None, nombre=NOMBRE_RUESMA_LEIDO)

    pasada(cliente, repo)

    assert repo.cif is None
    assert RUESMA not in (repo.notas or "")  # ni en la lista de candidatos de la nota
    assert OTRO in (repo.notas or "")


def test_f063_r9_candidato_paso1_obra_con_solo_el_cif_propio_es_obra_sin_candidatos():
    cliente = ClienteFalso(obra=[_resumen(RUESMA, RAZ_RUESMA)])
    repo = RepoF063(cif=None, nombre=NOMBRE_RUESMA_LEIDO)

    pasada(cliente, repo)

    assert repo.cif is None
    assert repo.notas is None


def test_f063_r9_candidato_paso2_la_busqueda_global_nunca_devuelve_el_cif_propio():
    cliente = ClienteFalso(globales=[(RUESMA, RAZ_RUESMA), (OTRO, RAZ_OTRO)])
    repo = RepoF063(cif=None, nombre=NOMBRE_RUESMA_LEIDO, obra=None)

    pasada(cliente, repo)

    assert repo.cif is None


def test_f063_r9_candidato_paso2_control_otro_proveedor_global_si_se_resuelve():
    cliente = ClienteFalso(globales=[(RUESMA, RAZ_RUESMA), (OTRO, RAZ_OTRO)])
    repo = RepoF063(cif=None, nombre="HORMIGONES DEL CENTRO", obra=None)

    pasada(cliente, repo)

    assert repo.cif == OTRO


def test_f063_r9_candidato_red_por_cif_ni_aplica_ni_propone_el_cif_propio():
    """CIF leído que no existe en prv y Ruesma, con CIF válido y nombre
    que casa, en la lista de la obra: F-062 lo aplicaría como candidato
    claro."""
    cliente = ClienteFalso(obra=[_resumen(RUESMA, RAZ_RUESMA), _resumen(OTRO, RAZ_OTRO)])
    repo = RepoF063(cif="B86056201", nombre=NOMBRE_RUESMA_LEIDO)

    pasada(cliente, repo)

    assert repo.aplicadas == []
    [(motivo, nota, _)] = repo.marcas
    assert motivo == "proveedor_cif_no_casa:B86056201"
    assert "PROPUESTA" not in nota
    assert repo.cif == "B86056201"
