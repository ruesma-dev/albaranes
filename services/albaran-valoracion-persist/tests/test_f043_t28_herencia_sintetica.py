# tests/test_f043_t28_herencia_sintetica.py
"""T28 · la guarda que sostiene el mutante equivalente de la herencia.

El superviviente `valuation_builder.py:1532` de la campana de F-043

    elif parent_record is not None and parent_record.cantidad_albaran is not None:
    ->  elif parent_record is not None and parent_record.cantidad_albaran is None:

es un mutante EQUIVALENTE, no un hueco de test. La rama decide de donde
hereda la cantidad una linea sintetica que NO cuelga de una base de
residuos:

    elif parent_record is not None and parent_record.cantidad_albaran is not None:
        cantidad = parent_record.cantidad_albaran
    elif parent_albaran is not None:
        cantidad = parent_albaran.cantidad
    else:
        cantidad = None

Los dos candidatos salen del MISMO sitio. `_build_synthetic_line` busca
`parent_albaran = albaran_by_id.get(parent_merge_line_id)`, y el
`parent_record` que recibe es el que la pasada 2 guardo en
`records_by_merge_id[parent_merge_line_id]`, construido por `_build_line`
con `cantidad_albaran = albaran_line.cantidad if albaran_line else None`
sobre ese mismo `albaran_by_id` y esa misma clave. De ahi que, caso por
caso, original y mutante den identica `cantidad`:

  * hay linea de albaran con cantidad -> `cantidad_albaran ==
    parent_albaran.cantidad`: el original toma la primera, el mutante cae
    a la segunda, y valen lo mismo.
  * hay linea de albaran con `cantidad = None` -> `cantidad_albaran` es
    None: el original cae al `elif` y toma `parent_albaran.cantidad`, que
    es None; el mutante entra y toma `cantidad_albaran`, que es None.
  * no hay linea de albaran -> `cantidad_albaran` es None y
    `parent_albaran` es None: el original llega al `else`, el mutante
    entra en el `elif`, y los dos dejan None.

Estos tests NO matan al mutante: ejecutan la rama, pero el valor
resultante coincide y ninguna asercion puede distinguirlos. Lo que
guardan es el INVARIANTE del que depende esa justificacion —que
`cantidad_albaran` de la base sale de la linea de albaran de su propio
`merge_line_id` y de ninguna otra fuente—. Si manana alguien alimenta
`cantidad_albaran` desde el contrato, desde `cantidad_override` o desde
la cantidad ya convertida, los dos candidatos dejan de coincidir, el
mutante deja de ser equivalente y pasa a ser un hueco real. Sin esta
guarda eso ocurriria en silencio.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest
from tests.f027_escenarios import construir_builder

#: Partida comun a la base y al contrato: la herencia de partida no es
#: lo que se mide aqui y conviene que no meta ruido.
PARTIDA = "32.01"

BASE_MERGE_ID = 621


def _envelope(*, cantidad_base: float | None, con_linea_de_albaran: bool):
    """Un albaran de hormigon con una base y una sintetica colgando.

    `con_linea_de_albaran=False` reproduce el tercer caso: IA3 devuelve
    una linea `from_albaran` cuyo `merge_line_id` no tiene contraparte en
    `context.lineas_albaran`, asi que `albaran_by_id` no lo conoce.
    """
    from domain.models.valuation_envelope import (
        AlbaranLineContextDto,
        ContratoLineContextDto,
        DocumentoValoracionDto,
        LineValuationDto,
        ValuationContextDto,
        ValuationEnvelope,
        ValuationEnvelopeMeta,
    )

    base = LineValuationDto(
        merge_line_id=BASE_MERGE_ID,
        line_kind="from_albaran",
        match_method="semantic",
        matched_contrato_line_id=9001,
        match_confidence_pct=90.0,
        unidad_categoria_albaran="volume",
        unidad_category_match=True,
        precio_unitario_contrato_db=72.0,
        descripcion_linea="HORMIGON HA-25/B/20/IIa",
    )
    sintetica = LineValuationDto(
        merge_line_id=None,
        line_kind="synthetic_modifier",
        parent_merge_line_id=BASE_MERGE_ID,
        modifier_source="servicio_bomba",
        match_method="no_match",
        precio_unitario_pdf_inferido=15.0,
        descripcion_linea="SERVICIO DE BOMBA",
    )

    contrato = [
        ContratoLineContextDto(
            contrato_line_id=9001,
            codigo_contrato="CTSU25/0085",
            codigo_producto="MA9999",
            descripcion="HORMIGON HA-25/B/20/IIa",
            unidad_medida="M3",
            precio_unitario=72.0,
            codigo_partida=PARTIDA,
        ),
    ]

    lineas_albaran = []
    if con_linea_de_albaran:
        lineas_albaran.append(
            AlbaranLineContextDto(
                merge_line_id=BASE_MERGE_ID,
                line_index=0,
                descripcion="HORMIGON HA-25/B/20/IIa",
                unidad_medida="M3",
                unidad_categoria="volume",
                cantidad=cantidad_base,
                precio_unitario_albaran=None,
                importe_albaran=None,
                codigo_partida_albaran=PARTIDA,
            )
        )

    return ValuationEnvelope(
        status="ok",
        meta=ValuationEnvelopeMeta(
            document_id="doc-T28",
            codigo_contrato="CTSU25/0085",
            numero_albaran="HM-0000001",
        ),
        data=DocumentoValoracionDto(lineas=[base, sintetica]),
        context=ValuationContextDto(
            lineas_albaran=lineas_albaran,
            lineas_contrato=contrato,
        ),
    )


def _valorar(*, cantidad_base: float | None, con_linea_de_albaran: bool = True):
    """Devuelve `(base, sintetica)` ya construidas por el builder real."""
    _, registros = construir_builder().build(
        envelope=_envelope(
            cantidad_base=cantidad_base,
            con_linea_de_albaran=con_linea_de_albaran,
        ),
        existing_document_already_valued=False,
    )
    bases = [r for r in registros if r.line_kind == "from_albaran"]
    sinteticas = [r for r in registros if r.line_kind == "synthetic_modifier"]
    assert len(bases) == 1 and len(sinteticas) == 1, registros
    return bases[0], sinteticas[0]


# ------------------------------------------------------------------ #
# El invariante: `cantidad_albaran` de la base ES la cantidad de SU
# linea de albaran. Es lo unico que hace equivalentes a los dos
# candidatos de la herencia.
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("cantidad", [8.0, 0.0, None])
def test_t28_la_base_copia_la_cantidad_de_su_linea_de_albaran(cantidad):
    """`cantidad_albaran` no se inventa ni se convierte: se copia.

    Si esta asercion cae, `parent_record.cantidad_albaran` y
    `parent_albaran.cantidad` han dejado de ser el mismo numero y el
    mutante de `valuation_builder.py:1532` ya NO es equivalente.
    """
    base, _ = _valorar(cantidad_base=cantidad)

    assert base.cantidad_albaran == cantidad


def test_t28_sin_linea_de_albaran_la_base_se_queda_sin_cantidad_albaran():
    """El tercer caso: `albaran_by_id` no conoce el `merge_line_id`.

    Entonces los DOS candidatos de la herencia son None a la vez —
    `parent_record.cantidad_albaran` porque `_build_line` no encontro
    linea, y `parent_albaran` porque es el mismo `get` fallido—, que es
    justamente lo que hace indistinguibles al original y al mutante.
    """
    base, sintetica = _valorar(cantidad_base=8.0, con_linea_de_albaran=False)

    assert base.cantidad_albaran is None
    assert sintetica.cantidad_albaran is None


# ------------------------------------------------------------------ #
# La consecuencia observable: la sintetica hereda ESA cantidad.
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("cantidad", [8.0, 0.0, None])
def test_t28_la_sintetica_hereda_la_cantidad_de_la_base(cantidad):
    """Fuera de residuos, la sintetica vale lo que valga la base.

    Se afirma contra los DOS candidatos a la vez: mientras coincidan, la
    rama mutada no puede cambiar el resultado.
    """
    base, sintetica = _valorar(cantidad_base=cantidad)

    assert sintetica.cantidad_albaran == cantidad
    assert sintetica.cantidad_albaran == base.cantidad_albaran
