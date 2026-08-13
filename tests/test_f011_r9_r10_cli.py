# tests/test_f011_r9_r10_cli.py
"""F-011 · R9 y R10 — Las dos corridas del runner y el gasto explícito.

R9: `--con-llm` ejecuta la pasada completa (cuatro fases + extremo-a-extremo);
no se trocea por fase (D2).
R10: sin `--con-llm` solo corre el modo determinista, y pedir IA1/IA2 sin él es
un error: el dinero no se gasta por defecto.
"""

import pytest

from evals.informe import MODO_COMPLETA, MODO_DETERMINISTA
from evals.runner import (
    FASES_COMPLETA,
    FASES_DETERMINISTA,
    UsoIncorrecto,
    comprobar_peticion,
    main,
    ruta_de_informe,
)


def test_f011_r9_la_pasada_completa_son_las_cuatro_fases_y_el_extremo_a_extremo():
    assert FASES_COMPLETA == ("IA1", "IA2", "IA3", "IA4", "E2E")


def test_f011_r10_el_modo_determinista_no_incluye_ia1_ni_ia2():
    assert "IA1" not in FASES_DETERMINISTA
    assert "IA2" not in FASES_DETERMINISTA
    assert "E2E" in FASES_DETERMINISTA


def test_f011_r10_pedir_ia1_sin_con_llm_se_rechaza():
    with pytest.raises(UsoIncorrecto) as error:
        comprobar_peticion(con_llm=False, fases=["IA1", "IA3"])

    assert "--con-llm" in str(error.value)


def test_f011_r10_pedir_la_pasada_completa_sin_con_llm_se_rechaza():
    with pytest.raises(UsoIncorrecto):
        comprobar_peticion(con_llm=False, fases=list(FASES_COMPLETA))


def test_f011_r10_con_con_llm_no_se_rechaza_nada():
    comprobar_peticion(con_llm=True, fases=list(FASES_COMPLETA))


def test_f011_r10_el_cli_rechaza_ia1_sin_con_llm_con_codigo_2(tmp_path, capsys):
    codigo = main(
        [
            "--fases",
            "IA1",
            "--fixtures",
            str(tmp_path / "fixtures"),
            "--informes",
            str(tmp_path / "progress"),
        ]
    )

    assert codigo == 2
    assert "--con-llm" in capsys.readouterr().err


def test_f011_r15_el_informe_va_a_progress_con_el_nombre_de_la_feature():
    assert ruta_de_informe("F-011").name == "evals_F-011.md"
    assert ruta_de_informe("").name == "evals_manual.md"


def test_f011_r9_el_modo_queda_escrito_en_el_informe(tmp_path):
    main(
        [
            "--fixtures",
            str(tmp_path / "fixtures"),
            "--informes",
            str(tmp_path / "progress"),
            "--feature",
            "F-011",
        ]
    )

    texto = (tmp_path / "progress" / "evals_F-011.md").read_text(encoding="utf-8")
    assert f"MODO: {MODO_DETERMINISTA}" in texto
    assert MODO_COMPLETA not in texto.split("MODO:")[1].splitlines()[0]
