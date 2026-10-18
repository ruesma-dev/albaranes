# tests/test_f064_r18_rutas_sensibles.py
"""F-064 · R18: la lista de empresas del cliente es ruta sensible.

Desde F-064 su contenido entra en el prompt de IA1 (y, dentro de él, en el de
IA2): cambiar una razón social de `CIFS_PROPIOS_POR_DEFECTO` o el bloque que
la pinta cambia lo que lee la IA, y ningún test unitario dice si extrae mejor
o peor. Tocar cualquiera de los dos debe pedir la pasada de evals.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness import rutas_sensibles as rs

RAIZ_REPO = Path(__file__).resolve().parent.parent

NUEVAS = (
    "services/albaranes-comun/ruesma_comun/proveedores/propios.py",
    "services/albaranes-api/application/services/empresas_cliente.py",
)


def _evals() -> rs.Verificacion:
    verificaciones = rs.cargar_declaracion(raiz=str(RAIZ_REPO))
    return next(v for v in verificaciones if v.nombre == "evals")


@pytest.mark.parametrize("fichero", NUEVAS)
def test_f064_r18_la_puerta_de_evals_cubre_el_fichero(fichero):
    assert (RAIZ_REPO / fichero).is_file()
    assert any(rs._casa(fichero, ruta.patron) for ruta in _evals().rutas), fichero


@pytest.mark.parametrize("fichero", NUEVAS)
def test_f064_r18_el_motivo_dice_que_entra_en_el_prompt(fichero):
    motivos = [ruta.motivo for ruta in _evals().rutas if rs._casa(fichero, ruta.patron)]
    assert any("F-064" in motivo and "prompt" in motivo for motivo in motivos), motivos


def test_f064_r18_las_identificador_y_demas_de_comun_no_entran():
    """Solo `propios.py`: `identificador.py` no llega al prompt."""
    fichero = "services/albaranes-comun/ruesma_comun/proveedores/identificador.py"
    assert not any(rs._casa(fichero, ruta.patron) for ruta in _evals().rutas)
