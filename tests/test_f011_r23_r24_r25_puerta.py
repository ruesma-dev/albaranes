# tests/test_f011_r23_r24_r25_puerta.py
"""F-011 · R23, R24, R25 y R26 — La puerta: qué mira y qué NO hace.

R23: el diff de la feature sale de `harness/alcance.py` (mismo cálculo que la
cobertura y la mutación), pero SIN el filtro de solo-Python: un prompt YAML
también es una ruta sensible.
R24: rutas tocadas + informe ausente, viejo o no VERDE ⇒ la puerta falla.
R25: sin rutas tocadas, o sin feature en curso, ⇒ N/A con el motivo impreso.
R26: la puerta NUNCA ejecuta los evals; solo lee el informe.

Sin git real: el ejecutor de git se inyecta, igual que en `harness.alcance`.
"""


import pytest

from harness.rutas_sensibles import (
    RutaSensible,
    Verificacion,
    evaluar_puerta,
    ficheros_tocados,
    informe_incumple,
    rutas_tocadas,
)

_DIFF_PROMPT = """diff --git a/services/albaranes-api/config/prompts.yaml b/services/albaranes-api/config/prompts.yaml
--- a/services/albaranes-api/config/prompts.yaml
+++ b/services/albaranes-api/config/prompts.yaml
@@ -1,3 +1,4 @@
 albaran_factura_es:
+  system: nuevo
"""

_DIFF_INOCENTE = """diff --git a/docs/ARCHITECTURE.md b/docs/ARCHITECTURE.md
--- a/docs/ARCHITECTURE.md
+++ b/docs/ARCHITECTURE.md
@@ -1,2 +1,3 @@
 arquitectura
+una línea más
"""

_INFORME_BUENO = """# Evals
MODO: completa
FASES: IA1,IA2,IA3,IA4,E2E
VEREDICTO: VERDE
"""

_INFORME_DETERMINISTA = """# Evals
MODO: determinista
FASES: IA3,IA4,E2E
VEREDICTO: VERDE
"""

_INFORME_ROJO = """# Evals
MODO: completa
FASES: IA1,IA2,IA3,IA4,E2E
VEREDICTO: ROJO
"""

_EXIGE = ("MODO: completa", "FASES: IA1,IA2,IA3,IA4,E2E", "VEREDICTO: VERDE")


def _verificacion(exigencia="bloqueo"):
    return Verificacion(
        nombre="evals",
        comando="python -m evals.runner --con-llm --feature {feature}",
        informe="progress/evals_{feature}.md",
        exigencia=exigencia,
        exige_lineas=_EXIGE,
        rutas=(
            RutaSensible(
                patron="services/albaranes-api/config/prompts.yaml",
                motivo="índice de prompts sv2",
            ),
            RutaSensible(
                patron="services/*/domain/models/**", motivo="schemas Pydantic"
            ),
        ),
    )


def _git(diff: str, rama_existe: bool = True):
    def ejecutar(args):
        if args[:2] == ["rev-parse", "--verify"]:
            return "abc123\n" if rama_existe else ""
        if args[0] == "merge-base":
            return "base123\n"
        if args[0] == "diff":
            return diff
        return ""

    return ejecutar


def test_f011_r23_el_diff_incluye_lo_que_no_es_python(tmp_path):
    tocados = ficheros_tocados("F-011", "dev", "feature/F-011", git=_git(_DIFF_PROMPT))

    assert tocados == ["services/albaranes-api/config/prompts.yaml"]


def test_f011_r23_un_patron_con_comodines_casa_dentro_del_servicio():
    tocados = ["services/albaran-valoracion-api/domain/models/valuation_models.py"]

    coincidencias = rutas_tocadas(_verificacion(), tocados)

    assert coincidencias[0].fichero == tocados[0]
    assert coincidencias[0].motivo == "schemas Pydantic"


def test_f011_r23_las_barras_de_windows_no_despistan_al_cotejo():
    tocados = ["services\\albaranes-api\\config\\prompts.yaml"]

    assert rutas_tocadas(_verificacion(), tocados)


def test_f011_r25_sin_rutas_tocadas_la_puerta_es_na(tmp_path):
    resultado = evaluar_puerta(
        [_verificacion()],
        feature="F-011",
        rama="feature/F-011",
        base="dev",
        raiz=tmp_path,
        git=_git(_DIFF_INOCENTE),
    )

    assert resultado.codigo == 0
    assert "N/A" in resultado.mensaje
    assert "no toca ninguna ruta sensible" in resultado.mensaje


def test_f011_r25_sin_feature_en_curso_la_puerta_es_na(tmp_path):
    resultado = evaluar_puerta(
        [_verificacion()],
        feature="",
        rama="",
        base="dev",
        raiz=tmp_path,
        git=_git(_DIFF_PROMPT),
    )

    assert resultado.codigo == 0
    assert "N/A" in resultado.mensaje
    assert "sin feature" in resultado.mensaje.lower()


def test_f011_r24_rutas_tocadas_sin_informe_es_ko(tmp_path):
    resultado = evaluar_puerta(
        [_verificacion(exigencia="bloqueo")],
        feature="F-011",
        rama="feature/F-011",
        base="dev",
        raiz=tmp_path,
        git=_git(_DIFF_PROMPT),
    )

    assert resultado.codigo == 1
    assert "prompts.yaml" in resultado.mensaje
    assert "python -m evals.runner --con-llm --feature F-011" in resultado.mensaje


def test_f011_r24_con_exigencia_aviso_el_codigo_es_3(tmp_path):
    resultado = evaluar_puerta(
        [_verificacion(exigencia="aviso")],
        feature="F-011",
        rama="feature/F-011",
        base="dev",
        raiz=tmp_path,
        git=_git(_DIFF_PROMPT),
    )

    assert resultado.codigo == 3
    assert "aviso" in resultado.mensaje.lower()


def test_f011_r24_un_informe_determinista_no_vale_como_evidencia(tmp_path):
    (tmp_path / "progress").mkdir()
    (tmp_path / "progress" / "evals_F-011.md").write_text(
        _INFORME_DETERMINISTA, encoding="utf-8"
    )

    resultado = evaluar_puerta(
        [_verificacion()],
        feature="F-011",
        rama="feature/F-011",
        base="dev",
        raiz=tmp_path,
        git=_git(_DIFF_PROMPT),
    )

    assert resultado.codigo == 1
    assert "MODO: completa" in resultado.mensaje


def test_f011_r24_un_informe_rojo_no_abre_la_puerta(tmp_path):
    (tmp_path / "progress").mkdir()
    (tmp_path / "progress" / "evals_F-011.md").write_text(_INFORME_ROJO, encoding="utf-8")

    resultado = evaluar_puerta(
        [_verificacion()],
        feature="F-011",
        rama="feature/F-011",
        base="dev",
        raiz=tmp_path,
        git=_git(_DIFF_PROMPT),
    )

    assert resultado.codigo == 1
    assert "VEREDICTO: VERDE" in resultado.mensaje


def test_f011_r24_con_una_pasada_completa_en_verde_la_puerta_abre(tmp_path):
    (tmp_path / "progress").mkdir()
    (tmp_path / "progress" / "evals_F-011.md").write_text(_INFORME_BUENO, encoding="utf-8")

    resultado = evaluar_puerta(
        [_verificacion()],
        feature="F-011",
        rama="feature/F-011",
        base="dev",
        raiz=tmp_path,
        git=_git(_DIFF_PROMPT),
    )

    assert resultado.codigo == 0
    assert "evals_F-011.md" in resultado.mensaje


@pytest.mark.parametrize(
    ("texto", "faltan"),
    [
        (_INFORME_BUENO, []),
        (_INFORME_ROJO, ["VEREDICTO: VERDE"]),
        (_INFORME_DETERMINISTA, ["MODO: completa", "FASES: IA1,IA2,IA3,IA4,E2E"]),
    ],
)
def test_f011_r24_el_informe_se_juzga_por_sus_lineas_declaradas(texto, faltan):
    assert informe_incumple(texto, _EXIGE) == faltan


def test_f011_r26_la_puerta_no_ejecuta_nada(tmp_path, monkeypatch):
    """Si la puerta lanzara los evals, `init.sh` costaría dinero cada arranque."""
    import subprocess

    def prohibido(*args, **kwargs):  # pragma: no cover - debe no llamarse
        raise AssertionError("la puerta ha intentado ejecutar un proceso")

    monkeypatch.setattr(subprocess, "run", prohibido)

    resultado = evaluar_puerta(
        [_verificacion()],
        feature="F-011",
        rama="feature/F-011",
        base="dev",
        raiz=tmp_path,
        git=_git(_DIFF_PROMPT),
    )

    assert resultado.codigo == 1


def test_f011_r23_un_diff_de_varios_ficheros_los_lista_todos():
    diff = _DIFF_PROMPT + _DIFF_INOCENTE

    tocados = ficheros_tocados("F-011", "dev", "feature/F-011", git=_git(diff))

    assert set(tocados) == {
        "services/albaranes-api/config/prompts.yaml",
        "docs/ARCHITECTURE.md",
    }


def test_f011_r23_sin_rama_ni_merge_no_se_inventa_un_alcance():
    with pytest.raises(SystemExit):
        ficheros_tocados("F-011", "dev", "", git=_git("", rama_existe=False))
