# tests/test_f048_r15_schema.py
"""F-048 · R15 y R17: IA1 devuelve ``lectura_correo`` junto al documento.

``lectura_correo`` es la lectura del CORREO (los codigos de obra que IA1 ve
en el asunto o el cuerpo y el fragmento donde los ve), separada de la del
PAPEL, que sigue en ``cabecera.obra_codigo``: las cruza sv2 despues (D3).
Del correo solo la obra (D8): el modelo no tiene sitio para una partida.

Es opcional (R17): un envelope sin el bloque valida igual que antes, y el
resolver lo tratara como ``ia_sin_lectura_correo``. ``DocumentoAlbaran`` es
``extra='forbid'``: sin declararlo, un documento con el bloque no validaria.

Sin red, sin BBDD y sin LLM. Textos inventados.
"""
from __future__ import annotations

import pytest
from domain.models.albaran_models import DocumentoAlbaran
from domain.models.lectura_correo import LecturaCorreo
from domain.models.revision_models import RevisionAlbaranFase2
from pydantic import ValidationError

_CABECERA = {"proveedor_nombre": "HORMIGONES DEL SUR", "obra_codigo": "0937"}
_LINEAS = [{"concepto": "HA-25/B/20/IIa", "cantidad": 7.5}]
_LECTURA = {"obra_codigos": ["0945"], "evidencia": "Para la obra 0945"}


def test_f048_r15_el_documento_acepta_lectura_correo():
    documento = DocumentoAlbaran.model_validate(
        {"cabecera": _CABECERA, "lineas": _LINEAS, "lectura_correo": _LECTURA}
    )

    assert documento.lectura_correo == LecturaCorreo(
        obra_codigos=["0945"], evidencia="Para la obra 0945"
    )
    # Dos lecturas independientes: la del papel no la toca el correo.
    assert documento.cabecera.obra_codigo == "0937"


def test_f048_r15_varios_codigos_en_el_correo_son_una_lista():
    lectura = LecturaCorreo.model_validate({"obra_codigos": ["0945", "1042"], "evidencia": None})

    assert lectura.obra_codigos == ["0945", "1042"]
    assert lectura.evidencia is None


def test_f048_r15_sin_codigos_la_lista_queda_vacia():
    assert LecturaCorreo.model_validate({}).obra_codigos == []


def test_f048_r15_lectura_correo_solo_lleva_obra_nunca_partida():
    """D8: del correo solo la obra. Un campo de partida no valida."""
    assert set(LecturaCorreo.model_fields) == {"obra_codigos", "evidencia"}
    with pytest.raises(ValidationError):
        LecturaCorreo.model_validate({**_LECTURA, "codigo_imputacion": "01.02"})


def test_f048_r15_la_fase2_devuelve_el_mismo_bloque():
    """``documento_revisado`` es el MISMO modelo: IA2 puede repetir el bloque."""
    revision = RevisionAlbaranFase2.model_validate(
        {
            "review_status": "ok",
            "documento_revisado": {
                "cabecera": _CABECERA,
                "lineas": _LINEAS,
                "lectura_correo": _LECTURA,
            },
            "razonamientos": [],
        }
    )

    assert revision.documento_revisado.lectura_correo.obra_codigos == ["0945"]


def test_f048_r15_el_schema_que_ve_el_llm_declara_el_bloque():
    """El schema de respuesta es el que recibe el LLM: sin el campo, IA1 no lo devolveria."""
    esquema = DocumentoAlbaran.model_json_schema()

    assert "lectura_correo" in esquema["properties"]
    lectura = esquema["$defs"]["LecturaCorreo"]
    assert set(lectura["properties"]) == {"obra_codigos", "evidencia"}
    assert lectura["additionalProperties"] is False


def test_f048_r17_un_envelope_sin_lectura_correo_sigue_validando():
    documento = DocumentoAlbaran.model_validate({"cabecera": _CABECERA, "lineas": _LINEAS})

    assert documento.lectura_correo is None
    assert "lectura_correo" not in documento.model_dump(exclude_none=True)
