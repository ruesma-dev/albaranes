# tests/test_f019_r8_r15_precedencia.py
"""F-019 · R8-R15: manda el unitario leido; el importe solo se despeja.

Regla del humano (2026-08-18): si el albaran trae cantidad, precio
unitario y descuento, el importe es
``cantidad x precio x (1 - descuento/100)`` y **el unitario leido
MANDA**. Solo cuando faltan esos campos y hay importe final se despeja
el unitario de esa misma formula.

Lo que NO cambia y aqui se blinda con tests de regresion:

* el precio del contrato JAMAS pisa un valor leido del albaran (R12,
  la proteccion contra partidas alzadas: una cinta de 18,84 EUR
  valorada a 960.000 EUR por casar con una PA de 8.000 EUR);
* la cadena de fallback al contrato 1a/1b (R11);
* un valor leido igual a 0 se trata como AUSENTE (R13);
* las derivaciones imposibles no inventan numeros (R14, R15).

``PriceReconciler`` es una clase pura de la capa application: no toca
red, ni BBDD, ni LLM.
"""
from __future__ import annotations

import pytest

from application.services.price_reconciler import PriceReconciliation


def reconciliar(reconciliador, **kwargs) -> PriceReconciliation:
    """``reconcile`` con todos los argumentos ausentes a None/False."""
    argumentos = {
        "precio_1a": None,
        "precio_1b": None,
        "precio_albaran_declarado": None,
        "cantidad_albaran": None,
        "importe_albaran": None,
        "line_already_valued": False,
        "descuento_pct": None,
    }
    argumentos.update(kwargs)
    return reconciliador.reconcile(**argumentos)


# --------------------------------------------------------------------- #
# R8 — el unitario declarado manda, haya o no importe del que derivar
# --------------------------------------------------------------------- #
def test_f019_r8_unitario_declarado_manda_habiendo_importe(reconciliador):
    """Feymaco linea 1: declarado 0,543 con importe 35,19 derivable."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=4000.0,
        precio_albaran_declarado=0.543,
        cantidad_albaran=108.0,
        importe_albaran=35.19,
        descuento_pct=40.0,
    )

    assert resultado.final_price == pytest.approx(0.543)
    assert resultado.source == "albaran_declared"
    assert "albaran_unitario_manda_derivado_coincide" in resultado.reasons


def test_f019_r8_unitario_declarado_manda_sin_importe(reconciliador):
    """Sin importe leido no hay nada que contrastar: manda igual."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=4000.0,
        precio_albaran_declarado=0.543,
        cantidad_albaran=108.0,
        importe_albaran=None,
        descuento_pct=40.0,
    )

    assert resultado.final_price == pytest.approx(0.543)
    assert resultado.source == "albaran_declared"
    assert resultado.agreement == "neither"
    assert "albaran_unitario_declarado_manda" in resultado.reasons


def test_f019_r8_unitario_declarado_manda_sin_cantidad(reconciliador):
    """Con importe pero sin cantidad el importe no es derivable: manda
    el declarado y queda el motivo de auditoria."""
    resultado = reconciliar(
        reconciliador,
        precio_albaran_declarado=0.543,
        cantidad_albaran=None,
        importe_albaran=35.19,
    )

    assert resultado.final_price == pytest.approx(0.543)
    assert resultado.source == "albaran_declared"
    assert "importe_leido_sin_cantidad_no_derivable" in resultado.reasons
    assert "albaran_unitario_declarado_manda" in resultado.reasons


def test_f019_r8_line_already_valued_se_sigue_registrando(reconciliador):
    """La marca de linea ya valorada sigue dejando su rastro."""
    resultado = reconciliar(
        reconciliador,
        precio_albaran_declarado=0.543,
        cantidad_albaran=108.0,
        importe_albaran=35.19,
        descuento_pct=40.0,
        line_already_valued=True,
    )

    assert resultado.reasons[0] == "line_already_valued"
    assert resultado.final_price == pytest.approx(0.543)


# --------------------------------------------------------------------- #
# R9 — sin unitario declarado, se despeja del importe
# --------------------------------------------------------------------- #
def test_f019_r9_sin_declarado_se_despeja_el_unitario_del_importe(
    reconciliador,
):
    """35,19 / (108 x 0,6) = 0,543055... (unitario BRUTO, no neto)."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=4000.0,
        precio_albaran_declarado=None,
        cantidad_albaran=108.0,
        importe_albaran=35.19,
        descuento_pct=40.0,
    )

    assert resultado.final_price == pytest.approx(35.19 / (108 * 0.6))
    assert resultado.source == "albaran_calculated"
    assert resultado.agreement == "neither"
    assert "albaran_importe_manda_derivado" in resultado.reasons


def test_f019_r9_sin_declarado_y_sin_descuento_el_despeje_es_directo(
    reconciliador,
):
    """Sin descuento el divisor es la cantidad a secas."""
    resultado = reconciliar(
        reconciliador,
        precio_albaran_declarado=None,
        cantidad_albaran=10.0,
        importe_albaran=25.0,
        descuento_pct=None,
    )

    assert resultado.final_price == pytest.approx(2.5)
    assert resultado.source == "albaran_calculated"


# --------------------------------------------------------------------- #
# R10 — discrepan: gana el declarado, agreement mismatch, va a revision
# --------------------------------------------------------------------- #
def test_f019_r10_discrepancia_gana_el_declarado_con_mismatch(
    reconciliador,
):
    """El caso del 18-08 con el importe todavia inflado: el unitario
    leido (0,543) manda sobre el derivado (58,65), y el desacuerdo se
    marca para revision en vez de persistirse en silencio."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=4000.0,
        precio_albaran_declarado=0.543,
        cantidad_albaran=108.0,
        importe_albaran=3800.52,
        descuento_pct=40.0,
    )

    assert resultado.final_price == pytest.approx(0.543)
    assert resultado.source == "albaran_declared"
    assert resultado.agreement == "mismatch"
    assert (
        "unitario_declarado_vs_derivado_mismatch:0.543!=58.65"
        in resultado.reasons
    )


def test_f019_r10_el_mismatch_es_lo_que_lleva_la_linea_a_revision(
    reconciliador,
):
    """``ValuationBuilder._build_line`` marca ``review_required`` con
    ``reconciliation.agreement == "mismatch"``: esa es la via elegida
    (decision D3) para que el desacuerdo llegue a revision sin tocar el
    builder. El test fija el contrato del que depende esa via."""
    resultado = reconciliar(
        reconciliador,
        precio_albaran_declarado=0.543,
        cantidad_albaran=108.0,
        importe_albaran=3800.52,
        descuento_pct=40.0,
    )

    review_required = resultado.agreement == "mismatch"
    assert review_required is True


def test_f019_r10_dentro_de_tolerancia_no_hay_mismatch(reconciliador):
    """Justo dentro del 2 %: coinciden, no se marca revision."""
    # cantidad 10, sin descuento: importe 10,15 -> derivado 1,015
    # frente a un declarado de 1,00 => 1,48 % de diferencia.
    resultado = reconciliar(
        reconciliador,
        precio_albaran_declarado=1.0,
        cantidad_albaran=10.0,
        importe_albaran=10.15,
    )

    assert resultado.final_price == pytest.approx(1.0)
    assert resultado.agreement == "neither"
    assert "albaran_unitario_manda_derivado_coincide" in resultado.reasons


def test_f019_r10_justo_fuera_de_tolerancia_hay_mismatch(reconciliador):
    """Justo fuera del 2 %: 10,30 -> derivado 1,03 => 2,91 %."""
    resultado = reconciliar(
        reconciliador,
        precio_albaran_declarado=1.0,
        cantidad_albaran=10.0,
        importe_albaran=10.30,
    )

    assert resultado.final_price == pytest.approx(1.0)
    assert resultado.agreement == "mismatch"


# --------------------------------------------------------------------- #
# R11 — sin valores leidos, la cadena de contrato queda INTACTA
# --------------------------------------------------------------------- #
def test_f019_r11_contrato_1a_y_1b_coinciden_se_promedian(reconciliador):
    resultado = reconciliar(reconciliador, precio_1a=10.0, precio_1b=10.1)

    assert resultado.final_price == pytest.approx(10.05)
    assert resultado.source == "both_agreed"
    assert resultado.agreement == "match"


def test_f019_r11_contrato_1a_y_1b_discrepan_prevalece_1a(reconciliador):
    resultado = reconciliar(reconciliador, precio_1a=10.0, precio_1b=50.0)

    assert resultado.final_price == pytest.approx(10.0)
    assert resultado.source == "contract_line_match"
    assert resultado.agreement == "mismatch"
    assert "price_1a_vs_1b_mismatch:10.0!=50.0" in resultado.reasons


def test_f019_r11_contrato_solo_1a(reconciliador):
    resultado = reconciliar(reconciliador, precio_1a=10.0)

    assert resultado.final_price == pytest.approx(10.0)
    assert resultado.source == "contract_line_match"
    assert resultado.agreement == "only_1a"
    assert "only_1a_available" in resultado.reasons


def test_f019_r11_contrato_solo_1b(reconciliador):
    resultado = reconciliar(reconciliador, precio_1b=7.0)

    assert resultado.final_price == pytest.approx(7.0)
    assert resultado.source == "pdf_inference"
    assert resultado.agreement == "only_1b"
    assert "only_1b_available" in resultado.reasons


def test_f019_r11_sin_nada_no_hay_precio(reconciliador):
    resultado = reconciliar(reconciliador)

    assert resultado.final_price is None
    assert resultado.source == "none"
    assert resultado.agreement == "neither"
    assert "no_price_available" in resultado.reasons


# --------------------------------------------------------------------- #
# R12 — REGRESION: el contrato no pisa lo leido (partidas alzadas)
# --------------------------------------------------------------------- #
def test_f019_r12_partida_alzada_no_pisa_el_importe_leido(reconciliador):
    """La cinta de senalizacion: 18,84 EUR leidos frente a una PA de
    8.000 EUR del contrato. Invertir la precedencia INTERNA del albaran
    (importe vs unitario) no puede reabrir esta puerta: ambos valores
    son del albaran, y el contrato sigue siendo solo fallback."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=8000.0,
        cantidad_albaran=1.0,
        importe_albaran=18.84,
    )

    assert resultado.final_price == pytest.approx(18.84)
    assert resultado.final_price != pytest.approx(8000.0)
    assert resultado.source == "albaran_calculated"


def test_f019_r12_partida_alzada_no_pisa_el_unitario_declarado(
    reconciliador,
):
    """Misma proteccion por la rama nueva (bloque 1): con unitario
    declarado, el precio del contrato tampoco entra."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=8000.0,
        precio_1b=8000.0,
        precio_albaran_declarado=18.84,
        cantidad_albaran=1.0,
        importe_albaran=18.84,
    )

    assert resultado.final_price == pytest.approx(18.84)
    assert resultado.source == "albaran_declared"


def test_f019_r12_los_960000_euros_no_vuelven(
    reconciliador, calculador_importe,
):
    """El numero exacto del incidente: 120 x 8.000 = 960.000 EUR. Con
    el albaran leido (18,84 EUR en 120 unidades) el importe final es
    18,84 EUR."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=8000.0,
        cantidad_albaran=120.0,
        importe_albaran=18.84,
    )
    importe = calculador_importe.compute(
        cantidad_convertida=120.0,
        cantidad_albaran=120.0,
        precio_unitario_final=resultado.final_price,
        importe_albaran_declarado=18.84,
    )

    assert resultado.final_price == pytest.approx(18.84 / 120)
    assert importe.importe_calculado == pytest.approx(18.84)
    assert importe.importe_calculado != pytest.approx(960000.0)


# --------------------------------------------------------------------- #
# R13 — REGRESION: un 0 leido es una celda vacia, no un precio de 0 EUR
# --------------------------------------------------------------------- #
def test_f019_r13_importe_leido_cero_se_ignora(reconciliador):
    resultado = reconciliar(
        reconciliador,
        precio_1a=10.0,
        cantidad_albaran=5.0,
        importe_albaran=0.0,
    )

    assert "importe_albaran_cero_ignorado" in resultado.reasons
    assert resultado.final_price == pytest.approx(10.0)
    assert resultado.source == "contract_line_match"


def test_f019_r13_unitario_declarado_cero_se_ignora(reconciliador):
    resultado = reconciliar(
        reconciliador,
        precio_1a=10.0,
        precio_albaran_declarado=0.0,
        cantidad_albaran=5.0,
    )

    assert "precio_declarado_cero_ignorado" in resultado.reasons
    assert resultado.final_price == pytest.approx(10.0)


def test_f019_r13_declarado_cero_con_importe_cae_al_despeje(reconciliador):
    """El 0 declarado no bloquea la segunda prioridad."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=10.0,
        precio_albaran_declarado=0.0,
        cantidad_albaran=5.0,
        importe_albaran=12.5,
    )

    assert "precio_declarado_cero_ignorado" in resultado.reasons
    assert resultado.final_price == pytest.approx(2.5)
    assert resultado.source == "albaran_calculated"


# --------------------------------------------------------------------- #
# R14 — derivaciones imposibles: ni excepcion, ni numero inventado
# --------------------------------------------------------------------- #
def test_f019_r14_descuento_100_no_es_derivable(reconciliador):
    """Dividir por (1 - 1) es imposible: se deja el motivo y se sigue."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=10.0,
        cantidad_albaran=5.0,
        importe_albaran=12.5,
        descuento_pct=100.0,
    )

    assert "descuento_100_no_derivable" in resultado.reasons
    assert resultado.final_price == pytest.approx(10.0)
    assert resultado.source == "contract_line_match"


def test_f019_r14_cantidad_cero_no_es_derivable(reconciliador):
    resultado = reconciliar(
        reconciliador,
        precio_1a=10.0,
        cantidad_albaran=0.0,
        importe_albaran=12.5,
    )

    assert "importe_leido_sin_cantidad_no_derivable" in resultado.reasons
    assert resultado.final_price == pytest.approx(10.0)


def test_f019_r14_cantidad_none_no_es_derivable(reconciliador):
    resultado = reconciliar(
        reconciliador,
        precio_1a=10.0,
        cantidad_albaran=None,
        importe_albaran=12.5,
    )

    assert "importe_leido_sin_cantidad_no_derivable" in resultado.reasons
    assert resultado.final_price == pytest.approx(10.0)


def test_f019_r14_descuento_100_con_declarado_manda_el_declarado(
    reconciliador,
):
    """La derivacion imposible no impide que el unitario leido mande."""
    resultado = reconciliar(
        reconciliador,
        precio_1a=10.0,
        precio_albaran_declarado=3.0,
        cantidad_albaran=5.0,
        importe_albaran=12.5,
        descuento_pct=100.0,
    )

    assert "descuento_100_no_derivable" in resultado.reasons
    assert resultado.final_price == pytest.approx(3.0)
    assert resultado.source == "albaran_declared"


# --------------------------------------------------------------------- #
# R15 — descuento fuera de [0,100]: no se aplica, y consta
# --------------------------------------------------------------------- #
def test_f019_r15_descuento_fuera_de_rango_no_se_usa_al_despejar(
    reconciliador,
):
    """El despeje ignora el descuento invalido: divide por la cantidad
    a secas en vez de fabricar un factor absurdo."""
    resultado = reconciliar(
        reconciliador,
        precio_albaran_declarado=None,
        cantidad_albaran=10.0,
        importe_albaran=100.0,
        descuento_pct=150.0,
    )

    assert resultado.final_price == pytest.approx(10.0)
    assert resultado.source == "albaran_calculated"


def test_f019_r15_descuento_negativo_no_se_usa_al_despejar(reconciliador):
    resultado = reconciliar(
        reconciliador,
        cantidad_albaran=10.0,
        importe_albaran=100.0,
        descuento_pct=-5.0,
    )

    assert resultado.final_price == pytest.approx(10.0)


def test_f019_r15_el_importe_deja_el_motivo_de_descuento_invalido(
    calculador_importe,
):
    """El motivo ``descuento_fuera_de_rango_ignorado`` vive en el
    ``ImporteCalculator``: se revalida porque la formula canonica de
    R4/R5 usa ese mismo descuento."""
    resultado = calculador_importe.compute(
        cantidad_convertida=10.0,
        precio_unitario_final=10.0,
        importe_albaran_declarado=None,
        descuento_pct=150.0,
    )

    assert "descuento_fuera_de_rango_ignorado:150.0" in resultado.reasons
    assert resultado.importe_calculado == pytest.approx(100.0)
    assert resultado.descuento_aplicado is None
