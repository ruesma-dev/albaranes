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
from decimal import Decimal
from pathlib import Path

from ruesma_comun.contratos.contexto_linea import ContextoLinea

from evals.comparador import (
    campos_no_observables,
    comparar_tablas,
    equivalentes,
)
from evals.criticidad import Criticidad, cargar_criticidad
from evals.modelos import ESPERA_REVISION, NO_COMPARAR, Discrepancia
from evals.procesos import canal
from evals.procesos.errores import avisar, describir_error

#: Campos del contrato compartido `ContextoLinea` — exactamente lo que el
#: pipeline real le entrega a sv6 en el bloque `contexto_linea` de cada línea
#: (sv5 lo lee de `albaran_lines_merge.contexto_linea_json` y lo vuelca al
#: envelope). El banco propaga al `contexto_linea` una CONDICIÓN del libro
#: `INPUTS` si —y solo si— su nombre está aquí: ni más (`tamano_contenedor_
#: contrato` es del caso y en producción sale del contrato, no de la línea) ni
#: menos (`volumen_m3` y `codigo_ler` son lo que hace contar contenedores).
#:
#: Se deriva del contrato, no se copia: el catálogo de campos vive en
#: `services/albaranes-comun` y dar de alta uno allí no puede exigir acordarse
#: de tocar también el banco.
CAMPOS_DE_CONTEXTO_LINEA: frozenset[str] = frozenset(ContextoLinea.model_fields)

#: Raíz del repositorio y del servicio sv6 (rutas, no imports).
RAIZ_REPO = Path(__file__).resolve().parent.parent.parent
RAIZ_SV6 = RAIZ_REPO / "services" / "albaran-valoracion-persist"

#: Valores por defecto de sv6 (`config/settings.py`), replicados aquí porque
#: instanciar sus `Settings` exigiría credenciales de BBDD que no hacen falta.
TOLERANCIA_PRECIO_PCT = 2.0
TOLERANCIA_IMPORTE_PCT = 5.0
CODIGO_PARTIDA_ALM = "ALM"
#: F-051 (R1, R4, R8, R9): almacén por línea y familias destinadas. Sin
#: ellos el banco valoraría como antes de F-051 (el constructor los trae
#: apagados). `tests/test_f051_puntos_de_composicion.py` vigila que sigan
#: iguales a los de `Settings` y que se pasen.
ALMACEN_SIN_PARTIDA = True
FAMILIAS_DESTINADAS = "hormigon,mortero,combustible,alquiler_maquinaria,residuos"

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

#: (F-084 R14) De la pestaña de tipología a la familia del DOCUMENTO del
#: catálogo de `ruesma_comun` (`contratos/familias.py`). Con ella sv5 elige el
#: prompt de producción (`valuation_residuos` para los RES) y sv6 resuelve la
#: familia efectiva. Lo que no está aquí es `generico`, que es una respuesta
#: legítima del catálogo y no un fallo.
MAPA_FAMILIA_DOCUMENTO = {
    "Residuos": "residuos",
    "Hormigon": "hormigon",
    "Mortero": "mortero",
    "Combustible": "combustible",
    "Alquiler": "alquiler_maquinaria",
}
FAMILIA_POR_DEFECTO = "generico"

#: Quién sella la clasificación del banco. En producción la decide IA1
#: (`origen = "ia1"`); aquí es el ground truth de la tipología, para aislar la
#: valoración (IA3) de la extracción (IA1).
ORIGEN_CLASIFICACION = "banco_evals"


class DescuentoCompuesto(ValueError):
    """(F-084 R13) La línea trae más de un descuento: sv5 solo admite uno."""


#: Campos que ESTA corrida puede observar en cada tabla del ground truth. Lo
#: que queda fuera no se compara y se declara en el informe: por ejemplo, obra,
#: proveedor, CIF y fecha no salen del build de sv6 —salen de la extracción—, y
#: su eval es el libro IA1, no el extremo-a-extremo.
OBSERVABLES: dict[str, tuple[str, ...]] = {
    "lineas_valoradas": (
        "num_linea",
        "match_method",
        "codigo_producto_contrato",
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


def condiciones_de(inputs: dict) -> dict:
    """Las CONDICIONES del caso, del formato largo del libro a un diccionario."""
    return {
        str(valor(fila, "campo")): valor(fila, "valor")
        for fila in _tablas(inputs, "condiciones")
        if valor(fila, "campo") is not None
    }


def contexto_linea_de(condiciones: dict, tipo_familia: str, fila: dict) -> dict:
    """El bloque `contexto_linea` de una línea, como lo recibiría sv6.

    En producción ese bloque lo rellena IA2 y llega ENTERO: sv5 lo lee de
    `albaran_lines_merge.contexto_linea_json` y lo vuelca al envelope. El banco
    lo reconstruye desde el ground truth con la misma regla: la familia y la
    descripción extendida salen de la línea, y de las CONDICIONES del caso
    entra lo que sea campo del contrato (`CAMPOS_DE_CONTEXTO_LINEA`).

    Los campos de las CONDICIONES que NO son del contrato —el número y la
    fecha del albarán, que van en `meta`, o `tamano_contenedor_contrato`, que
    en producción sale de la descripción de la línea de contrato o de IA3— se
    quedan fuera a propósito: el banco tiene que alimentar al builder con lo
    que el pipeline real le daría, ni más ni menos.
    """
    contexto = {
        "tipo_familia": tipo_familia,
        "rol_linea": "base",
        "descripcion_extendida": valor(fila, "observaciones_albaran"),
    }
    contexto.update(
        {
            campo: dato
            for campo, dato in condiciones.items()
            if campo in CAMPOS_DE_CONTEXTO_LINEA and dato is not None
        }
    )
    return contexto


# --- Líneas del albarán y clasificación: lo que sv5 lee del merge -----------


def _descuento_de(dato: object | None) -> float | None:
    """El descuento único de la línea (porcentaje), o `None` si no hay.

    El conversor guarda `descuentos` como lista cuando el libro escribe `a;b`
    y como número cuando la celda lo es. sv5 lee UNA columna `descuento` del
    merge: dos descuentos encadenados no tienen representación (R13) y el
    caso sale ERROR en vez de valorarse con uno de los dos.
    """
    if isinstance(dato, str):
        dato = [trozo for trozo in dato.split(";")]
    if isinstance(dato, (list, tuple)):
        valores = [
            trozo
            for trozo in dato
            if trozo is not None and str(trozo).strip() not in ("", "?", NO_COMPARAR)
        ]
        if len(valores) > 1:
            raise DescuentoCompuesto("descuento compuesto no representable")
        dato = valores[0] if valores else None
    return _decimal(dato)


def _importe_derivado(
    cantidad: float | None, precio: float | None, descuento: float | None
) -> float | None:
    """`cantidad × precio × (1 − descuento/100)`, en decimal y sin ruido de float.

    Es la rama 2 del `COALESCE` del `SELECT` de sv5: en PostgreSQL se calcula
    con `numeric` y 50 × 0,647 × 0,60 da 19,41 exacto, no 19,409999….
    """
    if cantidad is None or precio is None:
        return None
    factor = 1 - Decimal(str(descuento or 0)) / 100
    return float(Decimal(str(cantidad)) * Decimal(str(precio)) * factor)


def con_partidas_de_ia1(inputs: dict, ia1: dict | None) -> dict:
    """(F-084 R39) INPUTS con la partida que el libro IA1 espera de cada línea.

    En producción la partida del albarán la lee IA1 y llega a sv5 y a sv6 por
    el merge; INPUTS no la trae. Una línea sin `codigo_imputacion` recibe la
    de la línea del libro IA1 con su mismo `num_linea` y su misma descripción:
    en 21 casos los dos libros no numeran igual (FER-002: la 4 de IA1 es la 7
    de INPUTS) y el número solo no basta. INPUTS manda si la trae, y `?` o
    `REVISIÓN` del libro no son una partida. Devuelve una copia.
    """
    resultado = json.loads(json.dumps(inputs))
    del_libro = {_entero(valor(fila, "num_linea")): fila for fila in _tablas(ia1 or {}, "lineas")}
    for fila in _tablas(resultado, "lineas_albaran"):
        if fila.get("codigo_imputacion"):
            continue
        leida = del_libro.get(_entero(valor(fila, "num_linea")), {})
        partida = leida.get("codigo_imputacion")
        descripcion = valor(leida, "descripcion_esperada")
        if (
            partida
            and partida not in (NO_COMPARAR, ESPERA_REVISION)
            and descripcion is not None
            and equivalentes(descripcion, valor(fila, "descripcion"))
        ):
            fila["codigo_imputacion"] = partida
    return resultado


def lineas_albaran_de(inputs: dict) -> list[dict]:
    """(F-084 R12) Las líneas del albarán como las lee sv5 del merge.

    Una sola función para el contexto de IA3 y para el envelope estimulado, con
    la misma cascada que el `SELECT` de sv5 (`_SQL_ALBARAN_LINES`):

    - `descuento_albaran` = `descuentos` (R13: uno solo).
    - `precio_neto_albaran` = `importe`: en el merge `precio_neto` es el
      IMPORTE de la línea tras el descuento, nunca un unitario (F-019).
    - `importe_albaran` = `importe` o, si falta, la fórmula canónica.
    """
    tipo_familia = MAPA_TIPO_FAMILIA.get(str(inputs.get("tipologia", "")), "otro")
    condiciones = condiciones_de(inputs)

    lineas = []
    for fila in _tablas(inputs, "lineas_albaran"):
        numero = _entero(valor(fila, "num_linea"))
        if numero is None:
            continue
        cantidad = _decimal(valor(fila, "cantidad"))
        precio = _decimal(valor(fila, "precio_unitario"))
        importe = _decimal(valor(fila, "importe"))
        descuento = _descuento_de(valor(fila, "descuentos"))
        lineas.append(
            {
                "merge_line_id": numero,
                "line_index": numero,
                "codigo": valor(fila, "codigo_producto"),
                "descripcion": valor(fila, "descripcion"),
                "unidad_medida": valor(fila, "unidad"),
                "unidad_categoria": "unknown",
                "cantidad": cantidad,
                "precio_unitario_albaran": precio,
                "importe_albaran": (
                    importe
                    if importe is not None
                    else _importe_derivado(cantidad, precio, descuento)
                ),
                "codigo_partida_albaran": valor(fila, "codigo_imputacion"),
                "contexto_linea": contexto_linea_de(condiciones, tipo_familia, fila),
                "descuento_albaran": descuento,
                "precio_neto_albaran": importe,
            }
        )
    return lineas


def clasificacion_de(inputs: dict) -> dict:
    """(F-084 R14) La clasificación del DOCUMENTO, desde la tipología del caso.

    Con la forma de `ruesma_comun.contratos.ClasificacionAlbaran`, que es la
    que sv5 lee del merge y vuelca en el `context` del envelope.
    """
    return {
        "familia": MAPA_FAMILIA_DOCUMENTO.get(
            str(inputs.get("tipologia", "")), FAMILIA_POR_DEFECTO
        ),
        "confianza_pct": 100.0,
        "motivo": "tipología del caso en el banco de evals",
        "mixto": False,
        "familias_secundarias": [],
        "origen": ORIGEN_CLASIFICACION,
    }


# --- Estímulo: el envelope que sv5 habría devuelto --------------------------


def construir_envelope_estimulado(inputs: dict, ia3: dict) -> dict:
    """Fabrica el envelope de sv5 a partir del ground truth de INPUTS e IA3.

    Las sintéticas PROHIBIDAS de la TABLA 3 entran aquí como propuestas de la
    IA: es el estímulo que pone a prueba a las redes de sv6.
    """
    caso_id = str(inputs.get("caso_id", ""))
    caso = (_tablas(inputs, "caso") or [{}])[0]
    condiciones = condiciones_de(inputs)
    lineas_albaran = lineas_albaran_de(inputs)

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
            "clasificacion": clasificacion_de(inputs),
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
    from application.services.almacen_politica import familias_destinadas_de_csv
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
        partida_matcher=PartidaMatcher(
            alm_codigo_partida=CODIGO_PARTIDA_ALM,
            almacen_sin_partida=ALMACEN_SIN_PARTIDA,
        ),
        unit_converter=UnitConverter(registry=registro),
        importe_calculator=ImporteCalculator(tolerance_pct=TOLERANCIA_IMPORTE_PCT),
        familias_destinadas=familias_destinadas_de_csv(FAMILIAS_DESTINADAS),
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

    def construir(caso: dict) -> dict:
        envelope = ValuationEnvelope.model_validate(caso["envelope"])
        cabecera, lineas = builder.build(
            envelope=envelope, existing_document_already_valued=False
        )
        return {
            "header": _a_diccionario(cabecera),
            "lineas": [_a_diccionario(linea) for linea in lineas],
        }

    return {"resultados": procesar_casos(trabajo.get("casos", []), construir)}


def procesar_casos(casos: list[dict], construir) -> list[dict]:
    """El build de cada caso EN SECUENCIA (R17) y AISLADO.

    Un envelope que no valida en un caso —o un build que revienta— queda en el
    resultado de ESE caso (`error`: fase `build`, tipo y motivo sin valores)
    y el resto sigue: antes, uno solo tumbaba la corrida entera.
    """
    resultados = []
    for caso in casos:
        caso_id = caso.get("caso_id")
        try:
            construido = construir(caso)
        except Exception as error:  # noqa: BLE001 - se aísla el caso, no se oculta
            fallo = describir_error(error, "build")
            avisar("sv6_build", f"caso {caso_id}: error en build · {fallo['motivo']}")
            resultados.append({"caso_id": caso_id, "error": fallo})
            continue
        avisar("sv6_build", f"caso {caso_id}: ok")
        resultados.append({"caso_id": caso_id, **construido})
    return resultados


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
    return canal.leer(proceso.stdout, "sv6")


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - subproceso
    """Punto de entrada del subproceso: stdin → build de sv6 → stdout."""
    del argv
    canal.blindar_stdout()
    sys.path.insert(0, str(RAIZ_SV6))
    try:
        trabajo = json.loads(sys.stdin.read() or "{}")
        salida = ejecutar_trabajo(trabajo)
    except Exception as error:  # noqa: BLE001 - la frontera devuelve el motivo
        # Sin `str(error)`: el de pydantic arrastra los valores del envelope.
        avisar("sv6_build", f"la corrida entera falló · {describir_error(error, '')['motivo']}")
        return 1
    canal.emitir(salida)
    return 0


if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso
    raise SystemExit(main())
