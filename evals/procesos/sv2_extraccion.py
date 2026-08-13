# evals/procesos/sv2_extraccion.py
"""Adaptador de sv2: IA1 (extracción) e IA2 (refinado por tipología).

Composición mínima: repositorio de prompts YAML, registro de schemas, reglas de
revisión y los clientes LLM reales. No se importa `composition.py` de sv2
—arrastra los SDK de OCR de nube que ni siquiera están instalados— ni sus
`Settings`, que exigen credenciales de servicios que este eval no usa.

El material del albarán se preprocesa con la MISMA función que producción
(`ExtractAlbaranPipeline._build_attachments`): si el eval preprocesara distinto,
estaría midiendo otro sistema.

Proveedores (decisión D3): por defecto solo el primario de cada fase
(`IA_PRIMERA_FASE` / `IA_SEGUNDA_FASE`), ampliable con `--proveedores`. El
veredicto se calcula sobre los proveedores realmente invocados.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from evals.procesos.sv5_valoracion import (
    CLAVES_POR_PROVEEDOR,
    MODELOS_POR_PROVEEDOR,
    comprobar_claves,
)

RAIZ_REPO = Path(__file__).resolve().parent.parent.parent
RAIZ_SV2 = RAIZ_REPO / "services" / "albaranes-api"

#: Directorio de los albaranes de entrada (no versionados: R12).
RUTA_ALBARANES = RAIZ_REPO / "evals" / "inputs" / "albaranes"

#: Extensiones que acepta el contrato de datos para el fichero de un caso.
EXTENSIONES = (".pdf", ".jpg", ".jpeg", ".png")

#: Proveedor primario de cada fase y su variable de entorno en sv2.
PRIMARIO_POR_FASE = {
    "IA1": ("IA_PRIMERA_FASE", "gemini"),
    "IA2": ("IA_SEGUNDA_FASE", "openai"),
}

#: Prompt de cada fase; el de fase 2 se especializa por tipología, igual que
#: hace el worker de sv2 (`albaran_revision_fase2_{tipologia}`).
PROMPT_FASE_1 = "albaran_factura_es"
PROMPT_FASE_2 = "albaran_revision_fase2_es"

#: De la pestaña del libro al sufijo de prompt de fase 2 que usa sv2.
SUFIJO_TIPOLOGIA = {
    "Hormigon": "hormigon",
    "Mortero": "mortero",
    "Residuos": "residuos",
}


def proveedores_a_invocar(
    fase: str, solicitados: list[str] | None = None, entorno: dict | None = None
) -> list[str]:
    """Qué proveedores se invocan en una fase (D3): el primario, o los pedidos."""
    entorno = entorno if entorno is not None else dict(os.environ)
    if solicitados:
        return [p.strip().lower() for p in solicitados if p.strip()]
    variable, por_defecto = PRIMARIO_POR_FASE[fase]
    return [(entorno.get(variable) or por_defecto).strip().lower()]


def ruta_de_albaran(caso_id: str, directorio: Path | str = RUTA_ALBARANES) -> Path | None:
    """El fichero del caso, o `None` si no está (los albaranes no se versionan)."""
    directorio = Path(directorio)
    for extension in EXTENSIONES:
        candidato = directorio / f"{caso_id}{extension}"
        if candidato.is_file():
            return candidato
    return None


def prompt_de_fase_2(tipologia: str) -> str:
    """El mismo prompt que elegiría el worker de sv2 para esa tipología."""
    sufijo = SUFIJO_TIPOLOGIA.get(tipologia)
    return f"albaran_revision_fase2_{sufijo}" if sufijo else PROMPT_FASE_2


# --- Proyecciones al vocabulario de los libros IA1 e IA2 --------------------


def proyectar_ia1(documento: dict, caso_id: str) -> dict[str, list[dict]]:
    """Del `DocumentoAlbaran` de sv2 a las dos tablas del libro IA1."""
    cabecera = documento.get("cabecera") or {}
    return {
        "cabeceras": [
            {
                "proveedor_nombre": cabecera.get("proveedor_nombre"),
                "proveedor_cif": cabecera.get("proveedor_cif"),
                "fecha": cabecera.get("fecha"),
                "numero_albaran": cabecera.get("numero_albaran"),
                "obra_codigo": cabecera.get("obra_codigo"),
                "obra_nombre": cabecera.get("obra_nombre"),
                "forma_pago": cabecera.get("forma_pago"),
            }
        ],
        "lineas": [
            {
                "num_linea": indice,
                "descripcion_esperada": linea.get("concepto"),
                "cantidad": linea.get("cantidad"),
                "precio_unitario": linea.get("precio"),
                "importe": linea.get("precio_neto"),
                "codigo_imputacion": linea.get("codigo_imputacion"),
            }
            for indice, linea in enumerate(documento.get("lineas") or [], start=1)
        ],
    }


def proyectar_ia2(documento: dict, caso_id: str) -> dict[str, list[dict]]:
    """Del documento revisado al formato largo (caso, línea, campo) de IA2."""
    filas = []
    for indice, linea in enumerate(documento.get("lineas") or [], start=1):
        contexto = linea.get("contexto_linea") or {}
        for campo, dato in sorted(contexto.items()):
            if dato is None:
                continue
            filas.append(
                {
                    "num_linea": indice,
                    "campo_contexto": campo,
                    "valor_esperado": dato,
                }
            )
    return {"contexto": filas}


# --- Subproceso: aquí y solo aquí se importa sv2 ----------------------------


def _especificacion(proveedor: str):
    """`ProviderClientSpec` de sv2 con el cliente real del proveedor."""
    from application.services.albaran_extraction_service import ProviderClientSpec
    from ruesma_comun.llm.claude_messages_client import ClaudeMessagesVisionClient
    from ruesma_comun.llm.gemini_genai_client import GeminiGenAiVisionClient
    from ruesma_comun.llm.openai_responses_client import OpenAIResponsesVisionClient

    clave = os.environ.get(CLAVES_POR_PROVEEDOR[proveedor], "")
    variable, por_defecto = MODELOS_POR_PROVEEDOR[proveedor]
    modelo = os.environ.get(variable, por_defecto)

    if proveedor == "claude":
        cliente = ClaudeMessagesVisionClient(
            api_key=clave, tool_name="emit_albaran_extraction"
        )
    elif proveedor == "gemini":
        cliente = GeminiGenAiVisionClient(clave)
    else:
        cliente = OpenAIResponsesVisionClient(clave)
    return ProviderClientSpec(provider=proveedor, model_name=modelo, client=cliente)


def _adjuntos(ruta: Path) -> list:
    """Preprocesa el albarán exactamente como el pipeline de producción."""
    import mimetypes

    from application.pipelines.extract_albaran_pipeline import ExtractAlbaranPipeline

    mime = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"
    return ExtractAlbaranPipeline._build_attachments(
        ruta.name, mime, ruta.read_bytes()
    )


def ejecutar_trabajo(trabajo: dict, fabrica=None) -> dict:
    """IA1 e IA2 caso a caso, EN SECUENCIA. Requiere sv2 en path."""
    from application.services.albaran_extraction_service import (
        AlbaranExtractionService,
    )
    from application.services.schema_registry import SchemaRegistry
    from infrastructure.prompts.revision_rules_repository import (
        RevisionRulesRepository,
    )
    from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

    fabrica = fabrica or _especificacion
    proveedores = trabajo.get("proveedores") or ["gemini"]
    servicio = AlbaranExtractionService(
        providers=[fabrica(proveedor) for proveedor in proveedores],
        prompt_repo=YamlPromptRepository(RAIZ_SV2 / "config" / "prompts.yaml"),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(
            yaml_path=RAIZ_SV2 / "config" / "revision_rules.yaml"
        ),
        prompt_key_phase_1=PROMPT_FASE_1,
    )

    resultados = []
    for caso in trabajo.get("casos", []):
        adjuntos = _adjuntos(Path(caso["fichero"]))
        por_proveedor = {}
        for proveedor in proveedores:
            fase_1 = servicio.extract_phase_1(
                attachments=adjuntos, provider=proveedor, prompt_key=PROMPT_FASE_1
            )
            documento = fase_1.parsed.model_dump()
            fase_2 = servicio.review_phase_2(
                attachments=adjuntos,
                provider=proveedor,
                prompt_key=prompt_de_fase_2(caso.get("tipologia", "")),
                phase_1_json=documento,
            )
            revisado = fase_2.parsed.model_dump()
            por_proveedor[proveedor] = {
                "ia1": documento,
                "ia2": revisado.get("documento_revisado") or documento,
            }
        resultados.append(
            {"caso_id": caso.get("caso_id"), "proveedores": por_proveedor}
        )
    return {"resultados": resultados, "proveedores": proveedores}


def ejecutar_en_subproceso(trabajo: dict, interprete: str | None = None) -> dict:
    """Lanza este módulo en otro intérprete: sv2 no cabe con sv5 ni con sv6."""
    proceso = subprocess.run(
        [interprete or sys.executable, "-m", "evals.procesos.sv2_extraccion"],
        input=json.dumps(trabajo, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(RAIZ_REPO),
        check=False,
    )
    if proceso.returncode != 0:
        raise RuntimeError(
            f"el subproceso de sv2 falló con código {proceso.returncode}:\n"
            f"{proceso.stderr.strip()}"
        )
    return json.loads(proceso.stdout)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada del subproceso: stdin → IA1 + IA2 → stdout."""
    del argv
    sys.path.insert(0, str(RAIZ_SV2))
    try:
        trabajo = json.loads(sys.stdin.read() or "{}")
        comprobar_claves(trabajo.get("proveedores") or ["gemini"])
        salida = ejecutar_trabajo(trabajo)
    except Exception as error:  # noqa: BLE001 - la frontera devuelve el motivo
        print(f"sv2_extraccion: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(salida, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso
    raise SystemExit(main())
