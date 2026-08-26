# tests/test_f043_phase_merge_clasificacion.py
"""F-043 · La clasificacion viaja dentro de `data` (R9).

El defecto que arregla esta tarea: `phase_merge` sellaba la tipologia SOLO
en `meta.tipologia`, y `persistence_worker._sanear_envelope` de sv3 la
DESCARTA, porque `ExtractionMeta` es `extra='forbid'` y no la declara. Por
eso sv5 y sv6 la exigian sin recibirla nunca. Ahora va en `data`, que sv3
si persiste, y `meta.tipologia` se conserva solo como espejo para el log.

Funcion pura: sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

from ruesma_comun.contratos import ClasificacionAlbaran

from application.services.phase_merge import construir_envelope_final
from domain.models.albaran_models import DocumentoAlbaran


def _clasificacion(familia="residuos", **extra) -> ClasificacionAlbaran:
    campos = {
        "familia": familia,
        "confianza_pct": 91.0,
        "motivo": "gestor autorizado y LER 170504 en las lineas",
        "origen": "ia1",
    }
    campos.update(extra)
    return ClasificacionAlbaran(**campos)


def _documento(**extra) -> dict:
    doc = {"cabecera": {"numero_albaran": "SS-0003967"}, "lineas": []}
    doc.update(extra)
    return doc


def _env1(data=None) -> dict:
    return {"meta": {"phase": "phase_1", "provider": "gemini"},
            "data": data if data is not None else _documento(),
            "debug": {"raw": "..."}}


def _env2(documento=None) -> dict:
    return {
        "meta": {"phase": "phase_2", "provider": "openai"},
        "data": {
            "review_status": "ok_with_changes",
            "documento_revisado": (
                documento if documento is not None else _documento()
            ),
            "razonamientos": [{"campo": "cabecera.fecha",
                               "descripcion": "en la imagen se lee 12/06"}],
        },
        "debug": {},
    }


# ------------------------------------------------------------------ #
# R9 — en `data`, que es lo que sv3 persiste.
# ------------------------------------------------------------------ #
def test_f043_r9_phase_merge_escribe_la_clasificacion_en_data() -> None:
    envelope = construir_envelope_final(
        env_fase1=_env1(), clasificacion=_clasificacion(),
    )

    bloque = envelope["data"]["clasificacion"]
    assert bloque["familia"] == "residuos"
    assert bloque["confianza_pct"] == 91.0
    assert bloque["motivo"].startswith("gestor autorizado")
    assert bloque["origen"] == "ia1"


def test_f043_r9_phase_merge_tambien_con_fase2() -> None:
    """Cuando hay fase 2, el documento final es `documento_revisado`: es
    ahi donde tiene que acabar la clasificacion."""
    envelope = construir_envelope_final(
        env_fase1=_env1(), env_fase2=_env2(),
        clasificacion=_clasificacion("hormigon", origen="ia2"),
    )

    assert envelope["data"]["clasificacion"]["familia"] == "hormigon"
    assert envelope["data"]["clasificacion"]["origen"] == "ia2"
    assert envelope["meta"]["phase"] == "phase_2"


def test_f043_r9_meta_tipologia_queda_como_espejo() -> None:
    """El espejo se conserva para el log y para no romper a quien lo
    leyera; el dato de verdad es el de `data`."""
    envelope = construir_envelope_final(
        env_fase1=_env1(), clasificacion=_clasificacion("mortero"),
    )

    assert envelope["meta"]["tipologia"] == "mortero"
    assert envelope["data"]["clasificacion"]["familia"] == "mortero"


def test_f043_r9_el_data_resultante_sigue_validando_el_schema() -> None:
    """`data` lo parsea sv3 con un modelo `extra='forbid'`: si la
    clasificacion no encajara en el schema, el envelope entero se caeria en
    persistencia y no en un test."""
    envelope = construir_envelope_final(
        env_fase1=_env1(), clasificacion=_clasificacion(),
    )

    documento = DocumentoAlbaran.model_validate(envelope["data"])

    assert documento.clasificacion is not None
    assert documento.clasificacion.familia == "residuos"


def test_f043_r9_la_clasificacion_resuelta_pisa_la_que_trajo_la_ia() -> None:
    """El bloque que escribe el merge es el del resolver, con el `origen`
    sellado: si se colase el crudo de la IA, `origen` seria lo que ella
    dijera y R16 dejaria de ser comprobable."""
    revisado = _documento(clasificacion={"familia": "generico",
                                         "confianza_pct": 10.0,
                                         "motivo": "crudo de la IA",
                                         "origen": "humano"})

    envelope = construir_envelope_final(
        env_fase1=_env1(), env_fase2=_env2(revisado),
        clasificacion=_clasificacion("residuos", origen="ia2"),
    )

    assert envelope["data"]["clasificacion"]["familia"] == "residuos"
    assert envelope["data"]["clasificacion"]["origen"] == "ia2"


def test_f043_r9_phase_merge_no_muta_los_envelopes_de_entrada() -> None:
    """Los envelopes de fase 1 y 2 ya estan PERSISTIDOS cuando se llama a
    esto: escribirles la clasificacion dentro reescribiria la auditoria
    forense de lo que dijo cada IA (regla 1 de ARCHITECTURE)."""
    env1, env2 = _env1(), _env2()

    construir_envelope_final(
        env_fase1=env1, env_fase2=env2, clasificacion=_clasificacion(),
    )

    assert "clasificacion" not in env1["data"]
    assert "clasificacion" not in env2["data"]["documento_revisado"]


def test_f043_r27_phase_merge_sin_clasificacion_es_el_de_antes() -> None:
    """Compatibilidad: sin clasificacion, ni en `data` ni en `meta`. Un
    envelope anterior a la feature se comporta como hoy."""
    envelope = construir_envelope_final(env_fase1=_env1())

    assert "clasificacion" not in envelope["data"]
    assert "tipologia" not in envelope["meta"]
    assert envelope["meta"]["phase"] == "phase_1"
    assert envelope["meta"]["merged"] is False
