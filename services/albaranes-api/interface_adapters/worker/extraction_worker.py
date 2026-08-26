# interface_adapters/worker/extraction_worker.py
"""Handler del worker de extracción: consume q-extraccion, publica q-persistencia.

Sustituye al endpoint HTTP como entrada de sv2 en el modelo de colas. Recibe
``{document_id}``, resuelve el PDF (FuenteDocumento), ejecuta el pipeline de
extracción REAL de sv2 y publica el disparador de persistencia. El envelope se
persiste (SumideroEnvelope) para que sv3 lo recupere por document_id.

Ejecuta SIEMPRE fase 1 + fase 2 (extraccion + revision/extraccion especial).
grounding se activan cuando exista el adaptador de grounding (se mueve aquí
desde sv3); el esqueleto ya está listo.
"""
from __future__ import annotations

import logging
from typing import Callable

from application.pipelines.extract_albaran_pipeline import (
    ExtractAlbaranPipeline,
    ExtractAlbaranRequest,
    ReviewAlbaranRequest,
)
from application.services.phase_merge import construir_envelope_final
from application.services.clasificacion_resolver import (
    resolver_clasificacion,
)
from interface_adapters.worker.ports import (
    FuenteDocumento,
    GroundingCabecera,
    SumideroEnvelope,
)
from ruesma_comun.colas import (
    COLA_PERSISTENCIA,
    MensajeBase,
    MensajePersistencia,
    PublicadorColas,
)
from ruesma_comun.contratos.familias import prompt_fase2_de

logger = logging.getLogger(__name__)


def construir_handler_extraccion(
    *,
    pipeline: ExtractAlbaranPipeline,
    fuente: FuenteDocumento,
    grounding: GroundingCabecera,
    sumidero: SumideroEnvelope,
    publicador: PublicadorColas,
) -> Callable[[MensajeBase], None]:
    """Crea el handler (closure) que consume q-extraccion."""

    def handler(mensaje: MensajeBase) -> None:
        document_id = mensaje.document_id
        logger.info("[sv2-worker] document_id=%s START", document_id)

        # 1) PDF del documento (SharePoint en produccion).
        doc = fuente.obtener(document_id)

        # 2) Fase 1 — extraccion.
        env1 = pipeline.run_phase_1(
            ExtractAlbaranRequest(
                filename=doc.filename,
                mime_type=doc.mime_type,
                file_bytes=doc.file_bytes,
            )
        )
        sumidero.persistir(document_id=document_id, envelope=env1, fase="phase_1")

        # (F-043 · R12) Clasificacion de DOCUMENTO decidida por IA1. No
        # se deduce de nada: el resolver solo normaliza y sella el origen.
        clasificacion = resolver_clasificacion(env1.get("data") or {})

        # (F-043 · R15) El prompt de fase 2 sale del CATALOGO, por consulta
        # directa con la familia que dijo la IA. Antes se componia con un
        # f-string, y una familia sin prompt propio generaba una clave
        # inventada que el pipeline descartaba en silencio. `None` = "usa
        # el generico configurado", y aqui queda dicho en el log.
        prompt_fase2 = prompt_fase2_de(clasificacion.familia)
        if prompt_fase2 is None:
            logger.info(
                "[sv2-worker] document_id=%s familia=%s sin prompt propio "
                "de fase 2: cae al generico configurado",
                document_id, clasificacion.familia,
            )

        # 3) Fase 2 — revision + extraccion particular (SIEMPRE). El esquema
        #    de 4 IAs deja la extraccion especial (hormigon/residuos) en la
        #    fase 2, asi que ya no es opcional.
        ctx = grounding.contexto(
            document_id=document_id, phase_1_json=env1
        )
        env2 = pipeline.run_phase_2(
            ReviewAlbaranRequest(
                filename=doc.filename,
                mime_type=doc.mime_type,
                file_bytes=doc.file_bytes,
                phase_1_json=env1,
                sigrid_context=ctx,
                prompt_key=prompt_fase2,
            )
        )
        sumidero.persistir(
            document_id=document_id, envelope=env2, fase="phase_2"
        )

        # (F-043 · R16) IA2 ve el papel Y el JSON de fase 1: es quien mejor
        # puede decir que IA1 se equivoco de familia. Se vuelve a resolver
        # con su documento_revisado, y lo que diga prevalece (origen=ia2).
        # Limite conocido y escrito en el diseno: el prompt de fase 2 ya se
        # eligio con la clasificacion de IA1; releer con el otro prompt es
        # otra feature.
        clasificacion = resolver_clasificacion(
            env1.get("data") or {}, env2.get("data") or {},
        )

        # 4) Envelope FINAL: fusiona fase 2 y sella la clasificacion. Es el
        #    que consume sv3 (fase logica "phase_1"). La clasificacion va
        #    DENTRO de data (F-043 R9): sv3 filtra meta contra un modelo
        #    estricto y la descartaba. En meta queda solo el espejo. El
        #    detalle por linea (contexto_linea) viaja en data como siempre.
        envelope_final = construir_envelope_final(
            env_fase1=env1, env_fase2=env2,
            clasificacion=clasificacion,
        )
        sumidero.persistir(
            document_id=document_id, envelope=envelope_final, fase="phase_1"
        )

        # 5) Disparador de persistencia (el envelope ya esta guardado).
        publicador.publicar(
            COLA_PERSISTENCIA,
            MensajePersistencia(
                document_id=document_id,
                correlation_key=mensaje.correlation_key,
            ),
        )
        logger.info(
            "[sv2-worker] document_id=%s OK familia=%s origen=%s "
            "confianza=%.1f prompt_fase2=%s -> q-persistencia",
            document_id,
            clasificacion.familia,
            clasificacion.origen,
            clasificacion.confianza_pct,
            prompt_fase2 or "(generico configurado)",
        )
        # Si el handler lanza, el mensaje NO se borra: reaparece por
        # visibilidad y se reintenta (lo gestiona ConsumidorCola).
        _ = envelope_final

    return handler
