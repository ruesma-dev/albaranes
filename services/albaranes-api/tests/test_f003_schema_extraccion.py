# tests/test_f003_schema_extraccion.py
"""F-003 · Schema de extraccion de IA1: importe leido y total del documento (R2).

El importe de linea impreso NO existia en el pipeline: sv2 solo extraia
``precio``, ``descuento`` y ``precio_neto``, y la instruccion de "si no
figura, calcula cantidad*precio*(1-descuento/100)" metia un IMPORTE en un
campo que aguas abajo se trataba como precio UNITARIO (caso x120:
23.073,60 EUR persistidos por 191,40 EUR impresos).

Aqui se comprueba que el schema gana los campos para TRANSCRIBIR lo
impreso, que son opcionales (extracciones antiguas siguen validando) y
que el total del documento viaja con su marca de IVA.

Sin red ni LLM: solo validacion de modelos Pydantic.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.models.albaran_models import (
    CabeceraAlbaran,
    DocumentoAlbaran,
    LineaAlbaran,
)


# ---------------------------------------------------------------------
# R2 · La linea transcribe el importe impreso y todos los descuentos
# ---------------------------------------------------------------------


def test_f003_r2_linea_acepta_importe_leido() -> None:
    """El caso x120: 120,55 l a 1,5877 con importe impreso 191,40."""
    linea = LineaAlbaran(
        cantidad=120.55,
        precio=1.5877,
        importe=191.40,
    )

    assert linea.importe == pytest.approx(191.40)
    # El importe NO se cuela en precio_neto (la confusion que causo el x120).
    assert linea.precio_neto is None


def test_f003_r2_linea_acepta_lista_de_descuentos() -> None:
    """Varias columnas de descuento (DTO1/DTO2) se transcriben en orden."""
    linea = LineaAlbaran(precio=10.0, descuentos=[5.0, 2.5])

    assert linea.descuentos == [5.0, 2.5]
    # Con varios descuentos, la IA deja `descuento` a null: lo deriva sv3.
    assert linea.descuento is None


def test_f003_r2_los_campos_nuevos_de_linea_son_opcionales() -> None:
    linea = LineaAlbaran()

    assert linea.importe is None
    assert linea.descuentos is None


def test_f003_r2_descuentos_admite_lista_vacia_y_un_solo_valor() -> None:
    assert LineaAlbaran(descuentos=[]).descuentos == []
    assert LineaAlbaran(descuentos=[3.0]).descuentos == [3.0]


def test_f003_r2_importe_de_linea_rechaza_texto_no_numerico() -> None:
    with pytest.raises(ValidationError):
        LineaAlbaran(importe="ciento noventa")


# ---------------------------------------------------------------------
# R2 · La cabecera transcribe el total del documento con su marca de IVA
# ---------------------------------------------------------------------


def test_f003_r2_cabecera_acepta_total_base_sin_iva() -> None:
    cab = CabeceraAlbaran(importe_total=191.40, importe_total_incluye_iva=False)

    assert cab.importe_total == pytest.approx(191.40)
    assert cab.importe_total_incluye_iva is False


def test_f003_r2_cabecera_acepta_total_con_iva_marcado() -> None:
    """Decision del humano 2026-08-13: el total con IVA se transcribe y se
    MARCA, nunca se descarta."""
    cab = CabeceraAlbaran(importe_total=231.59, importe_total_incluye_iva=True)

    assert cab.importe_total == pytest.approx(231.59)
    assert cab.importe_total_incluye_iva is True


def test_f003_r2_los_campos_nuevos_de_cabecera_son_opcionales() -> None:
    cab = CabeceraAlbaran()

    assert cab.importe_total is None
    assert cab.importe_total_incluye_iva is None


# ---------------------------------------------------------------------
# R2 · Retrocompatibilidad: una extraccion anterior a F-003 sigue validando
# ---------------------------------------------------------------------


def test_f003_r2_extraccion_antigua_sigue_validando() -> None:
    """JSON tal y como lo devolvia IA1 antes de esta feature."""
    documento = DocumentoAlbaran.model_validate(
        {
            "cabecera": {
                "proveedor_nombre": "PROVEEDOR EJEMPLO, S.L.",
                "proveedor_cif": "B00000000",
                "fecha": "2026-07-01",
                "numero_albaran": "A-1",
                "obra_codigo": "0501",
            },
            "lineas": [
                {
                    "concepto": "GASOLEO B",
                    "cantidad": 120.55,
                    "precio": 1.5877,
                    "descuento": None,
                    "precio_neto": None,
                }
            ],
        }
    )

    assert documento.cabecera.importe_total is None
    assert documento.cabecera.importe_total_incluye_iva is None
    assert documento.lineas[0].importe is None
    assert documento.lineas[0].descuentos is None


def test_f003_r2_documento_valorado_completo_valida() -> None:
    documento = DocumentoAlbaran.model_validate(
        {
            "cabecera": {
                "numero_albaran": "A-1",
                "importe_total": 191.40,
                "importe_total_incluye_iva": False,
            },
            "lineas": [
                {
                    "concepto": "GASOLEO B",
                    "cantidad": 120.55,
                    "precio": 1.5877,
                    "descuentos": [0.0],
                    "importe": 191.40,
                }
            ],
        }
    )

    assert documento.cabecera.importe_total == pytest.approx(191.40)
    assert documento.lineas[0].importe == pytest.approx(191.40)


def test_f003_r2_el_schema_sigue_prohibiendo_campos_no_declarados() -> None:
    """StrictSchemaModel(extra='forbid') no se relaja al anadir campos."""
    with pytest.raises(ValidationError):
        LineaAlbaran(importe_total_linea=191.40)
