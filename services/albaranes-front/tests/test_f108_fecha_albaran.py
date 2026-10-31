# tests/test_f108_fecha_albaran.py
"""F-108 · A · la regla de lectura de la fecha y el número del albarán (R1–R4, R10).

Dominio puro de sv4 (``domain/services/fecha_albaran.py``): sin red ni BBDD.
La tabla ``CASOS`` es común con el test de node (R20,
``test_f108_fecha_js.py``): la función de la ficha (``parseFechaEs``) debe
dar lo mismo que la de Python en cada fila.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

#: Marca de «no admitida» en la columna esperada de ``CASOS``.
NO_VALIDA = "NO_VALIDA"

#: (texto escrito, esperado): ISO, ``None`` (sin fecha) o ``NO_VALIDA``.
CASOS: list[tuple[str | None, str | None]] = [
    ("28/10/2026", "2026-10-28"),
    ("28-10-26", "2026-10-28"),
    ("28.10.2026", "2026-10-28"),
    ("2026-10-28", "2026-10-28"),
    ("5/6/2026", "2026-06-05"),
    ("1/1/26", "2026-01-01"),
    ("1/1/00", "2000-01-01"),
    ("  28/10/2026  ", "2026-10-28"),
    ("28/10-2026", "2026-10-28"),
    ("29/02/2024", "2024-02-29"),
    ("31/12/2026", "2026-12-31"),
    ("", None),
    ("   ", None),
    (None, None),
    ("31/02/2026", NO_VALIDA),
    ("29/02/2026", NO_VALIDA),
    ("31/04/2026", NO_VALIDA),
    ("2026-02-30", NO_VALIDA),
    ("2026/10/28", NO_VALIDA),
    ("2026-1-5", NO_VALIDA),
    ("28/10", NO_VALIDA),
    ("abc", NO_VALIDA),
    ("28/13/2026", NO_VALIDA),
    ("00/10/2026", NO_VALIDA),
    ("28/00/2026", NO_VALIDA),
    ("28/10/226", NO_VALIDA),
    ("28/10/20266", NO_VALIDA),
    ("1/1/0000", NO_VALIDA),
    ("0000-01-01", NO_VALIDA),
    ("28 /10/2026", NO_VALIDA),
    ("28/10/2026 10:00", NO_VALIDA),
    ("２８/１０/２０２６", NO_VALIDA),  # cifras de ancho completo: \d de Python las admitiría
    ("28/10/2026\n", "2026-10-28"),
]

AVISO = ("Fecha del albarán no válida: «{texto}». Escríbela como dd/mm/aaaa "
         "(p. ej. 28/10/2026) o elígela en el calendario.")


def _ids(casos):
    return [repr(c[0]) for c in casos]


# =================================================================== #
# R1, R2, R3 · normalizar la fecha escrita
# =================================================================== #
@pytest.mark.parametrize("texto, esperado", [c for c in CASOS if c[1] != NO_VALIDA],
                         ids=_ids([c for c in CASOS if c[1] != NO_VALIDA]))
def test_f108_r1_r2_normaliza_lo_admitido(texto, esperado):
    from domain.services.fecha_albaran import normalizar_fecha_albaran

    assert normalizar_fecha_albaran(texto) == esperado


@pytest.mark.parametrize("texto", [c[0] for c in CASOS if c[1] == NO_VALIDA],
                         ids=_ids([c for c in CASOS if c[1] == NO_VALIDA]))
def test_f108_r3_rechaza_lo_no_admitido_con_el_aviso(texto):
    from domain.models.review_models import FechaAlbaranNoValidaError
    from domain.services.fecha_albaran import normalizar_fecha_albaran

    with pytest.raises(FechaAlbaranNoValidaError) as error:
        normalizar_fecha_albaran(texto)

    assert error.value.texto == texto.strip()
    assert error.value.aviso == AVISO.format(texto=texto.strip()) == str(error.value)
    assert isinstance(error.value, ValueError)


def test_f108_r3_el_aviso_es_el_de_la_spec():
    from domain.services.fecha_albaran import AVISO_FECHA_NO_VALIDA

    assert AVISO_FECHA_NO_VALIDA == AVISO
    assert AVISO_FECHA_NO_VALIDA.format(texto="31/02/2026") == (
        "Fecha del albarán no válida: «31/02/2026». Escríbela como dd/mm/aaaa "
        "(p. ej. 28/10/2026) o elígela en el calendario."
    )


# =================================================================== #
# R4 · la fecha guardada, en dd/mm/aaaa para verla
# =================================================================== #
@pytest.mark.parametrize("guardada, vista", [
    ("2026-10-28", "28/10/2026"),
    ("2026-06-05", "05/06/2026"),
    ("05/06/2026", "05/06/2026"),
    ("8/10/2026", "08/10/2026"),
    (None, ""),
    ("", ""),
    ("ayer", "ayer"),
    ("31/02/2026", "31/02/2026"),
    ("2026-02-30", "2026-02-30"),
])
def test_f108_r4_fecha_para_ver(guardada, vista):
    from domain.services.fecha_albaran import fecha_para_ver

    assert fecha_para_ver(guardada) == vista


# =================================================================== #
# R11 (apoyo) · ¿la fecha guardada es AAAA-MM-DD real?
# =================================================================== #
@pytest.mark.parametrize("valor, valida", [
    ("2026-10-28", True),
    ("2024-02-29", True),
    ("2026-02-29", False),
    ("08/10/2026", False),
    ("2026-1-05", False),
    (None, False),
    ("", False),
    (" 2026-10-28", False),
    ("２０２６-１０-２８", False),
])
def test_f108_r11_es_fecha_guardada_valida(valor, valida):
    from domain.services.fecha_albaran import es_fecha_guardada_valida

    assert es_fecha_guardada_valida(valor) is valida


# =================================================================== #
# R8, R9 · el número de albarán
# =================================================================== #
@pytest.mark.parametrize("texto, esperado", [
    ("  A-1/2026 ", "A-1/2026"),
    ("ab.12", "ab.12"),
    ("", None),
    ("   ", None),
    (None, None),
    ("x" * 128, "x" * 128),
    ("  " + "x" * 128 + "  ", "x" * 128),
], ids=["recorta", "sin_otro_cambio", "vacio", "espacios", "nulo", "128", "128_con_espacios"])
def test_f108_r8_numero_recortado_sin_otro_cambio(texto, esperado):
    from domain.services.fecha_albaran import normalizar_numero_albaran

    assert normalizar_numero_albaran(texto) == esperado


def test_f108_r9_numero_de_129_se_rechaza():
    from domain.models.review_models import NumeroAlbaranNoValidoError
    from domain.services.fecha_albaran import MAX_NUMERO_ALBARAN, normalizar_numero_albaran

    assert MAX_NUMERO_ALBARAN == 128
    with pytest.raises(NumeroAlbaranNoValidoError) as error:
        normalizar_numero_albaran("x" * 129)

    aviso = "El número de albarán no puede pasar de 128 caracteres"
    assert error.value.aviso == aviso == str(error.value)


# =================================================================== #
# R10 · lo guardado casa con la expresión de sv9 (que no cambia)
# =================================================================== #
_VALIDADOR_SV9 = (Path(__file__).resolve().parents[2] / "albaranes-alta-sigrid" / "domain"
                  / "services" / "validador_alta.py")


def test_f108_r10_lo_guardado_casa_con_re_fecha_de_sv9():
    from domain.services.fecha_albaran import normalizar_fecha_albaran

    fuente = _VALIDADOR_SV9.read_text(encoding="utf-8")
    patron = re.search(r'^_RE_FECHA = re\.compile\(r"([^"]+)"\)', fuente, re.MULTILINE)
    assert patron, "no se encuentra _RE_FECHA en validador_alta.py de sv9"
    re_fecha = re.compile(patron.group(1))
    salidas = [normalizar_fecha_albaran(t) for t, e in CASOS if e not in (None, NO_VALIDA)]
    assert salidas
    for salida in salidas:
        assert re_fecha.match(salida), salida
