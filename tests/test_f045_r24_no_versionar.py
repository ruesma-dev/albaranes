# tests/test_f045_r24_no_versionar.py
"""F-045 · R24: los originales de albarán no entran en git. En ningún formato.

Son documentos de proveedor CON PRECIOS. Hasta el 2026-09-15 solo los tapaba
la regla `*.pdf` del bloque del arnés, así que un original en PNG —y la rama
de imágenes de sv2 los admite desde julio— habría entrado sin que nadie lo
notara. Lo mismo vale para la copia del Excel de trabajo del humano.

Al repositorio entran únicamente los fixtures JSON, ya barridos por el
conversor.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _git(*argumentos: str) -> str:
    return subprocess.run(
        ["git", *argumentos], cwd=RAIZ, capture_output=True, text=True, check=False
    ).stdout


def test_f045_r24_gitignore_cubre_la_carpeta_de_entrada_entera():
    reglas = (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "evals/inputs/" in [linea.strip() for linea in reglas]


def test_f045_r24_git_no_traquea_nada_bajo_evals_inputs():
    traqueados = [f for f in _git("ls-files", "evals/inputs").splitlines() if f.strip()]
    assert traqueados == []


def test_f045_r24_las_cuatro_extensiones_quedan_ignoradas():
    for extension in (".pdf", ".png", ".jpg", ".jpeg"):
        ruta = f"evals/inputs/albaranes/PRUEBA{extension}"
        assert _git("check-ignore", "-v", ruta).strip(), ruta


def test_f045_r24_la_copia_del_excel_del_humano_tampoco_se_versiona():
    assert _git("check-ignore", "-v", "evals/inputs/fuente/evals_summary.xlsx").strip()


def test_f045_r24_los_fixtures_si_se_versionan():
    """Lo que se versiona es la traducción barrida, no el documento."""
    fixtures = _git("ls-files", "evals/fixtures").splitlines()
    assert any(f.endswith("IA1/RES-001.json") for f in fixtures)


def test_f045_r24_las_copias_de_seguridad_de_los_libros_no_entran():
    assert _git("check-ignore", "-v",
                "evals/ground_truth/copias/IA1_extraccion.xlsx.20260915-1830.xlsx").strip()
