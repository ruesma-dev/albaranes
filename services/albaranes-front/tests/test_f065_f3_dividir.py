# tests/test_f065_f3_dividir.py
"""F-065 · fase 3 · R29–R35: dividir una fila (F6) en varias partes.

- R29: F6 (o «Dividir») abre una ventana con el número de líneas (2–20), la
  cantidad y la partida de cada una y lo que falta por repartir; «Aceptar»
  solo con la suma = Q. F7 (duplicar) desaparece.
- R30: 404 si la fila no es del documento; 409 con alta bloqueante, aprobado
  o fila bloqueada; 422 sin cambios si es sintética, Q es nula o 0, una parte
  es nula, 0 o de otro signo, o la suma difiere de Q en 0,005 o más.
- R31: la original es la parte 1; cada parte k ≥ 2 nace ``reparto``, sin
  ``merge_line_id``, colgando de la blanca de la original y con sus campos
  copiados; ``cantidad_convertida = qk`` y ``cantidad_albaran = ca0 × qk / Q``.
- R32: con la partida de la original (o vacía) conserva origen y vínculo; con
  otra, Nueva con derivada propia.
- R33: ``round(importe0 × qk / Q, 2)`` y la última absorbe el redondeo; sin
  importe, la fórmula canónica.
- R34: una transacción, total recalculado y UNA entrada de «Deshacer».
- R35: «Parte k de N» bajo la original y el aviso mientras la familia no
  sume la cantidad de su blanca.

Decisión de la fase (pedida por el coordinador): una fila con la marca
«revisa la cantidad» (H2/CR3) NO se divide hasta resolverla (422, la Q no es
de fiar, como una Q nula): las partes no heredan una marca que habría que
propagar y quitar en N filas.

Repositorio real sobre SQLite (``f065_bbdd``), plantilla real y JS con node.
"""
from __future__ import annotations

import json

import pytest
from f053_sv4_bbdd import foto, poner_alta
from f065_bbdd import (
    CONTRATO,
    DOC,
    construir,
    ejecutar,
    fila,
    filas,
    repositorio,
    total,
)
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_f051_almacen_front import _app_js
from test_f065_f1_cabecera import _cliente
from test_f065_f1_js import _ejecutar, con_node


def _partes(*pares):
    from domain.models.review_models import ParteDivision

    return [ParteDivision(cantidad=q, codigo_partida=p) for q, p in pares]


def _dividir(motor, vid, *pares):
    return repositorio(motor).dividir_linea(
        document_id=DOC, valuation_line_id=vid, partes=_partes(*pares),
    )


def _derivada(motor, did):
    with Session(motor) as s:
        return dict(s.execute(text(
            "SELECT codigo_contrato, descripcion_linea, unidad_medida, precio_unitario, "
            "codigo_partida, origen, created_by_valuation_id, source_document_id "
            "FROM contrato_lines_derived WHERE id = :id"), {"id": did}).mappings().one())


def _columnas(motor, vid, *columnas):
    with Session(motor) as s:
        return dict(s.execute(text(
            f"SELECT {', '.join(columnas)} FROM albaran_line_valuations WHERE id = :id"),
            {"id": vid}).mappings().one())


def _fila_18(motor):
    """La 12 con 18 ud a 115 € (2070 €): el caso de T27 (6 / 7 / 5)."""
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = 18, "
             "cantidad_convertida = 18, importe_calculado = 2070 WHERE id = 12")
    ejecutar(motor, "UPDATE albaran_valuations SET total_valorado = 0 WHERE id = 'f065-val-1'")


# =================================================================== #
# T22 · dominio: repartir (R30, R31, R33) y el cuerpo (R29, R30)
# =================================================================== #
def test_f065_r31_dominio_cantidades_de_cada_parte():
    from domain.models.review_models import repartir

    partes = repartir(q=18.0, ca0=18.0, importe0=2070.0, precio=115.0, descuento=None,
                      partes=[6.0, 7.0, 5.0])

    assert [p.cantidad_convertida for p in partes] == [6.0, 7.0, 5.0]
    assert [p.cantidad_albaran for p in partes] == [6.0, 7.0, 5.0]
    assert [p.importe for p in partes] == [690.0, 805.0, 575.0]


def test_f065_r31_dominio_con_conversion_se_prorratea_la_del_albaran():
    """3 t leídas = 3000 kg a 0,05 €/kg: 1000 + 2000 kg son 1 + 2 t."""
    from domain.models.review_models import repartir

    partes = repartir(q=3000.0, ca0=3.0, importe0=150.0, precio=0.05, descuento=None,
                      partes=[1000.0, 2000.0])

    assert [p.cantidad_albaran for p in partes] == [1.0, 2.0]
    assert [p.importe for p in partes] == [50.0, 100.0]


def test_f065_r31_dominio_sin_cantidad_del_albaran_queda_sin_ella():
    from domain.models.review_models import repartir

    partes = repartir(q=10.0, ca0=None, importe0=100.0, precio=10.0, descuento=None,
                      partes=[4.0, 6.0])

    assert [p.cantidad_albaran for p in partes] == [None, None]


@pytest.mark.parametrize(("importe0", "q", "cantidades", "esperado"), [
    (100.0, 3.0, [1.0, 1.0, 1.0], [33.33, 33.33, 33.34]),
    (10.0, 3.0, [2.0, 1.0], [6.67, 3.33]),
    (-100.0, -3.0, [-1.0, -2.0], [-33.33, -66.67]),
    (0.05, 3.0, [1.0, 1.0, 1.0], [0.02, 0.02, 0.01]),
], ids=["tercios", "dos_tercios", "abono", "centimos"])
def test_f065_r33_dominio_la_ultima_absorbe_el_redondeo(importe0, q, cantidades, esperado):
    from domain.models.review_models import repartir

    partes = repartir(q=q, ca0=q, importe0=importe0, precio=None, descuento=None,
                      partes=cantidades)

    assert [p.importe for p in partes] == esperado
    assert round(sum(p.importe for p in partes), 2) == importe0


def test_f065_r33_dominio_sin_importe_la_formula_canonica():
    from domain.models.review_models import repartir

    partes = repartir(q=10.0, ca0=10.0, importe0=None, precio=115.0, descuento=10.0,
                      partes=[4.0, 6.0])

    assert [p.importe for p in partes] == [414.0, 621.0]


def test_f065_r33_dominio_sin_importe_ni_precio_sin_importe():
    from domain.models.review_models import repartir

    partes = repartir(q=10.0, ca0=10.0, importe0=None, precio=None, descuento=None,
                      partes=[4.0, 6.0])

    assert [p.importe for p in partes] == [None, None]


@pytest.mark.parametrize(("q", "cantidades"), [
    (None, [4.0, 6.0]),
    (0.0, [4.0, -4.0]),
    (10.0, [10.0]),
    (21.0, [1.0] * 21),
    (10.0, [4.0, None]),
    (10.0, [10.0, 0.0]),
    (10.0, [12.0, -2.0]),
    (-10.0, [-12.0, 2.0]),
    (10.0, [4.0, 6.005]),
    (10.0, [4.0, 5.995]),
    (10.0, [4.0, 5.0]),
], ids=["q_nula", "q_cero", "una_parte", "veintiuna", "parte_nula", "parte_cero",
        "signo_distinto", "signo_distinto_abono", "sobra_media_milesima",
        "falta_media_milesima", "no_suma"])
def test_f065_r30_dominio_reparto_invalido(q, cantidades):
    from domain.models.review_models import RepartoInvalido, repartir

    with pytest.raises(RepartoInvalido) as error:
        repartir(q=q, ca0=q, importe0=100.0, precio=10.0, descuento=None, partes=cantidades)

    assert str(error.value)


@pytest.mark.parametrize("cantidades", [
    [4.0, 6.004], [4.0, 5.996], [1.0] * 20, [-4.0, -6.0],
], ids=["sobra_menos_de_media", "falta_menos_de_media", "veinte", "abono"])
def test_f065_r30_dominio_reparto_valido_en_el_limite(cantidades):
    from domain.models.review_models import repartir

    q = 20.0 if len(cantidades) == 20 else (-10.0 if cantidades[0] < 0 else 10.0)

    assert len(repartir(q=q, ca0=q, importe0=None, precio=1.0, descuento=None,
                        partes=cantidades)) == len(cantidades)


def test_f065_r30_dominio_la_tolerancia_es_estricta_sin_ruido():
    """Difiere en «0,005 o más»: el umbral exacto ya no vale; una diezmilésima
    de millonésima menos, sí."""
    from domain.models.review_models import (
        _UMBRAL_REPARTO,
        _fuera_de_tolerancia,
        repartir,
    )

    assert _fuera_de_tolerancia(_UMBRAL_REPARTO, 0.0)
    assert not _fuera_de_tolerancia(0.00499994, 0.0)
    assert len(repartir(q=10.0, ca0=10.0, importe0=None, precio=1.0, descuento=None,
                        partes=[4.0, 6.00499994])) == 2


def test_f065_r33_dominio_la_ultima_tambien_en_centimos():
    """Un importe con más de dos decimales: la última parte sale en céntimos."""
    from domain.models.review_models import repartir

    partes = repartir(q=2.0, ca0=2.0, importe0=10.006, precio=None, descuento=None,
                      partes=[1.0, 1.0])

    assert [p.importe for p in partes] == [5.0, 5.01]


def test_f065_r30_dominio_los_mensajes_dicen_que_falla():
    from domain.models.review_models import RepartoInvalido, repartir

    def mensaje(q, cantidades):
        with pytest.raises(RepartoInvalido) as error:
            repartir(q=q, ca0=q, importe0=None, precio=1.0, descuento=None,
                     partes=cantidades)
        return str(error.value)

    assert "sin cantidad" in mensaje(None, [1.0, 1.0])
    assert "sin cantidad" in mensaje(0.0, [1.0, 1.0])
    assert "entre 2 y 20" in mensaje(10.0, [10.0])
    assert "parte 2" in mensaje(10.0, [10.0, 0.0])
    assert "parte 1" in mensaje(10.0, [-1.0, 11.0])
    assert "suman 9" in mensaje(10.0, [4.0, 5.0]) and "10" in mensaje(10.0, [4.0, 5.0])


def test_f065_r30_dominio_el_cuerpo_valida_partes_y_numeros():
    from domain.models.review_models import DivisionBody
    from pydantic import ValidationError

    cuerpo = DivisionBody(partes=[
        {"cantidad": "6,5", "codigo_partida": " 01.02 "},
        {"cantidad": 11.5, "codigo_partida": ""},
        {"cantidad": 1, "codigo_partida": None},
    ])

    assert [(p.cantidad, p.codigo_partida) for p in cuerpo.partes] == [
        (6.5, "01.02"), (11.5, None), (1.0, None)]
    for malo in ([{"cantidad": 1}], [{"cantidad": 1}] * 21, [{"cantidad": "x"}] * 2):
        with pytest.raises(ValidationError):
            DivisionBody(partes=malo)
    assert DivisionBody(partes=[{"cantidad": 1}] * 20)
    assert DivisionBody(partes=[{"cantidad": None}, {"cantidad": 1}]).partes[0].cantidad is None


# =================================================================== #
# T23 · repositorio (R30–R34)
# =================================================================== #
def test_f065_r31_r32_repositorio_divide_18_en_6_7_5():
    """T27 en SQLite: 6 con su partida, 7 con otra (Nueva), 5 a almacén."""
    motor = construir()
    _fila_18(motor)

    hecha = _dividir(motor, 12, (6, "01.02"), (7, "01.03"), (5, None))

    p2, p3 = hecha.partes
    original, nueva, almacen = fila(motor, 12), fila(motor, p2), fila(motor, p3)
    assert (original["cantidad_convertida"], original["cantidad_albaran"],
            original["importe_calculado"], original["importe_source"]) == (
        6.0, 6.0, 690.0, "calculated")
    assert (original["matched_contrato_line_id"], original["derived_contrato_line_id"],
            original["codigo_partida_final"], original["line_kind"]) == (
        502, None, "01.02", "from_albaran")
    for parte in (nueva, almacen):
        assert (parte["line_kind"], parte["merge_line_id"], parte["parent_merge_line_id"],
                parte["importe_source"], parte["bloqueada"]) == (
            "reparto", None, 702, "calculated", 0)
        # CR1 (sv9 la necesita) y O3 de la review: el texto que enseña la original
        # (una fila Contrato enseña el de su línea de contrato).
        assert parte["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-90"
    assert nueva["matched_contrato_line_id"] is None
    assert hecha.derivadas == [nueva["derived_contrato_line_id"]]
    assert _derivada(motor, nueva["derived_contrato_line_id"]) == {
        "codigo_contrato": CONTRATO, "descripcion_linea": "PUERTA CORTAFUEGOS EI2-90",
        "unidad_medida": "UD", "precio_unitario": 115.0, "codigo_partida": "01.03",
        "origen": "manual_override", "created_by_valuation_id": "f065-val-1",
        "source_document_id": DOC}
    assert (nueva["codigo_partida_final"], nueva["precio_unitario_agreement"],
            nueva["cantidad_convertida"], nueva["cantidad_albaran"],
            nueva["importe_calculado"]) == ("01.03", "manual", 7.0, 7.0, 805.0)
    assert (almacen["matched_contrato_line_id"], almacen["derived_contrato_line_id"],
            almacen["codigo_partida_final"], almacen["partida_action"]) == (
        502, None, None, "almacen_elegido")
    assert (almacen["cantidad_convertida"], almacen["importe_calculado"]) == (5.0, 575.0)
    assert total(motor) == 920.0 + 2070.0 + 50.0


def test_f065_r31_repositorio_las_partes_copian_los_campos_de_la_original():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_contrato_db = 115, "
             "precio_unitario_source = 'contract_db', unidad_albaran = 'UDS', "
             "unidad_categoria = 'unidad', unidad_category_match = 1, "
             "descuento_albaran_aplicado = 10, producto_sigrid = 'MA0001', "
             "codigo_externo = 'EXT-9', match_method = 'semantic', "
             "match_confidence_pct = 87.5, descripcion_linea = 'PUERTA EI2-90 HOJA' "
             "WHERE id = 12")
    copiadas = ("precio_unitario_contrato_db", "precio_unitario_final",
                "precio_unitario_source", "precio_unitario_agreement", "unidad_albaran",
                "unidad_contrato", "unidad_categoria", "unidad_category_match",
                "factor_conversion", "descuento_albaran_aplicado", "producto_sigrid",
                "codigo_externo", "match_method", "match_confidence_pct",
                "descripcion_linea", "matched_contrato_line_id", "codigo_partida_final")
    antes = _columnas(motor, 12, *copiadas)

    (p2,) = _dividir(motor, 12, (4, "01.02"), (6, "01.02")).partes

    assert _columnas(motor, p2, *copiadas) == antes
    assert _columnas(motor, 12, *copiadas) == antes
    assert (fila(motor, 12)["importe_calculado"], fila(motor, p2)["importe_calculado"]) == (
        460.0, 690.0)


def test_f065_r31_repositorio_las_partes_salen_de_revision_y_desbloqueadas():
    motor = construir()

    (p2,) = _dividir(motor, 12, (4, "01.02"), (6, "01.02")).partes

    parte = fila(motor, p2)
    assert (parte["review_required"], parte["review_reasons_json"], parte["bloqueada"]) == (
        0, None, 0)


def test_f065_r31_repositorio_con_conversion_la_del_albaran_se_prorratea():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = 2, "
             "cantidad_convertida = 2000, factor_conversion = 1000, "
             "precio_unitario_final = 0.575 WHERE id = 12")

    (p2,) = _dividir(motor, 12, (500, "01.02"), (1500, "01.02")).partes

    assert (fila(motor, 12)["cantidad_albaran"], fila(motor, 12)["cantidad_convertida"]) == (
        0.5, 500.0)
    assert (fila(motor, p2)["cantidad_albaran"], fila(motor, p2)["cantidad_convertida"],
            fila(motor, p2)["factor_conversion"]) == (1.5, 1500.0, 1000.0)
    assert (fila(motor, 12)["importe_calculado"], fila(motor, p2)["importe_calculado"]) == (
        287.5, 862.5)


def test_f065_r32_repositorio_una_nueva_reparte_con_derivada_propia_por_parte():
    """La 13 (Nueva, derivada 601, sin convertida: Q = la del albarán)."""
    motor = construir()

    hecha = _dividir(motor, 13, (0.4, "03.01"), (0.6, None))

    (p2,) = hecha.partes
    original, parte = fila(motor, 13), fila(motor, p2)
    assert original["derived_contrato_line_id"] == 601
    assert parte["derived_contrato_line_id"] not in (None, 601)
    assert hecha.derivadas == [parte["derived_contrato_line_id"]]
    assert _derivada(motor, parte["derived_contrato_line_id"])["origen"] == "manual_override"
    assert _derivada(motor, parte["derived_contrato_line_id"])["codigo_partida"] is None
    assert _derivada(motor, parte["derived_contrato_line_id"])["descripcion_linea"] == "PORTES"
    assert (parte["codigo_partida_final"], parte["partida_action"]) == (None, "almacen_elegido")
    assert (original["cantidad_convertida"], original["cantidad_albaran"]) == (0.4, 0.4)
    assert (parte["cantidad_convertida"], parte["cantidad_albaran"]) == (0.6, 0.6)
    assert (original["importe_calculado"], parte["importe_calculado"]) == (20.0, 30.0)
    assert _derivada(motor, 601)["codigo_partida"] == "03.01"


def test_f065_r32_repositorio_nueva_con_otra_partida_en_la_parte_1_edita_su_derivada():
    motor = construir()

    hecha = _dividir(motor, 13, (0.5, "03.02"), (0.5, "03.01"))

    assert fila(motor, 13)["codigo_partida_final"] == "03.02"
    assert _derivada(motor, 601)["codigo_partida"] == "03.02"
    assert _derivada(motor, fila(motor, hecha.partes[0])["derived_contrato_line_id"])[
        "codigo_partida"] == "03.01"


def test_f065_r32_repositorio_la_parte_1_con_otra_partida_pasa_a_nueva():
    motor = construir()

    hecha = _dividir(motor, 12, (4, "01.03"), (6, "01.02"))

    original, parte = fila(motor, 12), fila(motor, hecha.partes[0])
    assert original["matched_contrato_line_id"] is None
    # Con blanca y sin descripción fijada: sv9 manda el concepto leído (CR1/H1).
    assert original["descripcion_linea"] is None
    assert hecha.derivadas == [original["derived_contrato_line_id"]]
    assert _derivada(motor, original["derived_contrato_line_id"])["codigo_partida"] == "01.03"
    assert (original["codigo_partida_final"], original["precio_unitario_agreement"]) == (
        "01.03", "manual")
    assert (parte["matched_contrato_line_id"], parte["codigo_partida_final"]) == (502, "01.02")


def test_f065_r32_repositorio_la_parte_1_a_almacen_sigue_contrato():
    motor = construir()

    _dividir(motor, 12, (4, None), (6, "01.02"))

    original = fila(motor, 12)
    assert (original["matched_contrato_line_id"], original["codigo_partida_final"],
            original["partida_action"]) == (502, None, "almacen_elegido")


def test_f065_r32_repositorio_la_partida_de_su_linea_de_contrato_sigue_contrato():
    """P10: la fila estaba en otra partida; la parte que vuelve a la de su
    línea de contrato sigue Contrato; la que se queda en la actual, también."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET codigo_partida_final = '09.99' "
             "WHERE id = 12")

    hecha = _dividir(motor, 12, (4, "09.99"), (6, "01.02"))

    assert hecha.derivadas == []
    assert fila(motor, 12)["codigo_partida_final"] == "09.99"
    assert (fila(motor, hecha.partes[0])["matched_contrato_line_id"],
            fila(motor, hecha.partes[0])["codigo_partida_final"]) == (502, "01.02")


def test_f065_r33_repositorio_la_ultima_absorbe_el_redondeo():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = 3, "
             "cantidad_convertida = 3, importe_calculado = 100 WHERE id = 11")

    hecha = _dividir(motor, 11, (1, "01.01"), (1, "01.01"), (1, "01.01"))

    importes = [fila(motor, vid)["importe_calculado"] for vid in [11, *hecha.partes]]
    assert importes == [33.33, 33.33, 33.34]
    assert total(motor) == 100.0 + 1150.0 + 50.0


def test_f065_r33_repositorio_sin_importe_la_formula_canonica():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET importe_calculado = NULL, "
             "descuento_albaran_aplicado = 10 WHERE id = 12")

    (p2,) = _dividir(motor, 12, (4, "01.02"), (6, "01.02")).partes

    assert (fila(motor, 12)["importe_calculado"], fila(motor, p2)["importe_calculado"]) == (
        414.0, 621.0)


def test_f065_r31_repositorio_dividir_una_parte_cuelga_de_la_misma_blanca():
    motor = construir()
    (p2,) = _dividir(motor, 12, (4, "01.02"), (6, "01.02")).partes

    (p3,) = _dividir(motor, p2, (2, "01.02"), (4, "01.02")).partes

    assert (fila(motor, p3)["line_kind"], fila(motor, p3)["parent_merge_line_id"]) == (
        "reparto", 702)
    assert [f["cantidad_convertida"] for f in filas(motor) if f["id"] in (12, p2, p3)] == [
        4.0, 2.0, 4.0]


def test_f065_r31_repositorio_una_fila_sin_blanca_reparte_sin_padre():
    """Una fila traída del contrato (``manual``, sin blanca): sus partes no
    cuelgan de ninguna blanca y llevan la descripción de la original."""
    motor = construir()
    ids = repositorio(motor).add_valuation_lines_from_contrato(
        document_id=DOC, lineas=[(503, 5.0)])

    (p2,) = _dividir(motor, ids[0], (2, "01.03"), (3, "01.03")).partes

    parte = fila(motor, p2)
    assert (parte["line_kind"], parte["parent_merge_line_id"], parte["descripcion_linea"]) == (
        "reparto", None, "PUERTA CORTAFUEGOS EI2-120")


def test_f065_r31_repositorio_la_descripcion_de_su_linea_si_no_hay_otra():
    motor = construir()
    (vid,) = repositorio(motor).add_valuation_lines_from_contrato(
        document_id=DOC, lineas=[(503, 5.0)])
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = NULL "
             "WHERE id = :v", v=vid)

    (p2,) = _dividir(motor, vid, (2, "01.03"), (3, "01.03")).partes

    assert fila(motor, p2)["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-120"


def test_f065_r31_repositorio_sin_descripcion_ninguna_queda_nula():
    motor = construir()
    vid = repositorio(motor).add_standalone_valuation_line(document_id=DOC)
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = 2, "
             "cantidad_convertida = 2, importe_calculado = 10 WHERE id = :v", v=vid)

    (p2,) = _dividir(motor, vid, (1, None), (1, None)).partes

    assert fila(motor, p2)["descripcion_linea"] is None


@pytest.mark.parametrize(("precio", "unidad", "esperado"), [
    (120.0, "M2", (120.0, "M2", [480.0, 720.0])),
    (None, None, (115.0, "UD", [460.0, 690.0])),
], ids=["los_de_la_fila", "los_de_su_linea"])
def test_f065_r31_repositorio_precio_y_unidad_de_la_fila_o_de_su_linea(precio, unidad, esperado):
    """La derivada de la parte que pasa a Nueva y el importe sin ``importe0``
    salen del precio y la unidad de la fila; si no los tiene, de su línea."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = :p, "
             "unidad_contrato = :u, importe_calculado = NULL WHERE id = 12",
             p=precio, u=unidad)

    hecha = _dividir(motor, 12, (4, "01.02"), (6, "01.03"))

    derivada = _derivada(motor, hecha.derivadas[0])
    importes = [fila(motor, vid)["importe_calculado"] for vid in [12, *hecha.partes]]
    assert (derivada["precio_unitario"], derivada["unidad_medida"], importes) == esperado


def _sintetica(motor):
    ejecutar(motor, "INSERT INTO albaran_line_valuations (id, valuation_id, merge_line_id, "
             "derived_contrato_line_id, cantidad_albaran, cantidad_convertida, "
             "importe_calculado, line_kind, parent_merge_line_id, codigo_partida_final) "
             "VALUES (14, 'f065-val-1', NULL, 601, 1, 1, 10, 'synthetic_modifier', 703, "
             "'03.01')")
    return 14


def _sin_q(motor):
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = NULL, "
             "cantidad_convertida = NULL WHERE id = 12")
    return 12


def _q_cero(motor):
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_convertida = 0 WHERE id = 12")
    return 12


def _marcada(motor):
    ejecutar(motor, "UPDATE albaran_line_valuations SET review_reasons_json = :r WHERE id = 12",
             r=json.dumps(["front_unidad_cambiada_revisa_cantidad"]))
    return 12


def _huerfana(motor):
    ejecutar(motor, "UPDATE albaran_line_valuations SET matched_contrato_line_id = NULL "
             "WHERE id = 12")
    return 12


@pytest.mark.parametrize(("preparar", "pares", "texto"), [
    (_huerfana, [(4, "01.02"), (6, "01.02")], "revalora"),
    (_sintetica, [(0.5, "03.01"), (0.5, "03.01")], "sintética"),
    (_sin_q, [(4, "01.02"), (6, "01.02")], "sin cantidad"),
    (_q_cero, [(4, "01.02"), (-4, "01.02")], "sin cantidad"),
    (lambda m: 12, [(4, "01.02"), (5, "01.02")], "suman 9"),
    (lambda m: 12, [(10, "01.02"), (0, "01.02")], "parte 2"),
    (lambda m: 12, [(12, "01.02"), (-2, "01.02")], "parte 2"),
    (lambda m: 12, [(4, "01.02"), (None, "01.02")], "parte 2"),
    (_marcada, [(4, "01.02"), (6, "01.02")], "revisa la cantidad"),
], ids=["huerfana", "sintetica", "q_nula", "q_cero", "no_suma", "parte_cero", "signo", "parte_nula",
        "unidad_cambiada"])
def test_f065_r30_repositorio_422_sin_cambiar_nada(preparar, pares, texto):
    from domain.models.review_models import RepartoInvalido

    motor = construir()
    vid = preparar(motor)
    antes = foto(motor)

    with pytest.raises(RepartoInvalido) as error:
        _dividir(motor, vid, *pares)

    assert texto in str(error.value)
    assert foto(motor) == antes


def test_f065_r30_repositorio_fila_de_otro_documento_es_none_sin_cambiar_nada():
    motor = construir()
    antes = foto(motor)

    assert _dividir(motor, 21, (1, "01.01"), (2, "01.01")) is None
    assert _dividir(motor, 999, (1, "01.01"), (2, "01.01")) is None
    assert foto(motor) == antes


def test_f065_r30_repositorio_409_aprobado():
    from domain.models.review_models import AlbaranAprobadoError

    motor = construir(aprobado=True)
    antes = foto(motor)

    with pytest.raises(AlbaranAprobadoError):
        _dividir(motor, 12, (4, "01.02"), (6, "01.02"))
    assert foto(motor) == antes


def test_f065_r30_repositorio_409_fila_bloqueada():
    from domain.models.review_models import LineaBloqueadaError

    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET bloqueada = 1 WHERE id = 12")
    antes = foto(motor)

    with pytest.raises(LineaBloqueadaError):
        _dividir(motor, 12, (4, "01.02"), (6, "01.02"))
    assert foto(motor) == antes


def test_f065_r30_repositorio_409_alta_bloqueante():
    from domain.models.alta_sigrid_models import AlbaranBloqueadoError

    motor = construir(con_altas=True)
    poner_alta(motor, "registrado", document_id=DOC)
    antes = foto(motor)

    with pytest.raises(AlbaranBloqueadoError):
        _dividir(motor, 12, (4, "01.02"), (6, "01.02"))
    assert foto(motor) == antes


def test_f065_r34_repositorio_una_transaccion(monkeypatch):
    """Si algo falla después de insertar las partes, no queda nada."""
    from infrastructure.database.review_repository import AlbaranReviewRepository

    motor = construir()
    antes = foto(motor)

    def revienta(self, session, valuation_id):
        raise RuntimeError("total")

    monkeypatch.setattr(AlbaranReviewRepository, "_recalcular_total_in_session", revienta)
    with pytest.raises(RuntimeError):
        _dividir(motor, 12, (4, "01.02"), (6, "01.03"))
    assert foto(motor) == antes


# =================================================================== #
# T23 · deshacer (R34)
# =================================================================== #
def _deshacer(motor):
    """Lo que hace ``undo_last`` (que usa ``FOR UPDATE``, PostgreSQL): borra
    lo creado y restaura lo modificado, con los métodos reales."""
    repo = repositorio(motor)
    with Session(motor) as s:
        (payload,) = s.execute(text(
            "SELECT payload FROM undo_log WHERE document_id = :d AND undone = 0"),
            {"d": DOC}).scalars().all()
        entrada = json.loads(payload)
        for item in entrada["delete_created"]:
            s.execute(text(f"DELETE FROM {item['table']} WHERE id = :id"), {"id": item["id"]})
        for snap in entrada["reinsert"]:
            repo._undo_apply_reinsert(s, snap)
        for snap in entrada["restore"]:
            repo._undo_apply_restore(s, snap)
        s.execute(text("DELETE FROM undo_log"))
        s.commit()
    return entrada


def _sin_historial(motor):
    datos = foto(motor)
    datos.pop("undo_log")
    return datos


@pytest.mark.parametrize("pares", [
    [(6, "01.02"), (7, "01.03"), (5, None)],
    [(6, "01.03"), (12, "01.02")],
    [(6, None), (12, "01.02")],
], ids=["t27", "la_original_pasa_a_nueva", "la_original_a_almacen"])
def test_f065_r34_deshacer_una_entrada_lo_deja_como_estaba(pares):
    from application.services.review_service import ReviewService

    motor = construir()
    _fila_18(motor)
    antes = _sin_historial(motor)

    hecha = ReviewService(repositorio(motor), "ana").dividir_linea(
        document_id=DOC, valuation_line_id=12, partes=_partes(*pares))

    assert hecha is not None and _sin_historial(motor) != antes
    entrada = _deshacer(motor)
    assert [d["table"] for d in entrada["delete_created"]] == (
        ["albaran_line_valuations"] * len(hecha.partes)
        + ["contrato_lines_derived"] * len(hecha.derivadas))
    assert _sin_historial(motor) == antes


def test_f065_r34_deshacer_una_nueva_devuelve_su_derivada():
    from application.services.review_service import ReviewService

    motor = construir()
    antes = _sin_historial(motor)

    ReviewService(repositorio(motor), "ana").dividir_linea(
        document_id=DOC, valuation_line_id=13, partes=_partes((0.5, "03.02"), (0.5, "03.01")))

    assert _derivada(motor, 601)["codigo_partida"] == "03.02"
    _deshacer(motor)
    assert _sin_historial(motor) == antes


def test_f065_r34_deshacer_la_entrada_dice_que_se_dividio():
    from application.services.review_service import ReviewService

    motor = construir()

    ReviewService(repositorio(motor), "ana").dividir_linea(
        document_id=DOC, valuation_line_id=12, partes=_partes((4, "01.02"), (6, "01.02")))

    with Session(motor) as s:
        (accion, descripcion) = s.execute(text(
            "SELECT action, description FROM undo_log WHERE document_id = :d"),
            {"d": DOC}).one()
    assert accion == "dividir"
    assert descripcion.startswith("Dividir en 2 · 01.02")


def test_f065_r34_deshacer_sin_division_no_hay_entrada():
    from application.services.review_service import ReviewService

    motor = construir()

    assert ReviewService(repositorio(motor), "ana").dividir_linea(
        document_id=DOC, valuation_line_id=21,
        partes=_partes((1, "01.01"), (2, "01.01"))) is None
    assert foto(motor)["undo_log"] == []


# =================================================================== #
# T23 · la ruta (R30)
# =================================================================== #
class _Servicio:
    def __init__(self, resultado=None, error=None):
        self.resultado, self.error, self.llamadas = resultado, error, []

    def initialize(self):
        return True

    def dividir_linea(self, *, document_id, valuation_line_id, partes):
        self.llamadas.append((document_id, valuation_line_id,
                              [(p.cantidad, p.codigo_partida) for p in partes]))
        if self.error is not None:
            raise self.error
        return self.resultado


def _ruta(vid=12):
    return f"/api/documents/{DOC}/lines/{vid}/dividir"


def test_f065_r30_ruta_divide_y_devuelve_las_partes(monkeypatch):
    from domain.models.review_models import DivisionHecha

    servicio = _Servicio(DivisionHecha(partes=[31, 32], derivadas=[7]))
    cliente = _cliente(monkeypatch, servicio)

    respuesta = cliente.post(_ruta(), json={"partes": [
        {"cantidad": "6", "codigo_partida": "01.02"},
        {"cantidad": "7,5", "codigo_partida": "01.03"},
        {"cantidad": 4.5, "codigo_partida": ""}]})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True, "document_id": DOC, "valuation_line_id": 12,
                                "partes": [31, 32]}
    assert servicio.llamadas == [(DOC, 12, [(6.0, "01.02"), (7.5, "01.03"), (4.5, None)])]


def test_f065_r30_ruta_404_si_no_es_del_documento(monkeypatch):
    respuesta = _cliente(monkeypatch, _Servicio(None)).post(_ruta(21), json={"partes": [
        {"cantidad": 1}, {"cantidad": 2}]})

    assert respuesta.status_code == 404


def test_f065_r30_ruta_422_con_el_motivo(monkeypatch):
    from domain.models.review_models import RepartoInvalido

    respuesta = _cliente(monkeypatch, _Servicio(error=RepartoInvalido("Las partes suman 9"))).post(
        _ruta(), json={"partes": [{"cantidad": 4}, {"cantidad": 5}]})

    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "Las partes suman 9"}


@pytest.mark.parametrize("error", ["aprobado", "bloqueada", "alta"])
def test_f065_r30_ruta_409(monkeypatch, error):
    from domain.models.alta_sigrid_models import AlbaranBloqueadoError
    from domain.models.review_models import AlbaranAprobadoError, LineaBloqueadaError

    excepcion = {
        "aprobado": AlbaranAprobadoError(DOC),
        "bloqueada": LineaBloqueadaError(DOC, 12),
        "alta": AlbaranBloqueadoError(DOC, "registrado", "AC26/7"),
    }[error]
    respuesta = _cliente(monkeypatch, _Servicio(error=excepcion)).post(
        _ruta(), json={"partes": [{"cantidad": 4}, {"cantidad": 6}]})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == excepcion.aviso


@pytest.mark.parametrize("cuerpo", [
    {"partes": [{"cantidad": 10}]},
    {"partes": [{"cantidad": 1}] * 21},
    {"partes": [{"cantidad": "seis"}, {"cantidad": 4}]},
    {},
], ids=["una", "veintiuna", "ilegible", "sin_partes"])
def test_f065_r30_ruta_422_del_cuerpo_sin_llamar_al_servicio(monkeypatch, cuerpo):
    servicio = _Servicio(None)

    respuesta = _cliente(monkeypatch, servicio).post(_ruta(), json=cuerpo)

    assert respuesta.status_code == 422
    assert servicio.llamadas == []


# =================================================================== #
# T24 · el detalle: partes bajo su original y aviso de familia (R35)
# =================================================================== #
def _mostrar(cantidades_partes, *, cantidad_blanca=10.0, ca=None, sin_ca=False):
    from domain.models.review_models import (
        LineValuationPayload,
        MergeLinePayload,
        ValuationPayload,
    )
    from infrastructure.database.review_repository import AlbaranReviewRepository

    blancas = [MergeLinePayload(id=701, line_index=1, concepto="PUERTA EI2-60", cantidad=8.0),
               MergeLinePayload(id=702, line_index=2, concepto="PUERTA EI2-90",
                                cantidad=cantidad_blanca)]
    q1, *resto = cantidades_partes
    original = LineValuationPayload(valuation_line_id=12, merge_line_id=702,
                                    cantidad_convertida=q1,
                                    cantidad_albaran=None if sin_ca else ca or q1)
    otra = LineValuationPayload(valuation_line_id=11, merge_line_id=701,
                                cantidad_convertida=8.0, cantidad_albaran=8.0)
    partes = [LineValuationPayload(valuation_line_id=40 + i, merge_line_id=None,
                                   line_kind="reparto", parent_merge_line_id=702,
                                   cantidad_convertida=q,
                                   cantidad_albaran=None if sin_ca else ca or q)
              for i, q in enumerate(resto)]
    portes = LineValuationPayload(valuation_line_id=14, merge_line_id=None,
                                  line_kind="synthetic_modifier", parent_merge_line_id=702,
                                  cantidad_convertida=1.0)
    valoracion = ValuationPayload(
        valuation_id="v", status="ok", lines_by_merge_line_id={701: otra, 702: original},
        # El orden del cargador: las de sv6 al final, cada grupo por id.
        synthetic_lines=[*partes, portes])
    return AlbaranReviewRepository._build_display_lines(merge_lines=blancas,
                                                       valuation=valoracion)


def test_f065_r35_pintado_parte_k_de_n_bajo_la_original():
    lineas = _mostrar([4.0, 3.0, 3.0])

    assert [(d.valuation_line_id, d.line_kind, d.parte) for d in lineas] == [
        (11, "from_albaran", None),
        (12, "from_albaran", "Parte 1 de 3"),
        (40, "reparto", "Parte 2 de 3"),
        (41, "reparto", "Parte 3 de 3"),
        (14, "synthetic_modifier", None),
    ]
    assert all(d.aviso_reparto is None for d in lineas)


def test_f065_r35_pintado_aviso_mientras_la_familia_no_suma_la_blanca():
    lineas = _mostrar([4.0, 3.0, 2.5])

    avisos = [(d.valuation_line_id, d.aviso_reparto) for d in lineas if d.aviso_reparto]
    assert avisos == [(12, "Las partes de la línea 2 suman 9,5; el albarán dice 10")]


def test_f065_r35_pintado_el_aviso_compara_en_la_unidad_del_albaran():
    """Con conversión (t → kg) la familia se compara por la cantidad del albarán."""
    lineas = _mostrar([500.0, 1500.0], cantidad_blanca=2.0, ca=1.0)

    assert [d.aviso_reparto for d in lineas if d.aviso_reparto] == []


def test_f065_r35_pintado_sin_cantidad_en_la_blanca_no_hay_aviso():
    lineas = _mostrar([4.0, 3.0], cantidad_blanca=None)

    assert [d.aviso_reparto for d in lineas if d.aviso_reparto] == []


def test_f065_r35_pintado_menos_de_media_milesima_cuadra():
    lineas = _mostrar([4.0, 5.996])

    assert [d.aviso_reparto for d in lineas if d.aviso_reparto] == []


def test_f065_r35_pintado_sin_cantidad_del_albaran_suma_la_convertida():
    lineas = _mostrar([4.0, 3.0, 2.0], sin_ca=True)

    assert [d.aviso_reparto for d in lineas if d.aviso_reparto] == [
        "Las partes de la línea 2 suman 9; el albarán dice 10"]


def test_f065_r35_pintado_la_blanca_sin_valorar_no_esta_valorada():
    from domain.models.review_models import MergeLinePayload, ValuationPayload
    from infrastructure.database.review_repository import AlbaranReviewRepository

    (sola,) = AlbaranReviewRepository._build_display_lines(
        merge_lines=[MergeLinePayload(id=709, line_index=1, concepto="X", cantidad=1.0)],
        valuation=ValuationPayload(valuation_id="v", status="ok"))
    valorada = _mostrar([7.0])[1]

    assert (sola.is_valued, sola.parte, valorada.is_valued) == (False, None, True)


def test_f065_r35_pintado_sin_partes_no_hay_parte_ni_aviso():
    lineas = _mostrar([7.0])

    assert [(d.parte, d.aviso_reparto) for d in lineas] == [(None, None)] * 3


def _html_partes(render_detalle, documento_detalle, linea_valorada, fila_detalle, **extra):
    filas_ = [
        fila_detalle(valuation_line_id=900, merge_line_id=500, parte="Parte 1 de 2",
                     aviso_reparto="Las partes de la línea 1 suman 5; el albarán dice 6",
                     cantidad=3.0),
        fila_detalle(valuation_line_id=901, merge_line_id=None, line_kind="reparto",
                     parent_merge_line_id=500, parte="Parte 2 de 2", cantidad=2.0),
        fila_detalle(valuation_line_id=902, merge_line_id=None,
                     line_kind="synthetic_modifier", parent_merge_line_id=500, cantidad=1.0),
        fila_detalle(valuation_line_id=903, merge_line_id=501, cantidad=4.0,
                     conciliacion={"codigo_partida": None, "estado_partida": "almacen"}),
        fila_detalle(valuation_line_id=904, merge_line_id=502, cantidad=4.0),
    ]
    valoradas = [
        linea_valorada(valuation_line_id=900, merge_line_id=500),
        linea_valorada(valuation_line_id=901, merge_line_id=None, line_kind="reparto"),
        linea_valorada(valuation_line_id=902, merge_line_id=None,
                       line_kind="synthetic_modifier"),
        linea_valorada(valuation_line_id=903, merge_line_id=501, review_reasons=[]),
        linea_valorada(valuation_line_id=904, merge_line_id=502,
                       review_reasons=["front_unidad_cambiada_revisa_cantidad"]),
    ]
    doc = documento_detalle(lineas_valoracion=valoradas, display=filas_)
    return render_detalle(doc.model_copy(update=extra) if extra else doc)


def _boton_dividir(html, vid):
    import re

    return re.search(
        r'<button[^>]*js-dividir"[^>]*data-valuation-line-id="' + str(vid) + r'"[^>]*>', html)


def test_f065_r35_pintado_la_plantilla_dice_parte_y_avisa(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = _html_partes(render_detalle, documento_detalle, linea_valorada, fila_detalle)

    assert "Parte 1 de 2" in html and "Parte 2 de 2" in html
    assert "Las partes de la línea 1 suman 5; el albarán dice 6" in html
    assert 'data-line-kind="reparto"' in html


def test_f065_r29_pintado_boton_dividir_solo_donde_se_puede(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = _html_partes(render_detalle, documento_detalle, linea_valorada, fila_detalle)

    boton = _boton_dividir(html, 900)
    assert boton and 'data-q="3.0"' in boton.group(0) and 'data-partida="01.01"' in boton.group(0)
    assert _boton_dividir(html, 901)  # una parte se puede volver a dividir
    assert not _boton_dividir(html, 902)  # sintética
    assert 'data-partida=""' in _boton_dividir(html, 903).group(0)  # almacén
    assert not _boton_dividir(html, 904)  # «revisa la cantidad»: antes, resolverla
    assert '<dialog id="dividir-dialog"' in html


def test_f065_r29_pintado_sin_dividir_en_un_aprobado(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = _html_partes(render_detalle, documento_detalle, linea_valorada, fila_detalle,
                        approved=True)

    assert "js-dividir" not in html
    assert "dividir-dialog" not in html


def test_f065_r29_pintado_sin_dividir_en_una_fila_bloqueada(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    doc = documento_detalle(
        lineas_valoracion=[linea_valorada(valuation_line_id=900, bloqueada=True)],
        display=[fila_detalle(valuation_line_id=900)])

    assert not _boton_dividir(render_detalle(doc), 900)


# =================================================================== #
# T24 · el front: la ventana de F6 y sin F7 (R29)
# =================================================================== #
_DIVIDIR = ["parseNumEs", "faltaPorRepartir", "repartoValido", "cuerpoDivision"]


@con_node
def test_f065_r29_js_falta_por_repartir(tmp_path):
    casos = _ejecutar(tmp_path, _DIVIDIR, """
        console.log(JSON.stringify([
            faltaPorRepartir(18, ["6", "7", ""]),
            faltaPorRepartir(18, ["6", "7", "5"]),
            faltaPorRepartir(18, ["6", "7", "6"]),
            faltaPorRepartir(1, ["0,1", "0,2"]),
            faltaPorRepartir(-10, ["-4", ""]),
        ]));
    """)

    assert casos == [5, 0, -1, 0.7, -6]


@con_node
def test_f065_r29_js_aceptar_solo_si_el_reparto_vale(tmp_path):
    casos = _ejecutar(tmp_path, _DIVIDIR, """
        const veinte = Array(20).fill("1"), veintiuna = Array(21).fill("1");
        console.log(JSON.stringify([
            repartoValido(18, ["6", "7", "5"]),
            repartoValido(18, ["6", "7", "4"]),
            repartoValido(18, ["6", "12", ""]),
            repartoValido(18, ["18", "0"]),
            repartoValido(18, ["20", "-2"]),
            repartoValido(18, ["18"]),
            repartoValido(20, veinte),
            repartoValido(21, veintiuna),
            repartoValido(10, ["4", "6,004"]),
            repartoValido(10, ["4", "6,005"]),
            repartoValido(10, ["4", "5,995"]),
            repartoValido(10, ["4", "6,00499994"]),
            repartoValido(-10, ["-4", "-6"]),
            repartoValido(0, ["1", "-1"]),
            repartoValido(null, ["1", "1"]),
        ]));
    """)

    assert casos == [True, False, False, False, False, False, True, False, True, False,
                     False, True, True, False, False]


@con_node
def test_f065_r29_js_cuerpo_de_la_division(tmp_path):
    cuerpo = _ejecutar(tmp_path, _DIVIDIR, """
        console.log(JSON.stringify(cuerpoDivision(["6", "7,5", "4.5"], ["01.02", " 01.03 ", ""])));
    """)

    assert cuerpo == {"partes": [
        {"cantidad": 6, "codigo_partida": "01.02"},
        {"cantidad": 7.5, "codigo_partida": "01.03"},
        {"cantidad": 4.5, "codigo_partida": None},
    ]}


def test_f065_r29_js_f6_abre_la_ventana_y_f7_ya_no_existe():
    js = _app_js()

    assert '"F6"' in js and "wireDividir" in js
    assert '"F7"' not in js and "duplicateRow" not in js
    assert "/dividir" in js
    assert 'dividir: "Dividir"' in js  # la etiqueta del historial de «Deshacer»


def test_f065_r29_js_el_combo_de_la_ventana_no_manda_a_almacen_al_elegir():
    """En la ventana, «Almacén» solo deja la partida vacía (no llama a /almacen)."""
    js = _app_js()

    assert "function attachPartidaCombo(input, opciones)" in js
    assert "alElegirAlmacen" in js


# =================================================================== #
# Pasada 2 de la review de la fase 3
# =================================================================== #
_NO_FINITOS = [float("nan"), float("inf"), float("-inf")]


@pytest.mark.parametrize("raro", _NO_FINITOS, ids=["nan", "inf", "menos_inf"])
def test_f065_cr1p2_dominio_no_reparte_numeros_no_finitos(raro):
    """CR1: ni en una parte, ni en Q, ni en el importe de la línea."""
    from domain.models.review_models import RepartoInvalido, repartir

    casos = [
        {"q": 10.0, "ca0": 10.0, "importe0": 100.0, "partes": [raro, 10.0]},
        {"q": 10.0, "ca0": 10.0, "importe0": 100.0, "partes": [10.0, raro]},
        {"q": raro, "ca0": 10.0, "importe0": 100.0, "partes": [4.0, 6.0]},
        {"q": 10.0, "ca0": 10.0, "importe0": raro, "partes": [4.0, 6.0]},
    ]
    for caso in casos:
        with pytest.raises(RepartoInvalido):
            repartir(precio=10.0, descuento=None, **caso)


def test_f065_cr1p2_dominio_los_mensajes_de_lo_no_finito():
    from domain.models.review_models import RepartoInvalido, repartir

    def mensaje(**caso):
        with pytest.raises(RepartoInvalido) as error:
            repartir(ca0=10.0, precio=10.0, descuento=None, **caso)
        return str(error.value)

    assert "parte 1" in mensaje(q=10.0, importe0=None, partes=[float("nan"), 10.0])
    assert "sin cantidad" in mensaje(q=float("inf"), importe0=None, partes=[4.0, 6.0])
    assert "importe" in mensaje(q=10.0, importe0=float("nan"), partes=[4.0, 6.0])


def test_f065_cr1p2_dominio_el_signo_reescrito_es_el_de_antes():
    """RM5, demostración ejecutable de la reescritura del signo (T26): para todo
    lo que llega a esa comprobación (Q y la parte finitas y distintas de 0, ±0
    incluido, porque ``== 0`` lo rechaza antes) ``copysign`` decide lo mismo que
    la versión original ``(cantidad > 0) != (q > 0)``; lo demás (``NaN``, ±inf,
    ±0) lo rechazan las guardas de antes, que es lo que la reescritura perdía."""
    import itertools
    import math

    from domain.models.review_models import RepartoInvalido, repartir

    valores = [-1e9, -18.0, -0.5, -1e-9, 1e-9, 0.5, 18.0, 1e9]
    for cantidad, q in itertools.product(valores, valores):
        original = (cantidad > 0) != (q > 0)
        assert (math.copysign(1.0, cantidad) != math.copysign(1.0, q)) == original
    for raro in (*_NO_FINITOS, 0.0, -0.0):
        for caso in ({"q": 10.0, "partes": [raro, 10.0]}, {"q": raro, "partes": [4.0, 6.0]}):
            with pytest.raises(RepartoInvalido):
                repartir(ca0=10.0, importe0=None, precio=1.0, descuento=None, **caso)


@pytest.mark.parametrize("raro", ["NaN", "Infinity", "-Infinity"])
def test_f065_cr1p2_los_tres_cuerpos_rechazan_no_finitos(raro):
    from domain.models.review_models import (
        ConciliacionEditBody,
        ConciliacionOverridePayload,
        DivisionBody,
        MergeDocumentUpdatePayload,
        TraerLineasBody,
    )
    from pydantic import ValidationError

    for modelo, cuerpo in (
        # CR1b (pasada 3): «Origen ✎» y casar una blanca.
        (ConciliacionOverridePayload,
         f'{{"mode": "nueva", "precio_unitario": {raro}}}'),
        # El PUT las ignora (R1), pero tampoco las admite.
        (MergeDocumentUpdatePayload,
         f'{{"valuation_line_updates": [{{"valuation_line_id": 1, "importe_calculado": {raro}}}]}}'),
        (DivisionBody, f'{{"partes": [{{"cantidad": {raro}}}, {{"cantidad": 1}}]}}'),
        (ConciliacionEditBody, f'{{"cantidad": {raro}}}'),
        (ConciliacionEditBody, f'{{"precio_unitario": {raro}}}'),
        (ConciliacionEditBody, f'{{"descuento": {raro}}}'),
        (TraerLineasBody, f'{{"lineas": [{{"contrato_line_id": 1, "cantidad": {raro}}}]}}'),
    ):
        with pytest.raises(ValidationError):
            modelo.model_validate_json(cuerpo)
    # Como texto (coma decimal de la ficha) tampoco.
    with pytest.raises(ValidationError):
        DivisionBody(partes=[{"cantidad": raro.lower()}, {"cantidad": 1}])


def test_f065_cr1p2_los_cuerpos_siguen_admitiendo_numeros_finitos():
    from domain.models.review_models import (
        ConciliacionEditBody,
        DivisionBody,
        TraerLineasBody,
    )

    assert DivisionBody.model_validate_json(
        '{"partes": [{"cantidad": 6.5}, {"cantidad": "11,5"}]}').partes[1].cantidad == 11.5
    assert ConciliacionEditBody.model_validate_json(
        '{"cantidad": 7, "precio_unitario": 115.5, "descuento": 10}').campos() == {
        "cantidad": 7.0, "precio_unitario": 115.5, "descuento": 10.0}
    assert TraerLineasBody.model_validate_json(
        '{"lineas": [{"contrato_line_id": 1, "cantidad": -2}]}').lineas[0].cantidad == -2.0


def test_f065_cr1p2_la_ruta_responde_422_a_nan_sin_llamar_al_servicio(monkeypatch):
    servicio = _Servicio(None)

    respuesta = _cliente(monkeypatch, servicio).post(
        _ruta(), content='{"partes": [{"cantidad": NaN}, {"cantidad": 10}]}',
        headers={"Content-Type": "application/json"})

    assert respuesta.status_code == 422
    assert servicio.llamadas == []
    (error,) = respuesta.json()["detail"]
    assert (error["type"], error["input"]) == ("finite_number", "nan")


class _Anota:
    """Servicio falso que anota qué método se llamó (no debería ninguno)."""

    def __init__(self):
        self.llamadas = []

    def initialize(self):
        return True

    def __getattr__(self, nombre):
        def _anota(*args, **kwargs):
            self.llamadas.append(nombre)
            return True
        return _anota


@pytest.mark.parametrize(("ruta", "cuerpo"), [
    (f"/api/documents/{DOC}/lines/12/conciliacion/campos", '{"cantidad": NaN}'),
    (f"/api/documents/{DOC}/lines/12/conciliacion/campos", '{"precio_unitario": Infinity}'),
    (f"/api/documents/{DOC}/lines/from-contrato",
     '{"lineas": [{"contrato_line_id": 503, "cantidad": -Infinity}]}'),
    (f"/api/documents/{DOC}/lines/12/conciliacion",
     '{"mode": "nueva", "precio_unitario": NaN}'),
    (f"/api/documents/{DOC}/lines/by-merge/703/conciliacion",
     '{"mode": "nueva", "precio_unitario": Infinity}'),
    (f"/api/documents/{DOC}",
     '{"valuation_line_updates": [{"valuation_line_id": 1, "cantidad_albaran": NaN}]}'),
], ids=["campos_nan", "campos_inf", "traer_menos_inf", "origen_nan", "casar_blanca_inf",
        "put_ignoradas_nan"])
def test_f065_cr1p2_editar_y_traer_responden_422_a_no_finitos(monkeypatch, ruta, cuerpo):
    servicio = _Anota()
    cliente = _cliente(monkeypatch, servicio)
    metodo = (
        cliente.put if ruta.endswith(DOC)
        else cliente.patch if ruta.endswith("conciliacion/campos")
        or (ruta.endswith("/conciliacion") and "by-merge" not in ruta)
        else cliente.post
    )

    respuesta = metodo(ruta, content=cuerpo, headers={"Content-Type": "application/json"})

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"][0]["type"] == "finite_number"
    assert servicio.llamadas == []


def test_f065_cr1p2_el_error_se_puede_devolver_en_json():
    import json as _json

    from interface_adapters.web.app import sin_no_finitos

    errores = [{"input": float("nan"), "loc": ("body", 0),
                "ctx": {"lista": [float("inf"), 1.5, (float("-inf"),)]}}, 2.5, "x"]

    limpio = sin_no_finitos(errores)

    assert limpio == [{"input": "nan", "loc": ["body", 0],
                       "ctx": {"lista": ["inf", 1.5, ["-inf"]]}}, 2.5, "x"]
    assert _json.dumps(limpio, allow_nan=False)


# --- (b) una parte a 0,00 € con importe en la original ----------------- #
@pytest.mark.parametrize(("importe0", "cantidades", "parte"), [
    (0.01, [1.0, 1.0, 1.0], "parte 1"),
    (0.02, [1.0, 1.0, 1.0], "parte 3"),
    (-0.01, [1.0, 2.0], "parte 1"),
], ids=["un_centimo", "la_ultima_a_cero", "abono"])
def test_f065_obs4_dominio_no_deja_una_parte_a_cero_euros(importe0, cantidades, parte):
    """sv9 no registra las líneas de importe 0 (F-053 R13): repartir no puede
    dejar una parte a 0,00 € si la original tenía importe."""
    from domain.models.review_models import RepartoInvalido, repartir

    q = sum(cantidades)
    with pytest.raises(RepartoInvalido) as error:
        repartir(q=q, ca0=q, importe0=importe0, precio=None, descuento=None,
                 partes=cantidades)

    assert "0,00 €" in str(error.value) and parte in str(error.value)


def test_f065_obs4_dominio_una_linea_a_cero_euros_se_reparte_a_cero():
    from domain.models.review_models import repartir

    partes = repartir(q=2.0, ca0=2.0, importe0=0.0, precio=0.0, descuento=None,
                      partes=[1.0, 1.0])

    assert [p.importe for p in partes] == [0.0, 0.0]


def test_f065_obs4_dominio_sin_importe_la_formula_puede_dar_cero():
    """Sin ``importe0`` no hay importe que perder: la fórmula canónica manda."""
    from domain.models.review_models import repartir

    partes = repartir(q=2.0, ca0=2.0, importe0=None, precio=0.0, descuento=None,
                      partes=[1.0, 1.0])

    assert [p.importe for p in partes] == [0.0, 0.0]


# --- (c) el texto de las partes ------------------------------------------ #
def test_f065_obs3_una_nueva_sin_texto_propio_toma_el_concepto_de_la_blanca():
    motor = construir()
    ejecutar(motor, "UPDATE contrato_lines_derived SET descripcion_linea = NULL WHERE id = 601")

    (p2,) = _dividir(motor, 13, (0.5, "03.01"), (0.5, "03.01")).partes

    assert fila(motor, p2)["descripcion_linea"] == "PORTES"


def test_f065_obs3_la_descripcion_fijada_de_la_original_manda():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'PUERTA HOJA DOBLE' "
             "WHERE id = 12")

    (p2,) = _dividir(motor, 12, (4, "01.02"), (6, "01.02")).partes

    assert fila(motor, p2)["descripcion_linea"] == "PUERTA HOJA DOBLE"


# --- (a) P5: una familia que no suma se aprueba ------------------------- #
def test_f065_p5_una_familia_que_no_suma_avisa_pero_se_aprueba():
    """R35/P5: el aviso de familia no bloquea (una recepción parcial es legítima)."""
    motor = construir()
    repo = repositorio(motor)
    (p2,) = _dividir(motor, 12, (4, "01.02"), (6, "01.02")).partes
    assert repo.update_line_conciliacion(
        document_id=DOC, valuation_line_id=p2, campos={"cantidad": 5.0})

    detalle = _mostrar([4.0, 5.0])
    assert [d.aviso_reparto for d in detalle if d.aviso_reparto] == [
        "Las partes de la línea 2 suman 9; el albarán dice 10"]
    assert repo.set_approved(document_id=DOC, approved=True, approved_by="ana") is True
