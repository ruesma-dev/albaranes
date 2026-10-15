# tests/test_f053_r47_candidato.py
"""F-053 v8 · T41 · R47: de ``approved_by`` al login candidato de Sigrid.

``candidato_usuario`` es puro: la parte antes de la @ si ``approved_by`` es un
correo ``@ruesma.es`` (sin distinguir mayúsculas, con espacios alrededor
recortados) y esa parte no está vacía ni pasa de 24 caracteres; si no, ``None``
(y sv9 usará el Respaldo). Sin red ni BBDD.
"""
from __future__ import annotations

import pytest

from domain.services.usuario_sigrid import MAX_LOGIN, candidato_usuario


@pytest.mark.parametrize("approved_by, esperado", [
    ("pgris@ruesma.es", "pgris"),
    ("  PGris@Ruesma.ES  ", "PGris"),
    ("\tana@RUESMA.es\n", "ana"),
    ("a" * 24 + "@ruesma.es", "a" * 24),
    ("a@ruesma.es", "a"),
])
def test_f053_r47_candidato_correo_de_ruesma_da_la_parte_local(approved_by, esperado):
    assert candidato_usuario(approved_by) == esperado


@pytest.mark.parametrize("approved_by", [
    None,
    "",
    "   ",
    "reviewer",                                    # DEFAULT_REVIEWER de local
    "Revisor de compras",                          # texto libre
    "pgris@gmail.com",                             # otro dominio
    "pgris@ruesma.es.evil.com",                    # dominio que solo lo contiene
    "pgris@sub.ruesma.es",                         # subdominio
    "x_gmail.com#EXT#@ruesmaxx.onmicrosoft.com",   # UPN de invitado
    "@ruesma.es",                                  # sin parte local
    "a" * 25 + "@ruesma.es",                       # parte local de 25
    "a@b@ruesma.es",                               # dos arrobas
    "pgris ruesma.es",                             # sin arroba
])
def test_f053_r47_candidato_lo_demas_es_none(approved_by):
    assert candidato_usuario(approved_by) is None


def test_f053_r47_candidato_tope_de_24():
    assert MAX_LOGIN == 24
