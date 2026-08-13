# evals/procesos/sv6_build.py
"""Adaptador de sv6: redes deterministas y build final del albarán valorado.

Dos papeles en un mismo módulo, a propósito:

1. **Subproceso** (`python -m evals.procesos.sv6_build`): lee un trabajo JSON
   por stdin, importa sv6 con SU raíz en `sys.path` y devuelve por stdout los
   records finales de cada caso. Es lo único que necesita a sv6 importado.
2. **Biblioteca pura** (el resto del módulo): fabrica el envelope estimulado
   desde el ground truth, proyecta los records a la forma de los libros y
   evalúa el caso. No importa nada de sv6 y por eso el runner y los tests la
   usan en su propio proceso.

Lo que el modo determinista NO evalúa: el juicio del LLM. Evalúa que las redes
de sv6 hagan cumplir las reglas aunque la IA proponga lo prohibido.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from evals.comparador import (
    campos_no_observables,
    comparar_tablas,
)
from evals.criticidad import Criticidad, cargar_criticidad
from evals.modelos import NO_COMPARAR, Discrepancia

#: Raíz del repositorio y del servicio sv6 (rutas, no imports).
RAIZ_REPO = Path(__file__).resolve().parent.parent.parent
RAIZ_SV6 = RAIZ_REPO / "services" / "albaran-valoracion-persist"

#: Valores por defecto de sv6 (`config/settings.py`), replicados aquí porque
#: instanciar sus `Settings` exigiría credenciales de BBDD que no hacen falta.
TOLERANCIA_PRECIO_PCT = 2.0
TOLERANCIA_IMPORTE_PCT = 5.0
CODIGO_PARTIDA_ALM = "ALM"

#: Del vocabulario de sv6 al de los libros (`contrato_db` 1a / `pdf` 1b).
MAPA_PRECIO_SOURCE = {
    "contract_line_match": "contrato_db",
    "both_agreed": "contrato_db",
    "pdf_inference": "pdf",
    "albaran_declared": "albaran",
    "albaran_calculated": "albaran",
    "none": None,
}

#: De la pestaña de tipología al `tipo_familia` que leen las redes de sv6.
MAPA_TIPO_FAMILIA = {
    "Hormigon": "hormigon",
    "Mortero": "mortero",
    "Residuos": "residuos",
    "Combustible": "combustible",
    "Alquiler": "alquiler_maquinaria",
    "Bombeo": "otro",
    "Generico-Suministros": "otro",
}

#: Campos que ESTA corrida puede observar en cada tabla del ground truth. Lo
#: que queda fuera no se compara y se declara en el informe: por ejemplo, obra,
#: proveedor, CIF y fecha no salen del build de sv6 —salen de la extracción—, y
#: su eval es el libro IA1, no el extremo-a-extremo.
OBSERVABLES: dict[str, tuple[str, ...]] = {
    "lineas_valoradas": (
        "num_linea",
        "match_method",
        "codigo_producto_contrato",
        "codigo_partida_final",
        "precio_unitario_final",
        "precio_source",
        "importe_calculado",
        "review_required",
    ),
    "sinteticas_esperadas": (
        "num_linea_base",
        "modifier_source",
        "rol_linea",
        "cantidad",
        "precio_unitario",
        "codigo_partida",
    ),
    "datos_generales": (
        "contrato_elegido",
        "total_valorado_esperado",
        "requiere_revision",
    ),
    "lineas": (
        "num_linea",
        "casa_con_contrato",
        "linea_contrato",
        "partida_final",
        "precio_unitario_final",
        "precio_source",
        "importe_final",
        "linea_a_revision",
    ),
    "lineas_anadidas": (
        "num_linea_base",
        "cantidad",
        "precio_unitario",
        "partida",
        "importe",
    ),
}


# --- Utilidades de lectura del ground truth ---------------------------------


def valor(fila: dict, campo: str) -> object | None:
    """Valor de una celda del fixture, con el sentinela `?` como `None`."""
    dato = fila.get(campo)
    return None if dato == NO_COMPARAR else dato


def _entero(dato: object | None) -> int | None:
    try:
        return int(float(str(dato)))
    except (TypeError, ValueError):
        return None


def _decimal(dato: object | None) -> float | None:
    try:
        return float(str(dato).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _tablas(fixture: dict, nombre: str) -> list[dict]:
    return list(fixture.get("tablas", {}).get(nombre, []))


# --- Estímulo: el envelope que sv5 habría devuelto --------------------------


def construir_envelope_estimulado(inputs: dict, ia3: dict) -> dict:
    """Fabrica el envelope de sv5 a partir del ground truth de INPUTS e IA3.

    Las sintéticas PROHIBIDAS de la TABLA 3 entran aquí como propuestas de la
    IA: es el estímulo que pone a prueba a las redes de sv6.
    """
    caso_id = str(inputs.get("caso_id", ""))
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
    id_por_codigo: dict[str, int] = {}
    for indice, fila in enumerate(_tablas(inputs, "contrato_lineas"), start=1):
        codigo_producto = valor(fila, "codigo_producto")
        lineas_contrato.append(
            {
                "contrato_line_id": indice,
                "codigo_contrato": str(valor(caso, "contrato_codigo") or ""),
                "codigo_producto": codigo_producto,
                "descripcion": valor(fila, "descripcion_recurso"),
                "unidad_medida": valor(fila, "unidad"),
                "unidad_categoria": "unknown",
                "precio_unitario": _decimal(valor(fila, "precio_unitario")),
                "codigo_partida": valor(fila, "codigo_partida"),
            }
        )
        if codigo_producto is not None:
            id_por_codigo[str(codigo_producto)] = indice

    precio_por_id = {
        linea["contrato_line_id"]: linea["precio_unitario"] for linea in lineas_contrato
    }

    lineas: list[dict] = []
    for fila in _tablas(ia3, "lineas_valoradas"):
        numero = _entero(valor(fila, "num_linea"))
        if numero is None:
            continue
        codigo_contrato_linea = valor(fila, "codigo_producto_contrato")
        contrato_line_id = id_por_codigo.get(str(codigo_contrato_linea))
        lineas.append(
            {
                "merge_line_id": numero,
                "line_kind": "from_albaran",
                "match_method": str(valor(fila, "match_method") or "no_match"),
                "matched_contrato_line_id": contrato_line_id,
                "match_confidence_pct": 100.0 if contrato_line_id else 0.0,
                "unidad_categoria_albaran": "unknown",
                "unidad_category_match": True,
                "precio_unitario_contrato_db": precio_por_id.get(contrato_line_id),
                "razon_corta": "estímulo del eval desde el ground truth de IA3",
            }
        )

    base_por_defecto = lineas_albaran[0]["merge_line_id"] if lineas_albaran else None

    for fila in _tablas(ia3, "sinteticas_esperadas"):
        padre = _entero(valor(fila, "num_linea_base")) or base_por_defecto
        fuente = str(valor(fila, "modifier_source") or "otro")
        lineas.append(
            {
                "merge_line_id": None,
                "line_kind": "synthetic_modifier",
                "parent_merge_line_id": padre,
                "modifier_source": fuente,
                "modifier_reason": "sintética esperada por el ground truth",
                "descripcion_linea": str(
                    valor(fila, "descripcion_esperada") or f"SINTÉTICA {fuente}"
                ),
                "rol_linea": valor(fila, "rol_linea"),
                "cantidad_override": (
                    _decimal(valor(fila, "cantidad"))
                    if fuente in {"tiempo_exceso", "carga_incompleta"}
                    else None
                ),
                "match_method": "no_match",
                "match_confidence_pct": 0.0,
                "unidad_categoria_albaran": "unknown",
                "unidad_category_match": True,
                "precio_unitario_pdf_inferido": _decimal(
                    valor(fila, "precio_unitario")
                ),
                "razon_corta": "sintética esperada del ground truth",
            }
        )

    for fila in _tablas(ia3, "sinteticas_prohibidas"):
        concepto = str(valor(fila, "concepto_vetado") or "SINTÉTICA PROHIBIDA")
        lineas.append(
            {
                "merge_line_id": None,
                "line_kind": "synthetic_modifier",
                "parent_merge_line_id": base_por_defecto,
                "modifier_source": "otro",
                "modifier_reason": "PROHIBIDA inyectada por el eval (TABLA 3)",
                "descripcion_linea": concepto,
                "match_method": "no_match",
                "match_confidence_pct": 0.0,
                "unidad_categoria_albaran": "unknown",
                "unidad_category_match": True,
                "razon_corta": "prohibida inyectada por el eval",
            }
        )

    return {
        "status": "ok",
        "meta": {
            "document_id": caso_id,
            "codigo_contrato": valor(caso, "contrato_codigo"),
            "fecha_albaran": condiciones.get("fecha_albaran"),
            "numero_albaran": condiciones.get("numero_albaran"),
            "primary_provider": "ground_truth",
            "providers_used": [],
            "service": "evals-determinista",
        },
        "data": {"lineas": lineas},
        "context": {
            "lineas_albaran": lineas_albaran,
            "lineas_contrato": lineas_contrato,
        },
    }


# --- Proyección de los records a la forma de los libros ---------------------


def _codigo_producto_de(envelope: dict, contrato_line_id: object) -> object | None:
    for linea in envelope.get("context", {}).get("lineas_contrato", []):
        if linea.get("contrato_line_id") == contrato_line_id:
            return linea.get("codigo_producto")
    return None


def _base(resultado: dict) -> list[dict]:
    return [
        linea
        for linea in resultado.get("lineas", [])
        if linea.get("line_kind") == "from_albaran"
    ]


def _sinteticas(resultado: dict) -> list[dict]:
    return [
        linea
        for linea in resultado.get("lineas", [])
        if linea.get("line_kind") == "synthetic_modifier"
    ]


def proyectar_ia3(resultado: dict, envelope: dict) -> dict[str, list[dict]]:
    """Traduce los records de sv6 al vocabulario del libro IA3."""
    return {
        "lineas_valoradas": [
            {
                "num_linea": linea.get("merge_line_id"),
                "match_method": linea.get("match_method"),
                "codigo_producto_contrato": _codigo_producto_de(
                    envelope, linea.get("matched_contrato_line_id")
                ),
                "codigo_partida_final": linea.get("codigo_partida_final"),
                "precio_unitario_final": linea.get("precio_unitario_final"),
                "precio_source": MAPA_PRECIO_SOURCE.get(
                    str(linea.get("precio_unitario_source"))
                ),
                "importe_calculado": linea.get("importe_calculado"),
                "review_required": linea.get("review_required"),
            }
            for linea in _base(resultado)
        ],
        "sinteticas_esperadas": [
            {
                "num_linea_base": linea.get("parent_merge_line_id"),
                "modifier_source": linea.get("modifier_source"),
                "rol_linea": linea.get("rol_linea"),
                "cantidad": linea.get("cantidad_albaran"),
                "precio_unitario": linea.get("precio_unitario_final"),
                "codigo_partida": linea.get("codigo_partida_final"),
                "descripcion_linea": linea.get("descripcion_linea"),
            }
            for linea in _sinteticas(resultado)
        ],
    }


def proyectar_final(resultado: dict, envelope: dict) -> dict[str, list[dict]]:
    """Traduce el resultado del build al vocabulario de `RESULTADO_FINAL`."""
    cabecera = resultado.get("header", {})
    return {
        "datos_generales": [
            {
                "contrato_elegido": cabecera.get("contrato_codigo"),
                "total_valorado_esperado": cabecera.get("total_valorado"),
                "requiere_revision": cabecera.get("review_required"),
            }
        ],
        "lineas": [
            {
                "num_linea": linea.get("merge_line_id"),
                "casa_con_contrato": linea.get("matched_contrato_line_id") is not None,
                "linea_contrato": _codigo_producto_de(
                    envelope, linea.get("matched_contrato_line_id")
                ),
                "partida_final": linea.get("codigo_partida_final"),
                "precio_unitario_final": linea.get("precio_unitario_final"),
                "precio_source": MAPA_PRECIO_SOURCE.get(
                    str(linea.get("precio_unitario_source"))
                ),
                "importe_final": linea.get("importe_calculado"),
                "linea_a_revision": linea.get("review_required"),
            }
            for linea in _base(resultado)
        ],
        "lineas_anadidas": [
            {
                "num_linea_base": linea.get("parent_merge_line_id"),
                "cantidad": linea.get("cantidad_albaran"),
                "precio_unitario": linea.get("precio_unitario_final"),
                "partida": linea.get("codigo_partida_final"),
                "importe": linea.get("importe_calculado"),
                "descripcion_linea": linea.get("descripcion_linea"),
            }
            for linea in _sinteticas(resultado)
        ],
    }


# --- Evaluación de un caso --------------------------------------------------


@dataclass
class EvaluacionCaso:
    """Resultado de comparar un caso construido contra su ground truth."""

    caso_id: str
    discrepancias: list[Discrepancia] = field(default_factory=list)
    no_observables: list[str] = field(default_factory=list)


def _normalizar(texto: object) -> str:
    return " ".join(str(texto or "").split()).upper()


def comprobar_prohibidas(
    ia3: dict, proyeccion: dict[str, list[dict]]
) -> list[Discrepancia]:
    """Las sintéticas de la TABLA 3 no pueden acabar en los records finales.

    Se inyectan como propuestas de la IA precisamente para ver si algo las
    para. Si salen del build, el caso es ROJO: se estarían facturando.
    """
    emitidas = proyeccion.get("sinteticas_esperadas", [])
    discrepancias: list[Discrepancia] = []

    for fila in _tablas(ia3, "sinteticas_prohibidas"):
        concepto = valor(fila, "concepto_vetado")
        if concepto is None:
            continue
        buscado = _normalizar(concepto)
        culpables = [
            linea
            for linea in emitidas
            if buscado in _normalizar(linea.get("descripcion_linea"))
            or buscado == _normalizar(linea.get("modifier_source"))
        ]
        if culpables:
            discrepancias.append(
                Discrepancia(
                    campo="sinteticas_prohibidas",
                    esperado="no debe emitirse",
                    obtenido=culpables[0].get("descripcion_linea"),
                    severidad="fallo",
                    motivo=(
                        f"sintética prohibida emitida: {concepto} "
                        f"({valor(fila, 'motivo_veto') or 'sin motivo declarado'})"
                    ),
                )
            )
    return discrepancias


def evaluar_caso_determinista(
    *,
    caso_id: str,
    envelope: dict,
    resultado: dict,
    ia3: dict | None,
    final: dict | None,
    criticidad: Criticidad | None = None,
) -> EvaluacionCaso:
    """Compara el build de sv6 contra IA3 y contra `RESULTADO_FINAL`."""
    criticidad = criticidad or cargar_criticidad()
    evaluacion = EvaluacionCaso(caso_id=caso_id)

    if ia3:
        proyeccion = proyectar_ia3(resultado, envelope)
        for tabla, claves, sobrantes in (
            ("lineas_valoradas", ("num_linea",), "aviso"),
            ("sinteticas_esperadas", ("num_linea_base", "modifier_source"), "aviso"),
        ):
            esperadas = _tablas(ia3, tabla)
            evaluacion.discrepancias.extend(
                comparar_tablas(
                    esperadas,
                    proyeccion.get(tabla, []),
                    criticidad,
                    claves=claves,
                    prefijo=f"IA3.{tabla}",
                    observables=OBSERVABLES[tabla],
                    severidad_sobrantes=sobrantes,
                )
            )
            evaluacion.no_observables.extend(
                campos_no_observables(esperadas, OBSERVABLES[tabla])
            )
        evaluacion.discrepancias.extend(comprobar_prohibidas(ia3, proyeccion))

    if final:
        proyeccion_final = proyectar_final(resultado, envelope)
        for tabla, claves, sobrantes in (
            ("datos_generales", (), "fallo"),
            ("lineas", ("num_linea",), "fallo"),
            ("lineas_anadidas", ("num_linea_base",), "fallo"),
        ):
            esperadas = _tablas(final, tabla)
            evaluacion.discrepancias.extend(
                comparar_tablas(
                    esperadas,
                    proyeccion_final.get(tabla, []),
                    criticidad,
                    claves=claves,
                    prefijo=f"FINAL.{tabla}",
                    observables=OBSERVABLES[tabla],
                    severidad_sobrantes=sobrantes,
                )
            )
            evaluacion.no_observables.extend(
                campos_no_observables(esperadas, OBSERVABLES[tabla])
            )

    evaluacion.no_observables = sorted(set(evaluacion.no_observables))
    return evaluacion


# --- Subproceso: aquí y solo aquí se importa sv6 ----------------------------


def _construir_builder():  # pragma: no cover - solo corre dentro del subproceso
    """Compone `ValuationBuilder` con las redes reales y el registro de unidades."""
    from application.services.importe_calculator import ImporteCalculator
    from application.services.partida_matcher import PartidaMatcher
    from application.services.price_reconciler import PriceReconciler
    from application.services.unit_category_guard import UnitCategoryGuard
    from application.services.unit_converter import UnitConverter
    from application.services.valuation_builder import ValuationBuilder
    from infrastructure.units.yaml_unit_registry import YamlUnitRegistry

    registro = YamlUnitRegistry(RAIZ_SV6 / "config" / "unit_registry.yaml")
    return ValuationBuilder(
        unit_category_guard=UnitCategoryGuard(unit_registry=registro),
        price_reconciler=PriceReconciler(tolerance_pct=TOLERANCIA_PRECIO_PCT),
        partida_matcher=PartidaMatcher(alm_codigo_partida=CODIGO_PARTIDA_ALM),
        unit_converter=UnitConverter(registry=registro),
        importe_calculator=ImporteCalculator(tolerance_pct=TOLERANCIA_IMPORTE_PCT),
    )


def _a_diccionario(registro: object) -> dict:  # pragma: no cover - subproceso
    from dataclasses import asdict, is_dataclass

    if is_dataclass(registro):
        return asdict(registro)  # type: ignore[arg-type]
    return dict(registro)  # pragma: no cover - los records de sv6 son dataclasses


def ejecutar_trabajo(trabajo: dict) -> dict:  # pragma: no cover - subproceso
    """Ejecuta el build de cada caso EN SECUENCIA (R17). Requiere sv6 en path."""
    from domain.models.valuation_envelope import ValuationEnvelope

    builder = _construir_builder()
    resultados = []
    for caso in trabajo.get("casos", []):
        envelope = ValuationEnvelope.model_validate(caso["envelope"])
        cabecera, lineas = builder.build(
            envelope=envelope, existing_document_already_valued=False
        )
        resultados.append(
            {
                "caso_id": caso.get("caso_id"),
                "header": _a_diccionario(cabecera),
                "lineas": [_a_diccionario(linea) for linea in lineas],
            }
        )
    return {"resultados": resultados}


def ejecutar_en_subproceso(
    trabajo: dict, interprete: str | None = None
) -> dict:
    """Lanza este mismo módulo en otro intérprete y recoge su JSON.

    sv2, sv5 y sv6 no caben en el mismo proceso: comparten los nombres de sus
    paquetes de primer nivel. El subproceso es la frontera.
    """
    proceso = subprocess.run(
        [interprete or sys.executable, "-m", "evals.procesos.sv6_build"],
        input=json.dumps(trabajo, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(RAIZ_REPO),
        check=False,
    )
    if proceso.returncode != 0:
        raise RuntimeError(
            f"el subproceso de sv6 falló con código {proceso.returncode}:\n"
            f"{proceso.stderr.strip()}"
        )
    return json.loads(proceso.stdout)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - subproceso
    """Punto de entrada del subproceso: stdin → build de sv6 → stdout."""
    del argv
    sys.path.insert(0, str(RAIZ_SV6))
    try:
        trabajo = json.loads(sys.stdin.read() or "{}")
        salida = ejecutar_trabajo(trabajo)
    except Exception as error:  # noqa: BLE001 - la frontera devuelve el motivo
        print(f"sv6_build: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(salida, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso
    raise SystemExit(main())
