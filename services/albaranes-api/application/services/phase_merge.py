# application/services/phase_merge.py
"""Fusión de fases (antes en sv7, disuelto) — ahora en sv2.

Construye el envelope FINAL que consume sv3 a partir de:
  - el envelope de fase 1 (extracción), y
  - opcionalmente el de fase 2 (revisión).

Contrato de datos (recordatorio):
  - Fase 1 devuelve ``{meta, data, debug}`` donde ``data`` es un
    ``DocumentoAlbaran`` (``{cabecera, lineas}``).
  - Fase 2 devuelve ``{meta, data, debug}`` donde ``data`` es un
    ``RevisionAlbaranFase2`` (``{documento_revisado: DocumentoAlbaran,
    razonamientos: [...]}``).

Por eso el merge, cuando hay fase 2, EXTRAE ``data.documento_revisado``
como el documento final (sv3 espera la forma DocumentoAlbaran en
``data``), conserva la traza de ambas fases en ``debug`` y arrastra los
razonamientos. Sin fase 2, el final es la fase 1 tal cual.

Además SELLA la clasificación de DOCUMENTO que decidió la IA **dentro de
``data``** (F-043 · R9). Ahí es donde tiene que ir, y no en ``meta``:
``persistence_worker._sanear_envelope`` de sv3 filtra ``meta`` contra
``ExtractionMeta``, que es ``extra='forbid'`` y no declara la tipología,
así que la DESCARTABA — por eso sv5 y sv6 la exigían sin recibirla nunca.
``data`` sí se persiste, y su schema declara el campo (``DocumentoAlbaran.
clasificacion``), de modo que el ``extra='forbid'`` no estorba.
``meta.tipologia`` se conserva como ESPEJO para el log y para no romper a
quien lo leyera; el dato de verdad es el de ``data``. El detalle por línea
(LER, m³, Tn, familia) sigue viajando en ``contexto_linea``.

Función PURA: sin I/O, fácil de testear.
"""
from __future__ import annotations

from typing import Any, Mapping

from ruesma_comun.contratos import ClasificacionAlbaran


def _doc_final(
    env_fase1: Mapping[str, Any],
    env_fase2: Mapping[str, Any] | None,
) -> tuple[dict, list, str]:
    """Devuelve (data_documento, razonamientos, fase_efectiva)."""
    if env_fase2 is not None:
        data2 = env_fase2.get("data") or {}
        documento = data2.get("documento_revisado")
        if isinstance(documento, dict):
            razonamientos = data2.get("razonamientos") or []
            # Copia: el envelope de fase 2 ya está PERSISTIDO cuando se
            # llama a esto, y escribirle dentro la clasificación
            # reescribiría la auditoría forense de lo que dijo cada IA.
            return dict(documento), list(razonamientos), "phase_2"
        # Salvaguarda: si la fase 2 no trajo documento_revisado utilizable,
        # NO perdemos la extracción: caemos a fase 1.
    data1 = env_fase1.get("data") or {}
    return dict(data1), [], "phase_1"


def construir_envelope_final(
    *,
    env_fase1: Mapping[str, Any],
    env_fase2: Mapping[str, Any] | None = None,
    clasificacion: ClasificacionAlbaran | None = None,
) -> dict:
    """Envelope final ``{meta, data, debug}`` para sv3.

    ``clasificacion`` es la que consolidó ``clasificacion_resolver`` (con
    el ``origen`` ya sellado), no el crudo que devolvió la IA. ``None``
    deja el envelope exactamente como antes de F-043: sin bloque en
    ``data`` y sin espejo en ``meta`` (R27).
    """
    documento, razonamientos, fase = _doc_final(env_fase1, env_fase2)

    if clasificacion is not None:
        # Pisa lo que hubiera puesto la IA en `documento_revisado`: el
        # bueno es el resuelto, que es el que lleva el `origen` sellado.
        documento["clasificacion"] = clasificacion.model_dump()

    meta_base = dict(env_fase1.get("meta") or {})
    if env_fase2 is not None:
        # La revisión es la fase efectiva: reflejamos su meta por encima.
        meta_base.update(env_fase2.get("meta") or {})
    meta_base["phase"] = fase
    meta_base["merged"] = env_fase2 is not None
    if clasificacion is not None:
        meta_base["tipologia"] = clasificacion.familia

    debug: dict[str, Any] = {
        "phase_1": {
            "meta": env_fase1.get("meta"),
            "debug": env_fase1.get("debug"),
        },
    }
    if env_fase2 is not None:
        debug["phase_2"] = {
            "meta": env_fase2.get("meta"),
            "debug": env_fase2.get("debug"),
            "razonamientos": razonamientos,
        }

    return {"meta": meta_base, "data": documento, "debug": debug}
