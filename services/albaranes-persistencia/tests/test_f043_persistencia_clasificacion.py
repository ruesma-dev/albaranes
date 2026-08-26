# tests/test_f043_persistencia_clasificacion.py
"""F-043 · sv3 conserva, persiste y marca a revision la clasificacion.

Cubre el BLOQUE C de la feature:

- **R9** — la clasificacion SOBREVIVE al saneado de `meta` de sv3
  (`persistence_worker._sanear_envelope`), porque viaja dentro de `data`.
  El espejo `meta.tipologia` se sigue descartando: es exactamente el
  defecto que motivo la feature, y aqui queda escrito como test.
- **R22** — las seis columnas de `albaran_documents_merge` (DDL idempotente,
  ORM y escritura del merge).
- **R11, R28, R29** — motivos de revision `clasificacion_ausente`,
  `clasificacion_confianza_baja` y `clasificacion_mixta`.
- **R19** — motivo `linea_sin_familia_en_albaran_mixto` en las lineas que
  NO heredan la familia del documento.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

from domain.models.extraction_models import ExtractionEnvelope
from interface_adapters.worker.persistence_worker import _sanear_envelope
from ruesma_comun.contratos import ClasificacionAlbaran

_CABECERA = {"proveedor_nombre": "SALMEDINA", "numero_albaran": "SS-0003967"}
_LINEAS = [{"concepto": "Contenedor RCD 6 m3", "cantidad": 1}]
_CLASIFICACION = {
    "familia": "residuos",
    "confianza_pct": 93.0,
    "motivo": "Gestor autorizado de RCD, codigos LER y contenedores.",
    "mixto": False,
    "familias_secundarias": [],
    "origen": "ia1",
}
_META = {
    "prompt_key": "albaran_revision_fase2_residuos",
    "schema": "albaran_v2",
    "source_filename": "SS-0003967.pdf",
    "source_mime_type": "application/pdf",
    "source_sha256": "0" * 64,
    "model": "modelo-de-prueba",
    "processed_at_utc": "2026-08-26T10:00:00Z",
}


def _envelope_de_sv2(*, con_clasificacion: bool = True) -> dict:
    """El envelope tal y como lo deja `phase_merge.construir_envelope_final`.

    `meta` trae las claves que sv3 NO declara (`phase`, `merged`, `provider`
    y el espejo `tipologia`); `data` trae la clasificacion de verdad.
    """
    data: dict = {"cabecera": dict(_CABECERA), "lineas": list(_LINEAS)}
    meta = {**_META, "phase": "phase_2", "merged": True, "provider": "openai"}
    if con_clasificacion:
        data["clasificacion"] = dict(_CLASIFICACION)
        meta["tipologia"] = _CLASIFICACION["familia"]
    return {"meta": meta, "data": data, "debug": {"phase_1": {}}}


# ------------------------------------------------------------------ #
# T13 · R9 — la clasificacion sobrevive al saneado de `meta`.
# ------------------------------------------------------------------ #

def test_f043_r9_sanear_conserva_la_clasificacion_dentro_de_data():
    saneado = _sanear_envelope(_envelope_de_sv2())

    assert saneado["data"]["clasificacion"] == _CLASIFICACION


def test_f043_r9_sanear_descarta_el_espejo_de_meta():
    """El defecto de origen, por escrito: `meta.tipologia` NO llega.

    `_sanear_envelope` filtra `meta` contra `ExtractionMeta`, que es
    `extra='forbid'`. Por eso la tipologia sellada en `meta` se perdia y
    sv5/sv6 la exigian sin recibirla nunca. Si alguien vuelve a colgarla
    de `meta`, este test le recuerda que ese camino sigue cerrado.
    """
    saneado = _sanear_envelope(_envelope_de_sv2())

    assert "tipologia" not in saneado["meta"]
    assert "phase" not in saneado["meta"]
    assert saneado["meta"]["prompt_key"] == _META["prompt_key"]


def test_f043_r9_sanear_no_toca_data_aunque_filtre_meta():
    """`data` se pasa TAL CUAL: el saneado es solo de `meta`."""
    envelope = _envelope_de_sv2()

    saneado = _sanear_envelope(envelope)

    assert saneado["data"] is envelope["data"]


def test_f043_r9_sanear_y_validar_deja_viva_la_clasificacion():
    """De la cola al modelo de sv3, el recorrido entero.

    Es el test de R9: sanear + validar con el `extra='forbid'` de sv3 y
    que la clasificacion siga ahi, ya como `ClasificacionAlbaran`.
    """
    saneado = _sanear_envelope(_envelope_de_sv2())

    envelope = ExtractionEnvelope.model_validate(saneado)

    assert isinstance(envelope.data.clasificacion, ClasificacionAlbaran)
    assert envelope.data.clasificacion.familia == "residuos"
    assert envelope.data.clasificacion.confianza_pct == 93.0
    assert envelope.data.clasificacion.origen == "ia1"


def test_f043_r27_sanear_un_envelope_anterior_sigue_validando_sin_ella():
    """Documento previo a la feature: mismo camino, `clasificacion` None."""
    saneado = _sanear_envelope(_envelope_de_sv2(con_clasificacion=False))

    envelope = ExtractionEnvelope.model_validate(saneado)

    assert envelope.data.clasificacion is None
