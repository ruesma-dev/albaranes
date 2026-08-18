# tests/test_f027_r18_r22_contrato.py
"""F-027 · R18, R22, R23, R24: los límites que la feature se autoimpone.

F-027 corrige un error de tres órdenes de magnitud tocando **una sola
expresión** del `ValuationBuilder`. La tentación de arreglar de paso lo
que hay al lado es exactamente lo que haría imposible saber, en la
prueba local, qué feature produjo cada euro de diferencia. Por eso los
límites son requisitos y este fichero los vigila:

* **R18** — el conversor no se toca. No está mal: estaba desconectado.
* **R22** — no se renombra, añade ni retira ningún motivo de revisión
  (coordinación con **F-025**, que proponía uno nuevo justo en la rama
  que F-027 elimina).
* **R23** — no se toca la elección de línea de contrato (**F-031**: el
  precio 15,43 €/TN en vez de 12,87 sobrevive a esta feature a
  propósito).
* **R24** — no se toca ningún prompt ni ninguna fase de IA. La revisión
  razonada de plausibilidad de IA2 es **F-024** y debe existir
  igualmente: IA2 detecta arriba, sv6 protege abajo.

Este fichero lee los ficheros como TEXTO a propósito: no importa
paquetes de sv5 ni de sv6, porque ambos tienen `application`/`domain`/
`infrastructure` de primer nivel y colisionarían en `sys.modules` de la
suite de la raíz. Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[1]
SV6 = RAIZ / "services" / "albaran-valoracion-persist"
UNIT_CONVERTER = SV6 / "application" / "services" / "unit_converter.py"
VALUATION_BUILDER = SV6 / "application" / "services" / "valuation_builder.py"
PARTIDA_MATCHER = SV6 / "application" / "services" / "partida_matcher.py"
UNIT_REGISTRY_YAML = SV6 / "config" / "unit_registry.yaml"


def _arbol(ruta: Path) -> ast.Module:
    return ast.parse(ruta.read_text(encoding="utf-8"))


def _texto_de(nodo: ast.AST) -> str | None:
    """Devuelve el literal, con `{}` donde hay interpolación."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    if isinstance(nodo, ast.JoinedStr):
        partes = []
        for trozo in nodo.values:
            if isinstance(trozo, ast.Constant) and isinstance(trozo.value, str):
                partes.append(trozo.value)
            else:
                partes.append("{}")
        return "".join(partes)
    return None


def _motivos_de(ruta: Path) -> set[str]:
    """Los motivos que el módulo mete en una lista ``reasons``.

    Se recogen del AST, no por expresión regular: interesa lo que de
    verdad acaba en ``review_reasons``, no cualquier cadena en
    snake_case que aparezca en el fichero.
    """
    encontrados: set[str] = set()
    for nodo in ast.walk(_arbol(ruta)):
        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr == "append"
            and isinstance(nodo.func.value, ast.Name)
            and nodo.func.value.id.endswith("reasons")
            and nodo.args
        ):
            texto = _texto_de(nodo.args[0])
            if texto:
                encontrados.add(texto)
        if (
            isinstance(nodo, ast.keyword)
            and nodo.arg == "reasons"
            and isinstance(nodo.value, ast.List)
        ):
            for elemento in nodo.value.elts:
                texto = _texto_de(elemento)
                if texto:
                    encontrados.add(texto)
        if isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            objetivos = (
                nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
            )
            for objetivo in objetivos:
                if (
                    isinstance(objetivo, ast.Name)
                    and objetivo.id.endswith("reasons")
                    and isinstance(nodo.value, ast.List)
                ):
                    for elemento in nodo.value.elts:
                        texto = _texto_de(elemento)
                        if texto:
                            encontrados.add(texto)
    return encontrados


# --------------------------------------------------------------------- #
# R18 — el conversor no se toca
# --------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "constante, valor",
    [("_TN_UMBRAL_CONVERTIR", 1000.0), ("_TN_UMBRAL_AVISAR", 100.0)],
)
def test_f027_r18_los_umbrales_de_la_red_de_toneladas_no_cambian(
    constante, valor,
):
    """Los dos umbrales, con su valor exacto.

    Cambiarlos es legítimo —son la decisión D3 y además son parámetros
    del constructor de ``UnitConverter``, así que se pueden ajustar sin
    tocar código— pero tiene que ser una decisión, no un descuido: este
    test obliga a pasar por aquí.
    """
    asignaciones = {
        objetivo.id: nodo.value.value
        for nodo in ast.walk(_arbol(UNIT_CONVERTER))
        if isinstance(nodo, ast.Assign)
        for objetivo in nodo.targets
        if isinstance(objetivo, ast.Name)
        and isinstance(nodo.value, ast.Constant)
    }

    assert asignaciones[constante] == valor


def test_f027_r18_la_firma_publica_de_convert_no_cambia():
    """``convert(*, cantidad, unidad_albaran, unidad_contrato)``.

    La opción C del diseño —pasarle ``category_match`` al conversor para
    que decidiera qué redes aplica— se descartó porque ampliaba este
    contrato para expresar algo que el conversor ya sabe decir solo.
    """
    convert = next(
        nodo
        for nodo in ast.walk(_arbol(UNIT_CONVERTER))
        if isinstance(nodo, ast.FunctionDef) and nodo.name == "convert"
    )

    assert [a.arg for a in convert.args.args] == ["self"]
    assert [a.arg for a in convert.args.kwonlyargs] == [
        "cantidad", "unidad_albaran", "unidad_contrato",
    ]


def test_f027_r18_la_categoria_mass_del_registro_de_unidades_no_cambia():
    """El factor de la tonelada es lo que hace que 30.380 kg sean 30,38 TN.

    ``config/unit_registry.yaml`` es además ruta sensible por sí misma
    (``harness/rutas_sensibles.json``): no hay ningún motivo para que
    F-027 la toque, y este test lo deja fijado.
    """
    registro = yaml.safe_load(UNIT_REGISTRY_YAML.read_text(encoding="utf-8"))
    mass = registro["categories"]["mass"]

    assert mass["base"] == "kg"
    assert mass["units"] == {
        "kg": 1.0, "kgs": 1.0, "kilo": 1.0, "kilos": 1.0,
        "kilogramo": 1.0, "kilogramos": 1.0,
        "g": 0.001, "gr": 0.001, "grs": 0.001,
        "gramo": 0.001, "gramos": 0.001,
        "t": 1000.0, "tn": 1000.0, "tm": 1000.0,
        "ton": 1000.0, "tons": 1000.0,
        "tonelada": 1000.0, "toneladas": 1000.0,
    }


# --------------------------------------------------------------------- #
# R22 — ni un motivo de más, ni uno de menos
# --------------------------------------------------------------------- #

#: Inventario CONGELADO de motivos del builder, tal como estaba antes de
#: F-027. Cambiarlo es legítimo en features futuras —añadir un motivo es
#: normal— pero exige tocar esta lista, y eso obliga a comprobar quién
#: consume el string en sv6 y en el pintado de sv4.
MOTIVOS_DEL_BUILDER = {
    "at_least_one_line_requires_review",
    "descuento_heredado_aplicado:{}%",
    "horas_descarga_incompletas",
    "ia_no_match",
    "lines_without_match:{}",
    "modifier_derived_partida_distinta",
    "modifier_identified_no_tariff",
    "modifier_not_in_contract",
    "movimiento_residuos_sin_cantidad_asumido_1",
    "synthetic_parent_not_in_context",
    "synthetic_without_parent",
}

#: Ídem para el conversor. Los cuatro de la tabla de R19 salen de aquí.
MOTIVOS_DEL_CONVERSOR = {
    "ambiguous_unit_conversion",
    "cantidad_sin_unidad_reinterpretada_kg_a_tn",
    "cantidad_tn_implausible_revisar",
    "no_albaran_unit_assumed_same",
    "no_contract_unit_assumed_same",
    "no_quantity_in_albaran",
    "unit_category_mismatch_in_conversion",
}


def test_f027_r22_el_builder_no_introduce_ni_retira_motivos():
    """F-027 corrige el VALOR que se escribe, no el vocabulario.

    Coordinación con **F-025**: esa feature proponía emitir
    ``conversion_skipped_unit_category_mismatch`` en la rama ``else``
    que F-027 elimina. Al no quedar conversión omitida a propósito,
    F-025 se queda sin su caso principal y su alcance lo reevalúa el
    humano antes de arrancarla.
    """
    assert _motivos_de(VALUATION_BUILDER) == MOTIVOS_DEL_BUILDER


def test_f027_r22_el_conversor_no_introduce_ni_retira_motivos():
    assert _motivos_de(UNIT_CONVERTER) == MOTIVOS_DEL_CONVERSOR


def test_f027_r19_los_cuatro_motivos_de_la_tabla_existen_en_el_conversor():
    """Los cuatro estados que el revisor debe poder distinguir.

    No son motivos nuevos: ya existían. Lo que F-027 arregla es que
    lleguen a la línea.
    """
    assert {
        "cantidad_sin_unidad_reinterpretada_kg_a_tn",
        "cantidad_tn_implausible_revisar",
        "unit_category_mismatch_in_conversion",
        "no_quantity_in_albaran",
    } <= MOTIVOS_DEL_CONVERSOR


# --------------------------------------------------------------------- #
# R23 — la elección de línea de contrato es de F-031
# --------------------------------------------------------------------- #

def test_f027_r23_el_matcher_sigue_dando_a_la_derivada_la_unidad_del_contrato():
    """La premisa de la que depende R6, fijada donde vive.

    ``_build_derived`` inicializa la unidad con la del albarán y la pisa
    con la de la línea de contrato casada por la IA siempre que exista.
    Eso es lo que convierte a la derivada en «la línea que pone el
    precio», y por tanto en la que fija la unidad de destino. Si alguien
    lo cambia, R6 y R7 dejan de hablar del mismo caso y este test lo
    dice **en el fichero que se cambió**, no tres capas más abajo.
    """
    codigo = PARTIDA_MATCHER.read_text(encoding="utf-8")

    assert "unidad: str | None = unidad_albaran" in codigo
    assert "unidad = ia_line.unidad_medida or unidad" in codigo


# --------------------------------------------------------------------- #
# R23, R24 — qué ficheros ha tocado F-027, medido sobre git
# --------------------------------------------------------------------- #

#: Rutas que la feature declara NO tocar. `partida_matcher.py` es F-031;
#: los prompts son F-024 y además ruta sensible (dispararían la puerta de
#: evals sobre prompts sin necesidad).
PROHIBIDAS = (
    "services/albaran-valoracion-persist/application/services/partida_matcher.py",
)


def _ficheros_tocados_por_f027() -> set[str] | None:
    """Ficheros de los commits ``F-027 ...`` alcanzables desde HEAD.

    Se acota a los commits DE ESTA FEATURE (por prefijo del mensaje) y
    no a un diff contra `dev`: así el test sigue diciendo la verdad
    después del merge y no se rompe cuando una feature posterior toque
    legítimamente `partida_matcher.py`.
    """
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=RAIZ, capture_output=True, text=True,
            check=True,
        ).stdout

    try:
        commits = git(
            "log", "--format=%H", "--grep=^F-027", "HEAD",
        ).split()
    except (OSError, subprocess.CalledProcessError):
        return None
    if not commits:
        return None

    tocados: set[str] = set()
    for commit in commits:
        salida = git(
            "show", "--pretty=format:", "--name-only", "--no-renames", commit,
        )
        tocados.update(linea for linea in salida.splitlines() if linea.strip())
    return tocados


def test_f027_r23_r24_la_feature_no_toca_ni_el_matcher_ni_ningun_prompt():
    """R23 y R24, medidos sobre los commits reales de la feature.

    Mezclar F-027 con F-031 o con F-024 haría imposible saber cuál de
    las tres produjo cada euro de diferencia en la prueba local. Ese es
    el motivo, y no la pureza.
    """
    tocados = _ficheros_tocados_por_f027()
    if tocados is None:
        pytest.skip(
            "sin historia git de F-027 alcanzable desde HEAD "
            "(export sin .git o rama sin los commits de la feature)"
        )

    for prohibida in PROHIBIDAS:
        assert prohibida not in tocados, f"R23: F-027 tocó {prohibida}"

    prompts = [
        fichero for fichero in tocados
        if "prompts" in fichero and fichero.endswith((".yaml", ".yml"))
    ]
    assert prompts == [], f"R24: F-027 tocó prompts de IA: {prompts}"

    # La feature es de sv6: ningún fichero de código de otro servicio.
    otros_servicios = [
        fichero for fichero in tocados
        if fichero.startswith("services/")
        and not fichero.startswith("services/albaran-valoracion-persist/")
    ]
    assert otros_servicios == [], (
        f"F-027 declara tocar solo sv6, y tocó: {otros_servicios}"
    )
