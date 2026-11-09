# tests/test_f112_rutas_sensibles.py
"""F-112 · R25: el bloque de la fecha de recepción es ruta sensible.

``fecha_recepcion.py`` pinta el texto que sustituye a ``{fecha_recepcion}``
(IA1, y dentro de ``{prompt_fase_1}``, IA2) y a ``{revision_fecha}`` (IA2), con
la Regla del año. Cambiarlo cambia lo que lee la IA, y ningún test unitario
dice si lee mejor o peor el año: tocarlo debe pedir la pasada de evals.
"""

from __future__ import annotations

from pathlib import Path

from harness import rutas_sensibles as rs

RAIZ_REPO = Path(__file__).resolve().parent.parent
FICHERO = "services/albaranes-api/application/services/fecha_recepcion.py"


def _evals() -> rs.Verificacion:
    verificaciones = rs.cargar_declaracion(raiz=str(RAIZ_REPO))
    return next(v for v in verificaciones if v.nombre == "evals")


def test_f112_r25_la_puerta_de_evals_cubre_el_fichero():
    assert (RAIZ_REPO / FICHERO).is_file()
    assert any(rs._casa(FICHERO, ruta.patron) for ruta in _evals().rutas)


def test_f112_r25_el_motivo_dice_que_entra_en_el_prompt():
    motivos = [ruta.motivo for ruta in _evals().rutas if rs._casa(FICHERO, ruta.patron)]
    assert any("F-112" in motivo and "prompt" in motivo for motivo in motivos), motivos


def test_f112_r25_los_vecinos_que_no_llegan_al_prompt_no_entran():
    """Solo ese fichero: el resolver de clasificación no pinta texto para la IA."""
    vecino = "services/albaranes-api/application/services/clasificacion_resolver.py"
    assert not any(rs._casa(vecino, ruta.patron) for ruta in _evals().rutas)
