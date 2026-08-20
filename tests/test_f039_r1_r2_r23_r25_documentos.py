# tests/test_f039_r1_r2_r23_r25_documentos.py
"""F-039 · R1, R2, R23, R24 y R25: el inventario de campañas y las cabeceras.

Un informe de mutación cuyos números no valen sigue pareciendo evidencia salvo
que su cabecera lo diga, y la lista de cuáles valen se queda atrás en cuanto
alguien añade una campaña. Estos tests son el portero de las dos cosas: el
inventario tiene una fila por informe (R1/R2) y los avisos de invalidez que se
decidió conservar siguen ahí (R23, R24), sin tocar el que ya estaba remedido a
mano (R25).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

PROGRESO = Path("progress")
INVENTARIO = PROGRESO / "inventario_mutacion_F-039.md"

#: Los únicos veredictos que R1 admite. Uno nuevo se declara aquí a propósito:
#: inventar veredictos por fila haría el inventario incomparable consigo mismo.
VEREDICTOS = {
    "VÁLIDA",
    "INVÁLIDA (no se repone)",
    "REMEDIDA",
    "INVALIDADA PARA SIEMPRE",
    "MANUAL",
    "SIN SUJETO",
}

_FILA = re.compile(
    r"^\| `(?P<informe>progress/mutacion_[^`]+\.md)` \| (?P<fuera>[^|]+) \| "
    r"`(?P<veredicto>[^`]+)` \|"
)


def _filas() -> dict[str, tuple[str, str]]:
    texto = INVENTARIO.read_text(encoding="utf-8")
    filas: dict[str, tuple[str, str]] = {}
    for linea in texto.splitlines():
        casa = _FILA.match(linea)
        if casa:
            filas[casa.group("informe")] = (
                casa.group("fuera").strip(),
                casa.group("veredicto"),
            )
    return filas


def _informes_en_disco() -> set[str]:
    return {ruta.as_posix() for ruta in PROGRESO.glob("mutacion_*.md")}


# --- R1 y R2: el inventario no se queda atrás -------------------------------


def test_f039_r1_el_inventario_existe_y_tiene_filas() -> None:
    assert INVENTARIO.is_file(), "R1 exige progress/inventario_mutacion_F-039.md"
    assert _filas(), "el inventario no tiene ni una fila reconocible"


def test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario() -> None:
    """El requisito que impide que el inventario envejezca en silencio."""
    faltan = sorted(_informes_en_disco() - set(_filas()))

    assert not faltan, (
        "estos informes de mutación no figuran en "
        f"{INVENTARIO.as_posix()}: {faltan}. Añádeles su fila con veredicto "
        "antes de cerrar."
    )


def test_f039_r1_ninguna_fila_del_inventario_apunta_a_un_informe_que_no_existe() -> None:
    sobran = sorted(set(_filas()) - _informes_en_disco())

    assert not sobran, f"filas del inventario sin informe detrás: {sobran}"


def test_f039_r1_cada_fila_declara_alcance_fuera_de_services_y_veredicto() -> None:
    for informe, (fuera, veredicto) in _filas().items():
        assert veredicto in VEREDICTOS, (
            f"{informe}: veredicto {veredicto!r} fuera del vocabulario de R1"
        )
        assert "Sí" in fuera or "No" in fuera, (
            f"{informe}: la fila no dice si su alcance sale de services/"
        )


# --- R23 y R24: los avisos que no se retiran --------------------------------


def test_f039_r23_f012_conserva_el_aviso_y_apunta_al_informe_nuevo() -> None:
    texto = (PROGRESO / "mutacion_F-012.md").read_text(encoding="utf-8")

    assert "⚠ CAMPAÑA NO VÁLIDA" in texto, "el aviso de F-012 no se retira nunca"
    assert "mutacion_maquinaria_paralela_F-039.md" in texto
    assert "otro código" in texto, (
        "el puntero debe decir que el informe nuevo mide OTRO código, no que "
        "sea esta campaña rehecha"
    )
    assert "no se reponen" in texto or "NO se reponen" in texto


def test_f039_r24_f011_conserva_el_aviso_con_la_decision_y_su_consecuencia() -> None:
    texto = (PROGRESO / "mutacion_F-011.md").read_text(encoding="utf-8")

    assert "⚠ CAMPAÑA NO VÁLIDA" in texto
    assert "2026-08-20" in texto, "falta la fecha de la decisión del humano"
    assert "INVALIDADA PARA SIEMPRE" in texto
    assert "puerta de evals" in texto, (
        "falta la consecuencia: la puerta de evals de F-011 no tiene detrás "
        "ninguna medición de mutación válida"
    )


# --- R25: el informe ya remedido a mano no se toca --------------------------


def test_f039_r25_mutacion_f034_no_se_modifica_en_esta_rama() -> None:
    base = subprocess.run(
        ["git", "merge-base", "dev", "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if base.returncode != 0 or not base.stdout.strip():
        pytest.skip("sin rama dev con la que comparar")

    tocados = subprocess.run(
        ["git", "diff", "--name-only", base.stdout.strip(), "HEAD"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    ).stdout.splitlines()

    assert "progress/mutacion_F-034.md" not in tocados, (
        "R25: mutacion_F-034.md ya está remedido a mano y no se toca aquí"
    )
