# tests/test_f038_r17_r21_documentos.py
"""F-038 · R17–R21: lo que el arnés le pide por escrito a cada agente.

Los topes de tamaño, el umbral de reejecución y la revisión incremental no son
código: son reglas que viven en cuatro documentos y que ningún test vigilaba.
La consecuencia conocida es que se pierden —las reglas RM5 y RM6 se acordaron
con el humano y solo existían en `progress/current.md`, que es memoria de
sesión— o se contradicen entre documentos.

Estos tests son baratos y evitan exactamente eso: que una regla escrita hoy
desaparezca de un documento en la próxima reescritura sin que nadie se entere.
"""

from __future__ import annotations

from pathlib import Path

SPECS = Path("specs/SPECS.md")
SPEC_AUTHOR = Path(".claude/agents/spec-author.md")
IMPLEMENTER = Path(".claude/agents/implementer.md")


def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8", errors="replace")


# --- R17: los topes de tamaño, en los documentos que los tienen que aplicar --


def test_f038_r17_specs_md_declara_los_topes_de_requirements_y_design() -> None:
    texto = _texto(SPECS)

    assert "120" in texto, "tope de requirements.md"
    assert "200" in texto, "tope de design.md"


def test_f038_r17_specs_md_pide_una_tarea_por_linea_en_tasks() -> None:
    assert "una tarea por línea" in _texto(SPECS).lower()


def test_f038_r17_specs_md_dice_que_lo_que_no_cabe_se_resume_y_se_enlaza() -> None:
    """Son topes, no objetivos: recortar no puede significar tirar evidencia."""
    assert "se resume y se enlaza" in _texto(SPECS)


def test_f038_r17_el_spec_author_conoce_los_topes_de_su_producto() -> None:
    texto = _texto(SPEC_AUTHOR)

    assert "120" in texto and "200" in texto
    assert "se resume y se enlaza" in texto


def test_f038_r17_el_implementer_conoce_el_tope_de_su_informe() -> None:
    texto = _texto(IMPLEMENTER)

    assert "150" in texto, "tope de progress/impl_F-XXX.md"
    assert "se resume y se enlaza" in texto
