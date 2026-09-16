# tests/test_f045_r17_huella.py
"""F-045 · la huella, pieza a pieza: los 9 supervivientes del lote.

La campaña del lote del 2026-09-16 (44 mutantes) dejó 9 vivos, **todos en el
código que acababa de perder datos**: `huella.py` entero y las dos guardas de
`escritura.py` que deciden qué se retira. No hay ninguno que justificar como
equivalente; son huecos, y este fichero los cierra.

Tres de ellos son la misma clase de fallo que ya costó un bloqueante: la
serialización de `guardar` —`ensure_ascii`, `indent`, `sort_keys`— que en
`mapa.py` se justificó como «da el mismo byte» **sin comprobarlo** y no lo daba.
Aquí se fija el contenido escrito, que es lo único que lo demuestra.
"""

from __future__ import annotations

import json

import pytest

from evals.revision import escritura, huella, informe as informe_mod
from evals.revision.modelos import DEFECTO_CONOCIDO, NO_REGRESION, InformeImportacion


# --- `guardar`: determinista, y se demuestra fijando el byte --------------


def test_f045_r17_la_huella_se_escribe_byte_a_byte_como_dice_su_docstring(tmp_path):
    ruta = tmp_path / "huella.json"
    huella.guardar({"lineas": [["RES-002", "1"], ["RES-001", "2"]]}, ruta)
    esperado = """{
  "_doc": "%s",
  "tablas": {
    "lineas": [
      [
        "RES-001",
        "2"
      ],
      [
        "RES-002",
        "1"
      ]
    ]
  }
}
""" % huella._DOC
    assert ruta.read_text(encoding="utf-8") == esperado


def test_f045_r17_la_huella_no_escapa_los_acentos(tmp_path):
    """Un fichero versionado lleno de `\\u00f1` no se revisa en un diff."""
    ruta = tmp_path / "huella.json"
    huella.guardar({"lineas": [["RES-001", "INCREMENTO POR AÑO"]]}, ruta)
    texto = ruta.read_text(encoding="utf-8")
    assert "AÑO" in texto and "\\u" not in texto


def test_f045_r17_una_tabla_sin_claves_no_se_guarda(tmp_path):
    ruta = tmp_path / "huella.json"
    huella.guardar({"lineas": [["RES-001", "1"]], "contexto": []}, ruta)
    assert set(json.loads(ruta.read_text(encoding="utf-8"))["tablas"]) == {"lineas"}


def test_f045_r17_la_ruta_por_defecto_cae_junto_al_mapa_de_casos():
    import evals

    paquete = __import__("pathlib").Path(evals.__file__).resolve().parent
    assert huella.RUTA_HUELLA.parent == paquete
    assert huella.RUTA_HUELLA.name == "huella_importacion.json"


# --- `anotar`: solo las tablas cuya identidad está declarada --------------


def test_f045_r17_anotar_recoge_las_tablas_con_clave_declarada():
    tablas = {
        ("RES-001", "IA1"): {
            "lineas": [{"caso_id": "RES-001", "num_linea": 1}],
            "inventada": [{"caso_id": "RES-001"}],
        }
    }
    anotada = huella.anotar(tablas, {"lineas": ("caso_id", "num_linea")})
    assert anotada == {"lineas": [["RES-001", "1"]]}
    assert "inventada" not in anotada


def test_f045_r17_anotar_sin_ninguna_clave_declarada_no_anota_nada():
    tablas = {("X", "IA1"): {"lineas": [{"caso_id": "X", "num_linea": 1}]}}
    assert huella.anotar(tablas, {}) == {}


def test_f045_r17_claves_de_una_tabla_ausente_es_un_conjunto_vacio():
    assert huella.claves_de({"lineas": [["A", "1"]]}, "contexto") == set()
    assert huella.claves_de({"lineas": [["A", "1"]]}, "lineas") == {("A", "1")}


# --- Las dos guardas de `escritura.py` que deciden qué se retira ---------


def test_f045_r17_sin_filas_nuevas_no_se_retira_nada():
    """Son las filas nuevas las que dicen qué columnas deja el importador en

    `?`; sin ellas no hay con qué juzgar, y ante la duda no se toca lo del
    humano. Es lo que hace que una tabla que esta importación no alimenta se
    quede intacta en vez de vaciarse."""
    assert not escritura._solo_del_importador(
        {"caso_id": "RES-001", "numero_albaran": "SS-0000168"}, []
    )
    assert not escritura._solo_del_importador({"caso_id": "RES-002"}, [])


def test_f045_r17_una_tabla_que_esta_importacion_no_alimenta_se_queda_intacta():
    existentes = [
        {"caso_id": "RES-001", "num_linea": 1, "campo_contexto": "volumen_m3"},
        {"caso_id": "RES-001", "num_linea": 2, "campo_contexto": "codigo_ler"},
    ]
    fundidas = escritura.fundir_filas(
        existentes, [], ("caso_id", "num_linea", "campo_contexto"),
        mias={("RES-001", "1", "volumen_m3"), ("RES-001", "2", "codigo_ler")},
    )
    assert len(fundidas) == 2


def test_f045_r17_con_filas_nuevas_si_se_retira_lo_que_es_suyo():
    existentes = [
        {"caso_id": "RES-001", "num_linea": 1, "modifier_source": "gestion_residuos"},
        {"caso_id": "RES-001", "num_linea": 2, "modifier_source": "?"},
    ]
    nuevas = [{"caso_id": "RES-001", "num_linea": 9, "modifier_source": "?"}]
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea"),
        mias={("RES-001", "1"), ("RES-001", "2")},
    )
    assert [f["num_linea"] for f in fundidas] == [1, 9]


def test_f045_r17_el_casado_por_prefijo_no_duplica_la_sintetica_del_humano():
    """Si la clave casa EXACTA, esa es: buscar además por prefijo empareja la

    fila nueva con dos existentes y **escribe las dos**, duplicando la línea
    deducida que el humano anotó. El banco esperaría entonces dos sintéticas
    donde el sistema emite una.

    Las filas se comparan **en lista, sin colapsar**: la versión anterior de
    este test las metía en un `dict` por descripción, y ahí la fila duplicada
    pisaba a su gemela y el fallo pasaba invisible. Es la segunda vez en esta
    feature que un test dice cubrir algo y pasa con el fallo puesto.
    """
    existentes = [
        {"caso_id": "X", "num_linea_base": 1, "descripcion_esperada": "INCREMENTO",
         "precio_unitario": 10},
        {"caso_id": "X", "num_linea_base": 1,
         "descripcion_esperada": "INCREMENTO LER 170604", "precio_unitario": 20},
    ]
    nuevas = [
        {"caso_id": "X", "num_linea_base": 1,
         "descripcion_esperada": "INCREMENTO LER 170604", "precio_unitario": 99},
    ]
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea_base", "descripcion_esperada"),
        campo_prefijo="descripcion_esperada",
    )
    assert [(f["descripcion_esperada"], f["precio_unitario"]) for f in fundidas] == [
        ("INCREMENTO", 10),
        ("INCREMENTO LER 170604", 99),
    ]


# --- El informe dice bien en qué dirección va el cambio ------------------


@pytest.mark.parametrize(
    "antes,ahora,frase",
    [
        (DEFECTO_CONOCIDO, NO_REGRESION, "tiene que salir **VERDE**"),
        (NO_REGRESION, DEFECTO_CONOCIDO, "rojo esperado"),
    ],
)
def test_f045_r14_el_informe_no_confunde_la_direccion_del_cambio(antes, ahora, frase):
    """Decirlo al revés manda a mirar el caso equivocado."""
    texto = informe_mod.render(
        InformeImportacion(cambios_de_grupo=[("HOR-001", antes, ahora)])
    )
    linea = next(l for l in texto.splitlines() if l.startswith("- **HOR-001**"))
    assert frase in linea
