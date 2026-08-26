# tests/test_f043_schema_sv3_documento.py
"""F-043 R8/R9 · sv3 acepta el bloque `clasificacion` del documento.

La clasificacion viaja dentro de `data` a proposito: sv3 filtra `meta`
contra `ExtractionMeta` (`extra='forbid'`) y hoy DESCARTA `meta.tipologia`,
que es justo por lo que sv5 y sv6 la exigian sin recibirla nunca. Para que
sobreviva al saneado, `DocumentoAlbaran` de sv3 tiene que declararla.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest
from domain.models.extraction_models import (
    DocumentoAlbaran,
    ExtractionEnvelope,
)
from pydantic import ValidationError
from ruesma_comun.contratos import ClasificacionAlbaran

_CABECERA = {"proveedor_nombre": "SALMEDINA", "numero_albaran": "SS-0003967"}
_LINEAS = [{"concepto": "Contenedor RCD", "cantidad": 1}]
_CLASIFICACION = {
    "familia": "residuos",
    "confianza_pct": 93.0,
    "motivo": "Gestor autorizado de RCD, codigos LER y contenedores.",
    "origen": "ia1",
}
_META = {
    "prompt_key": "albaran_factura_es",
    "schema": "albaran_v2",
    "source_filename": "SS-0003967.pdf",
    "source_mime_type": "application/pdf",
    "source_sha256": "0" * 64,
    "model": "modelo-de-prueba",
    "processed_at_utc": "2026-08-26T10:00:00Z",
}


def test_f043_r8_schema_sv3_documento_acepta_el_bloque_clasificacion():
    documento = DocumentoAlbaran.model_validate(
        {
            "cabecera": _CABECERA,
            "lineas": _LINEAS,
            "clasificacion": _CLASIFICACION,
        }
    )

    assert documento.clasificacion is not None
    assert documento.clasificacion.familia == "residuos"
    assert documento.clasificacion.origen == "ia1"


def test_f043_r8_schema_sv3_documento_usa_el_contrato_compartido():
    """El mismo objeto que sv2: un solo contrato, no una copia por
    servicio (es lo que hizo divergir a `contexto_linea` en su dia)."""
    anotacion = DocumentoAlbaran.model_fields["clasificacion"].annotation

    assert ClasificacionAlbaran in getattr(anotacion, "__args__", (anotacion,))


def test_f043_r8_schema_sv3_documento_sin_clasificacion_sigue_validando():
    documento = DocumentoAlbaran.model_validate(
        {"cabecera": _CABECERA, "lineas": _LINEAS}
    )

    assert documento.clasificacion is None


def test_f043_r8_schema_sv3_documento_sigue_rechazando_campos_no_declarados():
    with pytest.raises(ValidationError):
        DocumentoAlbaran.model_validate(
            {
                "cabecera": _CABECERA,
                "lineas": _LINEAS,
                "campo_inventado": "x",
            }
        )


def test_f043_r8_schema_sv3_envelope_completo_la_conserva_dentro_de_data():
    """El envelope que llega por la cola: la clasificacion esta en `data`."""
    envelope = ExtractionEnvelope.model_validate(
        {
            "meta": _META,
            "data": {
                "cabecera": _CABECERA,
                "lineas": _LINEAS,
                "clasificacion": _CLASIFICACION,
            },
        }
    )

    assert envelope.data.clasificacion is not None
    assert envelope.data.clasificacion.familia == "residuos"


def test_f043_r9_schema_sv3_meta_sigue_sin_admitir_la_tipologia():
    """R9 documentado como test: `meta` NO es el camino. Si alguien vuelve
    a colgar la clasificacion de `meta`, esto lo delata."""
    with pytest.raises(ValidationError):
        ExtractionEnvelope.model_validate(
            {
                "meta": {**_META, "tipologia": "residuos"},
                "data": {"cabecera": _CABECERA, "lineas": _LINEAS},
            }
        )
