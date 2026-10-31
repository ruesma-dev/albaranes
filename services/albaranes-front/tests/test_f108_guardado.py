# tests/test_f108_guardado.py
"""F-108 · B · el guardado de la cabecera (R5–R9) y aprobar sin fecha o sin
número (R11, D4 = a).

Repositorio real sobre SQLite (``f065_bbdd``: el albarán de METALFIRE) y
``build_app`` real con un servicio falso, como ``test_f065_f1_cabecera.py``.
Sin red ni BBDD.
"""
from __future__ import annotations

from typing import Any

import pytest
from domain.models.review_models import MergeDocumentUpdatePayload
from f053_sv4_bbdd import foto
from f065_bbdd import CABECERA, DOC, construir, ejecutar, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session

AVISO_APROBADO = "Albarán aprobado: desapruébalo para editar"


def _aviso_fecha(texto: str) -> str:
    return (f"Fecha del albarán no válida: «{texto}». Escríbela como dd/mm/aaaa "
            "(p. ej. 28/10/2026) o elígela en el calendario.")


AVISO_NUMERO = "El número de albarán no puede pasar de 128 caracteres"


def _cabecera(motor) -> dict[str, Any]:
    with Session(motor) as s:
        return dict(s.execute(
            text("SELECT fecha, numero_albaran, approved FROM albaran_documents_merge "
                 "WHERE id = :id"), {"id": DOC},
        ).mappings().one())


def _guardar(repo, monkeypatch, **campos):
    monkeypatch.setattr(repo, "get_document_detail", lambda document_id: "detalle")
    return repo.update_document_y_transicion(
        document_id=DOC, payload=MergeDocumentUpdatePayload(**campos),
    )


# =================================================================== #
# R5 · lo admitido se guarda AAAA-MM-DD
# =================================================================== #
@pytest.mark.parametrize("escrita", ["28/10/2026", "28-10-26", "2026-10-28", " 28.10.2026 "])
def test_f108_r5_guarda_la_fecha_en_iso(monkeypatch, escrita):
    motor = construir()

    _guardar(repositorio(motor), monkeypatch, fecha=escrita, numero_albaran="A-1")

    assert _cabecera(motor)["fecha"] == "2026-10-28"


def test_f108_r5_la_fecha_guardada_dd_mm_se_arregla_al_guardar(monkeypatch):
    """R25: lo que ya está guardado en ``dd/mm/aaaa`` se arregla al guardar."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_documents_merge SET fecha = '05/06/2026' WHERE id = :d",
             d=DOC)

    _guardar(repositorio(motor), monkeypatch, fecha="05/06/2026", numero_albaran="A-1")

    assert _cabecera(motor)["fecha"] == "2026-06-05"


# =================================================================== #
# R6 · vacía ⇒ nula
# =================================================================== #
@pytest.mark.parametrize("escrita", [None, "", "   "])
def test_f108_r6_vacia_guarda_nula(monkeypatch, escrita):
    motor = construir()
    ejecutar(motor, "UPDATE albaran_documents_merge SET fecha = '2026-10-01' WHERE id = :d",
             d=DOC)

    _guardar(repositorio(motor), monkeypatch, fecha=escrita, numero_albaran="A-1")

    assert _cabecera(motor)["fecha"] is None


# =================================================================== #
# R7 · no admitida ⇒ error y nada cambia
# =================================================================== #
@pytest.mark.parametrize("escrita", ["31/02/2026", "abc"])
def test_f108_r7_no_admitida_no_cambia_nada(monkeypatch, escrita):
    from domain.models.review_models import FechaAlbaranNoValidaError

    motor = construir()
    antes = foto(motor)

    with pytest.raises(FechaAlbaranNoValidaError) as error:
        _guardar(repositorio(motor), monkeypatch, fecha=escrita, numero_albaran="OTRO",
                 review_notes="nota nueva", approved=True, approved_by="ana",
                 **CABECERA)

    assert error.value.aviso == _aviso_fecha(escrita)
    assert foto(motor) == antes


# =================================================================== #
# R8 · número recortado, sin otro cambio
# =================================================================== #
def test_f108_r8_numero_recortado_sin_otro_cambio(monkeypatch):
    motor = construir()

    _guardar(repositorio(motor), monkeypatch, fecha="28/10/2026", numero_albaran="  ab.12/x ")

    assert _cabecera(motor)["numero_albaran"] == "ab.12/x"


# =================================================================== #
# R9 · número de más de 128 ⇒ error y nada cambia
# =================================================================== #
def test_f108_r9_numero_largo_no_cambia_nada(monkeypatch):
    from domain.models.review_models import NumeroAlbaranNoValidoError

    motor = construir()
    antes = foto(motor)

    with pytest.raises(NumeroAlbaranNoValidoError) as error:
        _guardar(repositorio(motor), monkeypatch, fecha="28/10/2026",
                 numero_albaran="x" * 129, review_notes="nota nueva")

    assert error.value.aviso == AVISO_NUMERO
    assert foto(motor) == antes


def test_f108_r9_numero_de_128_si_se_guarda(monkeypatch):
    motor = construir()

    _guardar(repositorio(motor), monkeypatch, fecha="28/10/2026", numero_albaran="x" * 128)

    assert _cabecera(motor)["numero_albaran"] == "x" * 128


# =================================================================== #
# Orden (design §4.3): un aprobado da su 409 antes que la fecha mala
# =================================================================== #
def test_f108_r7_aprobado_con_fecha_mala_sigue_dando_el_409_de_aprobado(monkeypatch):
    from domain.models.review_models import AlbaranAprobadoError

    motor = construir(aprobado=True)
    antes = foto(motor)

    with pytest.raises(AlbaranAprobadoError):
        _guardar(repositorio(motor), monkeypatch, fecha="31/02/2026", numero_albaran="x" * 129)

    assert foto(motor) == antes
