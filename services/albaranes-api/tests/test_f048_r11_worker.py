# tests/test_f048_r11_worker.py
"""F-048 · R11 (y R22, R25 de extremo a extremo): el worker de sv2 con correo.

- ``FuenteContextoCorreoBlob`` lee ``input/{document_id}.correo.json`` con
  la MISMA funcion de ``ruesma_comun`` que escribe sv1; si el blob falta o
  no valida, ``None`` (R11).
- El handler lee ``correo_blob`` con ``getattr`` (un ``MensajeBase`` sin el
  campo vale) y pasa el MISMO contexto a las dos fases.
- Blob ausente o roto ⇒ se extrae sin correo y el documento sigue: nunca a
  poison por eso (R5/R11), con ``origen_datos.correo_presente = false``.
- Tras ``construir_envelope_final`` se sella ``origen_datos`` con la lectura
  del correo de FASE 1 (aviso A) y ``obras_conocidas()`` UNA sola vez por
  documento, y solo si hay correo (aviso B).
- ``main_worker.py`` cablea la fuente de Blob y la lista de obras del pipeline.

Sin red, sin BBDD y sin LLM: pipeline, puertos y almacen son dobles.
"""
from __future__ import annotations

import importlib.util
import logging
import sys
import types
from pathlib import Path

import pytest
from application.pipelines.extract_albaran_pipeline import (
    ExtractAlbaranPipeline,
    ExtractAlbaranRequest,
    ReviewAlbaranRequest,
)
from application.services.albaran_extraction_service import ProviderExtractionResult
from domain.models.albaran_models import DocumentoAlbaran
from domain.models.revision_models import RevisionAlbaranFase2
from interface_adapters.worker.correo_adapter import FuenteContextoCorreoBlob
from interface_adapters.worker.extraction_worker import construir_handler_extraccion
from interface_adapters.worker.ports import DocumentoPdf, FuenteContextoCorreo
from ruesma_comun.blobs import CONTENEDOR_INPUT
from ruesma_comun.colas import COLA_PERSISTENCIA, MensajeBase, MensajeExtraccion
from ruesma_comun.contratos.origen_datos import (
    MOTIVO_CORREO_UNICO,
    MOTIVO_SIN_CORREO,
    OrigenDatos,
)
from ruesma_comun.correo import construir_contexto_correo, nombre_blob_correo

CENTINELA = "CENTINELA-F048"
RAIZ = Path(__file__).resolve().parents[1]
DOC = "doc-f048"
BLOB = nombre_blob_correo(DOC)
CORREO = construir_contexto_correo("Albaran obra 945", f"Va para la 945. {CENTINELA}")
OBRAS = {"945": "0945", "1203": "1203"}


# ---------------------------------------------------------------- #
# Dobles.
# ---------------------------------------------------------------- #
class AlmacenDoble:
    """Forma de ``AlmacenBlobs`` que usa ``leer_contexto_correo``."""

    def __init__(self, blobs: dict | None = None, error: BaseException | None = None) -> None:
        self.blobs = dict(blobs or {})
        self.error = error
        self.leidos: list[tuple[str, str]] = []

    def get_json(self, contenedor: str, nombre: str):
        self.leidos.append((contenedor, nombre))
        if self.error is not None:
            raise self.error
        if (contenedor, nombre) not in self.blobs:
            raise FileNotFoundError(nombre)
        return self.blobs[(contenedor, nombre)]

    def put_json(self, contenedor: str, nombre: str, objeto) -> None:  # pragma: no cover
        self.blobs[(contenedor, nombre)] = objeto


class FuenteCorreoDoble(FuenteContextoCorreo):
    def __init__(self, correo=CORREO) -> None:
        self.correo = correo
        self.pedidos: list[str] = []

    def obtener(self, nombre_blob: str):
        self.pedidos.append(nombre_blob)
        return self.correo


def _data(obra: str | None, lectura: dict | None) -> dict:
    return {"cabecera": {"obra_codigo": obra}, "lineas": [], "lectura_correo": lectura}


class PipelineDoble:
    """Doble de ``ExtractAlbaranPipeline``: guarda las dos peticiones."""

    def __init__(self, *, papel1="1203", lectura1=None, papel2="1203", lectura2=None) -> None:
        self.data1 = _data(papel1, lectura1)
        self.data2 = _data(papel2, lectura2)
        self.peticion1: ExtractAlbaranRequest | None = None
        self.peticion2: ReviewAlbaranRequest | None = None

    def run_phase_1(self, request):
        self.peticion1 = request
        return {"meta": {"phase": "phase_1"}, "data": self.data1, "debug": {}}

    def run_phase_2(self, request):
        self.peticion2 = request
        return {
            "meta": {"phase": "phase_2"},
            "data": {"review_status": "ok", "documento_revisado": self.data2, "razonamientos": []},
            "debug": {"phase_1_json": request.phase_1_json},
        }


class ObrasDoble:
    def __init__(self, obras=OBRAS) -> None:
        self.obras = obras
        self.llamadas = 0

    def __call__(self):
        self.llamadas += 1
        return self.obras


class FuenteDoble:
    def obtener(self, document_id):
        return DocumentoPdf(filename="a.pdf", mime_type="application/pdf", file_bytes=b"%PDF-")


class GroundingDoble:
    def contexto(self, *, document_id, phase_1_json):
        return None


class SumideroDoble:
    def __init__(self) -> None:
        self.guardados: list[tuple[str, dict]] = []

    def persistir(self, *, document_id, envelope, fase) -> None:
        self.guardados.append((fase, envelope))


class PublicadorDoble:
    def __init__(self) -> None:
        self.publicados: list[tuple[str, object]] = []

    def publicar(self, cola, mensaje) -> None:
        self.publicados.append((cola, mensaje))


def _ejecutar(pipeline, mensaje, *, fuente_correo=None, obras=None, con_obras=True):
    sumidero, publicador = SumideroDoble(), PublicadorDoble()
    kwargs = {}
    if fuente_correo is not None:
        kwargs["fuente_correo"] = fuente_correo
    if con_obras:
        kwargs["obras_conocidas"] = obras if obras is not None else ObrasDoble()
    handler = construir_handler_extraccion(
        pipeline=pipeline, fuente=FuenteDoble(), grounding=GroundingDoble(),
        sumidero=sumidero, publicador=publicador, **kwargs,
    )
    handler(mensaje)
    return sumidero, publicador


def _mensaje(correo_blob: str | None = BLOB) -> MensajeExtraccion:
    return MensajeExtraccion(document_id=DOC, correlation_key="corr-1", correo_blob=correo_blob)


def _origen(sumidero: SumideroDoble) -> OrigenDatos:
    fase, final = sumidero.guardados[-1]
    assert fase == "phase_1"
    return OrigenDatos.model_validate(final["data"]["origen_datos"])


# ---------------------------------------------------------------- #
# FuenteContextoCorreoBlob.
# ---------------------------------------------------------------- #
def test_f048_r11_la_fuente_de_blob_lee_el_contexto_de_input():
    almacen = AlmacenDoble({(CONTENEDOR_INPUT, BLOB): CORREO.model_dump(mode="json")})

    assert FuenteContextoCorreoBlob(almacen).obtener(BLOB) == CORREO
    assert almacen.leidos == [(CONTENEDOR_INPUT, BLOB)]


@pytest.mark.parametrize(
    "almacen",
    [
        AlmacenDoble(),
        AlmacenDoble(error=ValueError("json roto")),
        AlmacenDoble({(CONTENEDOR_INPUT, BLOB): {"asunto": "sin huella"}}),
        AlmacenDoble({(CONTENEDOR_INPUT, BLOB): ["no", "es", "un", "objeto"]}),
    ],
    ids=["ausente", "ilegible", "no_valida", "no_es_objeto"],
)
def test_f048_r11_blob_ausente_o_roto_da_none(almacen):
    assert FuenteContextoCorreoBlob(almacen).obtener(BLOB) is None


def test_f048_r11_un_fallo_de_red_del_blob_se_propaga_para_reintentar():
    """Contrato del bloque A: la red NO es «blob roto»; la cola reintenta
    (igual que con el PDF) en vez de extraer sin correo por un corte."""
    almacen = AlmacenDoble(error=ConnectionError("corte"))

    with pytest.raises(ConnectionError):
        FuenteContextoCorreoBlob(almacen).obtener(BLOB)


# ---------------------------------------------------------------- #
# El handler: el MISMO correo a las dos fases.
# ---------------------------------------------------------------- #
def test_f048_r11_el_correo_llega_a_las_dos_fases():
    pipeline, fuente = PipelineDoble(), FuenteCorreoDoble()

    _ejecutar(pipeline, _mensaje(), fuente_correo=fuente)

    assert fuente.pedidos == [BLOB]
    assert pipeline.peticion1.contexto_correo is CORREO
    assert pipeline.peticion2.contexto_correo is CORREO


def test_f048_r11_con_blob_real_ausente_se_sigue_sin_correo_y_se_publica():
    pipeline = PipelineDoble(lectura1={"obra_codigos": ["945"], "evidencia": "la 945"})
    fuente = FuenteContextoCorreoBlob(AlmacenDoble())

    sumidero, publicador = _ejecutar(pipeline, _mensaje(), fuente_correo=fuente)

    assert pipeline.peticion1.contexto_correo is None
    assert pipeline.peticion2.contexto_correo is None
    origen = _origen(sumidero)
    assert origen.correo_presente is False
    assert origen.obra.motivo == MOTIVO_SIN_CORREO
    assert sumidero.guardados[-1][1]["data"]["cabecera"]["obra_codigo"] == "1203"
    assert publicador.publicados[0][0] == COLA_PERSISTENCIA


def test_f048_r11_un_mensaje_sin_el_campo_vale_y_no_se_pide_blob():
    """``getattr`` defensivo: un ``MensajeBase`` (o un modelo viejo) sin
    ``correo_blob`` se procesa como hoy."""
    pipeline, fuente = PipelineDoble(), FuenteCorreoDoble()

    sumidero, publicador = _ejecutar(
        pipeline, MensajeBase(tipo="extraccion", document_id=DOC), fuente_correo=fuente,
    )

    assert fuente.pedidos == []
    assert pipeline.peticion1.contexto_correo is None
    assert _origen(sumidero).obra.motivo == MOTIVO_SIN_CORREO
    assert len(publicador.publicados) == 1


def test_f048_r11_sin_correo_blob_no_se_pide_blob():
    pipeline, fuente = PipelineDoble(), FuenteCorreoDoble()

    _ejecutar(pipeline, _mensaje(None), fuente_correo=fuente)

    assert fuente.pedidos == []
    assert pipeline.peticion2.contexto_correo is None


def test_f048_r11_con_correo_blob_pero_sin_fuente_cableada_se_sigue_y_se_avisa(caplog):
    pipeline = PipelineDoble()

    with caplog.at_level(logging.WARNING):
        sumidero, _ = _ejecutar(pipeline, _mensaje())

    assert pipeline.peticion1.contexto_correo is None
    assert _origen(sumidero).correo_presente is False
    assert any(BLOB in r.getMessage() for r in caplog.records)


# ---------------------------------------------------------------- #
# El sello, tras construir_envelope_final.
# ---------------------------------------------------------------- #
def test_f048_r11_el_envelope_final_lleva_origen_datos_y_manda_el_correo():
    pipeline = PipelineDoble(
        papel1="1203", lectura1={"obra_codigos": ["945"], "evidencia": "Va para la 945"}, papel2="1203",
    )
    obras = ObrasDoble()

    sumidero, _ = _ejecutar(pipeline, _mensaje(), fuente_correo=FuenteCorreoDoble(), obras=obras)

    final = sumidero.guardados[-1][1]
    origen = _origen(sumidero)
    assert origen.correo_presente is True
    assert origen.correo_sha256 == CORREO.sha256
    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert origen.obra.discrepancia is True
    assert final["data"]["cabecera"]["obra_codigo"] == "0945"
    assert "lectura_correo" not in final["data"]
    assert obras.llamadas == 1


def test_f048_r11_las_fases_persistidas_quedan_como_las_devolvio_cada_ia():
    """El sello va en una copia: los envelopes de fase 1 y 2 son la
    auditoria de lo que dijo cada IA."""
    lectura = {"obra_codigos": ["945"], "evidencia": "Va para la 945"}
    pipeline = PipelineDoble(lectura1=lectura)

    sumidero, _ = _ejecutar(pipeline, _mensaje(), fuente_correo=FuenteCorreoDoble())

    fases = [fase for fase, _ in sumidero.guardados]
    assert fases == ["phase_1", "phase_2", "phase_1"]
    env1, env2 = sumidero.guardados[0][1], sumidero.guardados[1][1]
    assert env1["data"]["lectura_correo"] == lectura
    assert "origen_datos" not in env1["data"]
    assert env2["data"]["documento_revisado"]["cabecera"]["obra_codigo"] == "1203"
    assert "origen_datos" not in env2["data"]["documento_revisado"]


def test_f048_r25_el_worker_usa_la_lectura_de_fase_1_y_el_papel_de_fase_2():
    """Aviso A de extremo a extremo: IA2 cambia la cabecera (a 0945) y la
    lectura del correo (a 1203). Cuenta la lectura de IA1 (945) contra el
    papel de IA2 (0945): sin discrepancia."""
    pipeline = PipelineDoble(
        papel1="1203", lectura1={"obra_codigos": ["945"], "evidencia": "la 945"},
        papel2="0945", lectura2={"obra_codigos": ["1203"], "evidencia": "la 1203"},
    )

    sumidero, _ = _ejecutar(pipeline, _mensaje(), fuente_correo=FuenteCorreoDoble())

    origen = _origen(sumidero)
    assert origen.obra.valor_correo == "0945"
    assert origen.obra.valor_papel == "0945"
    assert origen.obra.discrepancia is False
    assert origen.evidencia == "la 945"


def test_f048_r11_sin_correo_no_se_consulta_la_lista_de_obras():
    """Aviso B: con sigrid-api caido cada consulta puede costar el timeout;
    un documento sin correo no la necesita."""
    obras = ObrasDoble()

    _ejecutar(PipelineDoble(), _mensaje(None), fuente_correo=FuenteCorreoDoble(), obras=obras)

    assert obras.llamadas == 0


def test_f048_r11_sin_lista_cableada_el_correo_cuenta_sin_validar():
    pipeline = PipelineDoble(lectura1={"obra_codigos": ["945"], "evidencia": "la 945"})

    sumidero, _ = _ejecutar(pipeline, _mensaje(), fuente_correo=FuenteCorreoDoble(), con_obras=False)

    origen = _origen(sumidero)
    assert origen.obra.validada is None
    assert sumidero.guardados[-1][1]["data"]["cabecera"]["obra_codigo"] == "945"


def test_f048_r11_el_log_del_worker_dice_el_origen_sin_texto_del_correo(caplog):
    pipeline = PipelineDoble(lectura1={"obra_codigos": ["945"], "evidencia": f"la 945 {CENTINELA}"})

    with caplog.at_level(logging.DEBUG):
        _ejecutar(pipeline, _mensaje(), fuente_correo=FuenteCorreoDoble())

    mensajes = [r.getMessage() for r in caplog.records if r.name.endswith("extraction_worker")]
    assert any("obra=correo/correo_unico" in m for m in mensajes), mensajes
    assert any(f"correo=SI({CORREO.caracteres_originales}, {CORREO.sha256[:8]})" in m for m in mensajes), mensajes
    assert not any(CENTINELA in m for m in mensajes)


# ---------------------------------------------------------------- #
# El pipeline pasa el correo al servicio.
# ---------------------------------------------------------------- #
class ServicioDoble:
    def __init__(self) -> None:
        self.kwargs1: dict = {}
        self.kwargs2: dict = {}
        self.obras_pedidas = 0

    def has_prompt(self, prompt_key):
        return True

    def extract_phase_1(self, **kwargs):
        self.kwargs1 = kwargs
        return ProviderExtractionResult(
            provider="gemini", model_name="fake", schema_name="s", prompt_key="p",
            parsed=DocumentoAlbaran(cabecera={}, lineas=[]), debug_payload={},
        )

    def review_phase_2(self, **kwargs):
        self.kwargs2 = kwargs
        return ProviderExtractionResult(
            provider="gemini", model_name="fake", schema_name="s", prompt_key="p",
            parsed=RevisionAlbaranFase2(
                review_status="ok", explicacion_global="",
                documento_revisado={"cabecera": {}, "lineas": []}, razonamientos=[],
            ),
            debug_payload={},
        )

    def obras_conocidas(self):
        self.obras_pedidas += 1
        return OBRAS


def _pipeline(servicio) -> ExtractAlbaranPipeline:
    return ExtractAlbaranPipeline(
        extraction_service=servicio, max_file_mb=10, service_version="t",
        provider_phase_1="gemini", provider_phase_2="gemini",
        prompt_key_phase_1="albaran_factura_es", prompt_key_phase_2="albaran_revision_fase2_es",
    )


@pytest.mark.parametrize("correo", [CORREO, None], ids=["con_correo", "sin_correo"])
def test_f048_r11_el_pipeline_pasa_el_correo_a_las_dos_fases_del_servicio(correo):
    servicio = ServicioDoble()
    pipeline = _pipeline(servicio)

    pipeline.run_phase_1(ExtractAlbaranRequest(
        filename="a.png", mime_type="image/png", file_bytes=b"x", contexto_correo=correo,
    ))
    pipeline.run_phase_2(ReviewAlbaranRequest(
        filename="a.png", mime_type="image/png", file_bytes=b"x", phase_1_json={}, contexto_correo=correo,
    ))

    assert servicio.kwargs1["contexto_correo"] is correo
    assert servicio.kwargs2["contexto_correo"] is correo


def test_f048_r11_las_peticiones_viejas_siguen_valiendo_sin_correo():
    assert ExtractAlbaranRequest(filename="a", mime_type="m", file_bytes=b"x").contexto_correo is None
    assert ReviewAlbaranRequest(
        filename="a", mime_type="m", file_bytes=b"x", phase_1_json={},
    ).contexto_correo is None


def test_f048_r11_el_pipeline_expone_la_lista_de_obras_del_servicio():
    servicio = ServicioDoble()

    assert _pipeline(servicio).obras_conocidas() == OBRAS
    assert servicio.obras_pedidas == 1


# ---------------------------------------------------------------- #
# main_worker.py: el cableado.
# ---------------------------------------------------------------- #
def test_f048_r11_main_worker_cablea_la_fuente_de_blob_y_la_lista_de_obras(monkeypatch, tmp_path):
    # ``composition`` arrastra los SDK de todos los proveedores (Document AI
    # incluido), que no hacen falta para ver el cableado: se sustituye.
    # Se carga con otro nombre para no dejar en ``sys.modules`` un
    # ``main_worker`` atado a la composicion sustituida.
    composicion = types.ModuleType("composition")
    composicion.build_pipeline = None
    monkeypatch.setitem(sys.modules, "interface_adapters.composition", composicion)
    spec = importlib.util.spec_from_file_location("main_worker_f048", RAIZ / "main_worker.py")
    main_worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_worker)

    capturado: dict = {}
    almacen = AlmacenDoble()
    pipeline = _pipeline(ServicioDoble())

    class _Settings:
        log_dir = str(tmp_path)
        log_level = "INFO"

    monkeypatch.setattr(main_worker, "Settings", _Settings)
    monkeypatch.setattr(main_worker, "configure_logging", lambda *a, **k: None)
    monkeypatch.setattr(main_worker, "construir_almacen_desde_entorno", lambda: almacen)
    monkeypatch.setattr(main_worker, "build_pipeline", lambda settings: pipeline)
    monkeypatch.setattr(main_worker, "construir_publicador", lambda **k: PublicadorDoble())
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **k: 0)

    def _handler(**kwargs):
        capturado.update(kwargs)
        return lambda mensaje: None

    monkeypatch.setattr(main_worker, "construir_handler_extraccion", _handler)

    assert main_worker.main() == 0
    fuente = capturado["fuente_correo"]
    assert isinstance(fuente, FuenteContextoCorreoBlob)
    assert fuente.obtener(BLOB) is None
    assert almacen.leidos == [(CONTENEDOR_INPUT, BLOB)]
    assert capturado["obras_conocidas"]() == OBRAS
