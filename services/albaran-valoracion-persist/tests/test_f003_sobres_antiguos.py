# tests/test_f003_sobres_antiguos.py
"""F-003 · Sobres anteriores a la feature (R14) y flags (R13).

Las colas son at-least-once y no se pueden vaciar: cuando este codigo
despliegue, habra sobres EN COLA generados por el sv5 anterior, sin
``importe_leido`` ni ``importe_total_albaran``. Tienen que valorarse sin
error y con el comportamiento de siempre.

Y los mecanismos nuevos deben poder apagarse uno a uno (R13).

Sin red, BBDD ni LLM.
"""
from __future__ import annotations

import pytest

from ayudas_f003 import (
    construir,
    construir_builder,
    envelope,
    linea_contexto,
    linea_valorada,
)
from domain.models.valuation_envelope import (
    AlbaranLineContextDto,
    ValuationEnvelope,
    ValuationEnvelopeMeta,
)


# ---------------------------------------------------------------------
# R14 · Los DTOs siguen validando sin los campos nuevos
# ---------------------------------------------------------------------


def test_f003_r14_la_linea_de_contexto_valida_sin_importe_leido() -> None:
    dto = AlbaranLineContextDto.model_validate(
        {
            "merge_line_id": 1,
            "line_index": 1,
            "descripcion": "ARENA",
            "cantidad": 2.0,
            "precio_unitario_albaran": 10.0,
            "importe_albaran": 20.0,
        }
    )

    assert dto.importe_leido is None


def test_f003_r14_el_meta_valida_sin_el_total_del_albaran() -> None:
    meta = ValuationEnvelopeMeta.model_validate({"document_id": "doc-1"})

    assert meta.importe_total_albaran is None
    assert meta.importe_total_incluye_iva is None


def test_f003_r14_el_meta_acepta_el_total_y_su_marca() -> None:
    meta = ValuationEnvelopeMeta.model_validate(
        {
            "document_id": "doc-1",
            "importe_total_albaran": 191.40,
            "importe_total_incluye_iva": False,
        }
    )

    assert meta.importe_total_albaran == pytest.approx(191.40)
    assert meta.importe_total_incluye_iva is False


def test_f003_r14_un_sobre_del_sv5_anterior_valida_entero() -> None:
    """Sobre tal cual lo dejaba sv5 antes de F-003."""
    sobre = ValuationEnvelope.model_validate(
        {
            "status": "ok",
            "meta": {
                "document_id": "doc-1",
                "codigo_contrato": "C-1",
                "fecha_albaran": "2026-07-01",
            },
            "data": {"lineas": [linea_valorada()]},
            "context": {
                "lineas_albaran": [linea_contexto()],
                "lineas_contrato": [],
            },
        }
    )

    assert sobre.meta.importe_total_albaran is None
    assert sobre.context.lineas_albaran[0].importe_leido is None


# ---------------------------------------------------------------------
# R14 · Y el builder los valora igual que siempre
# ---------------------------------------------------------------------


def test_f003_r14_el_builder_valora_un_sobre_antiguo_sin_error() -> None:
    header, records = construir(construir_builder(), envelope())

    assert len(records) == 1
    assert records[0].importe_calculado == pytest.approx(10.0)
    assert header.total_valorado == pytest.approx(10.0)


def test_f003_r14_sin_total_no_hay_motivos_de_guard_de_total() -> None:
    header, _ = construir(construir_builder(), envelope())

    assert not [
        motivo
        for motivo in header.review_reasons
        if motivo.startswith("guard_aritmetico_total")
    ]


def test_f003_r14_sin_importe_leido_no_hay_guard_de_linea() -> None:
    _, records = construir(construir_builder(), envelope())

    assert not [
        motivo
        for motivo in records[0].review_reasons
        if motivo.startswith("guard_aritmetico_linea")
    ]


# ---------------------------------------------------------------------
# R13 · Los flags existen, por defecto activos y desactivables
# ---------------------------------------------------------------------


def test_f003_r13_los_flags_vienen_activos_por_defecto() -> None:
    from config.settings import Settings

    campos = Settings.model_fields

    assert campos["guard_aritmetico_enabled"].default is True
    assert campos["red_atributo_sustantivo_enabled"].default is True


def test_f003_r13_los_flags_se_leen_del_entorno() -> None:
    from config.settings import Settings

    alias = {
        campo.alias for campo in Settings.model_fields.values()
    }

    assert "GUARD_ARITMETICO_ENABLED" in alias
    assert "RED_ATRIBUTO_SUSTANTIVO_ENABLED" in alias


def test_f003_r13_el_builder_acepta_los_dos_flags() -> None:
    builder = construir_builder(
        guard_aritmetico_enabled=False,
        red_atributo_sustantivo_enabled=False,
    )

    header, records = construir(builder, envelope())

    assert len(records) == 1
    assert header.total_valorado == pytest.approx(10.0)


def test_f003_r13_los_flags_del_builder_son_true_por_defecto() -> None:
    builder = construir_builder()

    assert builder._guard_aritmetico_enabled is True
    assert builder._red_atributo_sustantivo_enabled is True
