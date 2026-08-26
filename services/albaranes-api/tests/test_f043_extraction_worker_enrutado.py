# tests/test_f043_extraction_worker_enrutado.py
"""F-043 · El worker de sv2: quien clasifica y como enruta (R15, R16, R11).

Aqui se cierra el lazo que abre la feature. Antes: una regla determinista
deducia la tipologia y con ella elegia el prompt de fase 2, asi que la
regla acotaba lo que la IA podia concluir. Ahora: IA1 clasifica, el
catalogo dice que prompt le toca a esa familia (`prompt_fase2_de`) y, tras
la fase 2, IA2 puede corregir la clasificacion (R16).

Sin red, sin BBDD y sin LLM: el pipeline y los tres puertos son dobles.
"""
from __future__ import annotations

import logging

import pytest
from ruesma_comun.colas import COLA_PERSISTENCIA, MensajeBase
from ruesma_comun.contratos import familias as cat

from application.pipelines.extract_albaran_pipeline import (
    ExtractAlbaranPipeline,
    ReviewAlbaranRequest,
)
from application.services.albaran_extraction_service import (
    ProviderExtractionResult,
)
from domain.models.revision_models import RevisionAlbaranFase2
from interface_adapters.worker.extraction_worker import (
    construir_handler_extraccion,
)
from interface_adapters.worker.ports import DocumentoPdf

CLAVE_GENERICA = None  # el pipeline cae a su prompt_key_phase_2 configurado


def _bloque(familia, **extra) -> dict:
    campos = {"familia": familia, "confianza_pct": 80.0,
              "motivo": "lo que se lee en el documento"}
    campos.update(extra)
    return campos


def _data(clasificacion=None) -> dict:
    doc = {"cabecera": {"numero_albaran": "SS-0003967"}, "lineas": []}
    if clasificacion is not None:
        doc["clasificacion"] = clasificacion
    return doc


class PipelineDoble:
    """Doble de ``ExtractAlbaranPipeline``: captura la peticion de fase 2."""

    def __init__(self, data1=None, data2_revisado=None) -> None:
        self._data1 = data1 if data1 is not None else _data()
        self._data2 = data2_revisado
        self.peticion_fase2 = None

    def run_phase_1(self, request):
        return {"meta": {"phase": "phase_1"}, "data": self._data1,
                "debug": {}}

    def run_phase_2(self, request):
        self.peticion_fase2 = request
        revisado = self._data2 if self._data2 is not None else _data()
        return {
            "meta": {"phase": "phase_2"},
            "data": {"review_status": "ok", "documento_revisado": revisado,
                     "razonamientos": []},
            "debug": {},
        }


class FuenteDoble:
    def obtener(self, document_id: str) -> DocumentoPdf:
        return DocumentoPdf(filename="a.pdf", mime_type="application/pdf",
                            file_bytes=b"%PDF-")


class GroundingDoble:
    def contexto(self, *, document_id, phase_1_json):
        return None


class SumideroDoble:
    def __init__(self) -> None:
        self.guardados: list[tuple[str, dict]] = []

    def persistir(self, *, document_id, envelope, fase) -> None:
        self.guardados.append((fase, envelope))

    @property
    def envelope_final(self) -> dict:
        """El ultimo guardado: el envelope FINAL que consume sv3."""
        return self.guardados[-1][1]


class PublicadorDoble:
    def __init__(self) -> None:
        self.publicados: list[tuple[str, object]] = []

    def publicar(self, cola, mensaje) -> None:
        self.publicados.append((cola, mensaje))


def _ejecutar(pipeline) -> tuple[SumideroDoble, PublicadorDoble]:
    sumidero, publicador = SumideroDoble(), PublicadorDoble()
    handler = construir_handler_extraccion(
        pipeline=pipeline,
        fuente=FuenteDoble(),
        grounding=GroundingDoble(),
        sumidero=sumidero,
        publicador=publicador,
    )
    handler(MensajeBase(tipo="extraccion", document_id="doc-1"))
    return sumidero, publicador


# ------------------------------------------------------------------ #
# R15 — el prompt de fase 2 sale del CATALOGO, no de un f-string.
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("familia", "clave"),
    [
        ("residuos", "albaran_revision_fase2_residuos"),
        ("hormigon", "albaran_revision_fase2_hormigon"),
        ("mortero", "albaran_revision_fase2_mortero"),
        ("generico", CLAVE_GENERICA),
    ],
)
def test_f043_r15_el_worker_enruta_la_fase2_por_el_catalogo(
    familia, clave,
) -> None:
    pipeline = PipelineDoble(data1=_data(_bloque(familia)))

    _ejecutar(pipeline)

    assert pipeline.peticion_fase2.prompt_key == clave


def test_f043_r15_una_familia_nueva_del_catalogo_se_enruta_sin_tocar_codigo(
    monkeypatch,
) -> None:
    """R3 comprobado donde importa: se da de alta `bombeo` en caliente, con
    su clave de prompt, y el worker la enruta. Si el worker compusiera la
    clave con un f-string este test pasaria igual, asi que va acompanado
    del de abajo, que es el que lo distingue."""
    bombeo = cat.Familia(
        id="bombeo", nombre="Bombeo", definicion="d", no_es="n", senales="s",
        alcance=frozenset({"documento", "linea"}),
        prompt_fase2="albaran_revision_fase2_bombeo",
    )
    monkeypatch.setattr(cat, "CATALOGO", cat.CATALOGO + (bombeo,))
    pipeline = PipelineDoble(data1=_data(_bloque("bombeo")))

    _ejecutar(pipeline)

    assert pipeline.peticion_fase2.prompt_key == (
        "albaran_revision_fase2_bombeo"
    )


def test_f043_r15_una_familia_sin_prompt_propio_cae_al_generico(
    monkeypatch,
) -> None:
    """La distincion que el test anterior no hace: una familia de DOCUMENTO
    sin prompt propio NO se enruta a `albaran_revision_fase2_<familia>`
    (que no existe), sino que cae al generico configurado del pipeline.

    Un f-string mandaria una clave inventada; el catalogo manda `None`.
    """
    prefabricados = cat.Familia(
        id="prefabricados", nombre="Prefabricados", definicion="d",
        no_es="n", senales="s", alcance=frozenset({"documento"}),
        prompt_fase2=None,
    )
    monkeypatch.setattr(cat, "CATALOGO", cat.CATALOGO + (prefabricados,))
    pipeline = PipelineDoble(data1=_data(_bloque("prefabricados")))

    _ejecutar(pipeline)

    assert pipeline.peticion_fase2.prompt_key is None


def _log_del_worker(caplog) -> list[str]:
    return [
        r.getMessage() for r in caplog.records
        if r.name.endswith("extraction_worker")
    ]


def test_f043_r15_la_caida_al_generico_queda_en_el_log(caplog) -> None:
    """R15 lo pide literalmente: «cae al prompt generico configurado y lo
    deja en el log». Se comprueba el aviso CONCRETO, no que la palabra
    'generico' aparezca en algun sitio: la linea final del worker tambien
    la lleva, y con esa asercion floja el aviso podia desaparecer entero
    sin que nadie se enterara."""
    pipeline = PipelineDoble(data1=_data(_bloque("generico")))

    with caplog.at_level(logging.INFO):
        _ejecutar(pipeline)

    mensajes = _log_del_worker(caplog)
    assert any("sin prompt propio" in m for m in mensajes), mensajes
    assert any(
        "prompt_fase2=(generico configurado)" in m for m in mensajes
    ), mensajes


def test_f043_r15_con_prompt_propio_no_se_avisa_de_caida(caplog) -> None:
    """No-regresion del caso normal: el albaran de residuos se lee con su
    prompt y el log lo dice, sin avisos de caida."""
    pipeline = PipelineDoble(data1=_data(_bloque("residuos")))

    with caplog.at_level(logging.INFO):
        _ejecutar(pipeline)

    mensajes = _log_del_worker(caplog)
    assert not any("sin prompt propio" in m for m in mensajes), mensajes
    assert any(
        "prompt_fase2=albaran_revision_fase2_residuos" in m
        for m in mensajes
    ), mensajes


def test_f043_r10_una_familia_inventada_no_enruta_a_un_prompt_inventado(
) -> None:
    """La IA devuelve 'residuos_peligrosos': el resolver lo deja en
    `generico` y el enrutado cae al generico. Lo que NO puede pasar es que
    salga un `albaran_revision_fase2_residuos_peligrosos`."""
    pipeline = PipelineDoble(data1=_data(_bloque("residuos_peligrosos")))

    sumidero, _ = _ejecutar(pipeline)

    assert pipeline.peticion_fase2.prompt_key is None
    bloque = sumidero.envelope_final["data"]["clasificacion"]
    assert bloque["familia"] == "generico"
    assert "residuos_peligrosos" in bloque["motivo"]


# ------------------------------------------------------------------ #
# R16 — IA2 puede corregir la clasificacion, y su voto prevalece.
# ------------------------------------------------------------------ #
def test_f043_r16_el_worker_re_resuelve_con_la_fase2() -> None:
    """IA1 dijo `generico` (y por eso se leyo con el prompt generico), pero
    IA2, que ve el papel y el JSON, dice `residuos`. Manda IA2."""
    pipeline = PipelineDoble(
        data1=_data(_bloque("generico")),
        data2_revisado=_data(_bloque("residuos", confianza_pct=95.0)),
    )

    sumidero, _ = _ejecutar(pipeline)

    bloque = sumidero.envelope_final["data"]["clasificacion"]
    assert bloque["familia"] == "residuos"
    assert bloque["origen"] == "ia2"
    assert bloque["confianza_pct"] == 95.0
    # El prompt de fase 2 ya se habia elegido con la de IA1: el limite es
    # conocido y esta escrito en el diseno (una segunda pasada es otra
    # feature).
    assert pipeline.peticion_fase2.prompt_key is None


def test_f043_r16_si_ia2_no_la_toca_se_conserva_la_de_ia1() -> None:
    pipeline = PipelineDoble(
        data1=_data(_bloque("hormigon")), data2_revisado=_data(),
    )

    sumidero, _ = _ejecutar(pipeline)

    bloque = sumidero.envelope_final["data"]["clasificacion"]
    assert bloque["familia"] == "hormigon"
    assert bloque["origen"] == "ia1"


def test_f043_r11_sin_clasificacion_el_worker_registra_el_hueco() -> None:
    pipeline = PipelineDoble(data1=_data())

    sumidero, _ = _ejecutar(pipeline)

    bloque = sumidero.envelope_final["data"]["clasificacion"]
    assert bloque["familia"] == "generico"
    assert bloque["origen"] == "ausente"
    assert bloque["confianza_pct"] == 0
    assert pipeline.peticion_fase2.prompt_key is None


# ------------------------------------------------------------------ #
# No-regresion: el worker sigue haciendo lo que hacia.
# ------------------------------------------------------------------ #
def test_f043_r9_el_envelope_final_lleva_la_clasificacion_persistida() -> None:
    pipeline = PipelineDoble(data1=_data(_bloque("residuos")))

    sumidero, publicador = _ejecutar(pipeline)

    fases = [fase for fase, _ in sumidero.guardados]
    assert fases == ["phase_1", "phase_2", "phase_1"]
    assert sumidero.envelope_final["meta"]["tipologia"] == "residuos"
    assert publicador.publicados[0][0] == COLA_PERSISTENCIA


# ------------------------------------------------------------------ #
# R15 (segunda mitad) — la clave existe en el catalogo pero NO esta
# registrada en el indice de prompts del servicio.
#
# Es el fallo silencioso caro: se da de alta una familia con su clave, se
# olvida el prompt en el YAML, y todos sus albaranes se leen con las
# instrucciones genericas sin que nadie se entere.
# ------------------------------------------------------------------ #
class ServicioDoble:
    """Doble de ``AlbaranExtractionService``: solo el indice de prompts."""

    def __init__(self, claves: set[str]) -> None:
        self._claves = claves
        self.prompt_key_usada: str | None = None

    def has_prompt(self, prompt_key: str) -> bool:
        return prompt_key in self._claves

    def review_phase_2(self, *, prompt_key, **kwargs):
        self.prompt_key_usada = prompt_key
        return ProviderExtractionResult(
            provider="gemini", model_name="fake", schema_name="s",
            prompt_key=prompt_key, parsed=RevisionAlbaranFase2(
                review_status="ok", explicacion_global="",
                documento_revisado={"cabecera": {}, "lineas": []},
                razonamientos=[],
            ),
            debug_payload={},
        )


def _pipeline_real(servicio) -> ExtractAlbaranPipeline:
    return ExtractAlbaranPipeline(
        extraction_service=servicio,
        max_file_mb=10,
        service_version="test",
        provider_phase_1="gemini",
        provider_phase_2="gemini",
        prompt_key_phase_1="albaran_factura_es",
        prompt_key_phase_2="albaran_revision_fase2_es",
    )


def _avisos_del_pipeline(caplog) -> list[str]:
    """Solo los del pipeline: la cadena de preproceso de imagen tambien
    avisa (el PDF de estos dobles no es un PDF de verdad) y ese ruido no
    es lo que se esta midiendo."""
    return [
        r.getMessage() for r in caplog.records
        if r.name.endswith("extract_albaran_pipeline")
    ]


def test_f043_r15_el_pipeline_cae_al_generico_y_lo_deja_en_el_log(
    caplog,
) -> None:
    servicio = ServicioDoble({"albaran_revision_fase2_es"})

    with caplog.at_level(logging.WARNING):
        _pipeline_real(servicio).run_phase_2(
            ReviewAlbaranRequest(
                filename="a.pdf", mime_type="application/pdf",
                file_bytes=b"%PDF-", phase_1_json={},
                prompt_key="albaran_revision_fase2_bombeo",
            )
        )

    assert servicio.prompt_key_usada == "albaran_revision_fase2_es"
    avisos = _avisos_del_pipeline(caplog)
    assert any("albaran_revision_fase2_bombeo" in a for a in avisos), avisos


def test_f043_r15_con_la_clave_registrada_no_hay_aviso(caplog) -> None:
    """No-regresion del caso normal: el prompt de la familia se usa y el
    log no se llena de avisos que nadie mirara."""
    servicio = ServicioDoble(
        {"albaran_revision_fase2_es", "albaran_revision_fase2_residuos"}
    )

    with caplog.at_level(logging.WARNING):
        _pipeline_real(servicio).run_phase_2(
            ReviewAlbaranRequest(
                filename="a.pdf", mime_type="application/pdf",
                file_bytes=b"%PDF-", phase_1_json={},
                prompt_key="albaran_revision_fase2_residuos",
            )
        )

    assert servicio.prompt_key_usada == "albaran_revision_fase2_residuos"
    assert _avisos_del_pipeline(caplog) == []
