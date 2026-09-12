# tests/test_f043_canal_subproceso.py
"""F-043 · el canal de salida del subproceso no puede mezclar JSON y ruido.

El 2026-09-12, `python -m evals.runner --con-llm --feature F-043` murió en
`json.loads(proceso.stdout)` con `Expecting value: line 1 column 1 (char 0)`.
El subproceso terminaba en 0 y traía el JSON entero, pero PyMuPDF había
escrito antes en STDOUT su aviso de que `fitz` está deprecado. El canal por el
que vuelve el resultado era el mismo por el que cualquier librería escupe sus
avisos, así que la primera línea que leía `json.loads` no era JSON.

Estos tests fijan que el canal aguante ruido de CUALQUIER procedencia, no el
aviso concreto de hoy: mañana será otra librería. Nada de esto llama a un LLM
ni abre un PDF; el ruido se inyecta con un `sitecustomize` de mentira.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from evals.procesos import canal

RAIZ_REPO = Path(__file__).resolve().parent.parent

#: El aviso literal que PyMuPDF escribe en STDOUT al importar `fitz`.
RUIDO = (
    "warning: The `fitz` API is deprecated and will be removed in future. "
    "Use `import pymupdf` instead."
)


def test_f043_el_lector_tolera_ruido_en_stdout_del_subproceso(tmp_path, monkeypatch):
    """Reproduce el defecto: alguien imprime en stdout antes de que haya JSON.

    `sitecustomize` lo importa el propio arranque del intérprete, o sea que el
    ruido llega al canal ANTES de que el subproceso ejecute una sola línea
    suya: es el peor caso posible y el que de verdad ocurrió.
    """
    sucio = tmp_path / "sitecustomize.py"
    sucio.write_text(f"print({RUIDO!r})\n", encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))

    from evals.procesos.sv6_build import ejecutar_en_subproceso

    assert ejecutar_en_subproceso({"casos": []}) == {"resultados": []}


def test_f043_el_subproceso_manda_a_stderr_lo_que_se_imprima_durante_el_trabajo(
    tmp_path,
):
    """La otra mitad del arreglo: el que escribe blinda su propio stdout.

    El ruido no se pierde —se diagnostica peor un aviso tragado que uno fuera
    de sitio—: sale por stderr, que es donde el lector ya mira cuando algo
    falla.
    """
    hijo = tmp_path / "hijo.py"
    hijo.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(RAIZ_REPO)!r})\n"
        "from evals.procesos import canal\n"
        "canal.blindar_stdout()\n"
        f"print({RUIDO!r})\n"
        "canal.emitir({'ok': True})\n",
        encoding="utf-8",
    )

    proceso = subprocess.run(
        [sys.executable, str(hijo)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(RAIZ_REPO),
        check=False,
    )

    assert proceso.returncode == 0, proceso.stderr
    assert RUIDO in proceso.stderr
    assert RUIDO not in proceso.stdout
    assert canal.leer(proceso.stdout, "prueba") == {"ok": True}


def test_f043_el_aviso_real_de_pymupdf_ya_no_contamina_el_canal(tmp_path):
    """El caso original, sin gastar un céntimo: `import fitz` y nada más.

    Es el aviso de verdad, escrito por la librería de verdad en el momento de
    verdad (el import que hace `_adjuntos` al preparar el PDF del albarán).
    """
    pytest.importorskip("fitz", reason="PyMuPDF no está instalado en este entorno")

    hijo = tmp_path / "hijo_fitz.py"
    hijo.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(RAIZ_REPO)!r})\n"
        "from evals.procesos import canal\n"
        "canal.blindar_stdout()\n"
        "import fitz\n"
        "canal.emitir({'resultados': []})\n",
        encoding="utf-8",
    )

    proceso = subprocess.run(
        [sys.executable, str(hijo)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(RAIZ_REPO),
        check=False,
    )

    assert proceso.returncode == 0, proceso.stderr
    assert "deprecated" in proceso.stderr
    assert "deprecated" not in proceso.stdout
    assert canal.leer(proceso.stdout, "sv2") == {"resultados": []}


def test_f043_el_lector_se_queda_con_el_ultimo_json_marcado():
    """Si el ruido imitara la marca, manda el JSON que se emitió al final."""
    stdout = (
        f"{canal.MARCA_INICIO}\n{{\"impostor\": true}}\n{canal.MARCA_FIN}\n"
        f"{canal.MARCA_INICIO}\n{{\"resultados\": []}}\n{canal.MARCA_FIN}\n"
    )

    assert canal.leer(stdout, "sv6") == {"resultados": []}


def test_f043_el_lector_admite_la_marca_en_el_primer_caracter():
    """Sin ruido delante, la marca abre el stdout: eso no es «no hay marca»."""
    assert canal.leer(f"{canal.MARCA_INICIO}\n{{}}\n{canal.MARCA_FIN}\n", "sv6") == {}


def test_f043_el_lector_explica_que_llego_cuando_no_hay_json_marcado():
    """Un canal roto tiene que decir qué llegó, no `line 1 column 1`."""
    with pytest.raises(RuntimeError) as fallo:
        canal.leer("Killed: out of memory\n", "sv2")

    assert "sv2" in str(fallo.value)
    assert "Killed: out of memory" in str(fallo.value)


def test_f043_el_lector_avisa_si_el_json_llego_cortado():
    """Marca de inicio sin marca de fin = salida truncada, no JSON inválido."""
    with pytest.raises(RuntimeError) as fallo:
        canal.leer(f"{canal.MARCA_INICIO}\n{{\"resul", "sv5")

    assert "sv5" in str(fallo.value)


def test_f043_el_lector_avisa_si_lo_marcado_no_es_json():
    with pytest.raises(RuntimeError) as fallo:
        canal.leer(f"{canal.MARCA_INICIO}\nno soy json\n{canal.MARCA_FIN}\n", "sv6")

    assert "sv6" in str(fallo.value)


def test_f043_ningun_proceso_de_evals_vuelve_a_leer_stdout_a_pelo():
    """El mismo defecto esperaba su turno en sv2, sv5 y sv6: los tres, iguales."""
    culpables = [
        fichero.name
        for fichero in sorted((RAIZ_REPO / "evals" / "procesos").glob("*.py"))
        if "json.loads(proceso.stdout)" in fichero.read_text(encoding="utf-8")
    ]

    assert culpables == [], f"leen stdout como si fuera JSON puro: {culpables}"
