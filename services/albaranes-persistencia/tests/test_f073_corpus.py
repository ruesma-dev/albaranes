# tests/test_f073_corpus.py
"""F-073 · R19 — el corpus real: 19 candidatos y 31 lecturas.

Candidatos: las 18 razones sociales distintas de ``evals/fixtures/final/``
(con su CIF) más HIERROS RODRIGO, S.A. (la de la incidencia 0694). Lecturas:
las que la IA puede dar de esos nombres (design §5): las tres de FEYMACO de
la incidencia, solo el nombre comercial, con marca delante, con una letra mal
leída, sin forma jurídica o con otra, parciales y tres que no deben elegir.
Elegir por nombre (umbral 0,5, margen 0,25) debe acertar las 31 sin un solo
CIF equivocado. Control: el criterio de antes (``_match_score``, el máximo y
el primero en empate) en la misma lista. Sin red ni BBDD.
"""
from __future__ import annotations

import pytest

from application.services.header_resolver_service import _match_score, _norm
from application.services.similitud_proveedor import (
    MARGEN_NOMBRE_POR_DEFECTO,
    elegir_por_nombre,
)

UMBRAL = 0.5

FEYMACO = "A28733558"
HIERROS = "A19004589"
CUBAS = "B93649002"
SANEAMIENTO = "B85286318"
DICONA = "A31132590"
PAZ_DEL_BARRIO = "B86362290"
GALAPAGAR = "B56747264"
SIERRA_MADRID = "B86738812"
ANDALUCES = "B29679628"
HORPRESOL = "B04685541"
MACOTRAN = "B78507472"
MAHORSA = "B86615549"
PAVIMARSA = "A28800597"
PINSACON = "B83287276"
SALMEDINA = "B82899550"
SALTOKI = "A82825456"
MOSTOLES = "B86359866"
ANGEL_MARTIN = "B84535764"
VODALAND = "B98976111"

#: Por CIF, como llega la consulta agregada (``ORDER BY p.cif``).
CANDIDATOS = sorted([
    (CUBAS, "CARGA Y TRANSPORTE DE CUBAS, S.L."),
    (SANEAMIENTO, "CONDUCCIONES DE SANEAMIENTO INTEGRADO S.L."),
    (DICONA, "DICONA, S.A."),
    (PAZ_DEL_BARRIO, "FABRICACION DE HORMIGONES PAZ DEL BARRIO,S.L."),
    (FEYMACO, "FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)"),
    (GALAPAGAR, "GASOLEOS GALAPAGAR, S.L."),
    (SIERRA_MADRID, "HORMIGON SIERRA MADRID, S.L."),
    (ANDALUCES, "HORMIGONES Y CEMENTOS ANDALUCES, S.L."),
    (HORPRESOL, "HORPRESOL, S.L."),
    (MACOTRAN, "MACOTRAN, S.L.U."),
    (MAHORSA, "MATERIALES Y HORMIGONES, S.L. (MAHORSA)"),
    (PAVIMARSA, "PAVIMARSA, S.A."),
    (PINSACON, "PINSACON, S.L."),
    (SALMEDINA, "SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L."),
    (SALTOKI, "SALTOKI CENTRO, S.A."),
    (MOSTOLES, "SUMINISTROS DE OBRAS MOSTOLES, S.L."),
    (ANGEL_MARTIN, "TRANSPORTES Y GRUAS ANGEL MARTIN, S.L."),
    (VODALAND, "VODALAND ESPAÑA, S.L"),
    (HIERROS, "HIERROS RODRIGO, S.A."),
])

#: (lectura, CIF esperado o None si no debe elegir).
LECTURAS = [
    # La incidencia 0694.
    ("FEYMACO, S.A.", FEYMACO),
    ("TEYMACO, S.A.", FEYMACO),
    ("FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.", FEYMACO),
    # Solo el nombre comercial.
    ("Cubas", CUBAS),
    ("HORPRESOL", HORPRESOL),
    ("SALMEDINA", SALMEDINA),
    ("SALTOKI", SALTOKI),
    ("MAHORSA", MAHORSA),
    ("PINSACON", PINSACON),
    ("VODALAND", VODALAND),
    ("DICONA", DICONA),
    # Marca delante.
    ("GRUPO OTTO HORPRESOL", HORPRESOL),
    # Una letra mal leída.
    ("H0RPRESOL S.L.", HORPRESOL),
    ("DlCONA S.A.", DICONA),
    # Sin forma jurídica o con otra.
    ("MACOTRAN S.L.U.", MACOTRAN),
    ("PAVIMARSA S.A.", PAVIMARSA),
    ("Saltoki Centro S.A.", SALTOKI),
    ("VODALAND ESPAÑA S.L.", VODALAND),
    ("Gasoleos Galapagar", GALAPAGAR),
    ("HORMIGON SIERRA MADRID SL", SIERRA_MADRID),
    ("Hormigones y Cementos Andaluces", ANDALUCES),
    ("CONDUCCIONES DE SANEAMIENTO INTEGRADO", SANEAMIENTO),
    ("Suministros de Obras Móstoles S.L.", MOSTOLES),
    ("HIERROS RODRIGO", HIERROS),
    # Parciales.
    ("GRUAS ANGEL MARTIN", ANGEL_MARTIN),
    ("Hormigones Paz del Barrio", PAZ_DEL_BARRIO),
    ("MATERIALES Y HORMIGONES SL", MAHORSA),
    ("Salmedina Tratamiento de Residuos", SALMEDINA),
    # No deben elegir: una forma jurídica sola y dos palabras genéricas.
    ("S.A.", None),
    ("HORMIGONES", None),
    ("TRANSPORTES", None),
]


def test_f073_r19_el_corpus_tiene_19_candidatos_y_31_lecturas():
    assert len({cif for cif, _ in CANDIDATOS}) == 19
    assert len(LECTURAS) == 31


@pytest.mark.parametrize(("leido", "esperado"), LECTURAS, ids=[le for le, _ in LECTURAS])
def test_f073_r19_cada_lectura_elige_lo_esperado(leido, esperado):
    eleccion = elegir_por_nombre(leido, CANDIDATOS, umbral=UMBRAL, margen=MARGEN_NOMBRE_POR_DEFECTO)
    obtenido = eleccion.elegido.cif if eleccion.elegido else None
    assert obtenido == esperado


def _recuento(elegir) -> tuple[int, int, int]:
    """(aciertos, errores, sin decisión). Error = un CIF equivocado, o elegir
    cuando no se debía."""
    aciertos = errores = sin_decision = 0
    for leido, esperado in LECTURAS:
        obtenido = elegir(leido)
        if obtenido == esperado:
            aciertos += 1
        elif obtenido is None:
            sin_decision += 1
        else:
            errores += 1
    return aciertos, errores, sin_decision


def _elegir_f073(leido):
    eleccion = elegir_por_nombre(leido, CANDIDATOS, umbral=UMBRAL, margen=MARGEN_NOMBRE_POR_DEFECTO)
    return eleccion.elegido.cif if eleccion.elegido else None


def _elegir_antes(leido):
    """El atajo de antes de F-073: el máximo de ``_match_score`` y, en
    empate, el primero en llegar (``max`` se queda con el primero)."""
    q = _norm(leido)
    cif, nombre = max(CANDIDATOS, key=lambda c: _match_score(q, _norm(c[1])))
    return cif if _match_score(q, _norm(nombre)) >= UMBRAL else None


def test_f073_r19_f073_acierta_las_31_sin_errores():
    assert _recuento(_elegir_f073) == (31, 0, 0)


def test_f073_r19_control_el_criterio_de_antes_se_equivoca():
    """Medido sobre esta misma lista (2026-10-17): 24 aciertos, 6 CIF
    equivocados y 1 sin decisión («GRUPO OTTO HORPRESOL»). Los dos de la
    incidencia eligen HIERROS RODRIGO, como en producción. (El prototipo del
    spec-author, con otro orden y otras lecturas, daba 23/7/1.)"""
    assert _recuento(_elegir_antes) == (24, 6, 1)
    assert _elegir_antes("FEYMACO, S.A.") == HIERROS
    assert _elegir_antes("TEYMACO, S.A.") == HIERROS
