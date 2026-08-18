# tests/test_f019_r1_r2_r3_semantica_precio_neto.py
"""F-019 · R1-R3: contrato cruzado sobre la semántica de `precio_neto`.

`precio_neto` de una línea de albarán es el **IMPORTE de la línea tras
descuento**, nunca un precio unitario. Esa convención vivía solo en el
prompt de IA1 y en la cabeza de quien lo escribió: en junio de 2026 un
consumidor (el SELECT de sv5) la interpretó al revés, multiplicó el
importe por la cantidad y valoró el albarán Feymaco 2.137.569 —139,66 €
de papel higiénico y bolsas de basura— en 6.238,14 €. Este fichero
convierte esa convención tácita en un **contrato ejecutable** entre sv2
(quien lo escribe), sv5 (quien lo lee) y la documentación normativa.

PARA QUIEN VENGA A CAMBIAR EL PROMPT (F-003 R1/R2 lo tiene planeado):
si `precio_neto` deja de definirse como el importe total de la línea —
por ejemplo porque IA1 pasa a emitir un campo con nombre propio como
`importe_linea`— este test FALLA. No es un test que prohíba el cambio:
es un test que obliga a hacerlo ENTERO. Cámbialo **en el mismo trabajo**
en que reconcilies sv5 (`_SQL_ALBARAN_LINES`) y sv6
(`price_reconciler`), que son los que consumen el campo.

Este test lee ficheros como TEXTO a propósito: no importa paquetes de
sv5 ni de sv6, porque ambos tienen `application`/`domain`/
`infrastructure` de primer nivel y colisionarían en `sys.modules` de la
suite de la raíz. Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]

PROMPTS_IA1 = RAIZ / "services" / "albaranes-api" / "config" / "prompts.yaml"
SETTINGS_SV2 = RAIZ / "services" / "albaranes-api" / "config" / "settings.py"
REPOSITORIO_SV5 = (
    RAIZ / "services" / "albaran-valoracion-api" / "infrastructure"
    / "database" / "sqlalchemy_valuation_context_repository.py"
)
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"

#: Clave del prompt de fase 1 (IA1) por defecto en `config/settings.py`.
CLAVE_PROMPT_IA1 = "albaran_factura_es"


def _normalizar(texto: str) -> str:
    """Colapsa los espacios: el YAML y el SQL parten líneas donde quieren."""
    return re.sub(r"\s+", " ", texto).strip()


def _sql_sin_comentarios() -> str:
    """El fuente de sv5 sin comentarios Python (#) ni SQL (--).

    La prosa de los comentarios EXPLICA la fórmula, así que buscar en
    ella daría verde sin que el SQL hiciera nada. Se compara solo con
    lo que se ejecuta.
    """
    lineas: list[str] = []
    for linea in REPOSITORIO_SV5.read_text(encoding="utf-8").splitlines():
        if linea.lstrip().startswith("#"):
            continue
        lineas.append(linea.split("--")[0])
    return _normalizar("\n".join(lineas))


# --------------------------------------------------------------------- #
# R1 + R2 — quien ESCRIBE el campo: el prompt de IA1
# --------------------------------------------------------------------- #
def test_f019_r1_el_prompt_de_ia1_define_precio_neto_como_importe():
    """`precio_neto` = cantidad*precio*(1 - descuento/100)."""
    prompts = yaml.safe_load(PROMPTS_IA1.read_text(encoding="utf-8"))
    task = _normalizar(prompts[CLAVE_PROMPT_IA1]["task"])

    assert (
        "precio_neto: si figura, léelo; si no, calcula "
        "cantidad*precio*(1 - descuento/100)"
    ) in task, (
        "El prompt de IA1 ha dejado de definir precio_neto como el importe "
        "de la línea. sv5 (_SQL_ALBARAN_LINES) y sv6 (price_reconciler) "
        "consumen ese campo con esa semántica: reconcílialos en este mismo "
        "trabajo (ver F-019 R2)."
    )


def test_f019_r1_el_prompt_de_ia1_define_precio_como_unitario():
    """La otra mitad del contrato: `precio` es el unitario BRUTO."""
    prompts = yaml.safe_load(PROMPTS_IA1.read_text(encoding="utf-8"))
    task = _normalizar(prompts[CLAVE_PROMPT_IA1]["task"])

    assert "- precio: unitario sin IVA." in task
    assert "- descuento: si aparece, como número." in task


def test_f019_r2_la_clave_del_prompt_de_ia1_sigue_siendo_la_vigilada():
    """Si fase 1 pasa a usar otro prompt, este contrato mira al vacío."""
    settings = SETTINGS_SV2.read_text(encoding="utf-8")

    assert re.search(
        r'prompt_key_fase1:\s*str\s*=\s*Field\(\s*"' + CLAVE_PROMPT_IA1 + r'"',
        settings,
    ), (
        "El prompt de fase 1 por defecto ya no es "
        f"{CLAVE_PROMPT_IA1}: actualiza CLAVE_PROMPT_IA1 en este test para "
        "seguir vigilando el prompt que de verdad se usa."
    )


# --------------------------------------------------------------------- #
# R2 — quien LEE el campo: el SELECT de sv5
# --------------------------------------------------------------------- #
def test_f019_r2_el_select_de_sv5_no_multiplica_el_coalesce_por_cantidad():
    """El bug de jun 2026, con nombre y apellidos: `cantidad * COALESCE(`."""
    sql = _sql_sin_comentarios()

    assert "cantidad * COALESCE(" not in sql, (
        "El SELECT de sv5 vuelve a multiplicar por la cantidad un valor que "
        "YA es el importe de la línea (precio_neto). Es el defecto que infló "
        "el albarán Feymaco 2.137.569 de 139,66 € a 6.238,14 €."
    )


def test_f019_r2_el_select_de_sv5_usa_la_formula_canonica():
    """El importe leído manda; si falta, se deriva con la fórmula."""
    sql = _sql_sin_comentarios()

    assert (
        "COALESCE( precio_neto, "
        "cantidad * precio * (1 - COALESCE(descuento, 0) / 100.0) "
        ") AS importe_albaran"
    ) in sql


# --------------------------------------------------------------------- #
# R3 — la semántica queda escrita en la documentación normativa
# --------------------------------------------------------------------- #
def test_f019_r3_architecture_documenta_la_semantica_de_precio_neto():
    """`docs/ARCHITECTURE.md` §Semántica de dominio, regla de F-019."""
    arquitectura = _normalizar(ARQUITECTURA.read_text(encoding="utf-8"))

    assert "`precio_neto` de una línea de albarán es el IMPORTE" in arquitectura
    assert "tras descuento" in arquitectura
    assert (
        "importe = cantidad × precio × (1 − descuento/100)" in arquitectura
    )
    assert "el unitario leído manda" in arquitectura
