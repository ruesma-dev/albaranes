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
