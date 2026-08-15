# tests/test_f003_dto_no_contrato.py
"""F-003 · El descuento del albaran NO se aplica al precio de contrato (R5).

Hasta ahora el builder pasaba el descuento de la linea al
ImporteCalculator sin mirar de donde salia el precio final. Si el precio
venia del CONTRATO, aplicarle ademas el descuento del albaran es contar
dos veces la misma rebaja: el precio de contrato ya es el pactado.

La regla se limita a lineas ``from_albaran``. Las sinteticas M1-M7
MANTIENEN la herencia del descuento del padre (decision del humano
2026-08-13, D4): valen a precio de contrato pero heredan.

Sin red, BBDD ni LLM.
"""
from __future__ import annotations

import pytest

from ayudas_f003 import (
    construir,
    construir_builder,
    envelope,
    linea_contexto,
    linea_contrato,
    linea_valorada,
)

MOTIVO = "descuento_albaran_no_aplicado_a_precio_contrato"


def _construir_una_linea(**kwargs):
    """Un albaran de UNA linea, con los parametros que interesen."""
    contexto = linea_contexto(**kwargs.pop("contexto", {}))
    valorada = linea_valorada(**kwargs.pop("valorada", {}))
    header, records = construir(
        kwargs.pop("builder", None) or construir_builder(),
        envelope(
            lineas_data=[valorada],
            lineas_albaran=[contexto],
            lineas_contrato=[linea_contrato(**kwargs.pop("contrato", {}))],
        ),
    )
    return header, records[0]


# ---------------------------------------------------------------------
# R5 · Precio de CONTRATO + descuento del albaran -> sin descuento
# ---------------------------------------------------------------------


def test_f003_r5_precio_de_contrato_no_recibe_el_descuento() -> None:
    """10 ud x 10,00 EUR de contrato con un 20 % en el albaran: el
    importe es 100,00, no 80,00."""
    _, record = _construir_una_linea(
        contexto={
            "cantidad": 10.0,
            "descuento_albaran": 20.0,
            # Sin precio ni importe leidos: el precio sale del contrato.
            "precio_unitario_albaran": None,
            "importe_albaran": None,
        },
    )

    assert record.precio_unitario_source == "contract_line_match"
    assert record.importe_calculado == pytest.approx(100.0)
    assert record.descuento_albaran_aplicado is None


def test_f003_r5_queda_el_motivo_de_auditoria() -> None:
    _, record = _construir_una_linea(
        contexto={
            "cantidad": 10.0,
            "descuento_albaran": 20.0,
            "precio_unitario_albaran": None,
            "importe_albaran": None,
        },
    )

    assert MOTIVO in record.review_reasons


def test_f003_r5_sin_descuento_no_se_deja_motivo() -> None:
    """El motivo es informacion util, no ruido en cada linea."""
    _, record = _construir_una_linea(
        contexto={
            "cantidad": 10.0,
            "descuento_albaran": None,
            "precio_unitario_albaran": None,
            "importe_albaran": None,
        },
    )

    assert MOTIVO not in record.review_reasons


def test_f003_r5_descuento_cero_tampoco_deja_motivo() -> None:
    _, record = _construir_una_linea(
        contexto={
            "cantidad": 10.0,
            "descuento_albaran": 0.0,
            "precio_unitario_albaran": None,
            "importe_albaran": None,
        },
    )

    assert MOTIVO not in record.review_reasons


def test_f003_r5_el_precio_inferido_del_pdf_tampoco_recibe_descuento() -> None:
    _, record = _construir_una_linea(
        contexto={
            "cantidad": 10.0,
            "descuento_albaran": 20.0,
            "precio_unitario_albaran": None,
            "importe_albaran": None,
        },
        valorada={
            "precio_unitario_contrato_db": None,
            "precio_unitario_pdf_inferido": 10.0,
        },
    )

    assert record.precio_unitario_source == "pdf_inference"
    assert record.importe_calculado == pytest.approx(100.0)
    assert MOTIVO in record.review_reasons


# ---------------------------------------------------------------------
# R5 · Regresion: precio del ALBARAN + descuento -> formula de siempre
# ---------------------------------------------------------------------


def test_f003_r5_precio_del_albaran_si_recibe_el_descuento() -> None:
    """Precio unitario declarado en el albaran (sin importe leido): la
    formula con descuento se mantiene tal cual estaba."""
    _, record = _construir_una_linea(
        contexto={
            "cantidad": 10.0,
            "descuento_albaran": 20.0,
            "precio_unitario_albaran": 10.0,
            "importe_albaran": None,
        },
    )

    assert record.precio_unitario_source == "albaran_declared"
    assert record.importe_calculado == pytest.approx(80.0)
    assert record.descuento_albaran_aplicado == pytest.approx(20.0)
    assert MOTIVO not in record.review_reasons


def test_f003_r5_el_importe_leido_manda_y_el_descuento_se_respeta() -> None:
    """Con importe leido, el unitario se deriva de el (albaran_calculated)
    y el descuento sigue en juego: sale exactamente el importe impreso."""
    _, record = _construir_una_linea(
        contexto={
            "cantidad": 10.0,
            "descuento_albaran": 20.0,
            "precio_unitario_albaran": None,
            "importe_albaran": 80.0,
            "importe_leido": 80.0,
        },
    )

    assert record.precio_unitario_source == "albaran_calculated"
    assert record.importe_calculado == pytest.approx(80.0)
    assert MOTIVO not in record.review_reasons


# ---------------------------------------------------------------------
# R5/D4 · Las sinteticas M1-M7 mantienen la herencia del descuento
# ---------------------------------------------------------------------


def test_f003_r5_la_sintetica_hereda_el_descuento_del_padre() -> None:
    """Decision del humano (P1/D4): las sinteticas SIGUEN heredando el
    descuento aunque se valoren a precio de contrato."""
    header, records = construir(
        construir_builder(),
        envelope(
            lineas_data=[
                linea_valorada(
                    merge_line_id=1,
                    matched_contrato_line_id=100,
                ),
                linea_valorada(
                    merge_line_id=None,
                    line_kind="synthetic_modifier",
                    parent_merge_line_id=1,
                    modifier_source="incremento_year",
                    descripcion_linea="INCREMENTO 2026",
                    matched_contrato_line_id=200,
                    precio_unitario_contrato_db=5.0,
                    match_method="semantic",
                ),
            ],
            lineas_albaran=[
                linea_contexto(
                    merge_line_id=1,
                    cantidad=10.0,
                    descuento_albaran=20.0,
                    precio_unitario_albaran=10.0,
                    importe_albaran=80.0,
                )
            ],
            lineas_contrato=[
                linea_contrato(contrato_line_id=100),
                linea_contrato(
                    contrato_line_id=200,
                    codigo_producto="INC",
                    descripcion="INCREMENTO 2026",
                    precio_unitario=5.0,
                ),
            ],
        ),
    )

    sintetica = [r for r in records if r.line_kind == "synthetic_modifier"][0]

    assert sintetica.descuento_albaran_aplicado == pytest.approx(20.0)
    assert sintetica.importe_calculado == pytest.approx(40.0)
    assert MOTIVO not in sintetica.review_reasons
