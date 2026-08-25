# tests/test_f036_r14_ler.py
"""F-036 R14 · el catalogo LER vive en UN solo sitio.

Hasta F-036 el validador y el catalogo (Decision 2014/955/UE) vivian
solo en `services/albaranes-api/domain/models/tipologia.py`. sv5 lo
necesita para su regla dura de tipologia (R13) y no puede importar el
dominio de sv2: o se copiaba —dos catalogos que divergen— o se movia a
`ruesma_comun`. Se movio.

Estos tests son el contrato compartido. Funciones puras: sin red, sin
BBDD, sin LLM.
"""
from __future__ import annotations

import pytest
from ruesma_comun.ler import (
    es_ler_valido,
    normalizar_ler,
    texto_contiene_ler,
)


# ------------------------------------------------------------------ #
# R14 · el catalogo esta en comun y sv2 NO tiene copia
#
# El test de que la reexportacion de sv2 es EL MISMO objeto vive en
# `services/albaranes-api/tests/test_f036_r14_ler_reexportado.py`: solo
# ahi es importable el paquete `domain` de sv2.
# ------------------------------------------------------------------ #
def test_f036_r14_el_catalogo_no_esta_duplicado_en_sv2():
    """El diccionario de capitulos vive solo en `ruesma_comun.ler`."""
    from pathlib import Path

    import ruesma_comun.ler as modulo_comun

    # ler.py → ruesma_comun → albaranes-comun → services
    fuente_sv2 = (
        Path(modulo_comun.__file__).parents[2]
        / "albaranes-api"
        / "domain"
        / "models"
        / "tipologia.py"
    ).read_text(encoding="utf-8")

    assert "_CAPITULOS_LER: dict" not in fuente_sv2
    assert "_CAPITULOS_LER" in Path(modulo_comun.__file__).read_text(
        encoding="utf-8"
    )


# ------------------------------------------------------------------ #
# El comportamiento, tal cual estaba en sv2 (no puede cambiar al mover)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "codigo",
    ["170504", "17 05 04", "17.05.04", "170904", "200301", "010101"],
)
def test_f036_r14_codigos_del_catalogo_son_validos(codigo):
    assert es_ler_valido(codigo) is True


@pytest.mark.parametrize(
    "codigo",
    [
        None,
        "",
        "19213",      # cinco digitos
        "1921370",    # siete digitos
        "192137",     # el codigo de producto de Prebetong: 19 21 no existe
        "990101",     # capitulo 99 inexistente
        "175004",     # capitulo 17 llega al subcapitulo 09
    ],
)
def test_f036_r14_lo_que_no_es_ler_no_pasa(codigo):
    assert es_ler_valido(codigo) is False


def test_f036_r14_normalizar_devuelve_seis_digitos():
    assert normalizar_ler("Residuo LER 17 05 04 mezclado") == "170504"
    assert normalizar_ler("referencia 192137") is None


def test_f036_r14_texto_con_espacios_basta_por_si_solo():
    assert texto_contiene_ler("RCD 17 05 04") is True


def test_f036_r14_texto_pegado_exige_contexto_de_residuos():
    assert texto_contiene_ler("codigo 170504") is False
    assert texto_contiene_ler("LER 170504") is True


def test_f036_r14_una_fecha_no_es_un_ler():
    """`17-05-04` tiene forma de fecha: sin contexto no cuenta."""
    assert texto_contiene_ler("albaran de 17-05-04") is False
    assert texto_contiene_ler("residuo 17-05-04") is True
