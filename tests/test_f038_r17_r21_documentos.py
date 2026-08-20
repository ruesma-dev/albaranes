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


# --- R18, R19, R20: lo que cambia en el reviewer ----------------------------

REVIEWER = Path(".claude/agents/reviewer.md")


def test_f038_r17_el_reviewer_conoce_el_tope_de_su_informe() -> None:
    texto = _texto(REVIEWER)

    assert "100" in texto, "tope de progress/review_F-XXX.md"
    assert "se resume y se enlaza" in texto


def test_f038_r18_el_umbral_de_reejecucion_baja_a_60_segundos() -> None:
    """Sigue cubriendo el fraude barato y deja de duplicar las campañas caras."""
    texto = _texto(REVIEWER)

    assert "60 segundos" in texto or "60 s" in texto
    assert "inferior a 5 minutos" not in texto, "el umbral viejo, ya retirado"


def test_f038_r19_el_reviewer_revisa_incremental_y_declara_desde_que_sha() -> None:
    texto = _texto(REVIEWER)

    assert "incremental" in texto.lower()
    assert "último commit aprobado" in texto
    assert "SHA" in texto


def test_f038_r20_el_reviewer_recoge_las_seis_reglas_de_campania() -> None:
    texto = _texto(REVIEWER)

    for regla in ("RM1", "RM2", "RM3", "RM4", "RM5", "RM6"):
        assert regla in texto, regla


def test_f038_r20_rm5_solo_se_exige_en_rigor_critico_y_con_una_muestra() -> None:
    """Es la única regla que sube el coste: va acotada por decisión del humano."""
    bloque = _texto(REVIEWER).split("**RM5", 1)[1].split("**RM6", 1)[0]

    assert "critico" in bloque or "crítico" in bloque
    assert "muestra" in bloque or "UNO" in bloque or "uno" in bloque
