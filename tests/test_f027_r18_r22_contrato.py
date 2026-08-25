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


def _texto_de(nodo: ast.AST, tabla: dict[str, str] | None = None) -> str | None:
    """Devuelve el literal, con `{}` donde hay interpolación.

    ``tabla`` resuelve además los nombres de CONSTANTE: sin ella,
    ``reasons.append(RAZON_SIN_TARIFA)`` es un ``ast.Name`` y el motivo
    se cuela sin pasar por la congelación. Fue un agujero real: F-036
    metió `residuos_ler_sin_tarifa_en_contrato` sin tocar
    ``MOTIVOS_DEL_BUILDER`` y el test siguió en verde.
    """
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    if isinstance(nodo, ast.Name) and tabla:
        return tabla.get(nodo.id)
    if isinstance(nodo, ast.JoinedStr):
        partes = []
        for trozo in nodo.values:
            if isinstance(trozo, ast.Constant) and isinstance(trozo.value, str):
                partes.append(trozo.value)
            else:
                partes.append("{}")
        return "".join(partes)
    return None


def _constantes_str(ruta: Path) -> dict[str, str]:
    """Constantes de módulo cuyo valor es una cadena literal."""
    constantes: dict[str, str] = {}
    for nodo in _arbol(ruta).body:  # solo nivel de módulo
        if not isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            continue
        if nodo.value is None:
            continue
        texto = _texto_de(nodo.value)
        if texto is None:
            continue
        objetivos = (
            nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
        )
        for objetivo in objetivos:
            if isinstance(objetivo, ast.Name):
                constantes[objetivo.id] = texto
    return constantes


def _tabla_de_simbolos(ruta: Path) -> dict[str, str]:
    """Constantes visibles en el módulo: las propias y las importadas.

    Se sigue el ``from application.services.X import CONST`` hasta el
    fichero de sv6 y se lee su constante. Solo imports absolutos que
    resuelvan a un fichero del servicio; lo que no resuelva (paquetes
    externos, ``ruesma_comun``) simplemente no aporta símbolos.
    """
    tabla = _constantes_str(ruta)
    for nodo in _arbol(ruta).body:
        if not isinstance(nodo, ast.ImportFrom) or not nodo.module:
            continue
        if nodo.level:  # import relativo: no se usa en sv6
            continue
        origen = SV6.joinpath(*nodo.module.split(".")).with_suffix(".py")
        if not origen.is_file():
            continue
        del_origen = _constantes_str(origen)
        for alias in nodo.names:
            if alias.name in del_origen:
                tabla[alias.asname or alias.name] = del_origen[alias.name]
    return tabla


def _alias_de_modulo(ruta: Path) -> dict[str, Path]:
    """Alias con los que el módulo nombra OTROS módulos de sv6.

    Cubre ``from application.services import residuos_incrementos as ri``
    e ``import application.services.residuos_incrementos as ri``, para
    poder resolver ``ri.RAZON_SIN_TARIFA``. Lo que no resuelva a un
    fichero del servicio no entra: un ``res.reason`` cualquiera no es
    una constante de módulo, es un valor de tiempo de ejecución.
    """
    alias: dict[str, Path] = {}
    for nodo in _arbol(ruta).body:
        if isinstance(nodo, ast.ImportFrom):
            if not nodo.module or nodo.level:
                continue
            for nombre in nodo.names:
                fichero = SV6.joinpath(
                    *nodo.module.split("."), nombre.name,
                ).with_suffix(".py")
                if fichero.is_file():
                    alias[nombre.asname or nombre.name] = fichero
        elif isinstance(nodo, ast.Import):
            for nombre in nodo.names:
                fichero = SV6.joinpath(
                    *nombre.name.split("."),
                ).with_suffix(".py")
                if fichero.is_file() and nombre.asname:
                    alias[nombre.asname] = fichero
    return alias


class MotivoIlegible(AssertionError):
    """El analizador encontró un ``reasons`` que no sabe leer.

    Es `AssertionError` a propósito: un motivo que no se puede resolver
    invalida la congelación entera, así que tiene que romper el test que
    la ejecuta, no aparecer como error de infraestructura.
    """


def _exigir_texto(
    nodo: ast.AST,
    tabla: dict[str, str],
    alias: dict[str, Path],
    ruta: Path,
    forma: str,
    admite_propagacion: bool = False,
) -> str | None:
    """El literal del nodo, ``None`` si es propagación, o REVIENTA.

    El silencio es lo único que no vale: un motivo que el analizador no
    sabe resolver se cuela en el vocabulario sin pasar por la lista
    congelada, y el test sigue verde. Pasó de verdad en F-036 con una
    constante importada.

    ``admite_propagacion`` solo vale cuando el nodo es el valor ENTERO
    que se añade (``reasons.append(result.reason)``): ahí el motivo lo
    escribe otro módulo y lo congela el test de ese módulo. Dentro de
    una lista literal —que es el módulo escribiendo su vocabulario— no
    hay excusa: cada elemento tiene que resolverse.
    """
    texto = _texto_de(nodo, tabla)
    if texto is not None:
        return texto
    if isinstance(nodo, ast.Attribute) and isinstance(nodo.value, ast.Name):
        origen = alias.get(nodo.value.id)
        if origen is not None:
            del_origen = _constantes_str(origen)
            if nodo.attr in del_origen:
                return del_origen[nodo.attr]
        elif admite_propagacion:
            return None  # atributo de un objeto: propagación
    raise MotivoIlegible(
        f"{ruta.name}:{getattr(nodo, 'lineno', '?')} · {forma}: el "
        f"analizador de motivos no sabe resolver un "
        f"{type(nodo).__name__} a un literal — {ast.unparse(nodo)!r}. "
        "Si es un motivo nuevo, escríbelo como literal o como constante "
        "de módulo de sv6 y añádelo a la lista congelada; si son motivos "
        "que llegan de otro módulo, propágalos con `reasons.extend(...)` "
        "sobre el valor entero, no elemento a elemento."
    )


def _recoger(
    destino: set[str],
    nodo: ast.AST,
    tabla: dict[str, str],
    alias: dict[str, Path],
    ruta: Path,
    forma: str,
    admite_propagacion: bool = False,
) -> None:
    texto = _exigir_texto(
        nodo, tabla, alias, ruta, forma, admite_propagacion,
    )
    if texto:
        destino.add(texto)


#: Métodos de lista que meten motivos en un ``reasons``. ``extend`` e
#: ``insert`` no se usan hoy con literales en sv6, pero saltárselos era
#: la forma más barata de meter un motivo sin pasar por la congelación.
_METODOS_QUE_ANADEN = {"append": 0, "insert": 1, "extend": 0}


def _motivos_de(ruta: Path) -> set[str]:
    """Los motivos que el módulo mete en una lista ``reasons``.

    Se recogen del AST, no por expresión regular: interesa lo que de
    verdad acaba en ``review_reasons``, no cualquier cadena en
    snake_case que aparezca en el fichero. Los nombres de constante se
    resuelven a su valor (ver ``_texto_de``) y los atributos de un
    módulo de sv6 (``ri.RAZON_X``) siguiendo el import.

    Ante una forma que NO sabe resolver, **revienta** con
    ``MotivoIlegible`` diciendo cuál y dónde. Ver el bloque de tests
    «El portero del portero» al final de este fichero.
    """
    encontrados: set[str] = set()
    tabla = _tabla_de_simbolos(ruta)
    alias = _alias_de_modulo(ruta)
    for nodo in ast.walk(_arbol(ruta)):
        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr in _METODOS_QUE_ANADEN
            and isinstance(nodo.func.value, ast.Name)
            and nodo.func.value.id.endswith("reasons")
        ):
            metodo = nodo.func.attr
            posicion = _METODOS_QUE_ANADEN[metodo]
            forma = f"{nodo.func.value.id}.{metodo}(...)"
            if len(nodo.args) <= posicion:
                raise MotivoIlegible(
                    f"{ruta.name}:{nodo.lineno} · {forma}: llamada sin el "
                    f"argumento {posicion} del que sale el motivo."
                )
            valor = nodo.args[posicion]
            if metodo == "extend":
                # `extend(otra_lista)` es propagación; `extend([...])`
                # es vocabulario propio y se mira elemento a elemento.
                if isinstance(valor, (ast.List, ast.Tuple, ast.Set)):
                    for elemento in valor.elts:
                        _recoger(encontrados, elemento, tabla, alias, ruta, forma)
                continue
            _recoger(
                encontrados, valor, tabla, alias, ruta, forma,
                admite_propagacion=True,
            )
        if (
            isinstance(nodo, ast.keyword)
            and nodo.arg == "reasons"
            and isinstance(nodo.value, ast.List)
        ):
            for elemento in nodo.value.elts:
                _recoger(
                    encontrados, elemento, tabla, alias, ruta, "reasons=[...]",
                )
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
                        _recoger(
                            encontrados, elemento, tabla, alias, ruta,
                            f"{objetivo.id} = [...]",
                        )
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
    # (ago 2026 · F-036 R15, T15) La guarda anti-incremento: una línea
    # BASE de residuos casada con la tarifa de un INCREMENTO por LER
    # pierde el match y va a revisión. Motivo NUEVO, añadido aquí a
    # conciencia y no para callar el test. Consumidores comprobados:
    # sv6 solo lo escribe; sv4 pinta las razones de línea en crudo
    # desde `review_reasons_json` (F-036 R23), sin lista blanca de
    # cadenas que haya que ampliar.
    "residuos_base_casada_con_incremento",
    # (ago 2026 · F-036 R17 y R19, correcciones de la review B/C/D) Los
    # dos motivos de las SINTETICAS de residuos. Se escriben desde
    # constantes de `residuos_incrementos` (`RAZON_SIN_TARIFA`,
    # `RAZON_SIN_CANTIDAD`), y hasta que `_motivos_de` resolvió nombres
    # el primero llevaba ya un bloque entero sin pasar por esta lista.
    # Consumidores comprobados, mismo criterio que en el de R15: sv6
    # solo los escribe; sv4 pinta `review_reasons_json` en crudo
    # (`services/albaranes-front/tests/test_f036_r23_r24_trazabilidad.py`
    # afirma la cadena sobre el HTML), sin lista blanca que ampliar.
    "residuos_ler_sin_tarifa_en_contrato",
    "residuos_sintetica_sin_cantidad",
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


def test_f027_r22_la_congelacion_ve_los_motivos_escritos_como_constante():
    """El guardián del guardián: la resolución de nombres funciona.

    Sin esto, la congelación vuelve a ser una lista que solo mira
    literales y cualquier motivo escrito como constante importada entra
    sin pasar por ella. Pasó de verdad con
    ``residuos_ler_sin_tarifa_en_contrato`` en F-036, y el test siguió
    en verde una feature entera.
    """
    tabla = _tabla_de_simbolos(VALUATION_BUILDER)

    # Importada de `application.services.residuos_incrementos`.
    assert tabla["RAZON_SIN_TARIFA"] == "residuos_ler_sin_tarifa_en_contrato"
    assert tabla["RAZON_SIN_CANTIDAD"] == "residuos_sintetica_sin_cantidad"
    assert {
        "residuos_ler_sin_tarifa_en_contrato",
        "residuos_sintetica_sin_cantidad",
    } <= _motivos_de(VALUATION_BUILDER)


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


# --------------------------------------------------------------------- #
# El portero del portero: `_motivos_de` no puede callarse lo que no lee
# --------------------------------------------------------------------- #
#
# (ago 2026 · F-036, review de la pasada 2) La congelación de motivos
# vale lo que valga el analizador que la alimenta. Hasta aquí, ante un
# `reasons.append(<algo que no sabía resolver>)` se lo saltaba EN
# SILENCIO: el motivo no entraba en el conjunto, la comparación con
# `MOTIVOS_DEL_BUILDER` seguía cuadrando y la congelación decía «todo
# en orden» sobre un vocabulario que no había visto entero. Ya pasó una
# vez con `residuos_ler_sin_tarifa_en_contrato` (constante importada) y
# el test aguantó verde una feature completa.
#
# Las formas de abajo NO se usan hoy en sv6: esto es preventivo. Lo que
# se fija es que el analizador falle A GRITOS —diciendo qué forma vio y
# dónde— en vez de encogerse de hombros.

def _modulo(tmp_path, cuerpo: str, nombre: str = "sonda.py") -> Path:
    ruta = tmp_path / nombre
    ruta.write_text(cuerpo, encoding="utf-8")
    return ruta


#: Formas que el analizador NO sabe resolver a un literal. Todas deben
#: reventar; ninguna puede colarse en silencio.
ILEGIBLES = {
    "constante_de_fuera_de_sv6": (
        "from ruesma_comun.ler import RAZON_QUE_VIVE_FUERA\n"
        "def f(reasons):\n"
        "    reasons.append(RAZON_QUE_VIVE_FUERA)\n"
    ),
    "local_de_funcion": (
        "def f(reasons):\n"
        "    motivo = 'inventado_aqui'\n"
        "    reasons.append(motivo)\n"
    ),
    "atributo_de_modulo_inexistente": (
        "from application.services import residuos_incrementos as ri\n"
        "def f(reasons):\n"
        "    reasons.append(ri.RAZON_QUE_NO_EXISTE)\n"
    ),
    "llamada": (
        "def f(reasons):\n"
        "    reasons.append(_calcular_motivo())\n"
    ),
    "extend_con_lista_ilegible": (
        "def f(reasons, otro):\n"
        "    reasons.extend([otro.motivo_raro])\n"
    ),
    "insert_ilegible": (
        "def f(reasons, motivo):\n"
        "    reasons.insert(0, motivo)\n"
    ),
    "lista_literal_ilegible": (
        "def f(cualquier_cosa):\n"
        "    reasons = [cualquier_cosa]\n"
        "    return reasons\n"
    ),
    "keyword_reasons_ilegible": (
        "def f(cualquier_cosa):\n"
        "    return Resultado(reasons=[cualquier_cosa])\n"
    ),
}


@pytest.mark.parametrize("forma", sorted(ILEGIBLES))
def test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer(
    tmp_path, forma,
):
    """Un portero que calla ante lo que no entiende es decorado."""
    ruta = _modulo(tmp_path, ILEGIBLES[forma])

    with pytest.raises(AssertionError):
        _motivos_de(ruta)


@pytest.mark.parametrize("forma", sorted(ILEGIBLES))
def test_f027_r22_el_fallo_dice_QUE_forma_vio_y_DONDE(tmp_path, forma):
    """Sin el sitio y la forma, el fallo obliga a buscar a ciegas."""
    ruta = _modulo(tmp_path, ILEGIBLES[forma])

    with pytest.raises(AssertionError) as fallo:
        _motivos_de(ruta)

    mensaje = str(fallo.value)
    assert "sonda.py" in mensaje, mensaje
    # El número de línea del `reasons` ofensor (siempre la última del
    # cuerpo salvo en la forma con `return`).
    assert any(f":{n}" in mensaje for n in (2, 3, 4)), mensaje
    assert "reasons" in mensaje, mensaje


#: Formas que SÍ sabe leer, con lo que tiene que sacar de cada una.
LEGIBLES = {
    "append_literal": (
        "def f(reasons):\n    reasons.append('motivo_a')\n",
        {"motivo_a"},
    ),
    "extend_lista_de_literales": (
        "def f(reasons):\n    reasons.extend(['motivo_a', 'motivo_b'])\n",
        {"motivo_a", "motivo_b"},
    ),
    "insert_literal": (
        "def f(reasons):\n    reasons.insert(0, 'motivo_a')\n",
        {"motivo_a"},
    ),
    "atributo_de_modulo_resuelto": (
        "from application.services import residuos_incrementos as ri\n"
        "def f(reasons):\n"
        "    reasons.append(ri.RAZON_SIN_TARIFA)\n",
        {"residuos_ler_sin_tarifa_en_contrato"},
    ),
}


@pytest.mark.parametrize("forma", sorted(LEGIBLES))
def test_f027_r22_lo_que_sabe_leer_lo_recoge_entero(tmp_path, forma):
    """`extend` e `insert` cuentan igual que `append`: acaban en la lista."""
    cuerpo, esperado = LEGIBLES[forma]

    assert _motivos_de(_modulo(tmp_path, cuerpo)) == esperado


#: Formas que NO son vocabulario de este módulo, sino motivos que le
#: llegan ya hechos de otro sitio (`guard_reasons`, `result.reason`...).
#: Ni se recogen ni revientan: los congela el test de SU módulo.
PROPAGACIONES = {
    "extend_de_otra_lista": "def f(reasons, otras):\n    reasons.extend(otras)\n",
    "extend_de_un_atributo": (
        "def f(reasons, res):\n    reasons.extend(res.reasons)\n"
    ),
    "append_de_un_atributo_de_objeto": (
        "def f(reasons, res):\n    reasons.append(res.reason)\n"
    ),
    "asignacion_no_literal": (
        "def f(otro):\n    reasons = list(otro.reasons)\n    return reasons\n"
    ),
}


@pytest.mark.parametrize("forma", sorted(PROPAGACIONES))
def test_f027_r22_los_motivos_que_llegan_de_otro_modulo_no_son_de_este(
    tmp_path, forma,
):
    """`reasons.append(result.reason)` existe hoy en el conversor.

    No es vocabulario del conversor: es el motivo que le devuelve el
    `UnitRegistry`. Ni entra en la congelación de este fichero ni puede
    reventar el análisis — lo congela el test del módulo que lo escribe.
    """
    assert _motivos_de(_modulo(tmp_path, PROPAGACIONES[forma])) == set()
