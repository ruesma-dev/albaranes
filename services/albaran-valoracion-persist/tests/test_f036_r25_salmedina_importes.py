# tests/test_f036_r25_salmedina_importes.py
"""F-036 R25 · escenario de ACEPTACION del lote de SALMEDINA (T21, T22).

Los seis albaranes en alcance de
`progress/revision_residuos_salmedina_20260819.md` §8.1 (el ground truth
del Excel del administrativo), con sus importes reales. El septimo,
SS-0026122, queda FUERA: su tarifa de 9 m3 va contra la OFERTA y eso es
F-017.

| Albaran     | LER    | Contrato    | Contenedor | Incremento | TOTAL  |
|-------------|--------|-------------|------------|------------|--------|
| SS-0000168  | 170201 | CTSU24/0228 | 120,00     | no tarifado| 120,00 |
| SS-0000589  | 170802 | CTSU24/0228 | 120,00     | 51,00      | 171,00 |
| SS-0003935  | 170107 | CTSU24/0228 | 120,00     | no tarifado| 120,00 |
| SS-0003967  | 170604 | CTSU24/0228 | 120,00     | 90,00      | 210,00 |
| SS-0801977  | 170604 | CTSU24/0228 | 120,00     | 90,00      | 210,00 |
| SS-0025146  | 170904 | CTSU24/0402 | 136,00     | no tarifado| 136,00 |

Los tres de la derecha a 120/120/136 **YA salen bien hoy**, y su
invariante es el TOTAL: por R16/R17 los tres GANAN una linea sintetica
SIN precio y pasan a `review_required`. Eso es lo QUERIDO (decision del
humano del 2026-08-22), no una regresion: el incremento por LER existe
en la realidad aunque el contrato no lo tarife, y el revisor tiene que
poder ponerle el importe. Un test que exigiera "una sola linea" o
"nada que revisar" estaria fijando el defecto, no el requisito.

En los seis la cantidad valorada es **1 UD** (un contenedor), no los 6
del albaran: el numero del documento es la CAPACIDAD del contenedor
(§8.1 del ground truth).

ALCANCE DE ESTE FICHERO (leer antes de darlo por prueba de R25).
Mide **sv6 desde el sobre que le entrega sv5**, con fixtures: sin red,
sin BBDD y sin LLM. Los importes de R25 salen SOLO si se cumplen DOS
precondiciones, y ninguna de las dos la arregla F-036:

1. **El `contexto_linea` del merge trae `tipo_familia='residuos'`**,
   porque toda la maquinaria de residuos de sv6 esta cerrada tras esa
   comprobacion (`valuation_builder.py:1165`, `:846`, `:985`). En
   SS-0003967 no se cumple: su merge real tenia `contexto_linea = NULL`
   y ninguna tarea de F-036 lo restituye (R9-R12 rellenan las nueve
   MEDIDAS, y R12 deja los narrativos intactos a proposito). Fijado en
   `test_f036_r25_sin_tipo_familia_no_corre_ninguna_regla_de_residuos`.

2. **IA3 caso la linea base contra el CONTENEDOR del contrato**, no
   contra la linea de INCREMENTO. En SS-0003967 el match real fue a la
   26481 ("INCREMENTO LER 170604"), y con `tipo_familia` puesto la
   guarda de R15 lo ANULA —correctamente: esa linea no tarifa la
   retirada— dejando la base sin precio. El documento sale entonces en
   **90,00 EUR** (solo la sintetica) frente a los 210,00 de R25. Fijado
   en `test_f036_r25_con_el_match_real_de_ss_0003967_no_se_llega_a_210`.

O sea: de los tres importes de R25, el de SS-0003967 esta demostrado
aqui **bajo hipotesis**, no medido contra lo que hoy llega de sv5.
Arreglar el match de IA3 y la restitucion del `tipo_familia` es trabajo
FUERA de F-036 (ver `progress/impl_F-036_bloque_D.md`).
"""
from __future__ import annotations

import pytest

from tests.f036_escenarios_residuos import (
    EscenarioResiduos,
    LineaResiduos,
    base_de,
    linea_contrato,
    sinteticas_de,
    valorar,
)

# =================================================================== #
# Los dos contratos del lote (los precios son los del ground truth)
# =================================================================== #

CTSU24_0228 = "CTSU24/0228"
CTSU24_0402 = "CTSU24/0402"

#: Obra 687 · lo que se factura por retirada, mas los DOS incrementos
#: por LER que el contrato SI tiene cargados en Sigrid.
CAMBIO_6M3 = linea_contrato(
    26473, "CAMBIO CONTENEDOR 6M3", 120.0, codigo_contrato=CTSU24_0228,
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
    90.0,
    codigo_contrato=CTSU24_0228,
)
CONTRATO_0228 = (CAMBIO_6M3, INCREMENTO_170802, INCREMENTO_170604)

#: Obra 691 · otro contrato, otra tarifa y NINGUN incremento por LER.
CONTENEDOR_6M3_0402 = linea_contrato(
    31104, "CONTENEDOR RESIDUOS 6 M3", 136.0, codigo_contrato=CTSU24_0402,
)
CONTRATO_0402 = (CONTENEDOR_6M3_0402,)


class Albaran:
    """Un albaran del lote y lo que el administrativo espera de el."""

    def __init__(
        self,
        numero: str,
        codigo_ler: str,
        concepto: str,
        contrato: tuple,
        contenedor,
        total: float,
        incremento: float | None,
    ) -> None:
        self.numero = numero
        self.codigo_ler = codigo_ler
        self.concepto = concepto
        self.contrato = contrato
        self.contenedor = contenedor
        self.total = total
        #: Precio del incremento por LER, o ``None`` si el contrato no
        #: lo tarifa (la sintetica se emite igual, sin precio).
        self.incremento = incremento

    def __repr__(self) -> str:  # pragma: no cover - solo para el -v
        return self.numero

    def escenario(self) -> EscenarioResiduos:
        """El sobre de sv5 con el contexto ya reparado por sv3 (T9/T10).

        `cantidad=6.0` en M3 es lo que trae el albaran; `volumen_m3=6.0`
        es la medida que sv3 persiste en el contexto. El contenedor de
        6 m3 sale de la descripcion de la linea de contrato.
        """
        return EscenarioResiduos(
            lineas=(
                LineaResiduos(
                    descripcion=self.concepto,
                    cantidad=6.0,
                    unidad="M3",
                    codigo_ler=self.codigo_ler,
                    volumen_m3=6.0,
                    tipo_familia="residuos",
                    rol_linea="base",
                    matched_contrato_line_id=self.contenedor.contrato_line_id,
                    precio_contrato_db=self.contenedor.precio_unitario,
                ),
            ),
            contrato=self.contrato,
            numero_albaran=self.numero,
        )


#: T21 — los tres que HOY salen mal por no emitirse el incremento.
INFRAVALORADOS = [
    Albaran(
        "SS-0000589", "170802", "RETIRADA MATERIALES A BASE DE YESO",
        CONTRATO_0228, CAMBIO_6M3, 171.0, 51.0,
    ),
    Albaran(
        "SS-0003967", "170604", "RETIRADA MATERIALES DE AISLAMIENTO",
        CONTRATO_0228, CAMBIO_6M3, 210.0, 90.0,
    ),
    Albaran(
        "SS-0801977", "170604", "RETIRADA MATERIALES DE AISLAMIENTO",
        CONTRATO_0228, CAMBIO_6M3, 210.0, 90.0,
    ),
]

#: T22 — los tres que HOY ya aciertan el total y deben seguir igual.
CORRECTOS = [
    Albaran(
        "SS-0000168", "170201", "RETIRADA DE MADERA",
        CONTRATO_0228, CAMBIO_6M3, 120.0, None,
    ),
    Albaran(
        "SS-0003935", "170107", "RETIRADA DE HORMIGON LADRILLO Y CERAMICA",
        CONTRATO_0228, CAMBIO_6M3, 120.0, None,
    ),
    Albaran(
        "SS-0025146", "170904", "RETIRADA DE MATERIALES MEZCLADOS",
        CONTRATO_0402, CONTENEDOR_6M3_0402, 136.0, None,
    ),
]

TODOS = INFRAVALORADOS + CORRECTOS


# =================================================================== #
# T21 · los tres infravalorados alcanzan el total del administrativo
# =================================================================== #

@pytest.mark.parametrize("albaran", INFRAVALORADOS, ids=lambda a: a.numero)
def test_f036_r25_el_incremento_por_ler_completa_el_total(albaran):
    """171,00 / 210,00 / 210,00: contenedor + incremento del LER.

    Es la suma exacta del ground truth: 120 + 51 en el 170802 y
    120 + 90 en los dos del 170604. Hoy el pipeline se queda en el
    contenedor porque nadie emite la segunda linea.
    """
    cabecera, registros = valorar(albaran.escenario())

    assert cabecera.total_valorado == pytest.approx(albaran.total)
    assert len(registros) == 2


@pytest.mark.parametrize("albaran", INFRAVALORADOS, ids=lambda a: a.numero)
def test_f036_r25_la_sintetica_lleva_la_tarifa_del_ler(albaran):
    """La segunda linea es el incremento de ESE LER, a 1 contenedor.

    Se fija el CONCEPTO y no solo el importe: §8.2 del ground truth
    avisa de que un total correcto puede tapar un match equivocado.
    """
    _cabecera, registros = valorar(albaran.escenario())
    sinteticas = sinteticas_de(registros)

    assert len(sinteticas) == 1
    syn = sinteticas[0]
    assert syn.descripcion_linea == f"INCREMENTO LER {albaran.codigo_ler}"
    assert syn.rol_linea == "incremento_residuos"
    assert syn.modifier_source == "gestion_residuos"
    assert syn.precio_unitario_contrato_db == pytest.approx(albaran.incremento)
    assert syn.cantidad_convertida == pytest.approx(1.0)
    assert syn.importe_calculado == pytest.approx(albaran.incremento)
    assert syn.parent_merge_line_id == base_de(registros).merge_line_id


# =================================================================== #
# T22 · los tres correctos conservan el TOTAL y ganan la linea sin precio
# =================================================================== #

@pytest.mark.parametrize("albaran", CORRECTOS, ids=lambda a: a.numero)
def test_f036_r25_el_total_de_los_correctos_no_se_mueve(albaran):
    """120,00 / 120,00 / 136,00 siguen siendo los del administrativo.

    El invariante de estos tres es el TOTAL, no el nº de lineas: la
    sintetica del LER se emite igual y no suma nada porque el contrato
    no tarifa ese incremento.
    """
    cabecera, registros = valorar(albaran.escenario())

    assert cabecera.total_valorado == pytest.approx(albaran.total)
    assert base_de(registros).importe_calculado == pytest.approx(albaran.total)


@pytest.mark.parametrize("albaran", CORRECTOS, ids=lambda a: a.numero)
def test_f036_r25_ganan_una_sintetica_sin_precio_y_van_a_revision(albaran):
    """R16/R17: la linea sin tarifa se emite y PIDE revision.

    Es el efecto QUERIDO de la decision del humano del 2026-08-22, no
    una regresion de estos tres albaranes: el gestor cobra el recargo
    aunque Sigrid no lo tenga cargado, y sin linea visible nadie se lo
    reclama. Por eso se fija aqui, en el escenario de aceptacion.
    """
    cabecera, registros = valorar(albaran.escenario())
    sinteticas = sinteticas_de(registros)

    assert len(sinteticas) == 1
    syn = sinteticas[0]
    assert syn.descripcion_linea == f"INCREMENTO LER {albaran.codigo_ler}"
    assert syn.precio_unitario_contrato_db is None
    assert syn.importe_calculado is None
    assert syn.match_method == "no_match"
    assert "residuos_ler_sin_tarifa_en_contrato" in syn.review_reasons
    assert syn.review_required is True
    assert cabecera.review_required is True


# =================================================================== #
# Invariante comun a los seis (ground truth §8.1)
# =================================================================== #

@pytest.mark.parametrize("albaran", TODOS, ids=lambda a: a.numero)
def test_f036_r25_siempre_se_valora_un_contenedor_y_no_seis_m3(albaran):
    """1 UD, no 6 m3, y a la tarifa del contenedor del contrato.

    El 6 del albaran es la CAPACIDAD del contenedor. Valorarlo como
    cantidad da 720 (o 816 en el 0402), que es el defecto D1 medido en
    SS-0801977.
    """
    _cabecera, registros = valorar(albaran.escenario())
    base = base_de(registros)

    assert base.cantidad_convertida == pytest.approx(1.0)
    assert base.precio_unitario_contrato_db == pytest.approx(
        albaran.contenedor.precio_unitario
    )
    assert base.matched_contrato_line_id == albaran.contenedor.contrato_line_id


# =================================================================== #
# La precondicion de todo lo anterior, escrita como test
# =================================================================== #

def test_f036_r25_sin_tipo_familia_no_corre_ninguna_regla_de_residuos():
    """Toda la maquinaria de residuos de sv6 exige `tipo_familia`.

    No es un defecto: es el AISLAMIENTO deliberado que documenta
    `valuation_builder.py:1162` ("solo afecta a lineas
    tipo_familia='residuos'"), y se fija aqui para que nadie lo relaje
    sin darse cuenta.

    Tiene consecuencia directa sobre R25: el merge real de SS-0003967
    traia `contexto_linea = NULL` (`progress/explore_F-036.md`,
    apendice D2), y ni el scorer de sv3 (R9-R12, que solo restituye las
    nueve MEDIDAS y deja intactos los cinco campos NARRATIVOS por R12)
    ni ninguna otra tarea de F-036 le devuelven el `tipo_familia`. Con
    el contexto que de verdad llega —LER si, familia no— sv6 no calcula
    contenedores, no emite la sintetica y no aplica la guarda de R15:
    el albaran se queda en los 540,00 EUR medidos en BBDD.
    """
    caso = INFRAVALORADOS[1]
    assert caso.numero == "SS-0003967"

    escenario = EscenarioResiduos(
        lineas=(
            LineaResiduos(
                descripcion=caso.concepto,
                cantidad=6.0,
                unidad="M3",
                codigo_ler=caso.codigo_ler,
                volumen_m3=6.0,
                tipo_familia=None,
                rol_linea=None,
                matched_contrato_line_id=INCREMENTO_170604.contrato_line_id,
                precio_contrato_db=INCREMENTO_170604.precio_unitario,
                match_method="exact_concept",
            ),
        ),
        contrato=CONTRATO_0228,
        numero_albaran=caso.numero,
    )
    _cabecera, registros = valorar(escenario)

    assert sinteticas_de(registros) == []
    base = base_de(registros)
    assert base.cantidad_convertida is None
    assert "residuos_base_casada_con_incremento" not in base.review_reasons


def test_f036_r25_con_el_match_real_de_ss_0003967_no_se_llega_a_210():
    """La SEGUNDA precondicion de R25, escrita como test.

    Con `tipo_familia` puesto pero el match REAL de IA3 —la linea 26481,
    que es el INCREMENTO y no el CONTENEDOR— la guarda de R15 anula el
    match, y hace bien: esa linea no tarifa la retirada. Pero la base se
    queda sin precio y el documento sale en 90,00 EUR (solo la
    sintetica) en vez de los 210,00 de R25.

    No es un defecto de F-036 ni algo que F-036 arregle: es la hipotesis
    sobre la que descansa el importe de SS-0003967 en los tests de
    arriba, y se fija aqui para que nadie lea el escenario como si el
    numero ya estuviera conseguido de punta a punta.
    """
    caso = INFRAVALORADOS[1]
    assert caso.numero == "SS-0003967"

    escenario = EscenarioResiduos(
        lineas=(
            LineaResiduos(
                descripcion=caso.concepto,
                cantidad=6.0,
                unidad="M3",
                codigo_ler=caso.codigo_ler,
                volumen_m3=6.0,
                tipo_familia="residuos",
                rol_linea="base",
                matched_contrato_line_id=INCREMENTO_170604.contrato_line_id,
                precio_contrato_db=INCREMENTO_170604.precio_unitario,
                match_method="exact_concept",
            ),
        ),
        contrato=CONTRATO_0228,
        numero_albaran=caso.numero,
    )
    cabecera, registros = valorar(escenario)
    base = base_de(registros)

    assert "residuos_base_casada_con_incremento" in base.review_reasons
    assert base.precio_unitario_contrato_db is None
    assert base.importe_calculado is None
    assert cabecera.total_valorado == pytest.approx(90.0)
    assert cabecera.total_valorado != pytest.approx(caso.total)
