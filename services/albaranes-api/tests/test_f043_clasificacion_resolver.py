# tests/test_f043_clasificacion_resolver.py
"""F-043 · El resolver de clasificacion de sv2 (R10, R11, R12, R13, R16).

Sustituye al `tipologia_resolver`, que DECIDIA la familia con reglas y con
ella elegia el prompt de fase 2 (el lazo cerrado que F-043 desmonta). Este
no decide nada: la familia es la que dijo la IA. Lo unico que hace es
normalizar, sellar el origen y dejar constancia cuando la IA no clasifico o
se invento una etiqueta.

Sin red, sin BBDD y sin LLM: funcion pura sobre diccionarios.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from ruesma_comun.contratos import ClasificacionAlbaran
from ruesma_comun.contratos.clasificacion import (
    MOTIVO_SIN_CLASIFICACION,
    ORIGEN_AUSENTE,
    ORIGEN_IA1,
    ORIGEN_IA2,
)

from application.services import clasificacion_resolver as resolver_modulo
from application.services.clasificacion_resolver import (
    resolver_clasificacion,
)


def _documento(clasificacion=None, lineas=None) -> dict:
    """`data` de un envelope de fase 1, con o sin bloque clasificacion."""
    doc: dict = {"cabecera": {"proveedor_cif": "B12345678"},
                 "lineas": lineas or []}
    if clasificacion is not None:
        doc["clasificacion"] = clasificacion
    return doc


def _bloque(familia="residuos", **extra) -> dict:
    base = {
        "familia": familia,
        "confianza_pct": 88.0,
        "motivo": "el proveedor es gestor autorizado y cita el LER 170504",
    }
    base.update(extra)
    return base


# ------------------------------------------------------------------ #
# R11 — sin bloque: se registra el hueco, NO se adivina.
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "data",
    [None, {}, {"cabecera": {}, "lineas": []}, _documento(), _documento(None)],
    ids=["none", "vacio", "sin_clave", "sin_bloque", "bloque_none"],
)
def test_f043_r11_sin_clasificacion_se_registra_el_hueco(data) -> None:
    res = resolver_clasificacion(data)

    assert res.familia == "generico"
    assert res.confianza_pct == 0
    assert res.motivo == MOTIVO_SIN_CLASIFICACION
    assert res.origen == ORIGEN_AUSENTE


def test_f043_r11_el_bloque_vacio_es_ausencia_no_familia_vacia() -> None:
    """Un bloque con la familia en blanco es lo mismo que no traerlo: lo
    que NO puede pasar es que salga una familia vacia aguas abajo."""
    res = resolver_clasificacion(_documento({"familia": "  "}))

    assert res.familia == "generico"
    assert res.origen == ORIGEN_AUSENTE


# ------------------------------------------------------------------ #
# R10 — familia fuera de catalogo: generico + el valor original en el
# motivo. PROHIBIDO deducirla de otra senal.
# ------------------------------------------------------------------ #
def test_f043_r10_familia_fuera_de_catalogo_cae_a_generico() -> None:
    res = resolver_clasificacion(
        _documento(_bloque("residuos_peligrosos", confianza_pct=97.0))
    )

    assert res.familia == "generico"
    assert "residuos_peligrosos" in res.motivo
    assert "gestor autorizado" in res.motivo  # el motivo de la IA se conserva


def test_f043_r10_fuera_de_catalogo_va_a_revision_con_confianza_cero() -> None:
    """La confianza de la IA era sobre SU etiqueta, no sobre `generico`.

    Mantener el 97 % dejaria el documento por encima del umbral de sv3 y
    nadie lo miraria nunca: el hueco tiene que verse.
    """
    res = resolver_clasificacion(
        _documento(_bloque("residuos_peligrosos", confianza_pct=97.0))
    )

    assert res.confianza_pct == 0


def test_f043_r10_una_familia_de_solo_linea_no_clasifica_el_documento() -> None:
    """`combustible` esta en el catalogo pero es familia de LINEA: como
    clasificacion de documento no tiene prompt de fase 2 al que enrutar."""
    res = resolver_clasificacion(_documento(_bloque("combustible")))

    assert res.familia == "generico"
    assert "combustible" in res.motivo


# ------------------------------------------------------------------ #
# R12 — la familia es EXACTAMENTE la que dijo la IA.
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "familia", ["generico", "hormigon", "mortero", "residuos"],
)
def test_f043_r12_la_familia_del_documento_es_la_que_dijo_la_ia(
    familia,
) -> None:
    res = resolver_clasificacion(_documento(_bloque(familia)))

    assert res.familia == familia
    assert res.origen == ORIGEN_IA1
    assert res.confianza_pct == 88.0


def test_f043_r12_la_familia_se_normaliza_no_se_reinterpreta() -> None:
    """' Residuos ' no es otra familia; 'REZIDUOS' si (y cae a generico)."""
    assert resolver_clasificacion(
        _documento(_bloque(" Residuos "))
    ).familia == "residuos"
    assert resolver_clasificacion(
        _documento(_bloque("REZIDUOS"))
    ).familia == "generico"


def test_f043_r12_el_origen_lo_sella_el_resolver_no_la_ia() -> None:
    """Si la IA se inventa el origen, se pisa: es el unico campo del bloque
    que no le pertenece."""
    res = resolver_clasificacion(_documento(_bloque(origen="humano")))

    assert res.origen == ORIGEN_IA1


def test_f043_r12_mixto_y_secundarias_se_conservan() -> None:
    res = resolver_clasificacion(
        _documento(
            _bloque("residuos", mixto=True,
                    familias_secundarias=[" Hormigon ", "", "otro"])
        )
    )

    assert res.mixto is True
    assert res.familias_secundarias == ["hormigon", "otro"]


@pytest.mark.parametrize(
    ("bruta", "esperada"),
    [(150, 100.0), (-5, 0.0), ("alta", 0.0), (None, 0.0), ("75", 75.0)],
)
def test_f043_r12_la_confianza_se_acota_al_rango_del_contrato(
    bruta, esperada,
) -> None:
    """Un valor fuera de rango invalidaria el contrato entero y perderia la
    familia, que es el dato que importa."""
    res = resolver_clasificacion(
        _documento(_bloque("residuos", confianza_pct=bruta))
    )

    assert res.confianza_pct == esperada
    assert res.familia == "residuos"


def test_f043_r12_devuelve_siempre_el_contrato_compartido() -> None:
    assert isinstance(
        resolver_clasificacion(_documento(_bloque())), ClasificacionAlbaran,
    )
    assert isinstance(resolver_clasificacion(None), ClasificacionAlbaran)


# ------------------------------------------------------------------ #
# R16 — la de fase 2 prevalece y se sella con origen 'ia2'.
# ------------------------------------------------------------------ #
def test_f043_r16_la_clasificacion_de_fase2_prevalece() -> None:
    res = resolver_clasificacion(
        _documento(_bloque("generico")),
        _documento(_bloque("residuos", motivo="hay LER y planta de destino")),
    )

    assert res.familia == "residuos"
    assert res.origen == ORIGEN_IA2
    assert res.motivo == "hay LER y planta de destino"


def test_f043_r16_fase2_sin_bloque_no_borra_la_de_fase1() -> None:
    """IA2 que no toca la clasificacion no puede hacerla desaparecer."""
    res = resolver_clasificacion(_documento(_bloque("hormigon")),
                                 _documento())

    assert res.familia == "hormigon"
    assert res.origen == ORIGEN_IA1


def test_f043_r16_acepta_el_documento_revisado_envuelto() -> None:
    """La fase 2 devuelve `{documento_revisado, razonamientos}`. Que el
    llamante pase el envoltorio en vez del documento no puede degradar en
    silencio a la clasificacion de fase 1: seria invisible."""
    res = resolver_clasificacion(
        _documento(_bloque("generico")),
        {"documento_revisado": _documento(_bloque("mortero")),
         "razonamientos": []},
    )

    assert res.familia == "mortero"
    assert res.origen == ORIGEN_IA2


def test_f043_r16_fase2_fuera_de_catalogo_tambien_cae_a_generico() -> None:
    res = resolver_clasificacion(
        _documento(_bloque("residuos")),
        _documento(_bloque("chatarra")),
    )

    assert res.familia == "generico"
    assert res.origen == ORIGEN_IA2
    assert "chatarra" in res.motivo


def test_f043_r16_acepta_el_contrato_ya_validado_no_solo_dicts() -> None:
    """sv2 lo llama con dicts, pero el mismo bloque viaja validado."""
    res = resolver_clasificacion(
        {"cabecera": {}, "lineas": [],
         "clasificacion": ClasificacionAlbaran(
             familia="hormigon", confianza_pct=70, motivo="HA-25 en la linea",
         )},
    )

    assert res.familia == "hormigon"
    assert res.confianza_pct == 70


# ------------------------------------------------------------------ #
# R12 — cero heuristica: el modulo no puede ni MIRAR con que deducir.
# ------------------------------------------------------------------ #
def test_f043_r12_el_resolver_no_importa_ler_ni_funciones_de_texto() -> None:
    """Lista NEGRA de imports, como en `familias.py`.

    El `tipologia_resolver` deducia la familia con el catalogo LER, las
    funciones de texto de hormigon/mortero y un override por CIF. Que este
    modulo no pueda importarlos es la unica forma de que la prohibicion
    sobreviva a la siguiente sesion que "solo anade un caso".

    Es lista negra y no lista exacta: anadir un import legitimo no rompe el
    test, colar uno de los prohibidos si.
    """
    fuente = Path(resolver_modulo.__file__).read_text(encoding="utf-8")
    lineas_import = [
        linea.strip()
        for linea in fuente.splitlines()
        if linea.startswith(("import ", "from "))
    ]
    prohibidos = (
        "ler",
        "residuo",
        "proveedor",
        "cif",
        "texto",
        "producto",
        "tipologia",
        "regex",
        "unicodedata",
        "difflib",
        "rapidfuzz",
        "infrastructure",
        "domain.",
    )
    for linea in lineas_import:
        for prohibido in prohibidos:
            assert prohibido not in linea.lower(), (
                f"import sospechoso en clasificacion_resolver.py: {linea!r} "
                f"(contiene {prohibido!r})"
            )
    assert "import re" not in lineas_import
    assert not any(
        linea.startswith(("import re ", "from re "))
        for linea in lineas_import
    )


def test_f043_r12_el_resolver_no_lee_la_cabecera_ni_las_lineas() -> None:
    """Mismo documento, dos cabeceras y dos juegos de lineas distintos: la
    clasificacion resultante es la misma. Si algun dia alguien vuelve a
    mirar el CIF o el concepto, este test lo caza."""
    bloque = _bloque("generico")
    con_pistas = {
        "cabecera": {"proveedor_cif": "B99999999",
                     "proveedor_nombre": "GESTION DE RESIDUOS SA"},
        "lineas": [{"codigo": "170504", "concepto": "HA-25 residuo LER"}],
        "clasificacion": bloque,
    }
    sin_pistas = {"cabecera": {}, "lineas": [], "clasificacion": bloque}

    assert (
        resolver_clasificacion(con_pistas).model_dump()
        == resolver_clasificacion(sin_pistas).model_dump()
    )


# ------------------------------------------------------------------ #
# R13 · LA PROHIBICION (no-regresion)
#
# Decision expresa del humano del 2026-08-25, que mando revertir la T11 de
# F-036: «los residuos no se deben clasificar solo porque contenga LER, es
# una regla de mierda». Estos tests son el guardian de esa reversion: cada
# uno mete en el documento la senal con la que el `tipologia_resolver`
# decidia, y exige que la familia siga siendo la que dijo la IA.
#
# Fase RED de un test de no-regresion: el codigo correcto ya esta, asi que
# no puede fallar por si solo. Se demostro reintroduciendo a mano la regla
# LER -> residuos en el resolver y viendo que estos tests la cazan; la
# traza esta en progress/impl_F-043_bloque_B.md.
# ------------------------------------------------------------------ #
def _lineas_con_ler() -> list[dict]:
    """TODAS las lineas con LER, por los tres sitios donde lo miraba el
    resolver viejo: contexto, codigo y concepto."""
    return [
        {"codigo": "170504", "concepto": "Retirada tierras LER 170504",
         "contexto_linea": {"tipo_familia": "residuos",
                            "codigo_ler": "170504"}},
        {"codigo": "170203", "concepto": "Residuo madera LER 170203",
         "contexto_linea": {"tipo_familia": "residuos",
                            "codigo_ler": "170203"}},
    ]


def test_f043_r13_prohibicion_ler_en_todas_las_lineas_no_fuerza_residuos(
) -> None:
    """EL test de la feature: LER en todas las lineas y la IA dijo
    `generico` => sale `generico`."""
    res = resolver_clasificacion(
        _documento(
            _bloque("generico", motivo="suministro de material, sin gestion"),
            lineas=_lineas_con_ler(),
        )
    )

    assert res.familia == "generico"
    assert res.origen == ORIGEN_IA1
    assert res.confianza_pct == 88.0


def test_f043_r13_prohibicion_sin_clasificacion_el_ler_no_la_reconstruye(
) -> None:
    """R11 al pie de la letra: sin bloque, el LER NO reconstruye la
    familia. Se registra el hueco y se manda a revision."""
    res = resolver_clasificacion(
        {"cabecera": {"proveedor_nombre": "GESTORA DE RESIDUOS SL",
                      "proveedor_cif": "B99999999"},
         "lineas": _lineas_con_ler()}
    )

    assert res.familia == "generico"
    assert res.origen == ORIGEN_AUSENTE
    assert res.motivo == MOTIVO_SIN_CLASIFICACION


def test_f043_r13_prohibicion_la_familia_dominante_de_lineas_no_manda(
) -> None:
    """El paso 3 del resolver viejo: familia dominante de `contexto_linea`.
    La clasificacion es del DOCUMENTO (R17); las lineas la afinan, no la
    deciden."""
    res = resolver_clasificacion(
        _documento(_bloque("generico"), lineas=_lineas_con_ler())
    )

    assert res.familia == "generico"


def test_f043_r13_prohibicion_el_texto_de_hormigon_no_fuerza_hormigon(
) -> None:
    """`texto_contiene_hormigon` / `texto_contiene_mortero` eran la otra
    mitad del lazo cerrado (se borran en T10)."""
    lineas = [
        {"codigo": "HA-25/B/20/IIa", "concepto": "HORMIGON BOMBEADO HA-25"},
        {"codigo": "M-7,5", "concepto": "MORTERO SECO M-7,5"},
    ]

    res = resolver_clasificacion(
        _documento(_bloque("generico"), lineas=lineas)
    )

    assert res.familia == "generico"


def test_f043_r13_prohibicion_el_cif_del_proveedor_no_fuerza_nada() -> None:
    """R14: el override por CIF se retira. Un gestor de residuos conocido
    que emite un albaran de suministro es un albaran de suministro."""
    documento = _documento(
        _bloque("generico"), lineas=_lineas_con_ler(),
    )
    documento["cabecera"] = {"proveedor_cif": "A28526275",
                             "proveedor_nombre": "SALMEDINA TRANSFER SL"}

    assert resolver_clasificacion(documento).familia == "generico"


def test_f043_r13_prohibicion_tampoco_al_reves_residuos_sin_ler() -> None:
    """La prohibicion es simetrica: si la IA dice `residuos` en un albaran
    donde no aparece ni un LER, la familia sigue siendo `residuos`. No hay
    regla que la 'corrija' con las senales del papel."""
    res = resolver_clasificacion(
        _documento(
            _bloque("residuos", motivo="el proveedor es gestor autorizado"),
            lineas=[{"codigo": "PORTES", "concepto": "Transporte a planta"}],
        )
    )

    assert res.familia == "residuos"
