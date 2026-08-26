# tests/test_f043_familias.py
"""F-043 · el catalogo de familias de albaran vive en UN solo sitio.

Decision del humano del 2026-08-25: **la clasificacion la hace SIEMPRE la
IA**. Este catalogo es lo que la IA lee para decidir (definicion, en que se
diferencia de sus vecinas y que senales mirar) y lo que el pipeline consulta
despues para enrutar prompts. No contiene NINGUNA regla que infiera la
familia a partir del texto, del codigo LER o del CIF: eso esta prohibido.

Cubre R1-R5 (catalogo, familias derivadas, render y enrutado de prompts).
Funciones puras: sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ruesma_comun.contratos import familias as cat


# ------------------------------------------------------------------ #
# R1 · el catalogo existe y cada entrada trae los ocho campos
# ------------------------------------------------------------------ #
def test_f043_r1_catalogo_cada_familia_trae_los_ocho_campos():
    """Cada `Familia` declara id, nombre, definicion, no_es, senales,
    alcance y las dos claves de prompt."""
    assert len(cat.CATALOGO) >= 4

    for familia in cat.CATALOGO:
        assert familia.id and familia.id == familia.id.strip().lower()
        assert familia.nombre.strip()
        assert familia.definicion.strip()
        assert familia.no_es.strip()
        assert familia.senales.strip()
        assert familia.alcance <= {cat.ALCANCE_DOCUMENTO, cat.ALCANCE_LINEA}
        assert familia.alcance, f"{familia.id} sin alcance"
        # Las claves de prompt son opcionales, pero si estan, son texto.
        assert familia.prompt_fase2 is None or familia.prompt_fase2.strip()
        assert (
            familia.prompt_valoracion is None
            or familia.prompt_valoracion.strip()
        )


def test_f043_r1_catalogo_sin_ids_repetidos():
    """Dos entradas con el mismo id harian ambiguo el enrutado."""
    ids = [f.id for f in cat.CATALOGO]
    assert len(ids) == len(set(ids))


def test_f043_r1_catalogo_es_inmutable():
    """El catalogo es una tupla de dataclases congeladas: nadie lo parchea
    en caliente desde un servicio para 'arreglar' una clasificacion."""
    assert isinstance(cat.CATALOGO, tuple)
    with pytest.raises(Exception):
        cat.CATALOGO[0].id = "otra_cosa"  # type: ignore[misc]


# ------------------------------------------------------------------ #
# R2 · las familias validas se DERIVAN del catalogo
# ------------------------------------------------------------------ #
def test_f043_r2_catalogo_familias_documento_son_las_cuatro_con_prompt():
    """Duda 1 resuelta por el humano (2026-08-26): arranca con las cuatro
    familias de documento que HOY tienen prompt de fase 2 propio."""
    assert cat.familias_documento() == (
        "generico",
        "hormigon",
        "mortero",
        "residuos",
    )


def test_f043_r2_catalogo_familias_linea_incluyen_las_de_solo_linea():
    """`combustible`, `alquiler_maquinaria` y `otro` son familia de LINEA y
    NO son clasificacion de documento: no hay prompt al que enrutarlas."""
    de_linea = cat.familias_linea()

    assert "combustible" in de_linea
    assert "alquiler_maquinaria" in de_linea
    assert "otro" in de_linea
    for solo_linea in ("combustible", "alquiler_maquinaria", "otro"):
        assert solo_linea not in cat.familias_documento()


def test_f043_r2_catalogo_las_listas_se_derivan_no_se_declaran():
    """Nada de listas paralelas: ambas salen de recorrer el catalogo."""
    esperado_doc = tuple(
        f.id for f in cat.CATALOGO if cat.ALCANCE_DOCUMENTO in f.alcance
    )
    esperado_linea = tuple(
        f.id for f in cat.CATALOGO if cat.ALCANCE_LINEA in f.alcance
    )

    assert cat.familias_documento() == esperado_doc
    assert cat.familias_linea() == esperado_linea


def test_f043_r2_catalogo_obtener_devuelve_la_familia_o_none():
    """`obtener` es la unica puerta de consulta; fuera de catalogo, None."""
    hormigon = cat.obtener("hormigon")

    assert hormigon is not None
    assert hormigon.id == "hormigon"
    assert cat.obtener("familia_que_no_existe") is None
    assert cat.obtener("") is None
    assert cat.obtener(None) is None


def test_f043_r2_catalogo_obtener_normaliza_mayusculas_y_espacios():
    """La IA puede devolver ' Hormigon '; el catalogo no se rompe por eso."""
    assert cat.obtener("  HORMIGON  ") is cat.obtener("hormigon")


# ------------------------------------------------------------------ #
# R3 · anadir una familia = una entrada aqui
# ------------------------------------------------------------------ #
def test_f043_r3_catalogo_una_familia_nueva_se_enruta_sin_tocar_servicios(
    monkeypatch,
):
    """CUANDO se anade una familia con sus dos claves de prompt, queda
    enrutada en fase 2 y en valoracion sin modificar codigo de sv2/sv5/sv6.

    Se simula la alta anadiendo la entrada al catalogo: si el enrutado
    consultase una tabla propia en cada servicio, esto no bastaria.
    """
    bombeo = cat.Familia(
        id="bombeo",
        nombre="Bombeo",
        definicion="Servicio de bombeo de hormigon con rendimiento minimo.",
        no_es="No es el suministro del hormigon, es el servicio de bombeo.",
        senales="Metros bombeados, rendimiento minimo, hora de bomba.",
        alcance=frozenset({cat.ALCANCE_DOCUMENTO, cat.ALCANCE_LINEA}),
        prompt_fase2="albaran_revision_fase2_bombeo",
        prompt_valoracion="valuation_bombeo",
    )
    monkeypatch.setattr(cat, "CATALOGO", cat.CATALOGO + (bombeo,))

    assert "bombeo" in cat.familias_documento()
    assert "bombeo" in cat.familias_linea()
    assert cat.prompt_fase2_de("bombeo") == "albaran_revision_fase2_bombeo"
    assert cat.prompt_valoracion_de("bombeo") == "valuation_bombeo"
    assert "`bombeo`" in cat.render_catalogo_markdown(cat.ALCANCE_DOCUMENTO)


# ------------------------------------------------------------------ #
# R4 · `generico` es una CLASE LEGITIMA, no el cajon de sastre
# ------------------------------------------------------------------ #
def test_f043_r4_catalogo_generico_es_clase_legitima_con_definicion_propia():
    generico = cat.obtener("generico")

    assert generico is not None
    assert "generico" in cat.familias_documento()
    # Definicion POSITIVA: suministro de materiales o productos.
    definicion = generico.definicion.lower()
    assert "suministro" in definicion
    assert "material" in definicion or "producto" in definicion


def test_f043_r4_catalogo_generico_se_distingue_de_no_se_pudo_clasificar():
    """La duda NO se expresa eligiendo 'generico', se expresa bajando
    `confianza_pct`. El `no_es` tiene que decirlo con todas las letras."""
    generico = cat.obtener("generico")
    assert generico is not None

    no_es = generico.no_es.lower()
    assert "confianza_pct" in no_es
    assert "clasificar" in no_es or "duda" in no_es


# ------------------------------------------------------------------ #
# R5 · las dos parejas que hoy se confunden, separadas por definicion
# ------------------------------------------------------------------ #
def test_f043_r5_catalogo_hormigon_y_mortero_se_distinguen_entre_si():
    hormigon = cat.obtener("hormigon")
    mortero = cat.obtener("mortero")
    assert hormigon is not None and mortero is not None

    assert "mortero" in hormigon.no_es.lower()
    assert "hormigon" in mortero.no_es.lower()


def test_f043_r5_catalogo_residuos_no_es_transporte_ni_alquiler_de_contenedor():
    """Residuos = alguien se hace cargo del residuo. Poner un contenedor o
    mover material de un sitio a otro NO es residuos."""
    residuos = cat.obtener("residuos")
    assert residuos is not None

    no_es = residuos.no_es.lower()
    assert "transporte" in no_es
    assert "contenedor" in no_es
    assert "gestion" in no_es or "gestor" in no_es


# ------------------------------------------------------------------ #
# R1/R6 · el render que se inyecta en el prompt de fase 1
# ------------------------------------------------------------------ #
def test_f043_r1_render_documento_trae_las_cuatro_familias_de_documento():
    """Se busca el id ENTRECOMILLADO (`otro`) y no la palabra suelta: 'otro'
    es ademas una palabra corriente del castellano y aparece dentro de las
    definiciones."""
    texto = cat.render_catalogo_markdown(cat.ALCANCE_DOCUMENTO)

    for esperada in cat.familias_documento():
        assert f"`{esperada}`" in texto
    for solo_linea in ("combustible", "alquiler_maquinaria", "otro"):
        assert f"`{solo_linea}`" not in texto


def test_f043_r1_render_incluye_definicion_diferencia_y_senales():
    """El prompt necesita las tres cosas: que ES, en que se DIFERENCIA y
    que SENALES mirar. Sin el 'no_es' vuelven a confundirse las vecinas."""
    texto = cat.render_catalogo_markdown(cat.ALCANCE_DOCUMENTO)
    residuos = cat.obtener("residuos")
    assert residuos is not None

    assert residuos.definicion in texto
    assert residuos.no_es in texto
    assert residuos.senales in texto


def test_f043_r1_render_por_defecto_es_el_de_documento():
    assert cat.render_catalogo_markdown() == cat.render_catalogo_markdown(
        cat.ALCANCE_DOCUMENTO
    )


def test_f043_r2_render_de_linea_trae_las_familias_de_linea():
    texto = cat.render_catalogo_markdown(cat.ALCANCE_LINEA)

    for esperada in cat.familias_linea():
        assert f"`{esperada}`" in texto


def test_f043_r1_render_con_alcance_desconocido_falla_a_la_cara():
    """Un alcance mal escrito devolveria un prompt vacio en silencio."""
    with pytest.raises(ValueError):
        cat.render_catalogo_markdown("pagina")


# ------------------------------------------------------------------ #
# R3/R15/R24 · enrutado de prompts POR CONSULTA AL CATALOGO
# ------------------------------------------------------------------ #
def test_f043_r3_prompt_fase2_sale_del_catalogo():
    assert cat.prompt_fase2_de("hormigon") == "albaran_revision_fase2_hormigon"
    assert cat.prompt_fase2_de("mortero") == "albaran_revision_fase2_mortero"
    assert cat.prompt_fase2_de("residuos") == "albaran_revision_fase2_residuos"


def test_f043_r3_prompt_valoracion_sale_del_catalogo():
    assert cat.prompt_valoracion_de("residuos") == "valuation_residuos"


def test_f043_r15_prompt_sin_clave_registrada_devuelve_none_para_caer_al_generico():
    """`generico` no tiene prompt propio: cae al generico configurado en el
    servicio (fase 2 `albaran_revision_fase2_es`, valoracion `valuation_es`).
    Una familia fuera de catalogo tambien devuelve None: nunca revienta."""
    assert cat.prompt_fase2_de("generico") is None
    assert cat.prompt_valoracion_de("generico") is None
    assert cat.prompt_fase2_de("familia_que_no_existe") is None
    assert cat.prompt_valoracion_de("familia_que_no_existe") is None
    assert cat.prompt_fase2_de(None) is None
    assert cat.prompt_valoracion_de(None) is None


# ------------------------------------------------------------------ #
# R18-R21, R27 · familia EFECTIVA de una linea
#
# Las cuatro ramas del diseno §1.1, en este orden:
#   1. la linea trae `tipo_familia`      -> esa (lo que la IA dijo manda)
#   2. no hay clasificacion de documento -> None (R27, como hoy)
#   3. el documento esta marcado `mixto` -> None (R19, no se hereda)
#   4. si no                             -> la del documento, si es
#                                           familia de LINEA
#
# No es una regla que infiere la familia: propaga a la linea la decision
# que tomo la IA sobre el documento. No mira LER, ni texto, ni CIF.
# ------------------------------------------------------------------ #
def _clasif(familia: str, mixto: bool = False) -> SimpleNamespace:
    """Doble minimo de `ClasificacionAlbaran` (que llega en T3)."""
    return SimpleNamespace(familia=familia, mixto=mixto)


def test_f043_r18_familia_efectiva_rama1_la_de_la_linea_manda():
    """Lo que la IA dijo por LINEA gana siempre a lo del documento."""
    assert (
        cat.familia_efectiva("combustible", _clasif("residuos"))
        == "combustible"
    )


def test_f043_r18_familia_efectiva_rama1_la_linea_otro_no_hereda():
    """Duda 2 resuelta por el humano: 'otro' = 'no es de ninguna familia
    con reglas'. Si heredara, una linea de transporte dentro de un albaran
    de residuos se comeria la regla de contenedores."""
    assert cat.familia_efectiva("otro", _clasif("residuos")) == "otro"


def test_f043_r18_familia_efectiva_rama1_normaliza_lo_que_dijo_la_ia():
    assert cat.familia_efectiva("  RESIDUOS  ", None) == "residuos"


def test_f043_r27_familia_efectiva_rama2_sin_clasificacion_es_none():
    """Envelope anterior a F-043: exactamente el comportamiento de hoy."""
    assert cat.familia_efectiva(None, None) is None
    assert cat.familia_efectiva("", None) is None
    assert cat.familia_efectiva("   ", None) is None


def test_f043_r19_familia_efectiva_rama3_en_mixto_no_se_hereda():
    """MIENTRAS el documento este marcado mixto, la linea sin familia
    queda SIN familia efectiva (y sv3 le pone su motivo de revision)."""
    assert cat.familia_efectiva(None, _clasif("residuos", mixto=True)) is None


def test_f043_r19_familia_efectiva_rama3_en_mixto_la_linea_propia_sigue_valiendo():
    """El mixto no anula la rama 1: bloquea la HERENCIA, no lo que la IA
    dijo explicitamente de esa linea."""
    assert (
        cat.familia_efectiva("hormigon", _clasif("residuos", mixto=True))
        == "hormigon"
    )


def test_f043_r18_familia_efectiva_rama4_hereda_la_del_documento():
    """El caso SS-0003967: documento 'residuos', lineas sin tipo_familia."""
    assert cat.familia_efectiva(None, _clasif("residuos")) == "residuos"
    assert cat.familia_efectiva("", _clasif("hormigon")) == "hormigon"


def test_f043_r20_familia_efectiva_rama4_familia_fuera_de_catalogo_es_none():
    """Si la IA se invento la etiqueta, no se hereda nada: None."""
    assert cat.familia_efectiva(None, _clasif("familia_inventada")) is None


def test_f043_r20_familia_efectiva_rama4_solo_hereda_familias_de_linea(
    monkeypatch,
):
    """Una familia que solo tiene alcance de DOCUMENTO no puede bajar a la
    linea: no significa nada ahi."""
    solo_doc = cat.Familia(
        id="solo_documento",
        nombre="Solo documento",
        definicion="Familia de prueba con alcance unicamente de documento.",
        no_es="No baja a la linea.",
        senales="Ninguna.",
        alcance=frozenset({cat.ALCANCE_DOCUMENTO}),
    )
    monkeypatch.setattr(cat, "CATALOGO", cat.CATALOGO + (solo_doc,))

    assert "solo_documento" in cat.familias_documento()
    assert "solo_documento" not in cat.familias_linea()
    assert cat.familia_efectiva(None, _clasif("solo_documento")) is None


def test_f043_r20_familia_efectiva_acepta_dict_ademas_del_contrato():
    """UN solo punto compartido (R20): sv5 y sv6 lo llaman con el contrato
    Pydantic, pero el envelope viaja como dict antes de validarse."""
    assert cat.familia_efectiva(None, {"familia": "residuos"}) == "residuos"
    assert (
        cat.familia_efectiva(None, {"familia": "residuos", "mixto": True})
        is None
    )


def test_f043_r21_familia_efectiva_no_escribe_nada_en_la_linea():
    """R21: la herencia se resuelve EN LECTURA. Lo que la IA dijo por linea
    se conserva intacto; si se escribiera, se perderia la diferencia entre
    'lo dijo la IA' y 'se heredo del documento'."""
    clasificacion = _clasif("residuos")
    contexto = {"tipo_familia": None, "codigo_ler": "170504"}

    resultado = cat.familia_efectiva(contexto["tipo_familia"], clasificacion)

    assert resultado == "residuos"
    assert contexto == {"tipo_familia": None, "codigo_ler": "170504"}
    assert clasificacion.familia == "residuos"
    assert clasificacion.mixto is False


def test_f043_r13_familia_efectiva_no_mira_el_ler_ni_el_texto():
    """Prohibicion expresa del humano (2026-08-25): nada de deducir la
    familia por codigo LER, familia de producto o palabras del texto. Una
    linea con LER en un documento 'generico' NO se vuelve 'residuos'."""
    assert cat.familia_efectiva(None, _clasif("generico")) == "generico"

    # El modulo no importa NADA con lo que deducir una familia: ni el
    # catalogo LER, ni las funciones de texto de sv2, ni nada de proveedor.
    fuente = Path(cat.__file__).read_text(encoding="utf-8")
    lineas_import = [
        linea.strip()
        for linea in fuente.splitlines()
        if linea.startswith(("import ", "from "))
    ]
    assert lineas_import == [
        "from __future__ import annotations",
        "from dataclasses import dataclass",
        "from typing import Optional",
    ]
