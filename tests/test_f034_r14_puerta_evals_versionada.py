# tests/test_f034_r14_puerta_evals_versionada.py
"""F-034 · R14: la subida de la puerta de evals se condiciona a lo VERSIONADO.

Los libros `.xlsx` de `evals/ground_truth/` existen, pero `.gitignore` los
excluye: quien clona el repositorio no los ve. Condicionar una puerta a ellos
es condicionarla a algo que nadie puede comprobar. Lo que consume
`evals.runner` son los fixtures versionados de `evals/fixtures/`.

Hasta la 1.10.0 del arnés este test vivía dentro de
`tests/test_mutacion_operadores.py`, que es fichero del arnés (`arnes_puro`): al
actualizar, `arnes-base` lo trae con una versión genérica de la regla (una sola
frase de subida a `bloqueo`) que ya no nombra `evals/fixtures/` ni
`ground_truth`. La parte propia de este repositorio se mudó aquí, a un fichero
del proyecto, para que el instalador no vuelva a borrarla.
"""

from __future__ import annotations

import json

import pytest

from harness.rutas_sensibles import RUTA_DECLARACION


def test_f034_r14_la_puerta_de_evals_no_se_declara_sobre_lo_no_versionado() -> None:
    if not RUTA_DECLARACION.exists():
        pytest.skip(f"este repositorio no declara {RUTA_DECLARACION.as_posix()}")

    exigencia = json.loads(RUTA_DECLARACION.read_text(encoding="utf-8")).get(
        "_exigencia", ""
    )
    condiciones = [frase for frase in exigencia.split(". ") if "'bloqueo'" in frase]

    assert len(condiciones) == 1, (
        f"esperada UNA frase que declare cuándo se sube a 'bloqueo', "
        f"hay {len(condiciones)} en {RUTA_DECLARACION.as_posix()}"
    )
    assert "evals/fixtures/" in condiciones[0], (
        "la condición de la puerta no nombra los fixtures versionados: "
        f"{condiciones[0]!r}"
    )
    assert "ground_truth" not in condiciones[0], (
        "la condición de la puerta vuelve a apoyarse en los libros .xlsx no "
        f"versionados: {condiciones[0]!r}"
    )
