# tests/test_f043_schema_sv2_documento.py
"""F-043 R8 · sv2 acepta el bloque `clasificacion` en el documento.

IA1 devuelve la clasificacion de DOCUMENTO dentro de `data`, no en `meta`
(R9: sv3 filtra `meta` contra un modelo estricto y la descartaria). Para
que llegue hasta ahi, el schema del documento de fase 1 —y con el, el
`documento_revisado` de fase 2, que es el MISMO modelo— tiene que
declararla.

`DocumentoAlbaran` es `extra='forbid'`: sin declarar el campo, un envelope
con clasificacion no valida. Declarandolo con default `None`, un envelope
anterior a esta feature sigue validando igual que antes.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError
from ruesma_comun.contratos.clasificacion import ClasificacionAlbaran

from domain.models.albaran_models import DocumentoAlbaran
from domain.models.revision_models import RevisionAlbaranFase2

_CABECERA = {"proveedor_nombre": "SALMEDINA", "numero_albaran": "SS-0003967"}
_LINEAS = [{"concepto": "Contenedor RCD", "cantidad": 1}]
_CLASIFICACION = {
    "familia": "residuos",
    "confianza_pct": 93.0,
    "motivo": "Gestor autorizado de RCD, codigos LER y contenedores.",
    "mixto": False,
    "familias_secundarias": [],
}


def test_f043_r8_schema_sv2_documento_acepta_el_bloque_clasificacion():
    documento = DocumentoAlbaran.model_validate(
        {
            "cabecera": _CABECERA,
            "lineas": _LINEAS,
            "clasificacion": _CLASIFICACION,
        }
    )

    assert documento.clasificacion is not None
    assert documento.clasificacion.familia == "residuos"
    assert documento.clasificacion.confianza_pct == 93.0
    assert documento.clasificacion.origen == "ia1"


def test_f043_r8_schema_sv2_documento_usa_el_contrato_compartido():
    """El contrato vive en `ruesma_comun`, no copiado en el servicio."""
    anotacion = DocumentoAlbaran.model_fields["clasificacion"].annotation

    assert ClasificacionAlbaran in getattr(anotacion, "__args__", (anotacion,))


def test_f043_r8_schema_sv2_documento_sin_clasificacion_sigue_validando():
    """Un envelope anterior a F-043 no la trae y no puede romperse."""
    documento = DocumentoAlbaran.model_validate(
        {"cabecera": _CABECERA, "lineas": _LINEAS}
    )

    assert documento.clasificacion is None


def test_f043_r8_schema_sv2_documento_sigue_rechazando_campos_no_declarados():
    """El `extra='forbid'` no se ha aflojado para colar la clasificacion."""
    with pytest.raises(ValidationError):
        DocumentoAlbaran.model_validate(
            {
                "cabecera": _CABECERA,
                "lineas": _LINEAS,
                "campo_inventado": "x",
            }
        )


def test_f043_r8_schema_sv2_documento_rechaza_una_clasificacion_mal_formada():
    """Si la IA devuelve un porcentaje imposible, se ve; no se cuela."""
    with pytest.raises(ValidationError):
        DocumentoAlbaran.model_validate(
            {
                "cabecera": _CABECERA,
                "lineas": _LINEAS,
                "clasificacion": {**_CLASIFICACION, "confianza_pct": 150},
            }
        )


def test_f043_r8_schema_sv2_documento_revisado_de_fase2_tambien_la_acepta():
    """R8/R16: la fase 2 devuelve el MISMO modelo de documento, asi que
    puede confirmar o corregir la clasificacion en `documento_revisado`."""
    revision = RevisionAlbaranFase2.model_validate(
        {
            "review_status": "ok_with_changes",
            "documento_revisado": {
                "cabecera": _CABECERA,
                "lineas": _LINEAS,
                "clasificacion": {**_CLASIFICACION, "familia": "generico"},
            },
        }
    )

    assert revision.documento_revisado.clasificacion is not None
    assert revision.documento_revisado.clasificacion.familia == "generico"


def test_f043_r8_schema_sv2_documento_expone_clasificacion_en_el_json_schema():
    """El schema que se le manda al LLM tiene que incluir el bloque: si no,
    IA1 no sabe que se le pide (R7)."""
    esquema = DocumentoAlbaran.model_json_schema()

    assert "clasificacion" in esquema["properties"]
