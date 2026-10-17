# tests/test_f076_partidas.py
"""F-076 · partidas de la obra en comun (R1–R6).

``ruesma_comun.sigrid.partidas`` es puro: no abre HTTP ni BBDD. La lectura de
sigrid-api le llega como función (``LectorSql``) y aquí se simula con
``httpx.MockTransport`` o con un lector falso; el reloj de la caché es falso.

Portado de F-049 (bloques A y A2 APROBADOS, ``224f64e``) sin cambios de
semántica: ``normalizar_partida``, hojas, ``casar_partida``. Nuevo de F-076:
``leer_partidas_obra`` con la canonización de F-070, ``resolver_partida_obra``
con la guarda de no hoja y ``CachePartidasObra``.

Regla de fondo (H1 de F-049): se VERIFICA y se NORMALIZA, nunca se ELIGE «la
más parecida» (ni sufijo, ni prefijo, ni distancia).
"""
from __future__ import annotations

import logging

import httpx
import pytest
from ruesma_comun.sigrid import (
    MAX_FILAS_POR_PETICION,
    PoliticaTruncado,
    SigridRespuestaTruncada,
    comprobar_truncado,
)
from ruesma_comun.sigrid.partidas import (
    MOTIVO_ALM,
    MOTIVO_AMBIGUA,
    MOTIVO_COMPUESTA,
    MOTIVO_EXACTA,
    MOTIVO_FUERA_DE_LISTA,
    MOTIVO_NORMALIZADA,
    MOTIVO_SIN_PARTIDA,
    MOTIVOS_PARTIDA,
    SQL_PARTIDAS_POR_OBRA,
    CasePartida,
    ListaPartidasObra,
    PartidaObra,
    casar_partida,
    hojas_de_filas,
    leer_partidas_obra,
    normalizar_partida,
    partes_de_partida,
)

_LOG = logging.getLogger("test_f076_partidas")

_COLUMNAS = ["ide", "padide", "cod", "res"]


def _lista(*codigos: str, no_hojas: tuple[str, ...] = ()) -> ListaPartidasObra:
    return ListaPartidasObra(
        obra="0678",
        hojas=tuple(PartidaObra(codigo=c, descripcion=None, descripcion_agregada=None) for c in codigos),
        no_hojas=no_hojas,
    )


# ------------------------------------------------------------------ #
# R1 · normalizar_partida: la clave de F-049 R1
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("codigo", "esperado"),
    [
        ("CI.04.18", "CI.4.18"),
        ("CI.4.18", "CI.4.18"),
        ("ci 4 18", "CI.4.18"),
        ("ci.04.18", "CI.4.18"),
        (" CI-04 18 ", "CI.4.18"),
        ("CI..04__18", "CI.4.18"),
        ("CI.03A.02", "CI.03A.2"),  # 03A no es solo numérico: conserva el cero
        ("CI.03A.2", "CI.03A.2"),
        ("P05.03", "P05.3"),
        ("00", "0"),
        ("0.00.1", "0.0.1"),
        ("ＣＩ．０４．１８", "CI.4.18"),  # NFKC: ancho completo
        ("P4/P5.01.09", "P4/P5.1.9"),
        ("P4 / P5.01.09", "P4/P5.1.9"),
        ("P4//P5", "P4/P5"),
        ("P5.01.09/", "P5.1.9"),
        ("ñ.01", "Ñ.1"),
        ("", None),
        ("   ", None),
        ("...", None),
        ("/", None),
        (None, None),
    ],
)
def test_f076_r1_normalizar_partida(codigo, esperado):
    assert normalizar_partida(codigo) == esperado


def test_f076_r1_equivalencias_de_la_medicion():
    """Las dos clases medidas en producción (spec §2.2) dan la misma clave."""
    assert normalizar_partida("CI.04.18") == normalizar_partida("CI.4.18") == normalizar_partida("ci 4 18")
    assert normalizar_partida("CI.03A.02") == normalizar_partida("CI.03A.2")
    assert normalizar_partida("CI.04.18") != normalizar_partida("CI.4.19")
    assert normalizar_partida("CI.14.18") != normalizar_partida("CI.4.18")


@pytest.mark.parametrize(
    ("codigo", "esperado"),
    [
        ("P4/P5.01.09", ["P4", "P5.01.09"]),
        ("P4.01.09 / P5.01.09", ["P4.01.09", "P5.01.09"]),
        ("A/B/C", ["A", "B", "C"]),
        ("P5.01.09", ["P5.01.09"]),
        ("P4//P5/", ["P4", "P5"]),
        ("P4.01.09／P5.01.09", ["P4.01.09", "P5.01.09"]),  # «／» de ancho completo (NFKC)
        ("", []),
        (None, []),
    ],
)
def test_f076_r1_partes_de_partida(codigo, esperado):
    assert partes_de_partida(codigo) == esperado


# ------------------------------------------------------------------ #
# R2 · ListaPartidasObra.desde_filas: hojas con la semántica de sv4 y,
# aparte, los códigos no hoja
# ------------------------------------------------------------------ #
def _filas_arbol() -> list[list]:
    # 1 capítulo P5 > 2 subcapítulo P5.01 > 3 y 4 hojas; 5 capítulo con
    # padide 0 (sin padre) y hoja 6 colgando de él; 7 hoja con padide "0";
    # 8 hoja sin cod (fuera); 9 sin ide (fuera); 10 hoja de cod numérico.
    return [
        [1, None, "P5", "Capítulo cinco"],
        [2, 1, "P5.01", "Subcapítulo"],
        [3, 2, "P5.01.09", "Hormigón"],
        [4, 2, " P5.01.02 ", "  Ferralla  "],
        [5, 0, "P4", "Capítulo cuatro"],
        [6, 5, "P4.01.09", ""],
        [7, "0", "ALM.1", "Almacén"],
        [8, 2, None, "Sin código"],
        [None, 2, "X.1", "Sin ide"],
        [10, None, 123, None],
    ]


def test_f076_r2_hojas_de_filas_semantica_sv4():
    hojas = hojas_de_filas(_COLUMNAS, _filas_arbol())
    assert hojas == [
        PartidaObra(codigo="123", descripcion=None, descripcion_agregada=None),
        PartidaObra(codigo="ALM.1", descripcion="Almacén", descripcion_agregada="Almacén"),
        PartidaObra(codigo="P4.01.09", descripcion=None, descripcion_agregada="Capítulo cuatro"),
        PartidaObra(
            codigo="P5.01.02",
            descripcion="Ferralla",
            descripcion_agregada="Capítulo cinco › Subcapítulo › Ferralla",
        ),
        PartidaObra(
            codigo="P5.01.09",
            descripcion="Hormigón",
            descripcion_agregada="Capítulo cinco › Subcapítulo › Hormigón",
        ),
    ]


def test_f076_r2_lista_lleva_hojas_y_no_hojas():
    lista = ListaPartidasObra.desde_filas("0691", _COLUMNAS, _filas_arbol())
    assert lista.obra == "0691"
    assert lista.codigos == ("123", "ALM.1", "P4.01.09", "P5.01.02", "P5.01.09")
    assert lista.no_hojas == ("P4", "P5", "P5.01")
    assert lista.hojas == tuple(hojas_de_filas(_COLUMNAS, _filas_arbol()))


def test_f076_r2_columnas_en_otro_orden():
    columnas = ["cod", "res", "padide", "ide"]
    filas = [["P5", "Cap", None, 1], ["P5.1", "Hoja", 1, 2]]
    assert [h.codigo for h in hojas_de_filas(columnas, filas)] == ["P5.1"]


def test_f076_r2_ciclo_no_cuelga():
    filas = [[1, 2, "A", "a"], [2, 1, "B", "b"], [3, 1, "C", "c"]]
    hojas = hojas_de_filas(_COLUMNAS, filas)
    assert [h.codigo for h in hojas] == ["C"]
    assert hojas[0].descripcion_agregada == "b › a › c"


def test_f076_r2_padre_sin_cod_no_entra_en_no_hojas():
    filas = [
        [1, None, None, "Capítulo sin código"],
        [2, 1, "A.1", "Hoja a"],
        [3, None, "P5", "Capítulo cinco"],
        [4, 3, "P5.1", "Hoja b"],
    ]
    lista = ListaPartidasObra.desde_filas("0691", _COLUMNAS, filas)
    assert lista.no_hojas == ("P5",)
    assert lista.codigos == ("A.1", "P5.1")


def test_f076_r2_padide_cero_en_texto_es_sin_padre_aunque_exista_ide_cero():
    filas = [["0", None, "Z.0", "Fila de ide cero"], [7, "0", "ALM.1", "Almacén"]]
    lista = ListaPartidasObra.desde_filas("0691", _COLUMNAS, filas)
    assert lista.hojas == (
        PartidaObra(codigo="ALM.1", descripcion="Almacén", descripcion_agregada="Almacén"),
        PartidaObra(codigo="Z.0", descripcion="Fila de ide cero", descripcion_agregada="Fila de ide cero"),
    )
    assert lista.no_hojas == ()


def test_f076_r2_sin_filas():
    assert hojas_de_filas(_COLUMNAS, []) == []
    lista = ListaPartidasObra.desde_filas("0691", _COLUMNAS, [])
    assert (lista.hojas, lista.no_hojas, lista.codigos) == ((), (), ())


def test_f076_r2_sql_es_la_de_sv4_con_empresa_1():
    """La SQL de F-049 (review A, cambio 5): la de sv4 MÁS ``con_obr.emp = 1``."""
    assert SQL_PARTIDAS_POR_OBRA == (
        "SELECT\n"
        "    p.ide    AS ide,\n"
        "    p.padide AS padide,\n"
        "    p.cod    AS cod,\n"
        "    p.res    AS res\n"
        "FROM obrparpar AS p\n"
        "JOIN con AS con_obr ON p.obride = con_obr.ide\n"
        "WHERE con_obr.cod = ?\n"
        "  AND con_obr.emp = 1\n"
        "ORDER BY p.cod\n"
    )


# ------------------------------------------------------------------ #
# R4 · casar_partida: semántica de F-049 R5
# ------------------------------------------------------------------ #
def test_f076_r4_motivos_declarados():
    assert MOTIVOS_PARTIDA == frozenset(
        {"exacta", "normalizada", "compuesta", "alm", "sin_partida", "fuera_de_lista", "ambigua"}
    )
    assert (MOTIVO_EXACTA, MOTIVO_NORMALIZADA, MOTIVO_COMPUESTA) == ("exacta", "normalizada", "compuesta")
    assert (MOTIVO_ALM, MOTIVO_SIN_PARTIDA) == ("alm", "sin_partida")
    assert (MOTIVO_FUERA_DE_LISTA, MOTIVO_AMBIGUA) == ("fuera_de_lista", "ambigua")


def test_f076_r4_exacta():
    caso = casar_partida(_lista("CI.4.18", "P5.01.09"), "CI.4.18", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_EXACTA, codigos_lista=("CI.4.18",))
    assert caso.validada is True


def test_f076_r4_exacta_ignora_espacios_exteriores():
    caso = casar_partida(_lista("CI.4.18"), "  CI.4.18 ", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_EXACTA, codigos_lista=("CI.4.18",))


def test_f076_r4_normalizada_devuelve_el_codigo_de_la_lista():
    caso = casar_partida(_lista("CI.4.18", "P5.01.09"), "CI.04.18", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_NORMALIZADA, codigos_lista=("CI.4.18",))
    assert caso.validada is True


def test_f076_r4_exacta_gana_a_la_ambiguedad():
    caso = casar_partida(_lista("CI.04.18", "CI.4.18"), "CI.4.18", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_EXACTA, codigos_lista=("CI.4.18",))


def test_f076_r4_ambigua_no_elige():
    caso = casar_partida(_lista("CI.04.18", "CI.4.18"), "ci-04-18", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_AMBIGUA, codigos_lista=())
    assert caso.validada is False


def test_f076_r4_compuesta_todas_las_partes_casan():
    caso = casar_partida(_lista("P4.01.09", "P5.01.09", "P5.03.04"), "P4.1.9/P5.01.09", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_COMPUESTA, codigos_lista=("P4.01.09", "P5.01.09"))
    assert caso.validada is True


def test_f076_r4_compuesta_con_barra_de_ancho_completo():
    caso = casar_partida(_lista("P4.01.09", "P5.01.09"), "P4.01.09／P5.01.09", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_COMPUESTA, codigos_lista=("P4.01.09", "P5.01.09"))


def test_f076_r4_compuesta_abreviada_no_se_completa():
    caso = casar_partida(_lista("P4.01.09", "P5.01.09", no_hojas=("P4", "P5")), "P4/P5.01.09", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_FUERA_DE_LISTA, codigos_lista=())
    assert caso.validada is False


def test_f076_r4_compuesta_con_parte_ambigua():
    caso = casar_partida(_lista("A.01", "A.1", "B.2"), "A.001/B.2", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_AMBIGUA, codigos_lista=())


def test_f076_r4_compuesta_fuera_manda_sobre_ambigua():
    caso = casar_partida(_lista("A.01", "A.1", "B.2"), "A.001/Z.9", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_FUERA_DE_LISTA, codigos_lista=())


def test_f076_r4_compuesta_parte_exacta_gana_a_su_ambiguedad():
    caso = casar_partida(_lista("A.01", "A.1", "B.2"), "A.01/B.2", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_COMPUESTA, codigos_lista=("A.01", "B.2"))


def test_f076_r4_una_sola_parte_tras_la_barra_no_es_compuesta():
    caso = casar_partida(_lista("P5.01.09"), "P5.1.9/", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_NORMALIZADA, codigos_lista=("P5.01.09",))


@pytest.mark.parametrize(
    "lectura",
    [
        "03.09",  # sin prefijo de capítulo: sufijo de P5.03.09
        "PJ.0304",  # deformada
        "P5.03.0",  # prefijo de P5.03.09
        "P5.03.08",  # distancia 1
        "P5.3.09.1",  # más larga
        "CI.14.18",  # la de la 0694 sin candidata (spec §2.2)
    ],
)
def test_f076_r4_sin_parecidos(lectura):
    caso = casar_partida(_lista("P5.03.09", "P5.03.04", "CI.4.18"), lectura, "ALM")
    assert caso == CasePartida(motivo=MOTIVO_FUERA_DE_LISTA, codigos_lista=())


@pytest.mark.parametrize("lectura", ["ALM", " alm ", "Alm"])
def test_f076_r4_alm_literal(lectura):
    caso = casar_partida(_lista("P5.01.09"), lectura, "ALM")
    assert caso == CasePartida(motivo=MOTIVO_ALM, codigos_lista=())
    assert caso.validada is None


def test_f076_r4_alm_configurable_y_opcional():
    assert casar_partida(_lista("P5.01.09"), "ACOPIO", " acopio ").motivo == MOTIVO_ALM
    assert casar_partida(_lista("P5.01.09"), "ALM", None).motivo == MOTIVO_FUERA_DE_LISTA
    assert casar_partida(_lista("P5.01.09"), "ALM", "").motivo == MOTIVO_FUERA_DE_LISTA


@pytest.mark.parametrize("lectura", [None, "", "   ", "./-"])
def test_f076_r4_sin_partida(lectura):
    caso = casar_partida(_lista("P5.01.09"), lectura, "ALM")
    assert caso == CasePartida(motivo=MOTIVO_SIN_PARTIDA, codigos_lista=())
    assert caso.validada is None


def test_f076_r4_lista_vacia():
    assert casar_partida(_lista(), "P5.01.09", "ALM").motivo == MOTIVO_FUERA_DE_LISTA


def test_f076_r4_codigos_duplicados_en_la_lista_no_son_ambiguos():
    caso = casar_partida(_lista("P5.01.09", "P5.01.09"), "P5.1.9", "ALM")
    assert caso == CasePartida(motivo=MOTIVO_NORMALIZADA, codigos_lista=("P5.01.09",))


# ------------------------------------------------------------------ #
# R3 · leer_partidas_obra: obra de F-070, UNA consulta, NO_TOLERA
# ------------------------------------------------------------------ #
def _lector_http(cuerpo: dict, llamadas: list[dict]):
    """Lector como el de sv4 y sv6: POST a sigrid-api (simulado) + política."""

    def leer(sql, parametros, etiqueta, politica, max_rows):
        llamadas.append(
            {"sql": sql, "parametros": parametros, "etiqueta": etiqueta, "politica": politica, "max_rows": max_rows}
        )
        transporte = httpx.MockTransport(lambda peticion: httpx.Response(200, json=cuerpo))
        with httpx.Client(transport=transporte) as cliente:
            respuesta = cliente.post(
                "http://sigrid-api.test/api/sql/read",
                json={"sql": sql, "parameters": parametros, "max_rows": max_rows},
            )
        body = respuesta.json()
        comprobar_truncado(body, politica=politica, etiqueta=etiqueta, logger=_LOG)
        return list(body["columns"]), list(body["rows"])

    return leer


def _cuerpo(filas=None, truncated=False) -> dict:
    return {"ok": True, "columns": _COLUMNAS, "rows": _filas_arbol() if filas is None else filas,
            "truncated": truncated}


def test_f076_r3_una_consulta_no_tolera_y_tope_maximo():
    llamadas: list[dict] = []
    lista = leer_partidas_obra(_lector_http(_cuerpo(), llamadas), " 0691 ")
    assert len(llamadas) == 1
    (llamada,) = llamadas
    assert llamada["sql"] == SQL_PARTIDAS_POR_OBRA
    assert llamada["parametros"] == ["0691"]
    assert llamada["etiqueta"] == "partidas_obra_0691"
    assert llamada["politica"] is PoliticaTruncado.NO_TOLERA
    assert llamada["max_rows"] == MAX_FILAS_POR_PETICION == 500_000
    assert isinstance(lista, ListaPartidasObra)
    assert lista.obra == "0691"
    assert lista.codigos == ("123", "ALM.1", "P4.01.09", "P5.01.02", "P5.01.09")
    assert lista.no_hojas == ("P4", "P5", "P5.01")


@pytest.mark.parametrize(
    ("obra", "consultada"),
    [("686", "0686"), (" 686 ", "0686"), ("0686", "0686"), ("var", "VAR"), ("postv2", "POSTV2"),
     (" GG ", "GG"), ("0578-B", "0578-B")],
)
def test_f076_r3_obra_canonizada_con_f070(obra, consultada):
    """``canonizar_codigo_obra`` (F-070): canónica si la hay; si no, recortada."""
    llamadas: list[dict] = []
    lista = leer_partidas_obra(_lector_http(_cuerpo(), llamadas), obra)
    assert [ll["parametros"] for ll in llamadas] == [[consultada]]
    assert llamadas[0]["etiqueta"] == f"partidas_obra_{consultada}"
    assert lista is not None and lista.obra == consultada


@pytest.mark.parametrize("obra", [None, "", "   ", "	"])
def test_f076_r3_obra_vacia_no_consulta(obra):
    def leer(*args, **kwargs):  # pragma: no cover - no debe llamarse
        raise AssertionError("no debe consultarse sigrid-api sin obra")

    assert leer_partidas_obra(leer, obra) is None


def test_f076_r3_truncado_lanza_nunca_lista_parcial():
    llamadas: list[dict] = []
    with pytest.raises(SigridRespuestaTruncada) as info:
        leer_partidas_obra(_lector_http(_cuerpo(_filas_arbol()[:3], truncated=True), llamadas), "0691")
    assert info.value.etiqueta == "partidas_obra_0691"
    assert len(llamadas) == 1


def test_f076_r3_error_del_lector_se_propaga():
    def leer(*args, **kwargs):
        raise RuntimeError("sigrid-api respondio 500")

    with pytest.raises(RuntimeError, match="500"):
        leer_partidas_obra(leer, "0691")


def test_f076_r3_sin_filas_da_lista_vacia_no_none():
    """Quien decide qué es «sin lista» con 0 hojas es la caché (R6), no la lectura."""
    lista = leer_partidas_obra(_lector_http(_cuerpo([]), []), "0691")
    assert lista == ListaPartidasObra(obra="0691", hojas=(), no_hojas=())
