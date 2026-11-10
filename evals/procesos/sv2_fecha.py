# evals/procesos/sv2_fecha.py
"""sv2 montado para comparar la FECHA que leen IA1 e IA2 con la referencia de recepción (F-112).

Lo usa `evals/comparar_fecha.py`. Como `sv2_proveedor`, sv2 se importa solo
dentro de las funciones: el módulo se importa desde los tests de la raíz sin
arrastrar `application` ni `domain`.

Las variantes son las de `sv2_proveedor` (mismos `ficheros_de_base`,
`ficheros_de_rama` y `montar_servicio`): **rama** con los YAML de esta rama y
**base** con los de `--base` (por defecto `dev`), con el MISMO código. Un YAML
de la base sin `{fecha_recepcion}` ni `{revision_fecha}` no recibe nada (R8):
lo que lee el LLM es el prompt de hoy, byte a byte. F-112 no cambia el schema
de respuesta, así que las dos variantes usan el mismo (`sin_pie=False`): la
base de F-112 ya trae el pie de F-075.

Las dos fases, con la referencia del juego, sin correo, sin lista de obras y
sin contexto de Sigrid (R20).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

from evals.procesos.errores import describir_error
from evals.procesos.sv2_extraccion import PROMPT_FASE_1, prompt_de_fase_2
from evals.procesos.sv2_proveedor import (
    BASE_POR_DEFECTO,
    VARIANTES,
    BaseNoDisponible,
    ficheros_de_base,
    ficheros_de_rama,
    montar_servicio,
)

__all__ = [
    "BASE_POR_DEFECTO",
    "VARIANTES",
    "BaseNoDisponible",
    "dos_fases",
    "fecha_de",
    "ficheros_de_base",
    "ficheros_de_rama",
    "montar_extractor",
]


def fecha_de(documento) -> dict:
    """`cabecera.fecha` del documento, como `{fecha}` (texto o `None`, tal cual)."""
    datos = documento.model_dump() if hasattr(documento, "model_dump") else dict(documento or {})
    cabecera = datos.get("cabecera") or {}
    fecha = cabecera.get("fecha")
    return {"fecha": None if fecha is None else str(fecha)}


def dos_fases(
    servicio, material: list, proveedores: dict[str, str], tipologia: str, referencia: date | None
) -> dict:
    """IA1 y luego IA2 con la misma referencia; el fallo de cada fase, a su resultado.

    `proveedores` = `{"IA1": ..., "IA2": ...}`. IA2 recibe el JSON de IA1 y el
    prompt de fase 2 de la tipología, como el worker. Sin `documento_revisado`,
    IA2 vale lo de fase 1 (como `phase_merge`). Si IA1 falla, IA2 no se llama.
    """
    try:
        fase_1 = servicio.extract_phase_1(
            attachments=material,
            provider=proveedores["IA1"],
            prompt_key=PROMPT_FASE_1,
            fecha_recepcion=referencia,
        )
        documento = fase_1.parsed.model_dump()
    except Exception as error:  # noqa: BLE001 - se aísla la fase, no se oculta
        return {
            "ia1": {"error": describir_error(error, "IA1")},
            "ia2": {"error": {"fase": "IA2", "tipo": "SinFase1", "motivo": "IA1 no devolvió documento"}},
        }
    salida = {"ia1": fecha_de(documento), "ia2": None}
    try:
        fase_2 = servicio.review_phase_2(
            attachments=material,
            provider=proveedores["IA2"],
            prompt_key=prompt_de_fase_2(tipologia),
            phase_1_json=documento,
            fecha_recepcion=referencia,
        )
        revisado = fase_2.parsed.model_dump()
        salida["ia2"] = fecha_de(revisado.get("documento_revisado") or documento)
    except Exception as error:  # noqa: BLE001 - se aísla la fase, no se oculta
        salida["ia2"] = {"error": describir_error(error, "IA2")}
    return salida


def montar_extractor(
    ficheros: dict[str, dict[str, Path]], proveedores: dict[str, str], entorno: dict
) -> Callable[[str, str, Path, str, date], dict]:  # pragma: no cover - LLM real
    """La función `extraer(variante, caso_id, ruta, tipologia, referencia)` real.

    El albarán se preprocesa una vez por fichero con la función del pipeline
    de producción (`sv2_extraccion._adjuntos`).
    """
    del entorno
    from evals.procesos.sv2_extraccion import _adjuntos, _especificacion
    from evals.procesos.sv2_proveedor import _con_sv2_en_path

    _con_sv2_en_path()
    especificaciones = [_especificacion(p) for p in dict.fromkeys(proveedores.values())]
    servicios = {
        variante: montar_servicio(rutas, especificaciones, sin_pie=False)
        for variante, rutas in ficheros.items()
    }
    material_por_ruta: dict[str, list] = {}

    def extraer(variante: str, caso_id: str, ruta: Path, tipologia: str, referencia: date) -> dict:
        del caso_id
        clave = str(ruta)
        if clave not in material_por_ruta:
            material_por_ruta[clave] = _adjuntos(Path(ruta))
        return dos_fases(servicios[variante], material_por_ruta[clave], proveedores, tipologia, referencia)

    return extraer
