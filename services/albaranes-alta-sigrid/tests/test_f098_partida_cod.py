# tests/test_f098_partida_cod.py
"""F-098 T7 · sv9 manda el cod guardado, nunca el código completo (R30).

Con F-098 la ficha enseña ``CD.99.01.64`` pero guarda el cod de Sigrid
(``99.01.64``) en ``codigo_partida_final``; sv9 no cambia y lo manda tal cual
como ``partida``, sin ``paride`` (P2 = a: el ``ide`` queda para otra feature).
Mandar el completo es lo que hizo fallar el albarán ``8c4e026a`` («La obra no
tiene ninguna partida 'CD.99.01.64'»). Test de no regresión: sin código nuevo.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from domain.models.alta_models import PeticionAlbaran
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, HOY, USU, datos, sin_vincular, vinculada


def _lineas(*lineas):
    resultado = validar_y_construir(datos(*lineas), CONFIG, HOY, USU)
    assert isinstance(resultado, PeticionAlbaran), resultado
    return [linea.a_dict() for linea in resultado.lineas]


@pytest.mark.parametrize("fabrica", [vinculada, sin_vincular], ids=["vinculada", "sin_vincular"])
@pytest.mark.parametrize("cod", ["99.01.64", "CD2.01", "CI.01.01", "98.01"])
def test_f098_r30_el_cod_sale_tal_cual_sin_paride(fabrica, cod):
    (linea,) = _lineas(fabrica(1, codigo_partida_final=cod))
    assert linea["partida"] == cod
    assert "paride" not in linea


def test_f098_r30_sv9_no_traduce_al_codigo_completo():
    """sv9 no pinta ni compone: ni ``mostrar_partida`` ni ``codigo_completo``."""
    raiz = Path(__file__).resolve().parents[1]
    fuentes = [p for p in raiz.rglob("*.py") if ".venv" not in p.parts and "tests" not in p.parts]
    assert fuentes
    for nombre in ("mostrar_partida", "codigo_completo", "misma_partida"):
        assert not [p for p in fuentes if nombre in p.read_text(encoding="utf-8")], nombre
