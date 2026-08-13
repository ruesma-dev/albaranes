# tests/test_f011_r21_r22_ausente_o_rota.py
"""F-011 · R21 y R22 — Sin declaración no cambia nada; rota, el arnés cae.

Es la regla de oro de `harness/servicios.py` aplicada aquí: la AUSENCIA del
fichero es la configuración del caso mayoritario (un repositorio sin rutas
sensibles declaradas) y no puede alterar el comportamiento del arnés. Pero un
fichero roto NO degrada a «sin puerta»: eso sería dejar de vigilar mientras el
portero imprime que todo va bien.
"""

import json

import pytest

from harness.rutas_sensibles import (
    ErrorDeclaracion,
    cargar_declaracion,
    main,
)


def test_f011_r21_sin_fichero_la_declaracion_es_una_lista_vacia(tmp_path):
    assert cargar_declaracion(tmp_path / "no-existe.json") == []


def test_f011_r21_sin_fichero_el_validador_sale_con_cero(tmp_path, capsys):
    codigo = main(["--validar", "--declaracion", str(tmp_path / "no-existe.json")])

    assert codigo == 0
    assert "sin" in capsys.readouterr().out.lower()


def test_f011_r21_sin_fichero_la_puerta_no_dice_nada(tmp_path, capsys):
    codigo = main(
        [
            "--puerta",
            "--declaracion",
            str(tmp_path / "no-existe.json"),
            "--base",
            "dev",
        ]
    )

    assert codigo == 0
    assert capsys.readouterr().out.strip() == ""


def test_f011_r22_una_declaracion_rota_hace_fallar_al_validador(tmp_path, capsys):
    ruta = tmp_path / "rutas_sensibles.json"
    ruta.write_text("{roto", encoding="utf-8")

    codigo = main(["--validar", "--declaracion", str(ruta)])

    assert codigo == 1
    assert "rutas_sensibles.json" in capsys.readouterr().err


def test_f011_r22_una_declaracion_rota_hace_fallar_a_la_puerta(tmp_path, capsys):
    ruta = tmp_path / "rutas_sensibles.json"
    ruta.write_text(json.dumps({"sin_verificaciones": []}), encoding="utf-8")

    codigo = main(["--puerta", "--declaracion", str(ruta), "--base", "dev"])

    assert codigo == 1
    assert "verificaciones" in capsys.readouterr().err


def test_f011_r22_la_lista_verificaciones_es_obligatoria(tmp_path):
    ruta = tmp_path / "rutas_sensibles.json"
    ruta.write_text(json.dumps({"verificaciones": {}}), encoding="utf-8")

    with pytest.raises(ErrorDeclaracion) as error:
        cargar_declaracion(ruta)

    assert "verificaciones" in str(error.value)
