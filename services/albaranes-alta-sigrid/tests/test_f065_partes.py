# tests/test_f065_partes.py
"""F-065 · tests de contrato en sv9 (sv9 no cambia de código).

- R10 (fase 1): una fila Contrato editada en sv4 queda con
  ``cantidad_convertida`` = Q (la cantidad en la unidad del precio que ve y
  edita la ficha). sv9 la admite (sin ``cantidad_sin_convertir``) y la manda
  vinculada, con ``cantidad = Q`` y su ``ctrpro_ide``; el precio sale de
  ``importe / Q``. Las filas legadas que el PATCH viejo dejaba con la
  convertida nula son justo las que sv9 rechaza (fallo seguro).

Puro: ni red ni BBDD.
"""
from __future__ import annotations

import pytest
from domain.models.alta_models import Motivo, PeticionAlbaran
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, HOY, datos, vinculada


def _linea_unica(linea):
    peticion = validar_y_construir(datos(linea), CONFIG, HOY)
    assert isinstance(peticion, PeticionAlbaran), f"no admitida: {peticion!r}"
    (enviada,) = peticion.lineas
    return enviada


@pytest.mark.parametrize(
    ("cantidad_albaran", "cantidad_convertida", "importe", "q", "precio"),
    [
        # (b) sin conversión: la administrativa deja 7 puertas de 8 a 115 €.
        (7.0, 7.0, 805.0, 7.0, 115.0),
        # (c) contenedores: 6 m³ declarados, 2 contenedores a 120 €.
        (6.0, 2.0, 240.0, 2.0, 120.0),
        # (a) reproducible t → kg: 3 t = 3000 kg a 0,05 €/kg.
        (3.0, 3000.0, 150.0, 3000.0, 0.05),
    ],
    ids=["sin_conversion", "contenedores", "toneladas_a_kg"],
)
def test_f065_r10_fila_contrato_editada_se_admite_con_cantidad_q(
    cantidad_albaran, cantidad_convertida, importe, q, precio,
):
    enviada = _linea_unica(vinculada(
        11, cantidad_albaran=cantidad_albaran, cantidad_convertida=cantidad_convertida,
        importe_calculado=importe,
    ))

    assert enviada.ctrpro_ide == 700101
    assert enviada.cantidad == pytest.approx(q)
    assert enviada.precio == pytest.approx(precio)
    assert enviada.producto is None  # vinculada: el producto es el de su línea


def test_f065_r10_la_fila_legada_sin_convertida_es_la_que_se_rechaza():
    """Lo que el PATCH viejo dejaba (convertida nula): ``no_admitido``."""
    resultado = validar_y_construir(
        datos(vinculada(11, cantidad_albaran=7.0, cantidad_convertida=None,
                        importe_calculado=805.0)),
        CONFIG, HOY,
    )

    assert resultado == [Motivo("cantidad_sin_convertir", "", "11")]
