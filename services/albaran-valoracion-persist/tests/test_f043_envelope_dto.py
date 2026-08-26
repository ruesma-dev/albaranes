# tests/test_f043_envelope_dto.py
"""F-043 · T21 · el sobre de sv5 trae la clasificacion del DOCUMENTO.

``ValuationContextDto.clasificacion`` es el UNICO punto por el que la
decision de IA1 entra en sv6. De ahi la leen las puertas de familia
(T22) para resolver la familia EFECTIVA de cada linea.

Las dos mitades que este fichero fija:

* **R23** — un sobre CON clasificacion la deja tipada y completa, sin
  perder ningun campo por el camino.
* **R27** — un sobre SIN ella (documento anterior a la feature) sigue
  validando y deja ``clasificacion=None``, que es lo que hace que
  ``familia_efectiva`` devuelva ``None`` y sv6 se comporte como hoy.

Sin red, sin BBDD y sin LLM: solo validacion de modelos.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.models.valuation_envelope import ValuationEnvelope

#: El sobre minimo que sv5 entrega, sin bloque de clasificacion. Es
#: literalmente la forma de los sobres anteriores a F-043.
SOBRE_SIN_CLASIFICACION = {
    "status": "ok",
    "meta": {"document_id": "doc-f043", "codigo_contrato": "CTSU24/0228"},
    "data": {"lineas": []},
    "context": {"lineas_albaran": [], "lineas_contrato": []},
}

CLASIFICACION_RESIDUOS = {
    "familia": "residuos",
    "confianza_pct": 92.0,
    "motivo": "gestor autorizado de RCD, LER 170604, contenedor de 6 m3",
    "mixto": False,
    "familias_secundarias": [],
    "origen": "ia2",
}


def _sobre_con(clasificacion: dict | None) -> dict:
    sobre = {
        **SOBRE_SIN_CLASIFICACION,
        "context": {
            **SOBRE_SIN_CLASIFICACION["context"],
            "clasificacion": clasificacion,
        },
    }
    return sobre


def test_f043_r23_el_sobre_trae_la_clasificacion_tipada():
    """Los seis campos llegan enteros y con su tipo."""
    envelope = ValuationEnvelope.model_validate(
        _sobre_con(CLASIFICACION_RESIDUOS)
    )

    clasificacion = envelope.context.clasificacion
    assert clasificacion is not None
    assert clasificacion.familia == "residuos"
    assert clasificacion.confianza_pct == pytest.approx(92.0)
    assert "LER 170604" in clasificacion.motivo
    assert clasificacion.mixto is False
    assert clasificacion.familias_secundarias == []
    assert clasificacion.origen == "ia2"


def test_f043_r23_el_sobre_conserva_mixto_y_las_familias_secundarias():
    """En un albaran MIXTO, ``mixto`` es lo que corta la herencia (R19).

    Si el DTO lo perdiera, sv6 heredaria la familia mayoritaria a TODAS
    las lineas sin familia propia de un albaran mezclado, que es
    exactamente lo que R19 prohibe.
    """
    envelope = ValuationEnvelope.model_validate(
        _sobre_con(
            {
                **CLASIFICACION_RESIDUOS,
                "mixto": True,
                "familias_secundarias": ["hormigon", "generico"],
            }
        )
    )

    clasificacion = envelope.context.clasificacion
    assert clasificacion is not None
    assert clasificacion.mixto is True
    assert clasificacion.familias_secundarias == ["hormigon", "generico"]


def test_f043_r27_un_sobre_sin_clasificacion_sigue_validando():
    """Documento anterior a F-043: valida y deja ``clasificacion=None``.

    Es la puerta de entrada de R27 en sv6. El default no es un detalle
    de comodidad: es lo que impide que los sobres que ya estan en la
    cola `q-valoracion` revienten al desplegar esta feature.
    """
    envelope = ValuationEnvelope.model_validate(SOBRE_SIN_CLASIFICACION)

    assert envelope.context.clasificacion is None


def test_f043_r27_una_clasificacion_explicitamente_nula_tambien_vale():
    """sv5 escribe ``"clasificacion": null`` cuando el merge no la tiene.

    No es lo mismo que omitir la clave, y las dos formas tienen que
    valer: la primera es la que de verdad emite el pipeline de sv5.
    """
    envelope = ValuationEnvelope.model_validate(_sobre_con(None))

    assert envelope.context.clasificacion is None


def test_f043_r23_una_clasificacion_sin_familia_no_pasa_en_silencio():
    """``familia`` es obligatoria: un bloque a medias es un error.

    El contrato lo declara sin default a proposito. Si aqui se aceptara
    una clasificacion sin familia, sv6 la trataria como "sin familia
    efectiva" y el hueco quedaria invisible en vez de reventar donde se
    origina.
    """
    with pytest.raises(ValidationError):
        ValuationEnvelope.model_validate(
            _sobre_con({"confianza_pct": 92.0, "motivo": "algo"})
        )
