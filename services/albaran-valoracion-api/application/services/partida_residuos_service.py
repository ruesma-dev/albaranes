# application/services/partida_residuos_service.py
"""(F-111 R31–R33) La IA elige la partida de residuos entre las candidatas.

Como :class:`~application.services.conciliacion_service.ConciliacionService`:
UNA llamada por documento al primer proveedor de IA4 (``seleccionar_ia4``) con
el prompt ``partida_residuos_es``. La respuesta se VALIDA aquí: cada línea de
entrada recibe exactamente una elección, en el orden de entrada, y un código
que no es de una candidata vale ``null`` (la IA no puede colar una partida que
no sea del capítulo de residuos de la obra). sv5 no lee BBDD en este paso.
"""
from __future__ import annotations

import json
import logging
from typing import Any, List, Sequence

from application.services.valuation_extraction_service import ProviderClientSpec
from domain.models.partida_residuos_models import (
    DocumentoPartidaResiduos,
    EleccionPartida,
)

logger = logging.getLogger(__name__)

#: Razón de una línea para la que la IA no devolvió elección.
RAZON_SIN_RESPUESTA = "sin_respuesta_de_la_ia"
#: Prefijo de la razón cuando la IA devolvió un código que no es candidata.
PREFIJO_FUERA_DE_CANDIDATAS = "codigo_fuera_de_candidatas:"


class SinProveedorIA(RuntimeError):
    """No hay proveedor de IA configurado (el endpoint responde 503)."""


class PartidaResiduosService:
    def __init__(
        self,
        *,
        providers: Sequence[ProviderClientSpec],
        prompt_repo: Any,
        schema_registry: Any,
        prompt_key: str = "partida_residuos_es",
    ) -> None:
        self._providers = list(providers)
        self._prompts = prompt_repo
        self._schemas = schema_registry
        self._prompt_key = prompt_key

    def elegir(
        self,
        *,
        lineas: List[dict],
        candidatas: List[dict],
    ) -> DocumentoPartidaResiduos:
        """Una elección por línea, validada contra las candidatas."""
        if not lineas:
            return DocumentoPartidaResiduos(elecciones=[])
        if not self._providers:
            raise SinProveedorIA("sin proveedor de IA para elegir la partida de residuos")

        spec = self._prompts.get(self._prompt_key)
        response_model = self._schemas.get(spec.schema)
        provider = self._providers[0]
        logger.info(
            "[partida-residuos] proveedor=%s model=%s lineas=%s candidatas=%s",
            provider.provider, provider.model_name, len(lineas), len(candidatas),
        )
        parsed = provider.client.extract_document(
            model=provider.model_name,
            instructions=spec.system,
            user_text=self._texto(spec.task, spec.schema_hint, lineas, candidatas),
            attachment=None,
            response_model=response_model,
        )
        if not isinstance(parsed, DocumentoPartidaResiduos):
            parsed = DocumentoPartidaResiduos.model_validate(parsed.model_dump())
        return self._validar(parsed, lineas, candidatas)

    @staticmethod
    def _validar(
        parsed: DocumentoPartidaResiduos,
        lineas: List[dict],
        candidatas: List[dict],
    ) -> DocumentoPartidaResiduos:
        codigos = {str(c["codigo"]).strip() for c in candidatas}
        por_ref: dict[int, EleccionPartida] = {}
        for eleccion in parsed.elecciones:
            por_ref.setdefault(eleccion.line_ref, eleccion)
        salida: list[EleccionPartida] = []
        for linea in lineas:
            ref = linea["line_ref"]
            eleccion = por_ref.get(ref)
            if eleccion is None:
                salida.append(EleccionPartida(line_ref=ref, razon_corta=RAZON_SIN_RESPUESTA))
                continue
            codigo = eleccion.codigo.strip() if eleccion.codigo else None
            if codigo is not None and codigo not in codigos:
                salida.append(
                    EleccionPartida(
                        line_ref=ref,
                        razon_corta=f"{PREFIJO_FUERA_DE_CANDIDATAS}{codigo}",
                    )
                )
                continue
            salida.append(
                EleccionPartida(
                    line_ref=ref,
                    codigo=codigo,
                    confianza_pct=eleccion.confianza_pct,
                    razon_corta=eleccion.razon_corta,
                )
            )
        logger.info(
            "[partida-residuos] elecciones=%s",
            [(e.line_ref, e.codigo) for e in salida],
        )
        return DocumentoPartidaResiduos(elecciones=salida)

    @staticmethod
    def _texto(task: str, schema_hint: str, lineas: List[dict], candidatas: List[dict]) -> str:
        return (
            f"{task}\n\n{schema_hint}\n\n"
            "## LINEAS DE RESIDUOS SIN PARTIDA\n\n"
            f"```json\n{json.dumps(lineas, ensure_ascii=False, indent=2)}\n```\n\n"
            "## CANDIDATAS (hojas del capitulo de gestion de residuos de la obra)\n\n"
            f"```json\n{json.dumps(candidatas, ensure_ascii=False, indent=2)}\n```\n"
        )
