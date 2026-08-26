# tests/test_f043_r26_ss0003967.py
"""F-043 · T23 · R26 · SS-0003967 llega a 210,00 EUR SIN tocar la linea.

Es la prueba de aceptacion de la feature y la que desbloquea F-036.

EL CASO. Albaran de SALMEDINA del 2024-07-10, LER 170604 (materiales de
aislamiento), 6 m3, contra el contrato CTSU24/0228 de la obra 687. El
ground truth del administrativo
(`progress/revision_residuos_salmedina_20260819.md` §8.1) son
**210,00 EUR = 120,00 del contenedor + 90,00 del incremento por LER**.
En BBDD salio **540,00 EUR en una sola linea**.

POR QUE NO SE ARREGLABA. Toda la maquinaria de residuos de sv6 estaba
cerrada tras `contexto_linea.tipo_familia == 'residuos'`, y ese campo no
llega al merge porque **ningun proveedor lo puso** en este albaran (el
`contexto_linea` real era NULL; `progress/explore_F-036.md` §D2). F-036
lo midio y lo dejo escrito como hueco: sus importes de SS-0003967
estaban demostrados «bajo hipotesis», con el `tipo_familia` puesto a
mano en la fixture.

QUE CAMBIA AQUI. La linea sigue SIN `tipo_familia` —nadie la toca— y la
familia entra por el DOCUMENTO: IA1 clasifica el albaran como
`residuos`, sv3 lo persiste, sv5 lo mete en `context.clasificacion` y
`familia_efectiva` lo hereda a la linea en LECTURA. Se abren las tres
puertas de residuos y el albaran vale 210,00 EUR en 2 lineas.

LO QUE ESTE FICHERO **NO** DEMUESTRA, y esta escrito como test al final:
el 210,00 exige ademas que IA3 case la linea base contra el CONTENEDOR.
El match REAL de SS-0003967 fue contra la 26481, que es el INCREMENTO;
con clasificacion, la guarda de F-036 R15 lo anula —y hace bien: esa
linea tarifa el recargo, no la retirada— y el documento sale en 90,00
EUR **a revision**. Eso no lo arregla F-043 y no se disimula: se mide en
`test_f043_r26_con_el_match_real_de_ia3_la_guarda_deja_el_albaran_a_90`.
La comprobacion de extremo a extremo contra la BBDD real es T31, del
humano.

Sin red, sin BBDD y sin LLM: el builder real con sus cinco colaboradores
y el sobre de sv5 armado a mano, reutilizando
`tests/f036_escenarios_residuos.py`.
"""
from __future__ import annotations

import pytest
from ruesma_comun.contratos import ClasificacionAlbaran

from tests.f036_escenarios_residuos import (
    EscenarioResiduos,
    LineaResiduos,
    base_de,
    linea_contrato,
    sinteticas_de,
    valorar,
)

NUMERO = "SS-0003967"
CODIGO_LER = "170604"
CONCEPTO = "RETIRADA MATERIALES DE AISLAMIENTO"

#: Los tres importes del ground truth (§8.1).
TOTAL_ESPERADO = 210.0
PRECIO_CONTENEDOR = 120.0
PRECIO_INCREMENTO = 90.0

#: Lo que salio en BBDD con el prompt generico y sin familia: los 6 m3
#: del albaran valorados a 90 EUR/m3, la tarifa del INCREMENTO.
TOTAL_EN_BBDD = 540.0

# =================================================================== #
# El contrato CTSU24/0228 de la obra 687, reducido a lo que importa
# =================================================================== #

CTSU24_0228 = "CTSU24/0228"

CAMBIO_6M3 = linea_contrato(
    26473, "CAMBIO CONTENEDOR 6M3", PRECIO_CONTENEDOR,
    codigo_contrato=CTSU24_0228,
)
INCREMENTO_170802 = linea_contrato(
    26480,
    "INCREMENTO LER 170802 MATERIALES DE CONSTRUCCION A BASE DE YESO",
    51.0,
    codigo_contrato=CTSU24_0228,
)
INCREMENTO_170604 = linea_contrato(
    26481,
    "INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO",
    PRECIO_INCREMENTO,
    codigo_contrato=CTSU24_0228,
)
CONTRATO_0228 = (CAMBIO_6M3, INCREMENTO_170802, INCREMENTO_170604)

#: Lo que IA1 dice del DOCUMENTO. El motivo cita lo LEIDO en el papel,
#: que es lo que permite al revisor decidir si fiarse.
CLASIFICACION_IA1 = ClasificacionAlbaran(
    familia="residuos",
    confianza_pct=94.0,
    motivo=(
        "gestor autorizado de RCD: el albaran identifica el residuo por "
        "su codigo LER 170604 y documenta el cambio de un contenedor de "
        "6 m3 con destino a planta de tratamiento"
    ),
    origen="ia1",
)


def escenario(*, clasificacion, casa_con) -> EscenarioResiduos:
    """SS-0003967 tal como llega de sv5.

    ``tipo_familia=None`` y ``rol_linea=None`` NO son una simplificacion
    del test: son lo que de verdad traia el merge. Es justamente el
    campo que F-036 tuvo que poner a mano para llegar a los 210,00.
    """
    return EscenarioResiduos(
        lineas=(
            LineaResiduos(
                descripcion=CONCEPTO,
                cantidad=6.0,
                unidad="M3",
                codigo_ler=CODIGO_LER,
                volumen_m3=6.0,
                tipo_familia=None,
                rol_linea=None,
                matched_contrato_line_id=casa_con.contrato_line_id,
                precio_contrato_db=casa_con.precio_unitario,
                match_method="exact_concept",
            ),
        ),
        contrato=CONTRATO_0228,
        clasificacion=clasificacion,
        numero_albaran=NUMERO,
    )


# =================================================================== #
# R26 · el numero
# =================================================================== #

def test_f043_r26_ss0003967_vale_210_euros_en_dos_lineas():
    """**210,00 EUR en 2 lineas**, con la linea SIN ``tipo_familia``.

    El requisito, medido. 120,00 del contenedor + 90,00 del incremento
    por el LER 170604, que es la suma exacta del Excel del
    administrativo.
    """
    cabecera, registros = valorar(
        escenario(clasificacion=CLASIFICACION_IA1, casa_con=CAMBIO_6M3)
    )

    assert cabecera.total_valorado == pytest.approx(TOTAL_ESPERADO)
    assert len(registros) == 2


def test_f043_r26_la_base_es_un_contenedor_a_la_tarifa_del_contrato():
    """1 UD a 120,00, no los 6 m3 del papel.

    El 6 del albaran es la CAPACIDAD del contenedor. Valorarlo como
    cantidad da 720,00: es el defecto D1 del lote de SALMEDINA, y el
    total correcto podria taparlo si aqui solo se mirara la suma.
    """
    _cabecera, registros = valorar(
        escenario(clasificacion=CLASIFICACION_IA1, casa_con=CAMBIO_6M3)
    )
    base = base_de(registros)

    assert base.cantidad_convertida == pytest.approx(1.0)
    assert base.precio_unitario_contrato_db == pytest.approx(
        PRECIO_CONTENEDOR
    )
    assert base.importe_calculado == pytest.approx(PRECIO_CONTENEDOR)
    assert base.matched_contrato_line_id == CAMBIO_6M3.contrato_line_id


def test_f043_r26_la_segunda_linea_es_el_incremento_del_ler_170604():
    """Y es el incremento de ESE LER, no el del 170802 del mismo contrato.

    §8.2 del ground truth avisa: un total correcto puede tapar un match
    equivocado. Por eso se fija el concepto, el rol, la fuente y el
    padre, no solo el importe.
    """
    _cabecera, registros = valorar(
        escenario(clasificacion=CLASIFICACION_IA1, casa_con=CAMBIO_6M3)
    )
    sinteticas = sinteticas_de(registros)

    assert len(sinteticas) == 1
    sintetica = sinteticas[0]
    assert sintetica.descripcion_linea == f"INCREMENTO LER {CODIGO_LER}"
    assert sintetica.rol_linea == "incremento_residuos"
    assert sintetica.modifier_source == "gestion_residuos"
    assert sintetica.precio_unitario_contrato_db == pytest.approx(
        PRECIO_INCREMENTO
    )
    assert sintetica.cantidad_convertida == pytest.approx(1.0)
    assert sintetica.importe_calculado == pytest.approx(PRECIO_INCREMENTO)
    assert sintetica.parent_merge_line_id == base_de(registros).merge_line_id


# =================================================================== #
# El antes y el despues, con el MISMO sobre
# =================================================================== #

def test_f043_r26_el_unico_campo_que_cambia_es_la_clasificacion():
    """Mismo albaran, mismo contrato, mismo match: 720,00 -> 210,00.

    Es la medicion que aisla el efecto de la feature. Sin
    ``context.clasificacion`` no corre ninguna regla de residuos y los
    6 m3 se valoran como cantidad; con ella, 1 contenedor mas su
    incremento. Nadie ha escrito ``tipo_familia`` en la linea.
    """
    antes, registros_antes = valorar(
        escenario(clasificacion=None, casa_con=CAMBIO_6M3)
    )
    despues, registros_despues = valorar(
        escenario(clasificacion=CLASIFICACION_IA1, casa_con=CAMBIO_6M3)
    )

    assert antes.total_valorado == pytest.approx(720.0)
    assert len(registros_antes) == 1
    assert despues.total_valorado == pytest.approx(TOTAL_ESPERADO)
    assert len(registros_despues) == 2


def test_f043_r26_los_540_de_bbdd_eran_el_match_al_incremento_sin_familia():
    """De donde salieron los 540,00 EUR que se midieron en BBDD.

    6 m3 x 90,00 EUR/m3: la linea base casada con el INCREMENTO por LER
    —la 26481— y sin familia que dispare la guarda ni el calculo de
    contenedores. Se fija aqui para que el numero de R26 tenga su origen
    escrito y no sea un dato de contexto que se pierde.
    """
    cabecera, registros = valorar(
        escenario(clasificacion=None, casa_con=INCREMENTO_170604)
    )

    assert cabecera.total_valorado == pytest.approx(TOTAL_EN_BBDD)
    assert len(registros) == 1
    assert sinteticas_de(registros) == []


# =================================================================== #
# Lo que F-043 NO arregla, escrito como test
# =================================================================== #

def test_f043_r26_con_el_match_real_de_ia3_la_guarda_deja_el_albaran_a_90():
    """La precondicion que queda VIVA: el match de IA3.

    Con la clasificacion puesta pero el match REAL de SS-0003967 —la
    26481, que es el INCREMENTO y no el CONTENEDOR— la guarda de F-036
    R15 anula el casado y hace bien: esa linea no tarifa la retirada.
    Pero la base se queda sin precio y el documento sale en 90,00 EUR, a
    revision, en vez de los 210,00.

    O sea: F-043 abre las puertas de residuos, que era el hueco que
    tenia bloqueada F-036, y deja el albaran EXPLICADO en la pantalla
    del revisor en vez de valorado de mas en silencio. Que IA3 case el
    contenedor es trabajo del prompt (T30), no de esta tarea, y por eso
    T31 —la comprobacion contra la BBDD real— la hace el humano.
    """
    cabecera, registros = valorar(
        escenario(
            clasificacion=CLASIFICACION_IA1, casa_con=INCREMENTO_170604,
        )
    )
    base = base_de(registros)

    assert "residuos_base_casada_con_incremento" in base.review_reasons
    assert base.precio_unitario_contrato_db is None
    assert base.importe_calculado is None
    assert cabecera.total_valorado == pytest.approx(PRECIO_INCREMENTO)
    assert cabecera.review_required is True
    # Y el albaran ya NO sale en 540,00: valorar de menos y pedir
    # revision es lo que se buscaba frente a valorar de mas y callar.
    assert cabecera.total_valorado != pytest.approx(TOTAL_EN_BBDD)


def test_f043_r26_una_confianza_baja_no_impide_valorar_el_albaran():
    """La duda MARCA revision (en sv3), no bloquea la valoracion.

    Decision del humano (duda 3): un documento que no se valora no
    aparece en ninguna pantalla y nadie se entera — es lo que paso con
    los 20.632 EUR de PAVIMARSA. Con confianza por debajo del umbral,
    sv6 valora igual y son los 210,00 de siempre.
    """
    dudosa = ClasificacionAlbaran(
        familia="residuos",
        confianza_pct=35.0,
        motivo="el albaran esta muy borroso, pero se lee un codigo LER",
    )
    cabecera, registros = valorar(
        escenario(clasificacion=dudosa, casa_con=CAMBIO_6M3)
    )

    assert cabecera.total_valorado == pytest.approx(TOTAL_ESPERADO)
    assert len(registros) == 2
