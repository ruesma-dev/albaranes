# tests/test_f048_t34_supervivientes.py
"""F-048 · T34: el superviviente de la campaña de mutación de sv4 (mutante 26).

``review_models.py:928`` pasa el aviso de siempre a «historia» cambiando su
prefijo ``Obra: `` por ``Al extraer, ``. Solo el PREFIJO: la lectura del
papel es texto libre de la IA y puede traer ``Obra: `` dentro; esa se pinta
tal cual. Con ``count=2`` el revisor leería una obra del papel que no es la
que leyó la IA. El análisis de los 26 está en
``progress/impl_F-048_T34_supervivientes.md``. Sin red ni BBDD.
"""
from __future__ import annotations

import json


def _payload(obra_codigo: str):
    from domain.models.review_models import DocumentDetailPayload

    origen = {
        "version": 1, "correo_presente": True, "correo_sha256": "f" * 64, "correo_truncado": False,
        "evidencia": "la 945",
        "obra": {"fuente": "correo", "motivo": "correo_unico", "valor_final": "0945", "valor_correo": "0945",
                 "candidatos_correo": ["0945"], "valor_papel": "Obra: 0937", "discrepancia": True,
                 "validada": True},
    }
    raw = json.dumps({"meta": {}, "data": {"cabecera": {"obra_codigo": "0945"}, "lineas": [],
                                           "origen_datos": origen}, "debug": {}}, ensure_ascii=False)
    return DocumentDetailPayload(
        id="f048-doc-0026", source_filename="SS-26.pdf", provider_origin="merge", model_name="—",
        created_at_utc="2026-09-24T10:00:00Z", raw_extraction_json=raw, obra_codigo=obra_codigo,
    )


def test_f048_r32_la_historia_solo_cambia_el_prefijo_del_aviso():
    sin_cambio = _payload("0945").avisos_origen_datos
    cambiada = _payload("0999")

    assert sin_cambio == ["Obra: el correo dice 0945 y el papel dice Obra: 0937. Se ha usado la del correo."]
    assert cambiada.obra_cambiada_tras_extraer is True
    assert cambiada.avisos_origen_datos[1] == (
        "Al extraer, el correo dice 0945 y el papel dice Obra: 0937. Se ha usado la del correo."
    )
