# tests/test_f111_tamano.py
"""F-111 parte A · tamaño de contenedor 3, 6 o 9 m³ (R1–R11).

Regla del humano (2026-10-29): sin tamaño en el contrato, el contenedor es de
3, 6 o 9 m³ y se elige el MÁS PEQUEÑO en el que caben los m³ (un contenedor);
con más de 9 m³, ``ceil(m³ / 6)`` contenedores de 6, sin mezclar tamaños. El
precio es el de la línea casada (el precio general del contrato): cambia la
cantidad, no el precio. Si el contrato da tamaños, manda el contrato.

Función PURA más dos escenarios del builder real: sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from application.services.residuos_container_calc import (
    MOTIVO_TAMANO_DISTINTO_DE_CASADA,
    MOTIVO_TAMANO_ESTANDAR,
    ResultadoContenedores,
    _elegir_tamano,
    calcular_contenedores_residuos,
)


@dataclass(frozen=True)
class _Ctx:
    volumen_m3: float | None = None
    contenedores: float | None = None
    contenedores_entregados: float | None = None
    contenedores_retirados: float | None = None


@dataclass(frozen=True)
class _LineaContrato:
    descripcion: str | None = None
    unidad_medida: str | None = None


#: CTSU24/0524 (HERMANOS SAN JUAN): el contrato no da tamaño.
SIN_TAMANO = _LineaContrato(descripcion="CONTENEDOR LER 170201 MADERA")
C6 = _LineaContrato(descripcion="CONTENEDOR RCD 6 M3")
C8 = _LineaContrato(descripcion="CONTENEDOR RCD 8 M3")


def _calc(m3, *, lineas=(), casada=None, ia=None) -> ResultadoContenedores:
    return calcular_contenedores_residuos(
        contexto_linea=_Ctx(volumen_m3=m3),
        contrato_line=casada,
        contrato_lines=list(lineas),
        contenedor_m3_ia=ia,
    )


# ------------------------------------------------------------------ #
# R1 · estándar: el más pequeño de 3, 6 y 9 en el que caben
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("m3", "tamano"),
    [
        (0.5, 3.0), (2.0, 3.0), (3.0, 3.0),
        (3.01, 6.0), (5.0, 6.0), (6.0, 6.0),
        (6.01, 9.0), (8.0, 9.0), (9.0, 9.0),
    ],
)
def test_f111_r1_el_estandar_es_el_mas_pequeno_en_el_que_caben(m3, tamano):
    assert _elegir_tamano([], m3) == (1, tamano)
    res = _calc(m3, casada=SIN_TAMANO, lineas=[SIN_TAMANO])
    assert res.num_contenedores == 1
    assert res.contenedor_m3 == tamano


def test_f111_r1_una_milesima_de_redondeo_no_salta_de_tamano():
    """La tolerancia de 0,01 de hoy: 6,004 m³ caben en el de 6."""
    assert _elegir_tamano([], 6.004) == (1, 6.0)
    assert _elegir_tamano([], 3.004) == (1, 3.0)


# ------------------------------------------------------------------ #
# R2 · más de 9 m³: paquetes de 6, sin mezclar
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("m3", "num"),
    [(9.01, 2), (10.0, 2), (12.0, 2), (12.5, 3), (16.0, 3)],
)
def test_f111_r2_mas_de_9_son_paquetes_de_6(m3, num):
    assert _elegir_tamano([], m3) == (num, 6.0)
    res = _calc(m3)
    assert res.num_contenedores == num
    assert res.contenedor_m3 == 6.0


# ------------------------------------------------------------------ #
# R3 · el motivo del estándar sustituye al del 6 por defecto
# ------------------------------------------------------------------ #
def test_f111_r3_motivo_del_tamano_estandar():
    res = _calc(8.0, casada=SIN_TAMANO, lineas=[SIN_TAMANO])
    assert "residuos_tamano_estandar=9m3" in res.reasons
    assert "residuos_tamano_defecto_6m3" not in res.reasons
    assert res.revision is False


def test_f111_r3_con_mas_de_9_el_motivo_dice_6():
    res = _calc(12.0)
    assert "residuos_tamano_estandar=6m3" in res.reasons


def test_f111_r3_el_motivo_del_6_por_defecto_deja_de_escribirse():
    for m3 in (1.0, 4.0, 7.0, 8.0, 10.0, 15.0):
        res = _calc(m3)
        assert not any("defecto" in r for r in res.reasons), (m3, res.reasons)


def test_f111_r35_constantes_de_los_motivos_congeladas():
    assert MOTIVO_TAMANO_ESTANDAR == "residuos_tamano_estandar"
    assert MOTIVO_TAMANO_DISTINTO_DE_CASADA == "residuos_tamano_distinto_de_casada"


# ------------------------------------------------------------------ #
# R5 · el motivo del número no cambia de formato
# ------------------------------------------------------------------ #
def test_f111_r5_el_motivo_del_numero_mantiene_su_formato():
    res = _calc(8.0)
    assert "residuos_contenedores=1 (m3=8 / contenedor=9 m3)" in res.reasons
    res = _calc(12.5)
    assert "residuos_contenedores=3 (m3=12.5 / contenedor=6 m3)" in res.reasons


# ------------------------------------------------------------------ #
# R6 · el contrato da tamaños: el más pequeño de ellos en el que caben
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("m3", "tamano"),
    [(5.0, 6.0), (6.0, 6.0), (7.0, 8.0), (8.0, 8.0)],
)
def test_f111_r6_con_tamanos_del_contrato_el_mas_pequeno_en_que_caben(m3, tamano):
    assert _elegir_tamano([6.0, 8.0], m3) == (1, tamano)
    assert _elegir_tamano([8.0, 6.0], m3) == (1, tamano)
    res = _calc(m3, lineas=[C6, C8], casada=None)
    assert res.num_contenedores == 1
    assert res.contenedor_m3 == tamano
    assert not any(r.startswith(MOTIVO_TAMANO_ESTANDAR) for r in res.reasons)


# ------------------------------------------------------------------ #
# R7 · no caben en ningún tamaño del contrato (D2 = a)
# ------------------------------------------------------------------ #
def test_f111_r7_con_el_6_en_el_contrato_paquetes_de_6():
    assert _elegir_tamano([6.0, 8.0], 14.0) == (3, 6.0)
    res = _calc(14.0, lineas=[C6, C8])
    assert (res.num_contenedores, res.contenedor_m3) == (3, 6.0)


def test_f111_r7_sin_el_6_paquetes_del_mayor():
    assert _elegir_tamano([8.0], 14.0) == (2, 8.0)
    assert _elegir_tamano([4.0, 8.0], 17.0) == (3, 8.0)
    res = _calc(14.0, lineas=[C8])
    assert (res.num_contenedores, res.contenedor_m3) == (2, 8.0)


def test_f111_r7_un_unico_tamano_de_6_con_mas_m3_sigue_como_hoy():
    """F-036: 12 m³ con contrato de 6 ⇒ 2 de 6 (no cambia)."""
    assert _elegir_tamano([6.0], 12.0) == (2, 6.0)


# ------------------------------------------------------------------ #
# R8 · orden de las fuentes de tamaño
# ------------------------------------------------------------------ #
def test_f111_r8_la_tabla_del_contrato_gana_a_la_ia():
    res = _calc(7.0, lineas=[C6, C8], ia=6.0)
    assert res.contenedor_m3 == 8.0


def test_f111_r8_sin_tabla_manda_el_contenedor_de_la_ia():
    """R-1: si IA3 rellena 6 con 8 m³, sv6 lo usa (2 de 6)."""
    res = _calc(8.0, lineas=[SIN_TAMANO], casada=SIN_TAMANO, ia=6.0)
    assert (res.num_contenedores, res.contenedor_m3) == (2, 6.0)
    res = _calc(5.0, lineas=[SIN_TAMANO], casada=SIN_TAMANO, ia=8.0)
    assert (res.num_contenedores, res.contenedor_m3) == (1, 8.0)


def test_f111_r8_ia_no_numerica_o_cero_no_cuenta():
    assert _calc(8.0, ia="abc").contenedor_m3 == 9.0
    assert _calc(8.0, ia=0).contenedor_m3 == 9.0


def test_f111_r8_sin_tabla_ni_ia_manda_la_descripcion_de_la_casada():
    casada = _LineaContrato(descripcion="MOVIMIENTO CONTENEDOR 8 M3")
    res = _calc(5.0, casada=casada)
    assert (res.num_contenedores, res.contenedor_m3) == (1, 8.0)
    casada_unidad = _LineaContrato(descripcion="MOVIMIENTO", unidad_medida="CONT 3 M3")
    res = _calc(2.0, casada=casada_unidad)
    assert res.contenedor_m3 == 3.0


def test_f111_r8_sin_ninguna_fuente_el_estandar():
    res = _calc(5.0, casada=SIN_TAMANO, lineas=[SIN_TAMANO])
    assert res.contenedor_m3 == 6.0
    assert "residuos_tamano_estandar=6m3" in res.reasons


def test_f111_r8_la_tabla_lee_todas_las_lineas_de_contenedor():
    """Varias líneas con el mismo tamaño o de otros conceptos no estorban."""
    lineas = [
        C6,
        _LineaContrato(descripcion="CONTENEDOR MADERA 6 M3"),
        _LineaContrato(descripcion="INCREMENTO LER 170201 8 M3"),  # no es contenedor
        _LineaContrato(descripcion=None),
        _LineaContrato(descripcion="CONTENEDOR 0 M3"),
    ]
    res = _calc(7.0, lineas=lineas)
    # Solo el 6 es tamaño de contenedor: 7 m³ no caben ⇒ paquetes de 6.
    assert (res.num_contenedores, res.contenedor_m3) == (2, 6.0)


def test_f111_r8_descripcion_linea_tambien_vale_en_la_tabla():
    @dataclass(frozen=True)
    class _Otra:
        descripcion_linea: str

    res = _calc(7.0, lineas=[_Otra("CONTENEDOR RCD 8 M3")])
    assert res.contenedor_m3 == 8.0


# ------------------------------------------------------------------ #
# R9 · el tamaño elegido no es el de la casada ⇒ revisión
# ------------------------------------------------------------------ #
def test_f111_r9_tamano_distinto_de_la_casada_va_a_revision():
    res = _calc(7.0, lineas=[C6, C8], casada=C6)
    assert res.contenedor_m3 == 8.0
    assert res.num_contenedores == 1
    assert "residuos_tamano_distinto_de_casada=8/6" in res.reasons
    assert res.revision is True


def test_f111_r9_mismo_tamano_que_la_casada_sin_revision():
    res = _calc(8.0, lineas=[C6, C8], casada=C8)
    assert res.revision is False
    assert not any(r.startswith(MOTIVO_TAMANO_DISTINTO_DE_CASADA) for r in res.reasons)


def test_f111_r9_casada_sin_m3_no_compara():
    res = _calc(8.0, lineas=[SIN_TAMANO], casada=SIN_TAMANO)
    assert res.revision is False


def test_f111_r9_paquetes_del_mismo_tamano_que_la_casada_sin_revision():
    res = _calc(14.0, lineas=[C6], casada=C6)
    assert (res.num_contenedores, res.contenedor_m3) == (3, 6.0)
    assert res.revision is False


def test_f111_r9_estandar_distinto_de_la_casada():
    """Casada de 6 sin tabla ni IA: manda la casada (R8), no el estándar."""
    res = _calc(2.0, casada=C6)
    assert res.contenedor_m3 == 6.0
    assert res.revision is False


# ------------------------------------------------------------------ #
# R10 · prioridades de F-036 R22 intactas
# ------------------------------------------------------------------ #
def test_f111_r10_explicitos_y_resta_sin_revision_ni_tamano():
    res = calcular_contenedores_residuos(contexto_linea=_Ctx(contenedores=2.0, volumen_m3=8.0))
    assert res.num_contenedores == 2 and res.revision is False
    res = calcular_contenedores_residuos(
        contexto_linea=_Ctx(contenedores_entregados=3.0, contenedores_retirados=1.0)
    )
    assert res.num_contenedores == 2 and res.revision is False


def test_f111_r10_volumen_implausible_se_calcula_con_paquetes_de_6():
    res = _calc(29.0)
    assert (res.num_contenedores, res.contenedor_m3) == (5, 6.0)
    assert any(r.startswith("residuos_volumen_implausible") for r in res.reasons)


def test_f111_r10_resultado_sin_revision_por_defecto():
    assert ResultadoContenedores(1, 1.0, 1.0).revision is False


def test_f111_docstring_documenta_la_regla_3_6_9():
    import application.services.residuos_container_calc as modulo

    doc = modulo.__doc__ or ""
    assert "3, 6 o 9" in doc
    assert "6 m3 por defecto" not in doc


# ------------------------------------------------------------------ #
# R4, R9, R11 · en el builder real
# ------------------------------------------------------------------ #
def _escenario_builder(*, m3, contrato, matched_id, precio, tipo_familia="residuos"):
    from tests.f036_escenarios_residuos import EscenarioResiduos, LineaResiduos

    return EscenarioResiduos(
        lineas=(
            LineaResiduos(
                descripcion="MADERA LER 170201",
                cantidad=m3,
                volumen_m3=m3,
                codigo_ler="170201",
                tipo_familia=tipo_familia,
                matched_contrato_line_id=matched_id,
                precio_contrato_db=precio,
            ),
        ),
        contrato=tuple(contrato),
        numero_albaran="4839 B",
    )


def test_f111_r4_builder_4839b_8m3_sin_tamano_es_1_por_139():
    from tests.f036_escenarios_residuos import base_de, linea_contrato, valorar

    madera = linea_contrato(
        7001, "CONTENEDOR LER 170201 MADERA", 139.0, codigo_contrato="CTSU24/0524"
    )
    cab, regs = valorar(
        _escenario_builder(m3=8.0, contrato=[madera], matched_id=7001, precio=139.0)
    )
    base = base_de(regs)
    assert base.cantidad_convertida == 1.0
    assert base.precio_unitario_final == 139.0
    assert base.importe_calculado == pytest.approx(139.0)
    assert "residuos_tamano_estandar=9m3" in base.review_reasons
    assert "residuos_contenedores=1 (m3=8 / contenedor=9 m3)" in base.review_reasons


def test_f111_r9_builder_tamano_distinto_de_casada_manda_a_revision():
    from tests.f036_escenarios_residuos import base_de, linea_contrato, valorar

    c6 = linea_contrato(7101, "CONTENEDOR RCD 6 M3", 120.0)
    c8 = linea_contrato(7102, "CONTENEDOR RCD 8 M3", 150.0)
    _cab, regs = valorar(
        _escenario_builder(m3=7.0, contrato=[c6, c8], matched_id=7101, precio=120.0)
    )
    base = base_de(regs)
    assert base.review_required is True
    assert "residuos_tamano_distinto_de_casada=8/6" in base.review_reasons
    # La casada y su precio no cambian (R9): 1 × 120.
    assert base.matched_contrato_line_id == 7101
    assert base.precio_unitario_final == 120.0
    assert base.cantidad_convertida == 1.0


def test_f111_r11_builder_una_linea_que_no_es_de_residuos_no_cuenta_contenedores():
    from tests.f036_escenarios_residuos import base_de, linea_contrato, valorar

    hormigon = linea_contrato(7201, "HORMIGON HA-25/B/20/IIA", 80.0)
    _cab, regs = valorar(
        _escenario_builder(
            m3=8.0, contrato=[hormigon], matched_id=7201, precio=80.0,
            tipo_familia="hormigon",
        )
    )
    base = base_de(regs)
    # Sin regla de residuos: la cantidad es la del albarán (8 m³), no 1.
    assert base.cantidad_albaran == 8.0
    assert not any(r.startswith("residuos_") for r in base.review_reasons)
