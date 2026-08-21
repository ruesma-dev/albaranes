# tests/test_f040_r18_r26_huecos.py
"""F-040 · R18–R26: los ocho huecos que nadie estaba comprobando.

Cada uno de estos requisitos nació de mirar dentro de la maquinaria de
mutación y encontrar una rama sin test detrás. No comparten tema: comparten
que estaban descubiertas, y que una rama descubierta de la herramienta que
mide la calidad de los tests es exactamente el peor sitio donde tenerla.
"""

from __future__ import annotations

import pytest

from harness.mutacion import _analizar_argumentos
from harness.rigor import timeout_mutacion


# --- R22: el timeout configurado, validado de verdad ------------------------


def test_f040_r22_un_timeout_entero_positivo_se_acepta() -> None:
    assert timeout_mutacion({"mutacion": {"timeout_por_mutante_s": 120}}) == 120


def test_f040_r22_un_booleano_no_es_un_timeout() -> None:
    """El defecto de campo: `isinstance(True, int)` es cierto y `True > 0`.

    Con `"timeout_por_mutante_s": true` la campaña concedía **1 segundo** por
    mutante y salía entera en «timeout», sin que nada avisara de que el valor
    configurado no era un número.
    """
    with pytest.raises(ValueError) as error:
        timeout_mutacion({"mutacion": {"timeout_por_mutante_s": True}})

    assert "True" in str(error.value), (
        "el mensaje tiene que enseñar el valor que se rechaza"
    )
    assert "no vale" in str(error.value)


@pytest.mark.parametrize("valor", [0, -1, -600, 1.5, "120", [], {}])
def test_f040_r22_un_valor_que_no_es_entero_positivo_se_rechaza(valor: object) -> None:
    with pytest.raises(ValueError) as error:
        timeout_mutacion({"mutacion": {"timeout_por_mutante_s": valor}})

    assert "no vale" in str(error.value)


@pytest.mark.parametrize(
    "rigor",
    [
        {},
        {"mutacion": {}},
        # `null` explícito cuenta como ausencia, igual que en `workers` y
        # `max_mutantes`: declarar la clave sin valor es no declararla.
        {"mutacion": {"timeout_por_mutante_s": None}},
    ],
)
def test_f040_r22_la_clave_ausente_dice_que_FALTA_y_no_que_no_vale(
    rigor: dict,
) -> None:
    """«Falta la clave» y «el valor no vale» son dos averías distintas.

    Hasta hoy las dos daban el mismo mensaje —«Falta 'mutacion...'»— y quien lo
    leía se ponía a buscar una clave que estaba delante de sus ojos.
    """
    with pytest.raises(ValueError) as error:
        timeout_mutacion(rigor)

    assert "Falta" in str(error.value)
    assert "no vale" not in str(error.value)


def test_f040_r22_los_dos_mensajes_no_son_el_mismo() -> None:
    with pytest.raises(ValueError) as ausente:
        timeout_mutacion({"mutacion": {}})
    with pytest.raises(ValueError) as invalido:
        timeout_mutacion({"mutacion": {"timeout_por_mutante_s": 0}})

    assert str(ausente.value) != str(invalido.value)


# --- R23: `--timeout 0` deja de colarse -------------------------------------


@pytest.mark.parametrize("valor", ["0", "-5"])
def test_f040_r23_un_timeout_no_positivo_sale_con_codigo_2(valor: str) -> None:
    """Hoy `--timeout 0` es falsy y cae en silencio al timeout configurado.

    Quien lo escribe cree haber pedido algo y recibe otra cosa: el silencio
    esconde el error en vez de corregirlo.
    """
    with pytest.raises(SystemExit) as parada:
        _analizar_argumentos(["--feature", "F-040", "--timeout", valor])

    assert parada.value.code == 2


@pytest.mark.parametrize("valor", ["0", "-3"])
def test_f040_r23_unos_workers_no_positivos_salen_con_codigo_2(valor: str) -> None:
    """Misma guarda, mismo motivo: `--workers 0` no es una campaña de nada."""
    with pytest.raises(SystemExit) as parada:
        _analizar_argumentos(["--feature", "F-040", "--workers", valor])

    assert parada.value.code == 2


def test_f040_r23_los_valores_legitimos_siguen_pasando() -> None:
    opciones = _analizar_argumentos(
        ["--feature", "F-040", "--timeout", "600", "--workers", "3"]
    )

    assert opciones.timeout == 600
    assert opciones.workers == 3
    # 1 es el valor legítimo más pequeño: la campaña en serie de toda la vida.
    assert _analizar_argumentos(["--feature", "F-040", "--workers", "1"]).workers == 1
    assert _analizar_argumentos(["--feature", "F-040", "--timeout", "1"]).timeout == 1


def test_f040_r23_sin_flags_no_se_valida_nada() -> None:
    opciones = _analizar_argumentos(["--feature", "F-040"])

    assert opciones.timeout is None
    assert opciones.workers is None
