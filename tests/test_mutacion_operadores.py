# tests/test_mutacion_operadores.py
"""El mutador tiene que mutar `is` / `is not`: la guarda de ausencia de Python.

`x is None` es LA forma de preguntar por la ausencia en Python, y era el punto
ciego del mutador: la tabla `COMPARACIONES` no la conocía. Es justo el patrón
de los dos defectos más caros de este proyecto —la red KG→TN que se apagaba
con un `derived_line is not None` y la precedencia del importe de línea con un
`importe_albaran_declarado is not None`—, así que sus campañas se midieron
ciegas en el sitio que más importaba.

Aquí se fija, además, el efecto colateral que aparece al mutar un operador
escrito con letras: `is` cabe dentro de cualquier palabra («análisis»), y el
hueco entre los dos operandos puede contener un comentario cuando la condición
va entre paréntesis. Sin delimitación de palabra, el mutante caía dentro del
comentario: equivalente por construcción, superviviente eterno y ruido en el
informe.

Todos los tests son puros: AST sobre fuentes en cadena y lectura de un fichero
del propio repositorio. Ni red, ni BBDD, ni subprocesos.
"""

from __future__ import annotations

import ast
import json

import pytest

from harness.mutacion import aplicar_mutante, clave_de_mutante, generar_mutantes
from harness.rutas_sensibles import RUTA_DECLARACION

FICHERO = "modulo.py"

FUENTE_IS = (
    "def sin_valor(x):\n"
    "    if x is None:\n"
    "        return uno()\n"
    "    return dos()\n"
)

#: La guarda real de F-027 (`valuation_builder.py:1033`), palabra por palabra.
FUENTE_F027 = (
    "def construir(partida_result):\n"
    "    if partida_result.derived_line is not None:\n"
    "        return partida_result.derived_line\n"
    "    return None\n"
)

FUENTE_DOS_IS = (
    "def ambos(a, b):\n"
    "    if a is None or b is None:\n"
    "        return cero()\n"
    "    return uno()\n"
)

FUENTE_ENCADENADA = (
    "def encadenada(a, b, c):\n"
    "    if a is b is not c:\n"
    "        return cero()\n"
    "    return uno()\n"
)

#: El caso que destapa la falta de delimitación: «analisis» lleva dos veces la
#: secuencia `is` dentro, y está en el hueco entre los dos operandos.
FUENTE_COMENTARIO = (
    "def con_comentario(valor):\n"
    "    if (\n"
    "        valor  # el analisis previo\n"
    "        is None\n"
    "    ):\n"
    "        return uno()\n"
    "    return dos()\n"
)

FUENTE_SIMBOLOS = (
    "def sin_espacios(x, y, a, b):\n"
    "    if x==y:\n"
    "        return cero()\n"
    "    z=a+b\n"
    "    return z\n"
)

#: Espaciado que ningún formateador (ruff/black) deja pasar. Documentado como
#: límite conocido: no genera mutante y no puede reventar.
FUENTE_NO_CANONICA = (
    "def raro(x):\n"
    "    if x is  not None:\n"
    "        return uno()\n"
    "    return dos()\n"
)


def _mutantes(fuente: str) -> list:
    """Todos los mutantes de `fuente`, con el fichero entero en el alcance."""
    lineas = set(range(1, len(fuente.split("\n")) + 1))
    return generar_mutantes(fuente, lineas, FICHERO)


def _de_operador(fuente: str, operador: str) -> list:
    return [mutante for mutante in _mutantes(fuente) if mutante.operador == operador]


def _primera_comparacion(fuente: str) -> ast.Compare:
    return next(
        nodo for nodo in ast.walk(ast.parse(fuente)) if isinstance(nodo, ast.Compare)
    )


def test_f034_r1_muta_is_a_is_not():
    """R1: `x is None` produce el mutante `x is not None`."""
    mutantes = _de_operador(FUENTE_IS, "comparacion")

    assert len(mutantes) == 1, f"esperado 1 mutante de comparación, hay {len(mutantes)}"
    assert mutantes[0].linea == 2
    assert mutantes[0].original == "if x is None:"
    assert mutantes[0].mutado == "if x is not None:"


def test_f034_r2_muta_is_not_a_is():
    """R2: la guarda de F-027 produce el mutante que nadie generó en su día."""
    mutantes = _de_operador(FUENTE_F027, "comparacion")

    assert len(mutantes) == 1, f"esperado 1 mutante de comparación, hay {len(mutantes)}"
    assert mutantes[0].linea == 2
    assert mutantes[0].original == "if partida_result.derived_line is not None:"
    assert mutantes[0].mutado == "if partida_result.derived_line is None:"


def test_f034_r3_una_mutacion_por_operador_en_la_misma_linea():
    """R3: un mutante independiente por operador, unidos por `or` o encadenados."""
    unidos = _de_operador(FUENTE_DOS_IS, "comparacion")

    assert len(unidos) == 2, f"esperados 2 mutantes, hay {len(unidos)}"
    assert len({mutante.col for mutante in unidos}) == 2, "los dos en la misma columna"
    assert {mutante.mutado for mutante in unidos} == {
        "if a is not None or b is None:",
        "if a is None or b is not None:",
    }

    encadenados = _de_operador(FUENTE_ENCADENADA, "comparacion")

    assert len(encadenados) == 2, f"esperados 2 mutantes, hay {len(encadenados)}"
    assert {mutante.mutado for mutante in encadenados} == {
        "if a is not b is not c:",
        "if a is b is c:",
    }


def test_f034_r4_el_operador_declarado_es_comparacion():
    """R4: van etiquetados como `comparacion` y `clave_de_mutante` los distingue."""
    mutantes = _mutantes(FUENTE_IS)

    assert [mutante.operador for mutante in mutantes] == ["comparacion"]

    dos = _de_operador(FUENTE_DOS_IS, "comparacion")
    claves = {
        clave_de_mutante(
            mutante.fichero, mutante.operador, mutante.original, mutante.mutado
        )
        for mutante in dos
    }

    assert len(claves) == 2, (
        "los dos mutantes de la misma línea comparten clave: entre campañas se "
        "repondría el análisis del otro"
    )


def test_f034_r5_no_muta_dentro_de_una_palabra_del_comentario():
    """R5: la secuencia `is` de «analisis» no es un operador y no se muta."""
    mutantes = _de_operador(FUENTE_COMENTARIO, "comparacion")

    assert len(mutantes) == 1, f"esperado 1 mutante, hay {len(mutantes)}"
    assert mutantes[0].linea == 4, (
        f"el mutante cayó en la línea {mutantes[0].linea} "
        f"({mutantes[0].mutado!r}); el operador está en la 4"
    )
    assert mutantes[0].mutado == "is not None"


def test_f034_r6_los_simbolos_sin_espacios_siguen_mutando():
    """R6: delimitar palabras no puede dejar de mutar `x==y` ni `a+b`."""
    mutantes = _mutantes(FUENTE_SIMBOLOS)
    comparaciones = [m for m in mutantes if m.operador == "comparacion"]
    aritmeticos = [m for m in mutantes if m.operador == "aritmetico"]

    assert [m.mutado for m in comparaciones] == ["if x!=y:"]
    assert [m.mutado for m in aritmeticos] == ["z=a-b"]


def test_f034_r7_espaciado_no_canonico_no_genera_mutante_ni_falla():
    """R7: `is  not` es un límite declarado — cero mutantes, cero excepciones."""
    assert _de_operador(FUENTE_NO_CANONICA, "comparacion") == []


def test_f034_r8_el_mutante_compila_y_el_ast_lleva_el_operador_contrario():
    """R8: aplicado, el mutante compila y el AST lleva el operador contrario."""
    directo = _de_operador(FUENTE_IS, "comparacion")[0]
    mutada = aplicar_mutante(FUENTE_IS, directo)
    compile(mutada, FICHERO, "exec")

    assert isinstance(_primera_comparacion(mutada).ops[0], ast.IsNot)

    inverso = _de_operador(FUENTE_F027, "comparacion")[0]
    mutada_inversa = aplicar_mutante(FUENTE_F027, inverso)
    compile(mutada_inversa, FICHERO, "exec")

    assert isinstance(_primera_comparacion(mutada_inversa).ops[0], ast.Is)


def test_f034_r14_la_puerta_de_evals_no_se_declara_sobre_lo_no_versionado():
    """R14: la subida de la puerta se condiciona a artefactos VERSIONADOS.

    Los libros `.xlsx` de `evals/ground_truth/` existen, pero `.gitignore` los
    excluye: quien clona el repositorio no los ve. Condicionar una puerta a
    ellos es condicionarla a algo que nadie puede comprobar. Lo que consume
    `evals.runner` son los fixtures versionados de `evals/fixtures/`.

    En un repositorio sin declaración de rutas sensibles no hay puerta que
    comprobar y el test se salta: este fichero viaja tal cual a `arnes-base`.
    """
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
