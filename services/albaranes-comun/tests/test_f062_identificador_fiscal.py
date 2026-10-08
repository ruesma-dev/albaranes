# tests/test_f062_identificador_fiscal.py
"""F-062 · R1, R2 — identificador fiscal español en ``ruesma_comun``.

Los tres CIF que la IA leyó mal en los albaranes medidos (19407, 19394 y
1790636816) tienen el carácter de control INVÁLIDO; los dos CIF reales de
Sigrid, válido. Es la señal que sv3 cuenta en la nota de la red de
proveedor (F-062 R5, R7, R11) y la que decide qué candidatos de la obra
son elegibles para aplicarse (R3).
"""
from __future__ import annotations

import pytest

from ruesma_comun.proveedores import (
    identificador_fiscal_valido,
    normalizar_cif,
)


# ------------------------------------------------------------------ #
# R1 · normalizar_cif
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("B66056201", "B66056201"),
        (" b66056201 ", "B66056201"),
        ("B-66.056.201", "B66056201"),
        ("ESB66056201", "B66056201"),
        ("es-b66056201", "B66056201"),
        # 11 caracteres SIN «ES» delante: no se recorta nada.
        ("FR123456789", "FR123456789"),
        # «ES» delante pero no quedan 11: no es el prefijo de país.
        ("ES1234567", "ES1234567"),
        ("ESB660562011", "ESB660562011"),
        # Un CIF que empieza por la letra E no pierde su letra.
        ("E12345674", "E12345674"),
        ("12345678z", "12345678Z"),
        ("", None),
        ("   ", None),
        ("-./", None),
        (None, None),
    ],
)
def test_f062_r1_normalizar_cif(valor, esperado):
    assert normalizar_cif(valor) == esperado


def test_f062_r1_normalizar_cif_descarta_lo_que_no_es_ascii():
    """Solo ``[A-Z0-9]``: una letra con tilde o un dígito de otro alfabeto
    no es parte de un CIF."""
    assert normalizar_cif("B6605620١") == "B6605620"
    assert normalizar_cif("Ñ12345678") == "12345678"


# ------------------------------------------------------------------ #
# R2 · los cinco CIF reales de la medición del humano
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "cif",
    ["B66056201", "B18487421"],
    ids=["hormigones-mat-real", "aridos-anfersa-real"],
)
def test_f062_r2_los_cif_reales_de_sigrid_son_validos(cif):
    assert identificador_fiscal_valido(cif) is True


@pytest.mark.parametrize(
    "cif",
    ["B86056201", "B86056095", "B18437421"],
    ids=["19407-tocaba-7", "19394-tocaba-0", "1790636816-tocaba-6"],
)
def test_f062_r2_los_cif_mal_leidos_tienen_el_control_invalido(cif):
    assert identificador_fiscal_valido(cif) is False


@pytest.mark.parametrize(
    ("cif", "control_bueno"),
    [("B86056201", "7"), ("B86056095", "0"), ("B18437421", "6")],
)
def test_f062_r2_con_el_control_que_tocaba_serian_validos(cif, control_bueno):
    """El fallo de los mal leídos está SOLO en el control: con el dígito
    que les tocaba, la misma cadena pasa."""
    assert identificador_fiscal_valido(cif[:-1] + control_bueno) is True


# ------------------------------------------------------------------ #
# R2 · CIF: tipo de control según la letra
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("cif", "esperado"),
    [
        # A B E H: SOLO dígito de control.
        ("A28123453", True),
        ("A2812345C", False),
        ("B1234567D", False),
        ("E12345674", True),
        ("H12345674", True),
        ("H1234567D", False),
        # N P Q R S W: SOLO letra de control (JABCDEFGHI).
        ("Q2826000H", True),
        ("Q28260008", False),
        ("P1234567D", True),
        ("P12345674", False),
        ("N1234567D", True),
        ("R1234567D", True),
        ("S1234567D", True),
        ("W1234567D", True),
        ("W1234567E", False),
        # El resto (C D F G J U V): cualquiera de los dos.
        ("J12345674", True),
        ("J1234567D", True),
        ("J12345675", False),
        ("J1234567E", False),
        ("C12345674", True),
        ("D1234567D", True),
        ("F12345674", True),
        ("G1234567D", True),
        ("U12345674", True),
        ("V1234567D", True),
        # Control 0 ⇒ dígito 0 o letra J.
        ("B12345690", True),
        ("G1234569J", True),
        ("B1234569J", False),
    ],
)
def test_f062_r2_cif_control_por_tipo_de_letra(cif, esperado):
    assert identificador_fiscal_valido(cif) is esperado


@pytest.mark.parametrize(
    "cif",
    [
        "I12345674",  # letra que no es de CIF
        "O12345674",
        "T12345674",
        "B1234567",  # corto
        "B123456745",  # largo
        "B12A45674",  # letra en el cuerpo
        "B1234567-",
    ],
)
def test_f062_r2_formatos_de_cif_que_no_son_validos(cif):
    assert identificador_fiscal_valido(cif) is False


# ------------------------------------------------------------------ #
# R2 · NIF, NIE y NIF especial
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("12345678Z", True),
        ("12345678A", False),
        ("00000000T", True),
        ("00000001R", True),
        ("00000022E", True),
        ("00000023T", True),
        ("1234567Z", False),
        ("123456789", False),
        # NIE: X/Y/Z valen 0/1/2 y se aplica la regla del NIF.
        ("X1234567L", True),
        ("X1234567T", False),
        ("Y1234567X", True),
        ("Y1234567L", False),
        ("Z1234567R", True),
        ("Z1234567L", False),
        ("X12345678L", False),
        # NIF especial K L M: solo formato.
        ("K1234567L", True),
        ("L0000000A", True),
        ("M7654321Z", True),
        ("K123456L", False),
        ("M12345678", False),
    ],
)
def test_f062_r2_nif_nie_y_nif_especial(valor, esperado):
    assert identificador_fiscal_valido(valor) is esperado


# ------------------------------------------------------------------ #
# R2 · normaliza dentro; extranjero y vacío no son válidos
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "valor", [" b-66.056.201 ", "ESB66056201", "es 12345678-z"],
)
def test_f062_r2_valida_sobre_el_valor_normalizado(valor):
    assert identificador_fiscal_valido(valor) is True


@pytest.mark.parametrize(
    "valor",
    [None, "", "   ", "FR12345678901", "PT123456789", "DE123456789", "ESB86056201"],
)
def test_f062_r2_extranjero_vacio_o_invalido_no_es_valido(valor):
    assert identificador_fiscal_valido(valor) is False
