# evals/procesos/sv5_valoracion.py
"""Adaptador de sv5: IA3 (valoración) e IA4 (conciliación) con LLM reales.

sv5 «recibe el contexto ya construido»: esa es la costura por la que entra el
eval. Se construye `ContextoValoracion` desde los fixtures de INPUTS, se llama
a los servicios de aplicación con clientes LLM reales y se emite el **envelope**
—el mismo que produce el pipeline en producción— para que el adaptador de sv6
lo consuma. El hand-off entre servicios es ese JSON, igual que en producción.

Sin BBDD y sin SharePoint: el contexto no se lee por SQL y los adjuntos van a
`None`, camino que los tres clientes ya soportan.

La parte pura de este módulo (construir el contexto, montar el envelope,
aplicar la conciliación) no importa nada de sv5 y se prueba en el proceso del
test. Lo que necesita sv5 vive detrás del subproceso.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from evals.procesos.sv6_build import (
    MAPA_TIPO_FAMILIA,
    _decimal,
    _entero,
    _tablas,
    valor,
)

RAIZ_REPO = Path(__file__).resolve().parent.parent.parent
RAIZ_SV5 = RAIZ_REPO / "services" / "albaran-valoracion-api"

#: Variables de entorno de las que salen las claves de cada proveedor en sv5.
CLAVES_POR_PROVEEDOR = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
}

#: Modelo por defecto de cada proveedor, con el mismo nombre de variable que
#: usa sv5 para poder cambiarlo sin tocar código.
MODELOS_POR_PROVEEDOR = {
    "openai": ("OPENAI_MODEL", "gpt-5"),
    "gemini": ("GEMINI_MODEL", "gemini-2.5-flash"),
    "claude": ("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
}


class ClavesAusentes(RuntimeError):
    """Falta alguna clave LLM: se para ANTES de consumir ningún caso (R14)."""


def comprobar_claves(proveedores: list[str], entorno: dict | None = None) -> None:
    """Falla pronto si no están las claves de los proveedores pedidos."""
    entorno = entorno if entorno is not None else dict(os.environ)
    faltan = [
        CLAVES_POR_PROVEEDOR[proveedor]
        for proveedor in proveedores
        if not (entorno.get(CLAVES_POR_PROVEEDOR.get(proveedor, ""), "") or "").strip()
    ]
    if faltan:
        raise ClavesAusentes(
            "no se puede lanzar la pasada completa: faltan en el entorno "
            + ", ".join(sorted(set(faltan)))
            + ". No se ha consumido ningún caso."
        )


# --- Parte pura: contexto, envelope y conciliación --------------------------


def construir_contexto(inputs: dict) -> dict:
    """Contexto de valoración de un caso, con la forma que espera sv5."""
    caso = (_tablas(inputs, "caso") or [{}])[0]
    tipo_familia = MAPA_TIPO_FAMILIA.get(str(inputs.get("tipologia", "")), "otro")
    condiciones = {
        str(valor(fila, "campo")): valor(fila, "valor")
        for fila in _tablas(inputs, "condiciones")
        if valor(fila, "campo") is not None
    }

    lineas_albaran = []
    for fila in _tablas(inputs, "lineas_albaran"):
        numero = _entero(valor(fila, "num_linea"))
        if numero is None:
            continue
        lineas_albaran.append(
            {
                "merge_line_id": numero,
                "line_index": numero,
                "codigo": valor(fila, "codigo_producto"),
                "descripcion": valor(fila, "descripcion"),
                "unidad_medida": valor(fila, "unidad"),
                "unidad_categoria": "unknown",
                "cantidad": _decimal(valor(fila, "cantidad")),
                "precio_unitario_albaran": _decimal(valor(fila, "precio_unitario")),
                "importe_albaran": _decimal(valor(fila, "importe")),
                "codigo_partida_albaran": valor(fila, "codigo_imputacion"),
                "contexto_linea": {
                    "tipo_familia": tipo_familia,
                    "rol_linea": "base",
                    "descripcion_extendida": valor(fila, "observaciones_albaran"),
                },
            }
        )

    lineas_contrato = []
    for indice, fila in enumerate(_tablas(inputs, "contrato_lineas"), start=1):
        lineas_contrato.append(
            {
                "contrato_line_id": indice,
                "codigo_contrato": str(valor(caso, "contrato_codigo") or ""),
                "codigo_producto": valor(fila, "codigo_producto"),
                "descripcion": valor(fila, "descripcion_recurso"),
                "unidad_medida": valor(fila, "unidad"),
                "unidad_categoria": "unknown",
                "precio_unitario": _decimal(valor(fila, "precio_unitario")),
                "codigo_partida": valor(fila, "codigo_partida"),
            }
        )

    return {
        "document_id": str(inputs.get("caso_id", "")),
        "codigo_contrato": str(valor(caso, "contrato_codigo") or ""),
        "fecha_albaran": condiciones.get("fecha_albaran"),
        "numero_albaran": condiciones.get("numero_albaran"),
        "lineas_albaran": lineas_albaran,
        "lineas_contrato": lineas_contrato,
    }


def envelope_desde(
    contexto: dict, lineas_valoradas: list[dict], proveedor: str, modelo: str | None
) -> dict:
    """Monta el envelope de sv5 (el hand-off a sv6) con lo que devolvió IA3."""
    return {
        "status": "ok",
        "meta": {
            "document_id": contexto.get("document_id"),
            "codigo_contrato": contexto.get("codigo_contrato"),
            "fecha_albaran": contexto.get("fecha_albaran"),
            "numero_albaran": contexto.get("numero_albaran"),
            "primary_provider": proveedor,
            "model": modelo,
            "providers_used": [proveedor],
            "service": "albaranes-valuation-api",
        },
        "data": {"lineas": lineas_valoradas},
        "context": {
            "lineas_albaran": contexto.get("lineas_albaran", []),
            "lineas_contrato": contexto.get("lineas_contrato", []),
        },
    }


def lineas_no_casadas(envelope: dict) -> list[dict]:
    """Las líneas que IA3 dejó sin match o sin precio: la entrada de IA4."""
    albaran = {
        linea.get("merge_line_id"): linea
        for linea in envelope.get("context", {}).get("lineas_albaran", [])
    }
    pendientes = []
    for linea in envelope.get("data", {}).get("lineas", []):
        if linea.get("line_kind") != "from_albaran":
            continue
        sin_match = linea.get("matched_contrato_line_id") is None
        sin_precio = linea.get("precio_unitario_contrato_db") is None
        if not (sin_match or sin_precio):
            continue
        contexto = albaran.get(linea.get("merge_line_id"), {})
        pendientes.append(
            {
                "line_ref": linea.get("merge_line_id"),
                "descripcion": contexto.get("descripcion") or "",
                "unidad_medida": contexto.get("unidad_medida"),
                "cantidad": contexto.get("cantidad"),
                "codigo_partida": contexto.get("codigo_partida_albaran"),
                "precio_albaran": contexto.get("precio_unitario_albaran"),
            }
        )
    return pendientes


def aplicar_conciliacion(envelope: dict, conciliaciones: list[dict]) -> int:
    """Mete en el envelope lo que resolvió IA4; devuelve cuántas líneas mutó.

    Es lo mismo que hace `conciliacion_orchestrator` en producción, sobre el
    mismo envelope y antes del build: sin esto, IA4 no tendría efecto y su
    eval no mediría nada.
    """
    por_id = {
        linea.get("merge_line_id"): linea
        for linea in envelope.get("data", {}).get("lineas", [])
    }
    mutadas = 0
    for conciliacion in conciliaciones:
        linea = por_id.get(conciliacion.get("line_ref"))
        if linea is None or conciliacion.get("matched_contrato_line_id") is None:
            continue
        linea["matched_contrato_line_id"] = conciliacion["matched_contrato_line_id"]
        linea["precio_unitario_contrato_db"] = conciliacion.get(
            "precio_unitario_contrato_db"
        )
        linea["match_method"] = conciliacion.get("match_method") or "semantic"
        linea["match_confidence_pct"] = conciliacion.get("match_confidence_pct") or 0.0
        linea["razon_corta"] = conciliacion.get("razon_corta") or "conciliada por IA4"
        mutadas += 1
    return mutadas


def proyectar_ia4(conciliaciones: list[dict], envelope: dict) -> list[dict]:
    """Traduce la salida de IA4 al vocabulario del libro IA4."""
    codigo_por_id = {
        linea.get("contrato_line_id"): linea.get("codigo_producto")
        for linea in envelope.get("context", {}).get("lineas_contrato", [])
    }
    return [
        {
            "num_linea": conciliacion.get("line_ref"),
            "concilia": conciliacion.get("matched_contrato_line_id") is not None,
            "linea_contrato_esperada": codigo_por_id.get(
                conciliacion.get("matched_contrato_line_id")
            ),
            "precio_unitario_esperado": conciliacion.get(
                "precio_unitario_contrato_db"
            ),
        }
        for conciliacion in conciliaciones
    ]


# --- Subproceso: aquí y solo aquí se importa sv5 ----------------------------


def _clientes_reales(proveedor: str):  # pragma: no cover - subproceso
    """Un `ProviderClientSpec` de sv5 con el cliente real del proveedor."""
    from application.services.valuation_extraction_service import ProviderClientSpec
    from ruesma_comun.llm.claude_messages_client import ClaudeMessagesVisionClient
    from ruesma_comun.llm.gemini_genai_client import GeminiGenAiVisionClient
    from ruesma_comun.llm.openai_responses_client import OpenAIResponsesVisionClient

    clave = os.environ.get(CLAVES_POR_PROVEEDOR[proveedor], "")
    variable, por_defecto = MODELOS_POR_PROVEEDOR[proveedor]
    modelo = os.environ.get(variable, por_defecto)

    if proveedor == "claude":
        cliente = ClaudeMessagesVisionClient(
            api_key=clave, tool_name="emit_valuation_result"
        )
    elif proveedor == "gemini":
        cliente = GeminiGenAiVisionClient(clave)
    else:
        cliente = OpenAIResponsesVisionClient(clave)
    return ProviderClientSpec(provider=proveedor, model_name=modelo, client=cliente)


def _contexto_de_dict(datos: dict):  # pragma: no cover - subproceso
    """Reconstruye `ContextoValoracion` desde el diccionario del fixture."""
    from domain.models.contexto_linea import ContextoLinea
    from domain.models.valuation_context import (
        AlbaranLineForValuation,
        ContextoValoracion,
        ContratoLineForValuation,
    )

    lineas_albaran = [
        AlbaranLineForValuation(
            merge_line_id=linea["merge_line_id"],
            line_index=linea["line_index"],
            codigo=linea.get("codigo"),
            descripcion=linea.get("descripcion"),
            unidad_medida=linea.get("unidad_medida"),
            unidad_categoria=linea.get("unidad_categoria", "unknown"),
            cantidad=linea.get("cantidad"),
            precio_unitario_albaran=linea.get("precio_unitario_albaran"),
            importe_albaran=linea.get("importe_albaran"),
            codigo_partida_albaran=linea.get("codigo_partida_albaran"),
            contexto_linea=(
                ContextoLinea.model_validate(linea["contexto_linea"])
                if linea.get("contexto_linea")
                else None
            ),
        )
        for linea in datos.get("lineas_albaran", [])
    ]
    lineas_contrato = [
        ContratoLineForValuation(
            contrato_line_id=linea["contrato_line_id"],
            codigo_contrato=linea.get("codigo_contrato", ""),
            codigo_producto=linea.get("codigo_producto"),
            descripcion=linea.get("descripcion"),
            unidad_medida=linea.get("unidad_medida"),
            unidad_categoria=linea.get("unidad_categoria", "unknown"),
            precio_unitario=linea.get("precio_unitario"),
            codigo_partida=linea.get("codigo_partida"),
        )
        for linea in datos.get("lineas_contrato", [])
    ]
    return ContextoValoracion(
        document_id=datos.get("document_id", ""),
        codigo_contrato=datos.get("codigo_contrato", ""),
        nombre_contrato=None,
        cif_proveedor=None,
        nombre_proveedor=None,
        codigo_obra=None,
        nombre_obra=None,
        pdf_relative_path=None,
        pdf_filename=None,
        lineas_albaran=lineas_albaran,
        lineas_contrato=lineas_contrato,
        fecha_albaran=datos.get("fecha_albaran"),
        numero_albaran=datos.get("numero_albaran"),
    )


def ejecutar_trabajo(trabajo: dict, fabrica=None) -> dict:  # pragma: no cover - subproceso
    """IA3 + IA4 reales caso a caso, EN SECUENCIA. Requiere sv5 en path."""
    from application.services.conciliacion_service import ConciliacionService
    from application.services.schema_registry import SchemaRegistry
    from application.services.valuation_extraction_service import (
        ValuationExtractionService,
    )
    from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

    proveedor = trabajo.get("proveedor", "gemini")
    fabrica = fabrica or _clientes_reales
    especificacion = fabrica(proveedor)

    prompts = YamlPromptRepository(RAIZ_SV5 / "config" / "prompts.yaml")
    esquemas = SchemaRegistry()
    valoracion = ValuationExtractionService(
        providers=[especificacion],
        prompt_repo=prompts,
        schema_registry=esquemas,
        prompt_key=trabajo.get("prompt_key", "valuation_es"),
        ia3_provider=proveedor,
    )
    conciliacion = ConciliacionService(
        providers=[especificacion],
        prompt_repo=prompts,
        schema_registry=esquemas,
        prompt_key=trabajo.get("prompt_key_ia4", "conciliacion_es"),
    )

    resultados = []
    for caso in trabajo.get("casos", []):
        contexto_dict = caso["contexto"]
        salida = valoracion.extract(
            context=_contexto_de_dict(contexto_dict), pdf_attachment=None
        )
        resultado = salida[proveedor]
        envelope = envelope_desde(
            contexto_dict,
            resultado.parsed.model_dump().get("lineas", []),
            proveedor,
            especificacion.model_name,
        )
        pendientes = lineas_no_casadas(envelope)
        documento = conciliacion.conciliar(
            lineas_no_casadas=pendientes,
            lineas_contrato=contexto_dict.get("lineas_contrato", []),
        )
        conciliaciones = documento.model_dump().get("conciliaciones", [])
        aplicar_conciliacion(envelope, conciliaciones)
        resultados.append(
            {
                "caso_id": caso.get("caso_id"),
                "envelope": envelope,
                "conciliaciones": conciliaciones,
            }
        )
    return {"resultados": resultados, "proveedor": proveedor}


def ejecutar_en_subproceso(trabajo: dict, interprete: str | None = None) -> dict:  # pragma: no cover - subproceso
    """Lanza este módulo en otro intérprete: sv5 no cabe con sv2 ni con sv6."""
    proceso = subprocess.run(
        [interprete or sys.executable, "-m", "evals.procesos.sv5_valoracion"],
        input=json.dumps(trabajo, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(RAIZ_REPO),
        check=False,
    )
    if proceso.returncode != 0:
        raise RuntimeError(
            f"el subproceso de sv5 falló con código {proceso.returncode}:\n"
            f"{proceso.stderr.strip()}"
        )
    return json.loads(proceso.stdout)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - subproceso
    """Punto de entrada del subproceso: stdin → IA3 + IA4 → stdout."""
    del argv
    sys.path.insert(0, str(RAIZ_SV5))
    try:
        trabajo = json.loads(sys.stdin.read() or "{}")
        comprobar_claves([trabajo.get("proveedor", "gemini")])
        salida = ejecutar_trabajo(trabajo)
    except Exception as error:  # noqa: BLE001 - la frontera devuelve el motivo
        print(f"sv5_valoracion: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(salida, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso
    raise SystemExit(main())


def conciliaciones_desde_ground_truth(ia4: dict, envelope: dict) -> list[dict]:
    """Traduce el libro IA4 a la respuesta que habría dado la IA4 real.

    Es el estímulo del modo determinista para la conciliación: se aplica al
    envelope igual que lo haría el orquestador y se mira su efecto en el build.
    """
    id_por_codigo = {
        str(linea.get("codigo_producto")): linea.get("contrato_line_id")
        for linea in envelope.get("context", {}).get("lineas_contrato", [])
        if linea.get("codigo_producto") is not None
    }
    conciliaciones = []
    for fila in _tablas(ia4, "conciliacion"):
        numero = _entero(valor(fila, "num_linea"))
        if numero is None:
            continue
        concilia = str(valor(fila, "concilia") or "").strip().upper() in {"SI", "SÍ"}
        contrato = valor(fila, "linea_contrato_esperada")
        conciliaciones.append(
            {
                "line_ref": numero,
                "matched_contrato_line_id": (
                    id_por_codigo.get(str(contrato)) if concilia else None
                ),
                "precio_unitario_contrato_db": _decimal(
                    valor(fila, "precio_unitario_esperado")
                ),
                "match_method": "semantic" if concilia else "no_match",
                "match_confidence_pct": 90.0 if concilia else 0.0,
                "razon_corta": str(valor(fila, "motivo") or "ground truth IA4"),
            }
        )
    return conciliaciones
