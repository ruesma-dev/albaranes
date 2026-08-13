# tests/test_f011_r18_sin_casos.py
"""F-011 · R16 y R18 — Sin casos no hay verde, y el código de salida lo dice.

Un informe sin casos no es evidencia: mientras los libros estén vacíos, la
corrida sale NO_EVALUABLE (código 2). Lo contrario —VERDE por no haber
evaluado nada— es exactamente la falsa tranquilidad que este arnés existe para
evitar.
"""

import json

from evals.informe import es_pasada_completa, parsear_veredicto
from evals.modelos import NO_EVALUABLE
from evals.runner import cargar_fixtures, main


def _fixtures_vacios(raiz):
    for fase in ("IA1", "IA2", "IA3", "IA4", "inputs", "final"):
        carpeta = raiz / fase
        carpeta.mkdir(parents=True)
        (carpeta / "_indice.json").write_text(
            json.dumps({"casos": [], "fase": fase}), encoding="utf-8"
        )
    return raiz


def test_f011_r18_sin_casos_el_codigo_de_salida_es_2(tmp_path):
    fixtures = _fixtures_vacios(tmp_path / "fixtures")

    codigo = main(
        ["--fixtures", str(fixtures), "--informes", str(tmp_path / "progress")]
    )

    assert codigo == 2


def test_f011_r18_el_informe_dice_no_evaluable_y_por_que(tmp_path):
    fixtures = _fixtures_vacios(tmp_path / "fixtures")

    main(
        [
            "--fixtures",
            str(fixtures),
            "--informes",
            str(tmp_path / "progress"),
            "--feature",
            "F-011",
        ]
    )

    texto = (tmp_path / "progress" / "evals_F-011.md").read_text(encoding="utf-8")
    assert parsear_veredicto(texto) == NO_EVALUABLE
    assert "no hay ningún caso" in texto


def test_f011_r18_una_corrida_determinista_nunca_vale_como_pasada_completa(tmp_path):
    fixtures = _fixtures_vacios(tmp_path / "fixtures")

    main(
        ["--fixtures", str(fixtures), "--informes", str(tmp_path / "progress")]
    )

    texto = (tmp_path / "progress" / "evals_manual.md").read_text(encoding="utf-8")
    assert es_pasada_completa(texto) is False


def test_f011_r18_el_indice_no_se_confunde_con_un_caso(tmp_path):
    fixtures = _fixtures_vacios(tmp_path / "fixtures")

    assert cargar_fixtures(fixtures, "IA3") == {}


def test_f011_r18_un_directorio_de_fixtures_inexistente_no_revienta(tmp_path):
    assert cargar_fixtures(tmp_path / "no-existe", "IA3") == {}
