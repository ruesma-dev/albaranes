# tests/test_f011_r17_secuencial.py
"""F-011 · R17 — Los casos se ejecutan en secuencia estricta.

El pipeline real es secuencial por documento y las llamadas LLM se pagan: un
pool de hilos aquí solo sirve para desordenar el informe, saturar la cuota del
proveedor y hacer irreproducible una corrida que existe justamente para ser
reproducible.
"""

from pathlib import Path

RAIZ_EVALS = Path(__file__).resolve().parent.parent / "evals"

#: Lo que no puede aparecer en el código de los evals.
_CONCURRENCIA = (
    "import threading",
    "import asyncio",
    "import multiprocessing",
    "from threading",
    "from asyncio",
    "from multiprocessing",
    "concurrent.futures",
    "ThreadPool",
    "ProcessPool",
)


def test_f011_r17_el_codigo_de_evals_no_usa_hilos_ni_asyncio():
    culpables = []
    for fichero in sorted(RAIZ_EVALS.rglob("*.py")):
        texto = fichero.read_text(encoding="utf-8")
        for marca in _CONCURRENCIA:
            if marca in texto:
                culpables.append(f"{fichero.name}: {marca}")

    assert culpables == [], f"concurrencia prohibida por R17: {culpables}"


def test_f011_r17_el_subproceso_devuelve_los_casos_en_el_orden_recibido():
    from evals.procesos.sv6_build import ejecutar_en_subproceso

    envelope = {
        "status": "ok",
        "meta": {"document_id": "X"},
        "data": {"lineas": []},
        "context": {"lineas_albaran": [], "lineas_contrato": []},
    }
    trabajo = {
        "casos": [
            {"caso_id": f"CASO-{numero}", "envelope": {**envelope, "meta": {"document_id": f"CASO-{numero}"}}}
            for numero in (3, 1, 2)
        ]
    }

    salida = ejecutar_en_subproceso(trabajo)

    assert [r["caso_id"] for r in salida["resultados"]] == [
        "CASO-3",
        "CASO-1",
        "CASO-2",
    ]
