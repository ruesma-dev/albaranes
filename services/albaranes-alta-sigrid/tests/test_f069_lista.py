# tests/test_f069_lista.py
"""F-069 · T1 · la Lista de excepciones y el Correo de Ruesma (R1, R2).

Puro: ni red ni BBDD.

- ``correo_ruesma``: quien aprobó recortado y en minúsculas si es un correo
  ``@ruesma.es`` con una sola @ y parte local de 1 a 24; si no, ``None``.
- ``leer_equivalencias``: la Lista (``ALTA_SIGRID_EQUIVALENCIAS_USUARIO``);
  vacía es ``{}`` (R1) y cada caso de R2 es un ``ValueError`` con el motivo y
  la clave.
- ``entrada_de``: la Entrada por Login, sin distinguir mayúsculas.
- ``candidato_usuario`` (F-053 R47) no cambia de resultado: lo vigilan sus
  tests de ``test_f053_r47_candidato.py``.
Los Logins y los ``ide`` de los ejemplos son ficticios.
"""
from __future__ import annotations

import json

import pytest

from domain.services.usuario_sigrid import (
    MAX_LOGIN,
    Equivalencia,
    candidato_usuario,
    correo_ruesma,
    entrada_de,
    leer_equivalencias,
)


# ------------------------------------------------------------------ #
# Correo de Ruesma
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("approved_by, esperado", [
    ("login1@ruesma.es", "login1@ruesma.es"),
    ("  Login1@Ruesma.ES  ", "login1@ruesma.es"),
    ("\tLOGIN2@RUESMA.es\n", "login2@ruesma.es"),
    ("a" * 24 + "@ruesma.es", "a" * 24 + "@ruesma.es"),
    ("a@ruesma.es", "a@ruesma.es"),
])
def test_f069_r1_correo_ruesma_recortado_y_en_minusculas(approved_by, esperado):
    assert correo_ruesma(approved_by) == esperado


@pytest.mark.parametrize("approved_by", [
    None, "", "   ", "reviewer", "login1@gmail.com", "login1@ruesma.es.otro.com",
    "login1@sub.ruesma.es", "x_gmail.com#EXT#@ruesmaxx.onmicrosoft.com", "@ruesma.es",
    "a" * 25 + "@ruesma.es", "a@b@ruesma.es", "login1 ruesma.es",
])
def test_f069_r1_correo_ruesma_lo_demas_es_none(approved_by):
    assert correo_ruesma(approved_by) is None


@pytest.mark.parametrize("approved_by", [
    "login1@ruesma.es", "  Login1@Ruesma.ES  ", "reviewer", None, "a" * 25 + "@ruesma.es",
])
def test_f069_r1_candidato_usuario_coherente_con_correo_ruesma(approved_by):
    """Hay candidato si y solo si hay Correo de Ruesma, y es su parte local tal
    cual se escribió (F-053 R47)."""
    correo = correo_ruesma(approved_by)
    candidato = candidato_usuario(approved_by)
    assert (candidato is None) is (correo is None)
    if candidato is not None:
        assert candidato.lower() == correo.split("@")[0]
        assert candidato in approved_by


# ------------------------------------------------------------------ #
# R1 · Lista vacía
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("texto", [None, "", "   ", "\n\t", "{}", " { } "])
def test_f069_r1_lista_ausente_o_vacia_es_la_lista_vacia(texto):
    assert leer_equivalencias(texto) == {}


def test_f069_r1_lista_valida_se_lee_con_claves_en_minusculas():
    lista = leer_equivalencias(
        '{"Login1": {"usu": "  login1b "}, "login2": {"empide": 1234567},'
        ' "login3": {"usu": "l3", "empide": 7}}'
    )
    assert lista == {
        "login1": Equivalencia(usu="login1b", empide=None),
        "login2": Equivalencia(usu=None, empide=1234567),
        "login3": Equivalencia(usu="l3", empide=7),
    }


def test_f069_r1_equivalencia_es_inmutable():
    entrada = Equivalencia(usu="a", empide=None)
    with pytest.raises(AttributeError):
        entrada.usu = "b"  # type: ignore[misc]


def test_f069_r1_topes_exactos_admitidos():
    clave = "k" * MAX_LOGIN
    lista = leer_equivalencias(f'{{"{clave}": {{"usu": "{"u" * MAX_LOGIN}", "empide": 1}}}}')
    assert lista[clave] == Equivalencia(usu="u" * MAX_LOGIN, empide=1)


# ------------------------------------------------------------------ #
# R2 · cada caso que impide arrancar
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("texto, motivo", [
    ("{roto", "no es JSON"),
    ("[]", "objeto JSON"),
    ('"login1"', "objeto JSON"),
    ("3", "objeto JSON"),
    ("null", "objeto JSON"),
])
def test_f069_r2_lista_que_no_es_un_objeto_no_arranca(texto, motivo):
    with pytest.raises(ValueError, match=motivo) as error:
        leer_equivalencias(texto)
    assert "ALTA_SIGRID_EQUIVALENCIAS_USUARIO" in str(error.value)


@pytest.mark.parametrize("clave, motivo", [
    ("", "vacía"),
    ("login1@ruesma.es", "@"),
    ("login 1", "espacios"),
    (" login1", "espacios"),
    ("login1\t", "espacios"),
    ("k" * (MAX_LOGIN + 1), "24"),
])
def test_f069_r2_clave_no_valida_no_arranca(clave, motivo):
    with pytest.raises(ValueError, match=motivo) as error:
        leer_equivalencias(json.dumps({clave: {"usu": "u"}}))
    assert repr(clave) in str(error.value)


@pytest.mark.parametrize("texto, clave", [
    ('{"login1": {"usu": "a"}, "login1": {"usu": "b"}}', "login1"),
    ('{"login1": {"usu": "a"}, "LOGIN1": {"usu": "b"}}', "LOGIN1"),
    ('{"Login1": {"empide": 1}, "lOgIn1": {"usu": "b"}}', "lOgIn1"),
])
def test_f069_r2_claves_repetidas_no_arrancan(texto, clave):
    with pytest.raises(ValueError, match="repetida") as error:
        leer_equivalencias(texto)
    assert repr(clave) in str(error.value)


@pytest.mark.parametrize("valor, motivo", [
    ('"login1b"', "objeto"),
    ("[]", "objeto"),
    ("null", "objeto"),
    ("7", "objeto"),
    ("{}", "al menos"),
    ('{"usu": "a", "otro": 1}', "otro"),
    ('{"empide": 1, "nombre": "x"}', "nombre"),
    ('{"usu": "a", "usu": "b"}', "repetida"),
])
def test_f069_r2_valor_no_valido_no_arranca(valor, motivo):
    with pytest.raises(ValueError, match=motivo) as error:
        leer_equivalencias(f'{{"login1": {valor}}}')
    assert "'login1'" in str(error.value)


@pytest.mark.parametrize("usu", ['""', '"   "', '"' + "u" * (MAX_LOGIN + 1) + '"', "null",
                                 "7", "true", '["a"]', '{"a": 1}'])
def test_f069_r2_usu_no_valido_no_arranca(usu):
    with pytest.raises(ValueError, match="usu") as error:
        leer_equivalencias(f'{{"login1": {{"usu": {usu}}}}}')
    assert "'login1'" in str(error.value)


def test_f069_r2_usu_recortado_de_24_se_admite():
    lista = leer_equivalencias('{"login1": {"usu": "  ' + "u" * MAX_LOGIN + '  "}}')
    assert lista["login1"].usu == "u" * MAX_LOGIN


@pytest.mark.parametrize("empide", ["true", "false", '"1234567"', "1234567.0", "1.5", "0",
                                    "-3", "null", "[1]", '{"a": 1}'])
def test_f069_r2_empide_no_valido_no_arranca(empide):
    with pytest.raises(ValueError, match="empide") as error:
        leer_equivalencias(f'{{"login1": {{"empide": {empide}}}}}')
    assert "'login1'" in str(error.value)


def test_f069_r2_empide_uno_es_el_minimo():
    assert leer_equivalencias('{"login1": {"empide": 1}}')["login1"].empide == 1


def test_f069_r2_ni_un_texto_que_no_sea_str_pasa():
    with pytest.raises(ValueError, match="ALTA_SIGRID_EQUIVALENCIAS_USUARIO"):
        leer_equivalencias(3)  # type: ignore[arg-type]


# ------------------------------------------------------------------ #
# Entrada por Login
# ------------------------------------------------------------------ #
LISTA = {
    "login1": Equivalencia(usu="login1b", empide=None),
    "login2": Equivalencia(usu=None, empide=1234567),
}


@pytest.mark.parametrize("approved_by, esperada", [
    ("login1@ruesma.es", LISTA["login1"]),
    ("  LOGIN1@Ruesma.es ", LISTA["login1"]),
    ("Login2@ruesma.es", LISTA["login2"]),
    ("login3@ruesma.es", None),
    ("login1@gmail.com", None),       # sin Correo de Ruesma no hay Entrada
    ("login1", None),
    (None, None),
])
def test_f069_r1_entrada_por_login_sin_distinguir_mayusculas(approved_by, esperada):
    assert entrada_de(approved_by, LISTA) == esperada


def test_f069_r1_entrada_con_lista_vacia_es_none():
    assert entrada_de("login1@ruesma.es", {}) is None
