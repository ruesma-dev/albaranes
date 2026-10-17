# tests/test_f076_partida_final.py
"""F-076 T12 · contrato con sv9: la partida que normaliza sv6 sale tal cual (R16).

sv9 NO cambia: manda como ``partida`` exactamente ``codigo_partida_final`` de la
fila valorada. Con F-076 esa final ya es el código de la lista de la obra
(``CI.4.18``), mientras la leída (``CI.04.18``) queda en
``codigo_partida_albaran`` y en el motivo ``partida_normalizada:…``, que sv9 no
mira. Vacía ⇒ sin clave ``partida`` (almacén, regla 16).
"""
from __future__ import annotations

import pytest
from domain.models.alta_models import PeticionAlbaran
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, HOY, USU, datos, sin_vincular, vinculada


def _lineas(*lineas):
    resultado = validar_y_construir(datos(*lineas), CONFIG, HOY, USU)
    assert isinstance(resultado, PeticionAlbaran), resultado
    return [linea.a_dict() for linea in resultado.lineas]


@pytest.mark.parametrize("fabrica", [vinculada, sin_vincular], ids=["vinculada", "sin_vincular"])
def test_f076_r16_la_final_normalizada_sale_tal_cual(fabrica):
    (linea,) = _lineas(fabrica(1, codigo_partida_final="CI.4.18"))
    assert linea["partida"] == "CI.4.18"


def test_f076_r16_sv9_no_renormaliza_ni_mira_la_leida():
    """Lo que manda es la final; sv9 no aplica la clave de comun (sería otra copia)."""
    (linea,) = _lineas(sin_vincular(1, codigo_partida_final="CI.04.18"))
    assert linea["partida"] == "CI.04.18"


@pytest.mark.parametrize("vacia", [None, "", "   "])
@pytest.mark.parametrize("fabrica", [vinculada, sin_vincular], ids=["vinculada", "sin_vincular"])
def test_f076_r16_final_vacia_sin_clave_de_partida(fabrica, vacia):
    (linea,) = _lineas(fabrica(1, codigo_partida_final=vacia))
    assert "partida" not in linea


def test_f076_r16_sv9_no_importa_la_normalizacion_de_comun():
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    fuentes = [p for p in raiz.rglob("*.py") if ".venv" not in p.parts and "tests" not in p.parts]
    assert fuentes
    assert not [p for p in fuentes if "normalizar_partida" in p.read_text(encoding="utf-8")]
