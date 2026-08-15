# tests/test_f003_guard_aritmetico.py
"""F-003 · Guard aritmetico de linea y de total (R6, R7, R8, R13).

Que un albaran venga valorado no significa que su aritmetica cuadre con
lo que el pipeline calcula. Cuando no cuadra, la regla de negocio es
clarisima: se persiste LO LEIDO y se manda a revision. Jamas se
sustituye por el calculado ni por un valor inventado.

Caso de referencia (x120): 120,55 l a 1,5877 EUR con importe impreso de
191,40 EUR. La aritmetica da 191,40 y cuadra; lo que reventaba antes era
meter ese 191,40 en precio_neto y volver a multiplicar por 120,55 ->
23.073,60 EUR. Aqui se comprueba que el importe persistido es el
impreso.

Sin red, BBDD ni LLM.
"""
from __future__ import annotations

import pytest

from application.services.guard_aritmetico import (
    importe_efectivo_linea_unica,
    verificar_linea,
    verificar_total,
)
from ayudas_f003 import (
    IMPORTE_TOLERANCE_PCT,
    construir,
    construir_builder,
    envelope,
    linea_contexto,
    linea_contrato,
    linea_valorada,
)


def _verificar_linea(**kwargs):
    parametros = {
        "precio_declarado": 1.5877,
        "cantidad": 120.55,
        "descuento_pct": None,
        "importe_leido": 191.40,
        "tolerance_pct": IMPORTE_TOLERANCE_PCT,
    }
    parametros.update(kwargs)
    return verificar_linea(**parametros)


# ---------------------------------------------------------------------
# R6 · Guard de linea (funcion pura)
# ---------------------------------------------------------------------


def test_f003_r6_el_caso_x120_cuadra() -> None:
    """120,55 x 1,5877 = 191,38 ~ 191,40 impreso: dentro de tolerancia."""
    assert _verificar_linea() == []


def test_f003_r6_un_importe_disparatado_no_cuadra() -> None:
    motivos = _verificar_linea(importe_leido=23073.60)

    assert len(motivos) == 1
    assert motivos[0].startswith("guard_aritmetico_linea:")
    assert "23073.6" in motivos[0]


def test_f003_r6_el_descuento_entra_en_la_comprobacion() -> None:
    # 10 x 100 x (1 - 20/100) = 800
    assert _verificar_linea(
        precio_declarado=100.0,
        cantidad=10.0,
        descuento_pct=20.0,
        importe_leido=800.0,
    ) == []
    # Sin contar el descuento saldria 1000 y el guard saltaria.
    assert _verificar_linea(
        precio_declarado=100.0,
        cantidad=10.0,
        descuento_pct=20.0,
        importe_leido=1000.0,
    ) != []


def test_f003_r6_sin_importe_leido_no_hay_nada_que_comprobar() -> None:
    assert _verificar_linea(importe_leido=None) == []


def test_f003_r6_sin_precio_o_sin_cantidad_no_es_computable() -> None:
    assert _verificar_linea(precio_declarado=None) == []
    assert _verificar_linea(cantidad=None) == []


def test_f003_r6_la_tolerancia_es_un_porcentaje_del_importe() -> None:
    # 100 x 1 = 100; con 5 % de tolerancia, 104 pasa y 106 no.
    assert _verificar_linea(
        precio_declarado=1.0, cantidad=100.0, importe_leido=104.0,
    ) == []
    assert _verificar_linea(
        precio_declarado=1.0, cantidad=100.0, importe_leido=106.0,
    ) != []


def test_f003_r6_cantidad_cero_no_dispara_falsos_positivos() -> None:
    assert _verificar_linea(cantidad=0.0, importe_leido=0.0) == []


def test_f003_r6_un_importe_leido_de_cero_cuenta_como_ausente() -> None:
    """Misma convencion que ImporteCalculator y PriceReconciler: una
    celda vacia devuelta como 0 no manda nada a revision."""
    assert _verificar_linea(
        precio_declarado=1.0, cantidad=100.0, importe_leido=0.0,
    ) == []


def test_f003_r6_un_precio_a_cero_contra_un_importe_impreso_descuadra() -> None:
    """Calculado 0 y leido 100 no cuadran: el atajo del 0 no puede
    tragarse un descuadre real."""
    assert _verificar_linea(
        precio_declarado=0.0, cantidad=10.0, importe_leido=100.0,
    ) != []


def test_f003_r6_la_tolerancia_es_inclusiva_en_el_limite() -> None:
    """Justo el 5 % pasa; un pelo mas, no."""
    # 95 calculado contra 100 leido = 5,00 % exacto sobre el mayor.
    assert _verificar_linea(
        precio_declarado=1.0, cantidad=95.0, importe_leido=100.0,
    ) == []
    assert _verificar_linea(
        precio_declarado=1.0, cantidad=94.0, importe_leido=100.0,
    ) != []


def test_f003_r6_un_descuento_fuera_de_rango_se_ignora() -> None:
    """Un 150 % de descuento es basura de OCR: se ignora en vez de
    fabricar un importe negativo y un descuadre fantasma."""
    assert _verificar_linea(
        precio_declarado=10.0,
        cantidad=10.0,
        descuento_pct=150.0,
        importe_leido=100.0,
    ) == []


def test_f003_r6_un_descuento_del_cien_por_cien_si_se_aplica() -> None:
    """100 % es un descuento legitimo (linea regalada): el importe
    esperado es 0, y un importe impreso de 100 descuadra."""
    assert _verificar_linea(
        precio_declarado=10.0,
        cantidad=10.0,
        descuento_pct=100.0,
        importe_leido=100.0,
    ) != []


def test_f003_r6_el_motivo_redondea_a_dos_decimales() -> None:
    """El motivo lo lee un humano en el portal: 191.38, no
    191.38173500000002."""
    motivos = _verificar_linea(
        precio_declarado=1.11111, cantidad=100.0, importe_leido=500.0,
    )

    assert motivos == ["guard_aritmetico_linea:111.11!=500.0"]


# ---------------------------------------------------------------------
# R6 · Guard de linea integrado en el builder
# ---------------------------------------------------------------------


def _linea_x120(**extra):
    """El caso x120 tal y como llega del sobre."""
    contexto = {
        "merge_line_id": 1,
        "descripcion": "GASOLEO B",
        "unidad_medida": "l",
        "unidad_categoria": "volume",
        "cantidad": 120.55,
        "precio_unitario_albaran": 1.5877,
        "importe_albaran": 191.40,
        "importe_leido": 191.40,
    }
    contexto.update(extra)
    return linea_contexto(**contexto)


def test_f003_r6_el_importe_persistido_es_el_leido() -> None:
    """Nunca 23.073,60: el impreso manda."""
    _, records = construir(
        construir_builder(),
        envelope(
            lineas_data=[linea_valorada(matched_contrato_line_id=None,
                                        match_method="no_match")],
            lineas_albaran=[_linea_x120()],
            lineas_contrato=[],
        ),
    )

    assert records[0].importe_calculado == pytest.approx(191.40)
    assert records[0].importe_source == "declared_albaran"


def test_f003_r6_una_linea_que_no_cuadra_va_a_revision() -> None:
    _, records = construir(
        construir_builder(),
        envelope(
            lineas_data=[linea_valorada(matched_contrato_line_id=None,
                                        match_method="exact_concept")],
            lineas_albaran=[_linea_x120(importe_leido=500.0,
                                        importe_albaran=500.0)],
            lineas_contrato=[],
        ),
    )

    record = records[0]
    assert record.review_required is True
    assert any(
        motivo.startswith("guard_aritmetico_linea:")
        for motivo in record.review_reasons
    )
    # Y aun asi el importe persistido sigue siendo el LEIDO.
    assert record.importe_calculado == pytest.approx(500.0)


def test_f003_r13_el_guard_de_linea_se_puede_apagar() -> None:
    _, records = construir(
        construir_builder(guard_aritmetico_enabled=False),
        envelope(
            lineas_data=[linea_valorada(matched_contrato_line_id=None,
                                        match_method="exact_concept")],
            lineas_albaran=[_linea_x120(importe_leido=500.0,
                                        importe_albaran=500.0)],
            lineas_contrato=[],
        ),
    )

    assert not [
        motivo
        for motivo in records[0].review_reasons
        if motivo.startswith("guard_aritmetico_linea:")
    ]


# ---------------------------------------------------------------------
# R7 · Guard de total (funcion pura)
# ---------------------------------------------------------------------


def _verificar_total(**kwargs):
    parametros = {
        "suma_from_albaran": 100.0,
        "importe_total": 100.0,
        "incluye_iva": False,
        "tolerance_pct": IMPORTE_TOLERANCE_PCT,
    }
    parametros.update(kwargs)
    return verificar_total(**parametros)


def test_f003_r7_un_total_base_que_cuadra_no_dice_nada() -> None:
    assert _verificar_total() == ([], False)


def test_f003_r7_un_total_base_que_no_cuadra_exige_revision() -> None:
    motivos, revision = _verificar_total(importe_total=150.0)

    assert revision is True
    assert len(motivos) == 1
    assert motivos[0].startswith("guard_aritmetico_total:")


def test_f003_r7_un_total_con_iva_solo_avisa() -> None:
    """Los importes de linea son base imponible: descuadrar con un total
    con IVA es lo ESPERADO, no un error que mandar a revision."""
    motivos, revision = _verificar_total(importe_total=121.0, incluye_iva=True)

    assert revision is False
    assert motivos == ["guard_aritmetico_total_con_iva:100.0!=121.0"]


def test_f003_r7_un_total_de_marca_desconocida_solo_avisa() -> None:
    motivos, revision = _verificar_total(importe_total=121.0, incluye_iva=None)

    assert revision is False
    assert motivos[0].startswith("guard_aritmetico_total_con_iva:")


def test_f003_r7_sin_total_el_guard_no_actua() -> None:
    assert _verificar_total(importe_total=None) == ([], False)


def test_f003_r7_un_total_a_cero_no_manda_nada_a_revision() -> None:
    """Una celda vacia leida como 0 no puede tirar la valoracion."""
    assert _verificar_total(importe_total=0.0) == ([], False)


def test_f003_r7_la_tolerancia_es_la_misma_del_importe() -> None:
    assert _verificar_total(importe_total=104.0) == ([], False)
    motivos, revision = _verificar_total(importe_total=106.0)
    assert revision is True
    assert motivos


# ---------------------------------------------------------------------
# R7 · Guard de total integrado en la cabecera
# ---------------------------------------------------------------------


def _sobre_dos_lineas(**meta):
    return envelope(
        lineas_data=[
            linea_valorada(merge_line_id=1, matched_contrato_line_id=100),
            linea_valorada(merge_line_id=2, matched_contrato_line_id=100),
        ],
        lineas_albaran=[
            linea_contexto(merge_line_id=1, line_index=1),
            linea_contexto(merge_line_id=2, line_index=2),
        ],
        lineas_contrato=[linea_contrato()],
        meta=meta,
    )


def test_f003_r7_la_suma_de_lineas_cuadra_con_el_total() -> None:
    header, _ = construir(
        construir_builder(),
        _sobre_dos_lineas(
            importe_total_albaran=20.0,
            importe_total_incluye_iva=False,
        ),
    )

    assert not [
        motivo
        for motivo in header.review_reasons
        if motivo.startswith("guard_aritmetico_total")
    ]


def test_f003_r7_una_suma_que_no_cuadra_manda_la_cabecera_a_revision() -> None:
    header, _ = construir(
        construir_builder(),
        _sobre_dos_lineas(
            importe_total_albaran=500.0,
            importe_total_incluye_iva=False,
        ),
    )

    assert header.review_required is True
    assert any(
        motivo.startswith("guard_aritmetico_total:")
        for motivo in header.review_reasons
    )


def test_f003_r7_con_total_con_iva_la_cabecera_solo_avisa() -> None:
    header, records = construir(
        construir_builder(),
        _sobre_dos_lineas(
            importe_total_albaran=24.2,
            importe_total_incluye_iva=True,
        ),
    )

    assert any(
        motivo.startswith("guard_aritmetico_total_con_iva:")
        for motivo in header.review_reasons
    )
    # El aviso NO puede ser, por si solo, motivo de revision.
    assert header.review_required == any(r.review_required for r in records)


def test_f003_r7_las_sinteticas_no_suman_en_el_guard_de_total() -> None:
    """Las M1-M7 no estan impresas en el papel: no pueden entrar en la
    suma que se compara con el total del documento."""
    header, records = construir(
        construir_builder(),
        envelope(
            lineas_data=[
                linea_valorada(merge_line_id=1, matched_contrato_line_id=100),
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
            lineas_albaran=[linea_contexto(merge_line_id=1)],
            lineas_contrato=[
                linea_contrato(contrato_line_id=100),
                linea_contrato(
                    contrato_line_id=200,
                    codigo_producto="INC",
                    descripcion="INCREMENTO 2026",
                    precio_unitario=5.0,
                ),
            ],
            meta={
                "importe_total_albaran": 10.0,
                "importe_total_incluye_iva": False,
            },
        ),
    )

    # El total valorado incluye la sintetica...
    assert header.total_valorado > 10.0
    # ...pero el guard compara solo las from_albaran, que suman 10.
    assert not [
        motivo
        for motivo in header.review_reasons
        if motivo.startswith("guard_aritmetico_total")
    ]


def test_f003_r13_el_guard_de_total_se_puede_apagar() -> None:
    header, _ = construir(
        construir_builder(guard_aritmetico_enabled=False),
        _sobre_dos_lineas(
            importe_total_albaran=500.0,
            importe_total_incluye_iva=False,
        ),
    )

    assert not [
        motivo
        for motivo in header.review_reasons
        if motivo.startswith("guard_aritmetico_total")
    ]


# ---------------------------------------------------------------------
# R8 · Caso ORE OIL: una linea, el total ES su importe
# ---------------------------------------------------------------------


class _LineaFalsa:
    def __init__(self, merge_line_id: int, importe_leido=None) -> None:
        self.merge_line_id = merge_line_id
        self.importe_leido = importe_leido


def test_f003_r8_linea_unica_sin_importe_toma_el_total() -> None:
    resultado = importe_efectivo_linea_unica(
        lineas_albaran=[_LineaFalsa(7)],
        importe_total=191.40,
        incluye_iva=False,
    )

    assert resultado == (7, 191.40)


def test_f003_r8_con_varias_lineas_no_se_inyecta_nada() -> None:
    assert importe_efectivo_linea_unica(
        lineas_albaran=[_LineaFalsa(1), _LineaFalsa(2)],
        importe_total=191.40,
        incluye_iva=False,
    ) is None


def test_f003_r8_si_la_linea_ya_trae_importe_no_se_toca() -> None:
    assert importe_efectivo_linea_unica(
        lineas_albaran=[_LineaFalsa(1, importe_leido=100.0)],
        importe_total=191.40,
        incluye_iva=False,
    ) is None


def test_f003_r8_un_total_con_iva_no_se_inyecta() -> None:
    """Los importes de linea son base: meter un total con IVA como
    importe de linea seria inventar."""
    assert importe_efectivo_linea_unica(
        lineas_albaran=[_LineaFalsa(1)],
        importe_total=231.59,
        incluye_iva=True,
    ) is None


def test_f003_r8_un_total_de_marca_desconocida_no_se_inyecta() -> None:
    assert importe_efectivo_linea_unica(
        lineas_albaran=[_LineaFalsa(1)],
        importe_total=231.59,
        incluye_iva=None,
    ) is None


def test_f003_r8_sin_total_no_se_inyecta() -> None:
    assert importe_efectivo_linea_unica(
        lineas_albaran=[_LineaFalsa(1)],
        importe_total=None,
        incluye_iva=False,
    ) is None


def test_f003_r8_un_total_a_cero_no_se_inyecta() -> None:
    assert importe_efectivo_linea_unica(
        lineas_albaran=[_LineaFalsa(1)],
        importe_total=0.0,
        incluye_iva=False,
    ) is None


def test_f003_r8_ore_oil_integrado_en_el_builder() -> None:
    """Una linea sin importe impreso + total base: el importe de la
    linea ES el total, con su motivo."""
    _, records = construir(
        construir_builder(),
        envelope(
            lineas_data=[
                linea_valorada(merge_line_id=1, matched_contrato_line_id=None,
                               match_method="no_match")
            ],
            lineas_albaran=[
                linea_contexto(
                    merge_line_id=1,
                    cantidad=1.0,
                    precio_unitario_albaran=None,
                    importe_albaran=None,
                    importe_leido=None,
                )
            ],
            lineas_contrato=[],
            meta={
                "importe_total_albaran": 191.40,
                "importe_total_incluye_iva": False,
            },
        ),
    )

    assert records[0].importe_calculado == pytest.approx(191.40)
    assert "importe_desde_total_documento" in records[0].review_reasons


def test_f003_r8_una_linea_del_lote_sin_contexto_no_revienta() -> None:
    """Robustez: si la IA devuelve una linea cuyo merge_line_id no esta
    en el contexto, el builder no puede caerse buscandola."""
    _, records = construir(
        construir_builder(),
        envelope(
            lineas_data=[
                linea_valorada(merge_line_id=1),
                linea_valorada(merge_line_id=999),
            ],
            lineas_albaran=[linea_contexto(merge_line_id=1)],
            lineas_contrato=[linea_contrato()],
            meta={
                "importe_total_albaran": 10.0,
                "importe_total_incluye_iva": False,
            },
        ),
    )

    assert len(records) == 2


def test_f003_r6_una_linea_limpia_no_va_a_revision() -> None:
    """Regresion del contrato del builder: sin motivos, no hay revision.
    Si esta se pone en rojo, algo esta mandando TODO a revisar."""
    _, records = construir(construir_builder(), envelope())

    assert records[0].review_required is False
    # Los motivos que queden son informativos (trazabilidad del precio),
    # ninguno de guard ni de red.
    assert not [
        motivo
        for motivo in records[0].review_reasons
        if motivo.startswith(("guard_aritmetico", "atributo_sustantivo"))
    ]


def test_f003_r13_ore_oil_no_actua_con_el_guard_apagado() -> None:
    _, records = construir(
        construir_builder(guard_aritmetico_enabled=False),
        envelope(
            lineas_data=[
                linea_valorada(merge_line_id=1, matched_contrato_line_id=None,
                               match_method="no_match")
            ],
            lineas_albaran=[
                linea_contexto(
                    merge_line_id=1,
                    cantidad=1.0,
                    precio_unitario_albaran=None,
                    importe_albaran=None,
                    importe_leido=None,
                )
            ],
            lineas_contrato=[],
            meta={
                "importe_total_albaran": 191.40,
                "importe_total_incluye_iva": False,
            },
        ),
    )

    assert "importe_desde_total_documento" not in records[0].review_reasons
