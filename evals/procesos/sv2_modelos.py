# evals/procesos/sv2_modelos.py
"""Subproceso de sv2 del comparador de modelos (F-083): IA1, IA2 o la
preparación de IA1, para UN modelo.

Es el mismo camino que `sv2_extraccion` —prompt `albaran_factura_es`,
preprocesado `_build_attachments` de producción, sin correo, sin lista de
obras y sin Sigrid (R20)—, con dos diferencias:

- el `AlbaranExtractionService` lleva **una sola** `ProviderClientSpec`, la del
  modelo del bloque: dos modelos del mismo proveedor nunca chocan en el
  diccionario por proveedor del servicio;
- el cliente lleva el `MedidorDeUso` como `call_logger`, que mide tokens, coste
  y duración de cada llamada sin tocar el cliente (R8).

El trabajo llega por stdin: `fase` (`IA1`, `IA2`, `prep_IA1`), `modelo` (`id`,
`proveedor`, `herramienta_forzada`), `casos`, `presupuesto_usd`, `fecha` y,
opcional, `registros` (fichero donde el medidor deja cada llamada, por si el
proceso muere: R26). En IA2 cada caso trae `ia1`, la salida de la preparación
(R21). Responde por `canal.emitir` con `resultados` y `registros`.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

from evals.costes import cargar_tabla
from evals.procesos import canal, sv2_extraccion
from evals.procesos.errores import avisar, describir_error
from evals.procesos.medidor import MedidorDeUso, procesar
from evals.procesos.sv5_valoracion import comprobar_claves

FASES = ("IA1", "IA2", "prep_IA1")


def llamador(fase: str, servicio, adjuntos, proveedor: str):
    """La función que procesa UN caso en la fase pedida."""
    if fase not in FASES:
        raise ValueError(f"fase {fase} desconocida en sv2: {FASES}")

    def ia1(caso: dict) -> dict:
        material = adjuntos(Path(caso["fichero"]))
        resultado = servicio.extract_phase_1(
            attachments=material, provider=proveedor, prompt_key=sv2_extraccion.PROMPT_FASE_1
        )
        return {"documento": resultado.parsed.model_dump()}

    def ia2(caso: dict) -> dict:
        material = adjuntos(Path(caso["fichero"]))
        resultado = servicio.review_phase_2(
            attachments=material,
            provider=proveedor,
            prompt_key=sv2_extraccion.prompt_de_fase_2(caso.get("tipologia", "")),
            phase_1_json=caso["ia1"],
        )
        revisado = resultado.parsed.model_dump()
        # Igual que el runner: sin documento revisado, vale el de IA1.
        return {"documento": revisado.get("documento_revisado") or caso["ia1"]}

    return ia2 if fase == "IA2" else ia1


def ejecutar_trabajo(trabajo: dict, montar=None, adjuntos=None) -> dict:
    """Mide los casos del bloque. `montar` y `adjuntos` son costuras de test."""
    fase = trabajo["fase"]
    modelo = trabajo["modelo"]
    medidor = MedidorDeUso(
        "preparación" if fase.startswith("prep") else "candidato",
        cargar_tabla(),
        dt.date.fromisoformat(trabajo["fecha"]),
        fichero=trabajo.get("registros"),
    )
    # Solo los Claude que rechazan la herramienta forzada (P5 = a) van sin ella.
    forzar = modelo.get("herramienta_forzada") is not False
    servicio = (montar or _montar_servicio)(modelo["id"], modelo["proveedor"], forzar, medidor)
    llamar = llamador(fase, servicio, adjuntos or sv2_extraccion._adjuntos, modelo["proveedor"])
    resultados = procesar(
        trabajo.get("casos", []),
        llamar,
        medidor,
        trabajo["presupuesto_usd"],
        "IA2" if fase == "IA2" else "IA1",
    )
    return {"resultados": resultados, "registros": medidor.registros}


def _montar_servicio(modelo_id, proveedor, forzar, medidor):  # pragma: no cover - subproceso
    """El servicio de sv2 con UNA especificación: la del modelo del bloque."""
    from application.services.albaran_extraction_service import AlbaranExtractionService
    from application.services.schema_registry import SchemaRegistry
    from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
    from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

    raiz = sv2_extraccion.RAIZ_SV2
    return AlbaranExtractionService(
        providers=[
            sv2_extraccion._especificacion(
                proveedor, modelo=modelo_id, call_logger=medidor, forzar_herramienta=forzar
            )
        ],
        prompt_repo=YamlPromptRepository(raiz / "config" / "prompts.yaml"),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=raiz / "config" / "revision_rules.yaml"),
        prompt_key_phase_1=sv2_extraccion.PROMPT_FASE_1,
    )


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - subproceso
    """Punto de entrada del subproceso: stdin → un bloque de sv2 → stdout."""
    del argv
    canal.blindar_stdout()
    sys.path.insert(0, str(sv2_extraccion.RAIZ_SV2))
    try:
        trabajo = json.loads(sys.stdin.read() or "{}")
        comprobar_claves([trabajo["modelo"]["proveedor"]])
        salida = ejecutar_trabajo(trabajo)
    except Exception as error:  # noqa: BLE001 - la frontera devuelve el motivo
        avisar("sv2_modelos", f"el bloque entero falló · {describir_error(error, '')['motivo']}")
        return 1
    canal.emitir(salida)
    return 0


if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso
    raise SystemExit(main())
