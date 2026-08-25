# tests/test_f036_r22_contenedores_prioridades.py
"""F-036 R22 · el ORDEN de prioridades del calculo de contenedores.

Decision del humano (2026-08-19): el VOLUMEN manda sobre la resta
`entregados - retirados`. El orden queda:

    1) contenedores EXPLICITOS del albaran
    2) ceil(volumen_m3 / tamano de contenedor)
    3) resta entregados - retirados (ambas presentes y >= 1)
    4) nada utilizable -> None, razon `residuos_sin_volumen_m3`, revision

El motivo: la resta es una inferencia sobre el MOVIMIENTO de
contenedores (cuantos quedaron en obra), no sobre lo que se factura;
el volumen es un dato del documento. Un albaran que dice 12 m3 y
"llevadas 2 / retiradas 1" se factura por los 12 m3 (2 contenedores de
6), no por el 1 de la resta.

Los NOMBRES de las `reasons` NO cambian con el intercambio: hay codigo
aguas arriba (`valuation_builder.py`) que las inspecciona por prefijo.

Funcion PURA: sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from application.services.residuos_container_calc import (
    calcular_contenedores_residuos,
)


@dataclass(frozen=True)
class _Ctx:
    """Los campos de `contexto_linea` que el calculo mira."""

    volumen_m3: float | None = None
    contenedores: float | None = None
    contenedores_entregados: float | None = None
    contenedores_retirados: float | None = None


@dataclass(frozen=True)
class _LineaContrato:
    descripcion: str | None = None
    unidad_medida: str | None = None


CONTRATO_6 = [_LineaContrato(descripcion="CONTENEDOR RCD 6 M3")]


# ------------------------------------------------------------------ #
# Prioridad 1 · los contenedores EXPLICITOS mandan sobre todo
# ------------------------------------------------------------------ #
def test_f036_r22_prioridad_1_los_explicitos_ganan_al_volumen():
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(
            contenedores=3.0,
            volumen_m3=12.0,
            contenedores_entregados=5.0,
            contenedores_retirados=1.0,
        ),
        contrato_lines=CONTRATO_6,
    )

    assert res.num_contenedores == 3
    assert res.reasons == ["residuos_contenedores_explicitos=3"]


# ------------------------------------------------------------------ #
# Prioridad 2 · el VOLUMEN manda sobre la resta (el cambio de R22)
# ------------------------------------------------------------------ #
def test_f036_r22_prioridad_2_el_volumen_gana_a_la_resta():
    """El caso que motiva la decision del humano.

    Antes de F-036 la resta iba ANTES: este albaran salia con 1
    contenedor en vez de los 2 que dicen sus 12 m3.
    """
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(
            volumen_m3=12.0,
            contenedores_entregados=2.0,
            contenedores_retirados=1.0,
        ),
        contrato_lines=CONTRATO_6,
    )

    assert res.num_contenedores == 2
    assert res.contenedor_m3 == 6.0
    assert any(r.startswith("residuos_contenedores=") for r in res.reasons)
    assert not any(
        r.startswith("residuos_contenedores_resta") for r in res.reasons
    )


def test_f036_r22_el_volumen_gana_aunque_la_resta_diera_mas():
    """No es «el numero mayor»: es un ORDEN de fuentes."""
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(
            volumen_m3=6.0,
            contenedores_entregados=9.0,
            contenedores_retirados=1.0,
        ),
        contrato_lines=CONTRATO_6,
    )

    assert res.num_contenedores == 1


def test_f036_r22_un_volumen_de_cero_no_es_volumen_utilizable():
    """Con 0 m3 se sigue bajando a la resta, no se devuelve 0."""
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(
            volumen_m3=0.0,
            contenedores_entregados=3.0,
            contenedores_retirados=1.0,
        ),
        contrato_lines=CONTRATO_6,
    )

    assert res.num_contenedores == 2
    assert any(
        r.startswith("residuos_contenedores_resta") for r in res.reasons
    )


# ------------------------------------------------------------------ #
# Prioridad 3 · la resta, solo cuando no hay volumen
# ------------------------------------------------------------------ #
def test_f036_r22_prioridad_3_sin_volumen_manda_la_resta():
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(
            contenedores_entregados=3.0, contenedores_retirados=1.0
        ),
        contrato_lines=CONTRATO_6,
    )

    assert res.num_contenedores == 2
    assert res.reasons == [
        "residuos_contenedores_resta=2 (llevadas 3 - retiradas 1)"
    ]


@pytest.mark.parametrize(
    ("entregados", "retirados"),
    [
        (None, 1.0),      # falta una de las dos
        (2.0, None),
        (1.0, 1.0),       # resta 0
        (1.0, 3.0),       # resta negativa
    ],
)
def test_f036_r22_una_resta_no_utilizable_deja_la_linea_a_revision(
    entregados, retirados,
):
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(
            contenedores_entregados=entregados,
            contenedores_retirados=retirados,
        ),
        contrato_lines=CONTRATO_6,
    )

    assert res.num_contenedores is None
    assert res.reasons == ["residuos_sin_volumen_m3"]


# ------------------------------------------------------------------ #
# Prioridad 4 · ni volumen ni resta -> None y a revision
# ------------------------------------------------------------------ #
def test_f036_r22_sin_volumen_ni_resta_no_se_inventa_un_numero():
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(), contrato_lines=CONTRATO_6
    )

    assert res.num_contenedores is None
    assert res.volumen_m3 is None
    assert res.reasons == ["residuos_sin_volumen_m3"]


# ------------------------------------------------------------------ #
# Lo que el intercambio NO puede romper
# ------------------------------------------------------------------ #
def test_f036_r22_los_nombres_de_las_reasons_no_cambian():
    """`valuation_builder` las inspecciona por PREFIJO."""
    sin_tamano = calcular_contenedores_residuos(
        contexto_linea=_Ctx(volumen_m3=7.0), contrato_lines=[]
    )

    assert "residuos_tamano_defecto_6m3" in sin_tamano.reasons
    assert sin_tamano.num_contenedores == 2      # ceil(7 / 6)


def test_f036_r22_el_volumen_implausible_sigue_marcando_revision():
    """29 m3 suelen ser TONELADAS coladas en el campo de volumen."""
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(volumen_m3=29.0), contrato_lines=CONTRATO_6
    )

    assert res.num_contenedores == 5
    assert any(
        r.startswith("residuos_volumen_implausible") for r in res.reasons
    )


def test_f036_r22_el_tamano_exacto_del_contrato_sigue_ganando():
    """8 m3 con contenedores de 6 y 8 -> el de 8, 1 unidad."""
    contrato = [
        _LineaContrato(descripcion="CONTENEDOR RCD 6 M3"),
        _LineaContrato(descripcion="CONTENEDOR RCD 8 M3"),
    ]

    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(volumen_m3=8.0), contrato_lines=contrato
    )

    assert res.num_contenedores == 1
    assert res.contenedor_m3 == 8.0


def test_f036_r22_la_docstring_del_modulo_documenta_el_orden_nuevo():
    """R22 exige que la docstring diga el orden NUEVO, no el anterior.

    Sin esto, el proximo que lea el modulo aplicara el orden viejo.
    """
    import application.services.residuos_container_calc as modulo

    doc = modulo.__doc__ or ""
    pos_volumen = doc.find("volumen_m3 / m3_por_contenedor")
    pos_resta = doc.find("LLEVADAS - RETIRADAS")

    assert pos_volumen > 0, "la docstring no describe el calculo por volumen"
    assert pos_resta > 0, "la docstring no describe la resta"
    assert pos_volumen < pos_resta, (
        "la docstring sigue poniendo la resta antes que el volumen"
    )
