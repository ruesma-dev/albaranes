# tests/test_f011_r16_exit_codes.py
"""F-011 · R16 — Códigos de salida: 0 VERDE, 1 ROJO, 2 NO_EVALUABLE.

Quien lea el runner desde un script (o el humano desde la terminal) tiene que
poder distinguir «pasó», «falló» y «no había nada que evaluar» sin parsear el
Markdown.
"""

import json

from evals.modelos import (
    Discrepancia,
    ResultadoCaso,
    ResultadoFase,
    ResultadoPasada,
)
from evals.runner import main

_CASO_INPUTS = {
    "caso_id": "GEN-500",
    "tipologia": "Generico-Suministros",
    "tablas": {
        "caso": [{"caso_id": "GEN-500", "contrato_codigo": "CTSU26/0500"}],
        "lineas_albaran": [
            {
                "caso_id": "GEN-500",
                "num_linea": 1,
                "descripcion": "TORNILLERÍA",
                "cantidad": 10,
                "unidad": "ud",
                "precio_unitario": 2.0,
                "importe": 20.0,
            }
        ],
        "contrato_lineas": [
            {
                "caso_id": "GEN-500",
                "codigo_producto": "T-1",
                "descripcion_recurso": "TORNILLERÍA",
                "unidad": "ud",
                "precio_unitario": 2.0,
                "codigo_partida": "07.01",
            }
        ],
        "condiciones": [],
    },
}

_CASO_IA3 = {
    "caso_id": "GEN-500",
    "tipologia": "Generico-Suministros",
    "tablas": {
        "lineas_valoradas": [
            {
                "caso_id": "GEN-500",
                "num_linea": 1,
                "match_method": "exact_concept",
                "codigo_producto_contrato": "T-1",
                "codigo_partida_final": "99.99",
                "precio_unitario_final": 2.0,
                "importe_calculado": 20.0,
            }
        ],
        "sinteticas_esperadas": [],
        "sinteticas_prohibidas": [],
    },
}


def _escribir(raiz, fase, caso):
    carpeta = raiz / fase
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / f"{caso['caso_id']}.json").write_text(
        json.dumps(caso, ensure_ascii=False), encoding="utf-8"
    )


def test_f011_r16_verde_sale_con_cero():
    pasada = ResultadoPasada(
        modo="determinista",
        fases=[
            ResultadoFase(
                nombre="IA3",
                casos=[ResultadoCaso.desde_discrepancias("X", "IA3", [])],
            )
        ],
    )

    assert pasada.codigo_salida() == 0


def test_f011_r16_rojo_sale_con_uno():
    pasada = ResultadoPasada(
        modo="determinista",
        fases=[
            ResultadoFase(
                nombre="IA3",
                casos=[
                    ResultadoCaso.desde_discrepancias(
                        "X",
                        "IA3",
                        [
                            Discrepancia(
                                campo="codigo_partida_final",
                                esperado="a",
                                obtenido="b",
                                severidad="fallo",
                            )
                        ],
                    )
                ],
            )
        ],
    )

    assert pasada.codigo_salida() == 1


def test_f011_r16_un_fallo_manda_sobre_una_fase_sin_casos():
    """Un fallo detectado no se disfraza de «no evaluable»."""
    pasada = ResultadoPasada(
        modo="determinista",
        fases=[
            ResultadoFase(
                nombre="IA3",
                casos=[
                    ResultadoCaso.desde_discrepancias(
                        "X",
                        "IA3",
                        [
                            Discrepancia(
                                campo="importe_final",
                                esperado=1,
                                obtenido=2,
                                severidad="fallo",
                            )
                        ],
                    )
                ],
            ),
            ResultadoFase(nombre="E2E"),
        ],
    )

    assert pasada.codigo_salida() == 1


def test_f011_r16_una_discrepancia_critica_real_devuelve_uno(tmp_path):
    """De punta a punta: fixtures en disco, build real de sv6 y código 1."""
    fixtures = tmp_path / "fixtures"
    _escribir(fixtures, "inputs", _CASO_INPUTS)
    _escribir(fixtures, "IA3", _CASO_IA3)

    codigo = main(
        [
            "--fixtures",
            str(fixtures),
            "--informes",
            str(tmp_path / "progress"),
            "--fases",
            "IA3",
        ]
    )

    assert codigo == 1
    texto = (tmp_path / "progress" / "evals_manual.md").read_text(encoding="utf-8")
    assert "99.99" in texto
