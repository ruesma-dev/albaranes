# tests/test_f048_r8_r9_mensaje.py
"""F-048 · R8 y R9 · ``MensajeExtraccion.correo_blob``.

- R8: el texto del correo NO viaja en el mensaje. Con un cuerpo de 60.000
  caracteres, el mensaje sigue midiendo menos de 1 KB (solo lleva el nombre
  del blob lateral).
- R9: ``correo_blob`` es opcional y nulo por defecto; compatible en los dos
  sentidos: un mensaje sin el campo valida en el modelo nuevo, y uno con el
  campo valida en un modelo que no lo declare (el sv2 viejo durante el
  despliegue sv3 -> sv2 -> sv1).

Sin red: solo serializacion.
"""
from __future__ import annotations

import json
from typing import Literal

from ruesma_comun.colas.mensajes import MensajeBase, MensajeExtraccion, desde_texto
from ruesma_comun.correo import construir_contexto_correo, nombre_blob_correo

CENTINELA = "CENTINELA-F048"


class MensajeExtraccionSinCorreo(MensajeBase):
    """Copia del modelo de antes de F-048: no declara ``correo_blob``."""

    tipo: Literal["extraccion"] = "extraccion"


# ------------------------------------------------------------------ #
# R9 · opcional y nulo por defecto
# ------------------------------------------------------------------ #
def test_f048_r9_correo_blob_es_nulo_por_defecto():
    mensaje = MensajeExtraccion(document_id="doc-1")
    assert mensaje.correo_blob is None


def test_f048_r9_sin_correo_el_texto_del_mensaje_no_cambia():
    """``a_texto`` excluye los nulos: sin correo, el JSON es el de siempre."""
    mensaje = MensajeExtraccion(
        document_id="doc-1", correlation_key="corr-1", emitido_en_utc="2026-09-23T08:00:00Z"
    )
    assert json.loads(mensaje.a_texto()) == {
        "tipo": "extraccion",
        "document_id": "doc-1",
        "correlation_key": "corr-1",
        "emitido_en_utc": "2026-09-23T08:00:00Z",
    }


def test_f048_r9_con_correo_el_campo_viaja_y_vuelve():
    mensaje = MensajeExtraccion(document_id="doc-1", correo_blob="doc-1.correo.json")
    leido = desde_texto(mensaje.a_texto(), tipo_esperado="extraccion")
    assert isinstance(leido, MensajeExtraccion)
    assert leido.correo_blob == "doc-1.correo.json"
    assert json.loads(mensaje.a_texto())["correo_blob"] == "doc-1.correo.json"


def test_f048_r9_mensaje_viejo_sin_campo_valida_en_el_modelo_nuevo():
    viejo = MensajeExtraccionSinCorreo(document_id="doc-1", correlation_key="c")
    leido = desde_texto(viejo.a_texto(), tipo_esperado="extraccion")
    assert isinstance(leido, MensajeExtraccion)
    assert leido.document_id == "doc-1"
    assert leido.correo_blob is None


def test_f048_r9_mensaje_nuevo_con_campo_valida_en_un_modelo_que_no_lo_declara():
    nuevo = MensajeExtraccion(document_id="doc-1", correo_blob="doc-1.correo.json")
    viejo = MensajeExtraccionSinCorreo.model_validate_json(nuevo.a_texto())
    assert viejo.document_id == "doc-1"
    assert not hasattr(viejo, "correo_blob")


# ------------------------------------------------------------------ #
# R8 · el texto no viaja en el mensaje
# ------------------------------------------------------------------ #
def test_f048_r8_con_60000_caracteres_el_mensaje_mide_menos_de_1_kb():
    cuerpo = (CENTINELA + " ") * (60_000 // (len(CENTINELA) + 1) + 1)
    assert len(cuerpo) >= 60_000
    ctx = construir_contexto_correo("Albaran obra 1234", cuerpo)
    mensaje = MensajeExtraccion(
        document_id="doc-1",
        correlation_key="corr-" + "x" * 64,
        emitido_por="sv1-email",
        correo_blob=nombre_blob_correo("doc-1"),
    )
    texto = mensaje.a_texto()
    assert len(texto.encode("utf-8")) < 1024
    assert CENTINELA not in texto
    assert ctx.sha256 not in texto
    assert "correo_blob" in texto


def test_f048_r8_el_mensaje_no_declara_campos_de_texto_del_correo():
    """Solo el NOMBRE del blob: ningun campo para asunto ni cuerpo."""
    campos = set(MensajeExtraccion.model_fields) - set(MensajeBase.model_fields)
    assert campos == {"correo_blob"}
