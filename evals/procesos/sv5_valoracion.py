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

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from evals.procesos import canal
from evals.procesos.errores import avisar, describir_error
from evals.procesos.sv5_documentos import (
    CAMPOS_CABECERA,
    RUTA_CACHE,
    RUTA_INDICE,
    leer_indice,
    nombre_en_cache,
)
from evals.procesos.sv6_build import (
    _decimal,
    _entero,
    _tablas,
    clasificacion_de,
    condiciones_de,
    lineas_albaran_de,
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

#: (R33) Por qué un caso no se manda a sv5 si su documento no está en local.
MOTIVO_SIN_DOCUMENTO = "documento del contrato no disponible en local"


def documento_de(codigo: str, indice: dict, raiz: Path | str) -> dict | None:
    """(R32, R33) El documento del contrato en la caché local, comprobado.

    - Sin entrada en el índice, o con `tipo = ninguno`: `None`. IA3 valora
      sin documento, que es lo que hace producción con ese contrato.
    - Con documento en el índice y el fichero local con su `sha256`:
      `{tipo, ruta}`, que el subproceso de sv5 lee sin red.
    - Con documento en el índice y el fichero ausente o distinto (un clon
      limpio, otra importación): `{falta: motivo}`. Mejor no medir que medir
      otra cosa: el caso sale OMITIDO y no se manda a sv5.
    """
    entrada = indice.get(codigo) or {}
    tipo = entrada.get("tipo")
    if tipo not in ("md", "pdf"):
        return None
    ruta = Path(raiz) / nombre_en_cache(codigo, tipo)
    if not ruta.is_file() or hashlib.sha256(ruta.read_bytes()).hexdigest() != entrada.get("sha256"):
        return {"falta": MOTIVO_SIN_DOCUMENTO}
    return {"tipo": tipo, "ruta": str(ruta)}


def construir_contexto(
    inputs: dict, indice: dict | None = None, raiz: Path | str | None = None
) -> dict:
    """Contexto de valoración de un caso, con la forma que espera sv5.

    `indice` y `raiz` son el índice de documentos y la caché local; sin ellos,
    los versionados (`evals/fixtures/contratos/_indice.json`) y
    `evals/inputs/contratos/`.
    """
    documentos = leer_indice(RUTA_INDICE) if indice is None else indice
    raiz = RUTA_CACHE if raiz is None else raiz
    caso = (_tablas(inputs, "caso") or [{}])[0]
    codigo = str(valor(caso, "contrato_codigo") or "")
    entrada = documentos.get(codigo) or {}
    condiciones = condiciones_de(inputs)
    # (R12) Las mismas líneas que el envelope estimulado: descuento, precio
    # neto e importe derivado como el SELECT de sv5. Puede lanzar
    # `DescuentoCompuesto` (R13): el runner deja ese caso en ERROR.
    lineas_albaran = lineas_albaran_de(inputs)

    lineas_contrato = []
    for posicion, fila in enumerate(_tablas(inputs, "contrato_lineas"), start=1):
        lineas_contrato.append(
            {
                "contrato_line_id": posicion,
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
        "codigo_contrato": codigo,
        # (R17) La cabecera del contrato que sv5 lee de albaran_contratos_merge.
        **{campo: entrada.get(campo) for campo in CAMPOS_CABECERA},
        "fecha_albaran": condiciones.get("fecha_albaran"),
        "numero_albaran": condiciones.get("numero_albaran"),
        "lineas_albaran": lineas_albaran,
        "lineas_contrato": lineas_contrato,
        # (R14) La clasificación del DOCUMENTO: sv5 elige con ella el prompt.
        "clasificacion": clasificacion_de(inputs),
        "documento": documento_de(codigo, documentos, raiz),
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
            # (R14) Como `_build_envelope` de sv5: sv6 resuelve con ella la
            # familia efectiva de cada línea.
            "clasificacion": contexto.get("clasificacion"),
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


def cliente_llm(
    proveedor: str, tool_name: str, modelo: str | None, call_logger, forzar_herramienta: bool
):
    """(modelo, cliente real de comun) de un proveedor, para sv2 y para sv5.

    Con `modelo=None`, `call_logger=None` y `forzar_herramienta=True`, lo de
    siempre: el modelo del entorno (o el de `MODELOS_POR_PROVEEDOR`) y el
    cliente sin logger. El comparador de
    modelos (F-083) pide un modelo concreto, mete su medidor como `call_logger`
    y, solo para los Claude que rechazan la herramienta forzada,
    `forzar_herramienta=False`: el argumento solo llega al cliente entonces.
    """
    from ruesma_comun.llm.claude_messages_client import ClaudeMessagesVisionClient
    from ruesma_comun.llm.gemini_genai_client import GeminiGenAiVisionClient
    from ruesma_comun.llm.openai_responses_client import OpenAIResponsesVisionClient

    clave = os.environ.get(CLAVES_POR_PROVEEDOR[proveedor], "")
    variable, por_defecto = MODELOS_POR_PROVEEDOR[proveedor]
    modelo = modelo or os.environ.get(variable, por_defecto)
    extra = {} if call_logger is None else {"call_logger": call_logger}

    if proveedor == "claude":
        if not forzar_herramienta:
            extra["forzar_herramienta"] = False
        cliente = ClaudeMessagesVisionClient(api_key=clave, tool_name=tool_name, **extra)
    elif proveedor == "gemini":
        cliente = GeminiGenAiVisionClient(clave, **extra)
    else:
        cliente = OpenAIResponsesVisionClient(clave, **extra)
    return modelo, cliente


def _clientes_reales(
    proveedor: str, modelo: str | None = None, call_logger=None, forzar_herramienta: bool = True
):
    """Un `ProviderClientSpec` de sv5 con el cliente real del proveedor."""
    from application.services.valuation_extraction_service import ProviderClientSpec

    modelo, cliente = cliente_llm(
        proveedor, "emit_valuation_result", modelo, call_logger, forzar_herramienta
    )
    return ProviderClientSpec(provider=proveedor, model_name=modelo, client=cliente)


def _lineas_de_produccion(datos: dict):  # pragma: no cover - subproceso
    """(R15) Las líneas por `Raw*` + `UnitCategoryPrefilter`, como el pipeline de sv5."""
    from application.services.unit_category_prefilter import UnitCategoryPrefilter
    from domain.ports.valuation_context_repository import RawAlbaranLine, RawContratoLine

    prefiltro = UnitCategoryPrefilter()
    lineas_albaran = prefiltro.build_albaran_lines(
        RawAlbaranLine(
            merge_line_id=linea["merge_line_id"],
            line_index=linea["line_index"],
            codigo=linea.get("codigo"),
            descripcion=linea.get("descripcion"),
            unidad_medida=linea.get("unidad_medida"),
            cantidad=linea.get("cantidad"),
            precio_unitario_albaran=linea.get("precio_unitario_albaran"),
            importe_albaran=linea.get("importe_albaran"),
            codigo_partida_albaran=linea.get("codigo_partida_albaran"),
            # En producción es el JSON que sv3 guardó en el merge.
            contexto_linea_json=(
                json.dumps(linea["contexto_linea"], ensure_ascii=False)
                if linea.get("contexto_linea")
                else None
            ),
            descuento=linea.get("descuento_albaran"),
            precio_neto=linea.get("precio_neto_albaran"),
        )
        for linea in datos.get("lineas_albaran", [])
    )
    lineas_contrato = prefiltro.build_contrato_lines(
        RawContratoLine(
            contrato_line_id=linea["contrato_line_id"],
            codigo_contrato=linea.get("codigo_contrato", ""),
            codigo_producto=linea.get("codigo_producto"),
            descripcion=linea.get("descripcion"),
            unidad_medida=linea.get("unidad_medida"),
            precio_unitario=linea.get("precio_unitario"),
            codigo_partida=linea.get("codigo_partida"),
        )
        for linea in datos.get("lineas_contrato", [])
    )
    return lineas_albaran, lineas_contrato


def _contexto_de_dict(datos: dict, pdf_filename: str | None = None):  # pragma: no cover - subproceso
    """Reconstruye `ContextoValoracion` desde el diccionario del fixture."""
    from domain.models.valuation_context import ContextoValoracion
    from ruesma_comun.contratos import ClasificacionAlbaran

    lineas_albaran, lineas_contrato = _lineas_de_produccion(datos)
    clasificacion = datos.get("clasificacion")
    return ContextoValoracion(
        document_id=datos.get("document_id", ""),
        codigo_contrato=datos.get("codigo_contrato", ""),
        nombre_contrato=datos.get("nombre_contrato"),
        cif_proveedor=datos.get("cif_proveedor"),
        nombre_proveedor=datos.get("nombre_proveedor"),
        codigo_obra=datos.get("codigo_obra"),
        nombre_obra=datos.get("nombre_obra"),
        pdf_relative_path=None,
        pdf_filename=pdf_filename,
        lineas_albaran=lineas_albaran,
        lineas_contrato=lineas_contrato,
        fecha_albaran=datos.get("fecha_albaran"),
        numero_albaran=datos.get("numero_albaran"),
        clasificacion=(
            ClasificacionAlbaran.model_validate(clasificacion) if clasificacion else None
        ),
    )


def preparar_contexto(contexto: dict) -> dict:  # pragma: no cover - subproceso
    """(R15) El contexto con la `unidad_categoria` de producción en cada línea.

    Requiere sv5 en `sys.path`. Lo aplican los subprocesos de sv5 antes de
    valorar, para que el envelope que llega a sv6 lleve las mismas categorías
    que vio el LLM.
    """
    from application.services.unit_category_prefilter import UnitCategoryPrefilter

    clasificar = UnitCategoryPrefilter().classify
    return {
        **contexto,
        **{
            tabla: [
                {**linea, "unidad_categoria": clasificar(linea.get("unidad_medida"))}
                for linea in contexto.get(tabla, [])
            ]
            for tabla in ("lineas_albaran", "lineas_contrato")
        },
    }


def documento_para_ia3(documento: dict | None):  # pragma: no cover - subproceso
    """(R32) (contrato_markdown, adjunto PDF) como en `ValueAlbaranPipeline`.

    El MD va al texto, sin adjunto; el PDF, como adjunto; sin documento, ni
    uno ni otro (sv5 añade la nota de solo fase 1a). Un documento que falta no
    llega nunca hasta aquí desde el runner (R33); si llega, el caso revienta.
    """
    from domain.models.llm_attachment import LlmAttachment

    if not documento:
        return None, None
    if documento.get("falta"):
        raise RuntimeError(MOTIVO_SIN_DOCUMENTO)
    ruta = Path(documento["ruta"])
    if documento["tipo"] == "md":
        return (ruta.read_text(encoding="utf-8").strip() or None), None
    return None, LlmAttachment(
        kind="pdf", filename=ruta.name, mime_type="application/pdf", data=ruta.read_bytes()
    )


def servicios(
    especificacion, proveedor: str, prompt_key: str = "valuation_es",
    prompt_key_ia4: str = "conciliacion_es",
):  # pragma: no cover - subproceso
    """(valorar, conciliar) de sv5 con UNA especificación. Requiere sv5 en path.

    `valorar(contexto)` devuelve las líneas valoradas por IA3 y
    `conciliar(envelope, contexto)`, las conciliaciones de IA4. Los usan el
    runner y el comparador de modelos (F-083).
    """
    from application.services.conciliacion_service import ConciliacionService
    from application.services.schema_registry import SchemaRegistry
    from application.services.valuation_extraction_service import (
        ValuationExtractionService,
    )
    from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

    prompts = YamlPromptRepository(RAIZ_SV5 / "config" / "prompts.yaml")
    esquemas = SchemaRegistry()
    valoracion = ValuationExtractionService(
        providers=[especificacion],
        prompt_repo=prompts,
        schema_registry=esquemas,
        prompt_key=prompt_key,
        ia3_provider=proveedor,
    )
    conciliacion = ConciliacionService(
        providers=[especificacion],
        prompt_repo=prompts,
        schema_registry=esquemas,
        prompt_key=prompt_key_ia4,
    )

    def valorar(contexto: dict) -> list:
        contrato_markdown, adjunto = documento_para_ia3(contexto.get("documento"))
        salida = valoracion.extract(
            context=_contexto_de_dict(contexto, adjunto.filename if adjunto else None),
            pdf_attachment=adjunto,
            contrato_markdown=contrato_markdown,
        )
        return salida[proveedor].parsed.model_dump().get("lineas", [])

    def conciliar(envelope: dict, contexto: dict) -> list[dict]:
        documento = conciliacion.conciliar(
            lineas_no_casadas=lineas_no_casadas(envelope),
            lineas_contrato=contexto.get("lineas_contrato", []),
        )
        return documento.model_dump().get("conciliaciones", [])

    return valorar, conciliar


def ejecutar_trabajo(trabajo: dict, fabrica=None, preparar=None) -> dict:  # pragma: no cover - subproceso
    """IA3 + IA4 reales caso a caso, EN SECUENCIA. Requiere sv5 en path.

    `fabrica` y `preparar` son costuras: el subproceso entra por
    `valorar_casos`, que pasa `preparar_contexto` (R15). Con `modelo` en el
    trabajo, la fábrica lo recibe (R20); la salida dice qué modelo valoró (R21).
    """
    proveedor = trabajo.get("proveedor", "gemini")
    fabrica = fabrica or _clientes_reales
    modelo = trabajo.get("modelo")
    especificacion = fabrica(proveedor, modelo) if modelo else fabrica(proveedor)
    preparar = preparar or (lambda contexto: contexto)
    casos = [{**caso, "contexto": preparar(caso["contexto"])} for caso in trabajo.get("casos", [])]
    valorar, conciliar = servicios(
        especificacion,
        proveedor,
        trabajo.get("prompt_key", "valuation_es"),
        trabajo.get("prompt_key_ia4", "conciliacion_es"),
    )

    def construir_envelope(contexto: dict, lineas: list) -> dict:
        return envelope_desde(contexto, lineas, proveedor, especificacion.model_name)

    resultados = procesar_casos(
        casos,
        proveedor,
        valorar=valorar,
        construir_envelope=construir_envelope,
        conciliar=conciliar,
    )
    return {"resultados": resultados, "proveedor": proveedor, "modelo": especificacion.model_name}


def valorar_casos(trabajo: dict, fabrica=None) -> dict:  # pragma: no cover - subproceso
    """La puerta del subproceso: el trabajo con el contexto de producción (R15)."""
    return ejecutar_trabajo(trabajo, fabrica=fabrica, preparar=preparar_contexto)


def procesar_casos(
    casos: list[dict], proveedor: str, *, valorar, construir_envelope, conciliar
) -> list[dict]:
    """IA3 y luego IA4 caso a caso, cada caso AISLADO.

    El mismo agujero que tumbó la pasada del 2026-09-24 en sv2: una respuesta
    del LLM que no valida en UN caso no puede llevarse por delante los demás.
    El fallo queda en el resultado de ese caso (`error`: fase, tipo y motivo
    sin valores) y el bucle sigue. Las tres piezas llegan inyectadas para que
    los tests prueben el bucle sin sv5 ni LLM.
    """
    resultados = []
    for caso in casos:
        caso_id = caso.get("caso_id")
        contexto = caso["contexto"]
        fase = "IA3"
        try:
            envelope = construir_envelope(contexto, valorar(contexto))
            fase = "IA4"
            conciliaciones = conciliar(envelope, contexto)
            aplicar_conciliacion(envelope, conciliaciones)
        except Exception as error:  # noqa: BLE001 - se aísla el caso, no se oculta
            fallo = describir_error(error, fase)
            avisar(
                "sv5_valoracion",
                f"caso {caso_id}, proveedor {proveedor}: error en {fase} · {fallo['motivo']}",
            )
            resultados.append({"caso_id": caso_id, "error": fallo})
            continue
        avisar("sv5_valoracion", f"caso {caso_id}, proveedor {proveedor}: ok")
        resultados.append(
            {"caso_id": caso_id, "envelope": envelope, "conciliaciones": conciliaciones}
        )
    return resultados


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
    return canal.leer(proceso.stdout, "sv5")


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - subproceso
    """Punto de entrada del subproceso: stdin → IA3 + IA4 → stdout."""
    del argv
    canal.blindar_stdout()
    sys.path.insert(0, str(RAIZ_SV5))
    try:
        trabajo = json.loads(sys.stdin.read() or "{}")
        comprobar_claves([trabajo.get("proveedor", "gemini")])
        salida = valorar_casos(trabajo)
    except Exception as error:  # noqa: BLE001 - la frontera devuelve el motivo
        # Sin `str(error)`: el de pydantic arrastra la respuesta del LLM.
        avisar("sv5_valoracion", f"la corrida entera falló · {describir_error(error, '')['motivo']}")
        return 1
    canal.emitir(salida)
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
