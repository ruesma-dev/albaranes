# tests/test_f075_alta_directa.py
"""F-075 R26 · sv9 da de alta una valoración directa SIN código nuevo.

Tests de contrato (caracterización): fijan que lo que sv6 deja con la
valoración directa —cabecera ``no_contract`` sin contrato, líneas sin
vincular con su derivada ``nueva_no_match`` (``codigo_contrato=""``) y el
importe leído del albarán— ya produce la petición correcta, y que con una
línea sin importe no se manda nada. Si alguien cambia sv9 y rompe el paso
directo, falla aquí. Puro: sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from domain.models.alta_models import EstadoAlta, PeticionAlbaran
from domain.services.validador_alta import estado_de_motivos, validar_y_construir
from tests.f053_datos import CONFIG, HOY, USU, datos, sin_vincular


def _directa(id_, *, importe, cantidad=2.0, partida=None, descripcion="TUBO PVC 110", unidad="ml",
             tipo_familia=None):
    """Una línea como la deja ``ValoracionDirectaBuilder`` (y F-078 al guardarla)."""
    return sin_vincular(
        id_, importe_calculado=importe, cantidad_albaran=cantidad, cantidad_convertida=cantidad,
        unidad_albaran=unidad, derived_contrato_line_id=9000 + id_, codigo_partida_final=partida,
        descripcion_linea=descripcion, descripcion_merge=descripcion, tipo_familia=tipo_familia,
    )


def _datos_directa(*lineas):
    return datos(*lineas, valoracion_status="no_contract", contrato_codigo=None)


def test_f075_r26_directa_completa_da_una_peticion_sin_contrato():
    peticion = validar_y_construir(_datos_directa(
        _directa(1, importe=35.19, cantidad=108.0, partida="CI.4.18"),
        _directa(2, importe=-30.0, cantidad=-1.0, descripcion="ABONO ENVASE"),
        _directa(3, importe=20.0, cantidad=1.0, tipo_familia="alquiler_maquinaria", descripcion="GRUA"),
    ), CONFIG, HOY, USU)
    assert isinstance(peticion, PeticionAlbaran), peticion
    assert peticion.cod_contrato is None
    assert "cod_contrato" not in peticion.a_dict() or peticion.a_dict()["cod_contrato"] is None
    uno, dos, tres = peticion.lineas
    # Todas sin vincular: producto por familia, sin ctrpro.
    assert [l.ctrpro_ide for l in peticion.lineas] == [None, None, None]
    assert (uno.producto, dos.producto, tres.producto) == ("MA9999", "MA9999", "QA9999")
    # Partida impresa o ninguna (almacén).
    assert (uno.partida, dos.partida, tres.partida) == ("CI.4.18", None, None)
    assert uno.descripcion == "TUBO PVC 110" and uno.unidad == "ml"
    # precio · cantidad = importe (con el signo del abono en la cantidad).
    for linea, importe in zip(peticion.lineas, (35.19, -30.0, 20.0)):
        assert linea.precio * linea.cantidad == pytest.approx(importe, abs=1e-4)
    assert dos.cantidad < 0 and dos.precio > 0


def test_f075_r26_directa_con_una_linea_sin_importe_no_se_admite():
    motivos = validar_y_construir(_datos_directa(
        _directa(1, importe=10.0), _directa(2, importe=None),
    ), CONFIG, HOY, USU)
    assert isinstance(motivos, list)
    assert "no_valorado" in [m.codigo for m in motivos]
    assert estado_de_motivos(motivos) is EstadoAlta.NO_ADMITIDO


def test_f075_r26_cabecera_vacia_de_siempre_no_se_admite():
    motivos = validar_y_construir(_datos_directa(), CONFIG, HOY, USU)
    assert isinstance(motivos, list)
    assert estado_de_motivos(motivos) is EstadoAlta.NO_ADMITIDO
