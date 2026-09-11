# tests/test_f043_t31_cadena_merge_a_puertas.py
"""F-043 · T31 — la cadena REAL merge -> sobre de sv5 -> puertas de sv6.

Los tests de residuos de este servicio (``f036_escenarios_residuos``,
``test_f043_r26_ss0003967``) construyen la linea con su
``contexto_linea`` YA puesto. Por eso ninguno vio el defecto medido el
2026-09-11 contra el pipeline local con LLM real: en el merge de
SS-0003967 ese contexto era **NULL**, y el sobre que sv5 le paso a sv6
llevaba ``"contexto_linea": null`` con la clasificacion del documento
correctamente puesta al lado.

Aqui se mide esa cadena de punta a punta con los artefactos REALES de
aquella corrida —el sobre que sv6 persistio en
``albaran_valuations.raw_ia_envelope_json`` (valuation_id
``0220e926-1919-4f9a-a055-69b6fa102de6``)— cambiando UNA sola cosa: el
``contexto_linea_json`` de la fila del merge.

  * como estaba el 2026-09-11 (NULL) -> **720,00 EUR en 1 linea**;
  * con el contexto que IA2 SI habia emitido -> **210,00 EUR en 2**.

Los 720 no son un fallo de sv6: la clasificacion del documento abre las
puertas de familia (la valoracion real trae la razon
``residuos_sin_volumen_m3``, que solo se alcanza DENTRO de la puerta de
residuos), pero sin ``volumen_m3`` no hay contenedores que contar y sin
``codigo_ler`` no hay incremento que inyectar. El defecto esta en sv3,
que en su rama de duplicado no escribia el contexto en el merge; su
test RED vive en ``services/albaranes-persistencia/tests/
test_f043_t31_contexto_linea_en_duplicado.py``.

El JSON de ``CONTEXTO_LINEA_MERGE`` es literalmente lo que sv3 escribe
en la columna y lo que sv5 valida contra ``ContextoLinea`` de
``ruesma_comun`` antes de meterlo en el sobre: es el punto exacto donde
se tocan los tres servicios, y ningun proceso de pytest puede recorrer
los tres a la vez (sv3, sv5 y sv6 tienen todos un paquete ``domain``).

Sin red, sin BBDD y sin LLM.
"""
from __future__ import annotations

import json

import pytest

from domain.models.valuation_envelope import ValuationEnvelope
from tests.f027_escenarios import construir_builder

DOCUMENT_ID = "1dc06154-00ce-4c80-9de3-7a41cc0a08c3"
MERGE_LINE_ID = 401

#: Lo que IA2 emitio para la unica linea y sv3 perdia en el re-proceso,
#: tal cual queda en ``albaran_lines_merge.contexto_linea_json`` (sv3 lo
#: serializa con ``exclude_none``). Mismo dato que en el test RED de sv3.
CONTEXTO_LINEA_MERGE = json.dumps(
    {
        "tipo_familia": "residuos",
        "rol_linea": "base",
        "codigo_ler": "170604",
        "volumen_m3": 6.0,
        "peso_toneladas": 0.18,
    },
    ensure_ascii=False,
)

#: El contrato CTSU24/0228 tal como lo leyo sv5 el 2026-09-11 (7 lineas).
LINEAS_CONTRATO = [
    (26523, "LLEVADA CONTENEDOR 6M3", 120.0),
    (26524, "CAMBIO CONTENEDOR 6M3", 120.0),
    (26525, "CAMBIO CONTENEDOR PODA", 220.0),
    (26526, "INCREMENTO LER 170202 VIDRIO-E", 120.0),
    (26527, "INCREMENTO LER 170302 MEZCLAS BITUMINOSAS-E", 30.0),
    (26528, "INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO-E", 90.0),
    (26529, "INCREMENTO LER 170802 MAT. DE CONST. A PARTIR DE YESOS-E", 51.0),
]

PRECIO_CONTENEDOR = 120.0
PRECIO_INCREMENTO = 90.0
#: Lo que salio de verdad el 2026-09-11: 6 m3 x 120 EUR.
TOTAL_MEDIDO_SIN_CONTEXTO = 720.0
#: El ground truth del administrativo (R26): 120 + 90.
TOTAL_ESPERADO = 210.0


def _sobre(*, contexto_linea_json: str | None) -> ValuationEnvelope:
    """El sobre REAL de sv5, con el contexto de la linea como parametro.

    ``contexto_linea`` entra como el JSON de la columna del merge y se
    deserializa igual que hace sv5 antes de armar el sobre; ``None`` es
    la columna a NULL, que es como estaba el merge aquel dia.
    """
    return ValuationEnvelope.model_validate(
        {
            "status": "ok",
            "meta": {
                "document_id": DOCUMENT_ID,
                "codigo_contrato": "CTSU24/0228",
                "fecha_albaran": "2024-07-10",
                "numero_albaran": "SS-0003967",
                "prompt_key": "valuation_residuos",
                "schema": "documento_valoracion",
                "primary_provider": "claude",
                "model": "claude-opus-4-8",
                "providers_used": ["claude"],
            },
            # Salida LITERAL de IA3 en la corrida del 2026-09-11.
            "data": {
                "lineas": [
                    {
                        "merge_line_id": MERGE_LINE_ID,
                        "line_kind": "from_albaran",
                        "rol_linea": "base",
                        "match_method": "semantic",
                        "matched_contrato_line_id": 26523,
                        "match_confidence_pct": 80.0,
                        "unidad_categoria_albaran": "volume",
                        "unidad_category_match": False,
                        "precio_unitario_contrato_db": PRECIO_CONTENEDOR,
                        "precio_unitario_pdf_inferido": PRECIO_CONTENEDOR,
                        "contenedor_m3": 6.0,
                    }
                ]
            },
            "context": {
                "lineas_albaran": [
                    {
                        "merge_line_id": MERGE_LINE_ID,
                        "line_index": 1,
                        "codigo": "170604",
                        "descripcion": "Mat. Aislamiento",
                        "unidad_medida": None,
                        "unidad_categoria": "unknown",
                        "cantidad": 6.0,
                        "contexto_linea": (
                            json.loads(contexto_linea_json)
                            if contexto_linea_json is not None
                            else None
                        ),
                    }
                ],
                "lineas_contrato": [
                    {
                        "contrato_line_id": cid,
                        "codigo_contrato": "CTSU24/0228",
                        "codigo_producto": "QA9999",
                        "descripcion": desc,
                        "unidad_medida": "UD",
                        "unidad_categoria": "unit",
                        "precio_unitario": precio,
                    }
                    for cid, desc, precio in LINEAS_CONTRATO
                ],
                # La clasificacion SI llegaba, y bien: es lo que F-043
                # entrega y lo que abre las puertas de familia.
                "clasificacion": {
                    "familia": "residuos",
                    "confianza_pct": 100.0,
                    "motivo": (
                        "Documento de identificacion y control de traslado "
                        "de residuos con codigo LER 170604."
                    ),
                    "mixto": False,
                    "familias_secundarias": [],
                    "origen": "ia2",
                },
            },
            "debug": {},
        }
    )


def _valorar(*, contexto_linea_json: str | None):
    return construir_builder().build(
        envelope=_sobre(contexto_linea_json=contexto_linea_json),
        existing_document_already_valued=False,
    )


def _base(registros):
    bases = [r for r in registros if r.line_kind == "from_albaran"]
    assert len(bases) == 1, bases
    return bases[0]


def _sinteticas(registros):
    return [r for r in registros if r.line_kind == "synthetic_modifier"]


# ------------------------------------------------------------------ #
# Lo que se midio el 2026-09-11: el merge SIN contexto de linea.
# ------------------------------------------------------------------ #

def test_f043_t31_sin_contexto_en_el_merge_salen_los_720_medidos():
    """Reproduce el numero real de la corrida con LLM: 720,00 en 1 linea.

    Con la clasificacion puesta y el contexto de la linea a NULL, la
    puerta de residuos se abre pero no hay nada que contar: la cantidad
    valorada cae a los 6 m3 del albaran contra los 120 EUR/contenedor.
    """
    cabecera, registros = _valorar(contexto_linea_json=None)

    assert cabecera.total_valorado == pytest.approx(
        TOTAL_MEDIDO_SIN_CONTEXTO
    )
    assert len(registros) == 1
    assert _base(registros).cantidad_convertida == pytest.approx(6.0)


def test_f043_t31_sin_contexto_la_puerta_de_residuos_si_estaba_abierta():
    """La prueba de que la clasificacion NO se perdia entre sv5 y sv6.

    ``residuos_sin_volumen_m3`` la emite ``calcular_contenedores_
    residuos``, a la que solo se llega dentro de la puerta
    ``_familia_de(ctx, clasificacion) == 'residuos'``. Con la linea sin
    ``tipo_familia``, esa familia solo puede venir del DOCUMENTO. Es la
    misma razon que trae la fila REAL de ``albaran_line_valuations``.
    """
    _cabecera, registros = _valorar(contexto_linea_json=None)

    assert "residuos_sin_volumen_m3" in _base(registros).review_reasons


# ------------------------------------------------------------------ #
# Con el contexto que sv3 ya escribe: el numero del administrativo.
# ------------------------------------------------------------------ #

def test_f043_t31_con_el_contexto_en_el_merge_el_albaran_vale_210():
    """120,00 del contenedor + 90,00 del incremento por el LER 170604."""
    cabecera, registros = _valorar(
        contexto_linea_json=CONTEXTO_LINEA_MERGE
    )

    assert cabecera.total_valorado == pytest.approx(TOTAL_ESPERADO)
    assert len(registros) == 2


def test_f043_t31_con_el_contexto_la_base_es_un_contenedor():
    """1 UD a 120,00: el 6 del papel son los m3, no las unidades."""
    _cabecera, registros = _valorar(
        contexto_linea_json=CONTEXTO_LINEA_MERGE
    )
    base = _base(registros)

    assert base.cantidad_convertida == pytest.approx(1.0)
    assert base.matched_contrato_line_id == 26523
    assert base.importe_calculado == pytest.approx(PRECIO_CONTENEDOR)


def test_f043_t31_con_el_contexto_se_inyecta_el_incremento_del_ler():
    """La sintetica que IA3 dijo expresamente que no emitia porque la
    inyecta sv6 (``razon_corta`` de la corrida real)."""
    _cabecera, registros = _valorar(
        contexto_linea_json=CONTEXTO_LINEA_MERGE
    )
    sinteticas = _sinteticas(registros)

    assert len(sinteticas) == 1
    sintetica = sinteticas[0]
    assert sintetica.descripcion_linea == "INCREMENTO LER 170604"
    assert sintetica.rol_linea == "incremento_residuos"
    assert sintetica.matched_contrato_line_id == 26528
    assert sintetica.importe_calculado == pytest.approx(PRECIO_INCREMENTO)
    assert sintetica.parent_merge_line_id == MERGE_LINE_ID


# ------------------------------------------------------------------ #
# R27 — sin clasificacion, el sobre se comporta exactamente como hoy.
# ------------------------------------------------------------------ #

def test_f043_r27_sin_clasificacion_no_se_abre_ninguna_puerta():
    """Mismo sobre, con contexto de linea pero SIN clasificacion y sin
    ``tipo_familia``: ninguna regla de residuos corre."""
    sobre = _sobre(contexto_linea_json=CONTEXTO_LINEA_MERGE)
    sobre.context.clasificacion = None
    sobre.context.lineas_albaran[0].contexto_linea.tipo_familia = None

    cabecera, registros = construir_builder().build(
        envelope=sobre, existing_document_already_valued=False,
    )

    assert cabecera.total_valorado == pytest.approx(
        TOTAL_MEDIDO_SIN_CONTEXTO
    )
    assert len(registros) == 1
