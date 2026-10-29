# tests/test_f106_fila.py
"""F-106 R4–R10, R16, R32 a: editar una fila recalcula lo que toca y la deja cuadrando.

Regla del humano (D1): cantidad, precio o dto ⇒ importe; importe ⇒ precio (el
dto se queda); las columnas grises (blancas del merge) nunca se tocan.

Dominio puro (``recalculo_de_fila``, el cuerpo del PATCH, el aviso de aprobar)
y repositorio real sobre SQLite (``f065_bbdd``). Sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


# =================================================================== #
# Dominio · recalculo_de_fila (tabla de design §4)
# =================================================================== #
@pytest.mark.parametrize(
    ("cambios", "cuadrar", "no_cuadra", "esperado"),
    [
        ({"cantidad": 48.0}, None, False, "importe"),
        ({"precio_unitario": 2.0}, None, False, "importe"),
        ({"descuento": 5.0}, None, True, "importe"),
        ({"importe": 104.16}, None, False, "precio"),
        ({"importe": 104.16, "cantidad": 48.0}, None, False, "precio"),
        ({"importe": 104.16, "descuento": 7.0}, None, False, "precio"),
        ({"codigo_partida": "01.02"}, None, True, None),
        ({}, None, True, None),
        ({}, "importe", True, "importe"),
        ({}, "precio", True, "precio"),
        ({}, "importe", False, None),
        ({}, "precio", False, None),
        ({}, "precio", None, None),
        ({"codigo_partida": "01.02"}, "precio", True, "precio"),
        # Lo tecleado manda sobre el botón.
        ({"cantidad": 48.0}, "precio", True, "importe"),
        ({"importe": 1.0}, "importe", True, "precio"),
    ],
)
def test_f106_dominio_r9_recalculo_de_fila(cambios, cuadrar, no_cuadra, esperado):
    from domain.models.review_models import recalculo_de_fila

    assert recalculo_de_fila(cambios=cambios, cuadrar=cuadrar, no_cuadra=no_cuadra) == esperado


# =================================================================== #
# Dominio · ConciliacionEditBody (R4, R7)
# =================================================================== #
def test_f106_dominio_r4_importe_con_coma_decimal():
    from domain.models.review_models import ConciliacionEditBody

    cuerpo = ConciliacionEditBody.model_validate({"importe": "1.104,16"})
    assert cuerpo.importe == pytest.approx(1104.16)
    assert cuerpo.campos() == {"importe": pytest.approx(1104.16)}


@pytest.mark.parametrize("valor", ["NaN", "Infinity", "-Infinity", "doce", float("nan"),
                                   float("inf")])
def test_f106_dominio_r4_importe_ilegible_es_422(valor):
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError):
        ConciliacionEditBody.model_validate({"importe": valor})


@pytest.mark.parametrize("valor", [None, "", "—"])
def test_f106_dominio_r4_importe_vacio_es_422(valor):
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError, match="importe"):
        ConciliacionEditBody.model_validate({"importe": valor})


@pytest.mark.parametrize("valor", ["importe", "precio"])
def test_f106_dominio_r4_cuadrar_valido_y_fuera_de_campos(valor):
    from domain.models.review_models import ConciliacionEditBody

    cuerpo = ConciliacionEditBody.model_validate({"cuadrar": valor})
    assert cuerpo.cuadrar == valor
    assert cuerpo.campos() == {}
    cuerpo = ConciliacionEditBody.model_validate({"cuadrar": valor, "cantidad": "2"})
    assert cuerpo.campos() == {"cantidad": 2.0}


@pytest.mark.parametrize("valor", ["cantidad", "IMPORTE", "", 1, None])
def test_f106_dominio_r4_cuadrar_otro_valor_es_422(valor):
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError):
        ConciliacionEditBody.model_validate({"cuadrar": valor})


def test_f106_dominio_r7_importe_y_precio_a_la_vez_es_422():
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError, match="Cambia el precio o el importe, no los dos"):
        ConciliacionEditBody.model_validate({"importe": 10, "precio_unitario": 2})


def test_f106_dominio_r4_sin_importe_ni_cuadrar_es_lo_de_hoy():
    from domain.models.review_models import ConciliacionEditBody

    cuerpo = ConciliacionEditBody.model_validate({"cantidad": "48"})
    assert cuerpo.importe is None
    assert cuerpo.cuadrar is None
    assert cuerpo.campos() == {"cantidad": 48.0}


# =================================================================== #
# Dominio · LineasIncompletasError(no_cuadran=) (R16)
# =================================================================== #
def test_f106_dominio_r16_aviso_de_lineas_que_no_cuadran():
    from domain.models.review_models import LineasIncompletasError

    error = LineasIncompletasError("doc", [], no_cuadran=[3])
    assert error.no_cuadran == [3]
    assert error.aviso == (
        "Líneas que no cuadran (cantidad × precio × (1 − dto) ≠ importe): 3"
    )
    assert str(error) == error.aviso


def test_f106_dominio_r16_aviso_junto_a_los_demas():
    from domain.models.review_models import LineasIncompletasError

    error = LineasIncompletasError("doc", [1], no_cuadran=[2, 4])
    assert error.aviso == (
        "Líneas sin cantidad o importe: 1. "
        "Líneas que no cuadran (cantidad × precio × (1 − dto) ≠ importe): 2, 4"
    )


def test_f106_dominio_r16_sin_no_cuadran_el_aviso_es_el_de_hoy():
    from domain.models.review_models import LineasIncompletasError

    error = LineasIncompletasError("doc", [1])
    assert error.no_cuadran == []
    assert error.aviso == "Líneas sin cantidad o importe: 1"
