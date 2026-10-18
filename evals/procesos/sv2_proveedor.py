# evals/procesos/sv2_proveedor.py
"""sv2 montado para comparar el PROVEEDOR que leen IA1 e IA2 con los YAML de la base y los de la rama.

Lo usa `evals/comparar_proveedor.py` (F-064). Como `sv2_obra`, sv2 se importa
solo dentro de las funciones: el módulo se puede importar desde los tests de
la raíz sin arrastrar `application` ni `domain`, y el comparador corre en su
propio intérprete (solo usa sv2).

Qué se monta, variante a variante:

- **rama**: el `AlbaranExtractionService` de esta rama con su
  `config/prompts.yaml` y su `config/revision_rules.yaml`.
- **base**: el MISMO código con los dos YAML de la referencia `--base` (por
  defecto `dev`), sacados con `git show`. Un YAML anterior a F-064 no lleva
  `{empresas_cliente}` y sin marcador el render no añade nada (R7), así que lo
  que recibe el LLM es lo de la base. El schema de respuesta no cambia con
  F-064 (R11), pero F-075 añade el pie a la cabecera: la variante `base` lo
  recorta (`sin_pie`, con el `RegistroSinCampo` de `sv2_obra`). Lo fija
  `tests/test_f064_comparar_proveedor_base.py` contra el código de la base.

Las dos fases, sin correo ni lista de obras ni contexto de Sigrid (como el
runner): fase 1 con el proveedor de `IA_PRIMERA_FASE` y fase 2 con el de
`IA_SEGUNDA_FASE` y el prompt de la tipología del caso.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from evals.procesos.errores import describir_error
from evals.procesos.sv2_obra import CAMPOS_SOLO_RAMA_CABECERA, RegistroSinCampo
from evals.procesos.sv2_extraccion import (
    PROMPT_FASE_1,
    RAIZ_REPO,
    RAIZ_SV2,
    prompt_de_fase_2,
)

#: Variantes que sabe montar este módulo.
VARIANTES: tuple[str, ...] = ("base", "rama")

#: Referencia de git de la que salen los YAML de la variante `base`.
BASE_POR_DEFECTO = "dev"
RUTA_PROMPTS = "services/albaranes-api/config/prompts.yaml"
RUTA_REGLAS = "services/albaranes-api/config/revision_rules.yaml"

#: Los dos YAML de una variante, con el nombre del fichero temporal de la base.
_FICHEROS = (
    ("prompts", RUTA_PROMPTS, "prompts_base.yaml"),
    ("reglas", RUTA_REGLAS, "revision_rules_base.yaml"),
)


class BaseNoDisponible(RuntimeError):
    """`git show <base>:...` no devolvió alguno de los dos YAML."""


def _con_sv2_en_path() -> None:  # pragma: no cover - lo ejerce el subproceso del test de la base
    ruta = str(RAIZ_SV2)
    if ruta not in sys.path:
        sys.path.insert(0, ruta)


# --- Los YAML de cada variante ---------------------------------------------------


def ficheros_de_base(
    directorio: Path | str, base: str = BASE_POR_DEFECTO, raiz: Path = RAIZ_REPO
) -> dict[str, Path]:
    """Escribe en `directorio` los dos YAML de `base`, tal cual, y devuelve sus rutas."""
    ficheros: dict[str, Path] = {}
    for clave, ruta, nombre in _FICHEROS:
        proceso = subprocess.run(
            ["git", "-C", str(raiz), "show", f"{base}:{ruta}"],
            capture_output=True,
            check=False,
        )
        if proceso.returncode != 0 or not proceso.stdout:
            raise BaseNoDisponible(
                f"`git show {base}:{ruta}` falló (código {proceso.returncode}): "
                f"{proceso.stderr.decode('utf-8', 'replace').strip()}"
            )
        destino = Path(directorio) / nombre
        destino.write_bytes(proceso.stdout)
        ficheros[clave] = destino
    return ficheros


def ficheros_de_rama() -> dict[str, Path]:
    """Los dos YAML de esta rama, los que carga sv2 en producción."""
    return {clave: RAIZ_REPO / ruta for clave, ruta, _nombre in _FICHEROS}


# --- Montaje del servicio y las dos fases ----------------------------------------


def montar_servicio(ficheros: dict[str, Path], especificaciones: list, *, sin_pie: bool = False):
    """El `AlbaranExtractionService` con los YAML de `ficheros`, sin obras ni correo.

    ``sin_pie`` (F-075): el schema de respuesta sin el pie de la cabecera, que
    la base de antes de F-075 no conoce (lo usa la variante `base`)."""
    if not {"prompts", "reglas"} <= set(ficheros):
        raise ValueError("faltan ficheros: hacen falta prompts y reglas")
    return _servicio(ficheros, especificaciones, sin_pie=sin_pie)


def _servicio(ficheros: dict[str, Path], especificaciones: list, *, sin_pie: bool = False):  # pragma: no cover - subproceso del test de la base
    """Importa sv2 y monta el servicio como el runner (sin `obras_activas_provider`)."""
    _con_sv2_en_path()
    from application.services.albaran_extraction_service import AlbaranExtractionService
    from application.services.schema_registry import SchemaRegistry
    from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
    from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

    return AlbaranExtractionService(
        providers=list(especificaciones),
        prompt_repo=YamlPromptRepository(ficheros["prompts"]),
        schema_registry=(
            RegistroSinCampo(SchemaRegistry(), campos=frozenset(CAMPOS_SOLO_RAMA_CABECERA))
            if sin_pie
            else SchemaRegistry()
        ),
        revision_rules_repo=RevisionRulesRepository(yaml_path=ficheros["reglas"]),
        prompt_key_phase_1=PROMPT_FASE_1,
    )


def proveedor_de(documento) -> dict:
    """`proveedor_nombre` y `proveedor_cif` de la cabecera, como `{nombre, cif}`."""
    datos = documento.model_dump() if hasattr(documento, "model_dump") else dict(documento)
    cabecera = datos.get("cabecera") or {}
    return {"nombre": cabecera.get("proveedor_nombre"), "cif": cabecera.get("proveedor_cif")}


def dos_fases(servicio, material: list, proveedores: dict[str, str], tipologia: str) -> dict:
    """IA1 y luego IA2 de un caso; el fallo de cada fase, a su resultado (sin valores).

    `proveedores` = `{"IA1": ..., "IA2": ...}`. IA2 recibe el JSON de IA1 y el
    prompt de fase 2 de la tipología, como el worker. Sin `documento_revisado`,
    IA2 vale lo de fase 1 (como `phase_merge`). Si IA1 falla, IA2 no se llama.
    """
    try:
        fase_1 = servicio.extract_phase_1(
            attachments=material, provider=proveedores["IA1"], prompt_key=PROMPT_FASE_1
        )
        documento = fase_1.parsed.model_dump()
    except Exception as error:  # noqa: BLE001 - se aísla la fase, no se oculta
        return {
            "ia1": {"error": describir_error(error, "IA1")},
            "ia2": {"error": {"fase": "IA2", "tipo": "SinFase1", "motivo": "IA1 no devolvió documento"}},
        }
    salida = {"ia1": proveedor_de(documento), "ia2": None}
    try:
        fase_2 = servicio.review_phase_2(
            attachments=material,
            provider=proveedores["IA2"],
            prompt_key=prompt_de_fase_2(tipologia),
            phase_1_json=documento,
        )
        revisado = fase_2.parsed.model_dump()
        salida["ia2"] = proveedor_de(revisado.get("documento_revisado") or documento)
    except Exception as error:  # noqa: BLE001 - se aísla la fase, no se oculta
        salida["ia2"] = {"error": describir_error(error, "IA2")}
    return salida


def montar_extractor(
    ficheros: dict[str, dict[str, Path]], proveedores: dict[str, str], entorno: dict
) -> Callable[[str, str, Path, str], dict]:  # pragma: no cover - LLM real
    """La función `extraer(variante, caso_id, ruta, tipologia)` real: las dos fases de sv2.

    El albarán se preprocesa una vez por caso con la función del pipeline de
    producción (`sv2_extraccion._adjuntos`).
    """
    del entorno
    _con_sv2_en_path()
    from evals.procesos.sv2_extraccion import _adjuntos, _especificacion

    especificaciones = [_especificacion(p) for p in dict.fromkeys(proveedores.values())]
    servicios = {
        variante: montar_servicio(rutas, especificaciones, sin_pie=variante == "base")
        for variante, rutas in ficheros.items()
    }
    material_por_ruta: dict[str, list] = {}

    def extraer(variante: str, caso_id: str, ruta: Path, tipologia: str) -> dict:
        del caso_id
        clave = str(ruta)
        if clave not in material_por_ruta:
            material_por_ruta[clave] = _adjuntos(Path(ruta))
        return dos_fases(servicios[variante], material_por_ruta[clave], proveedores, tipologia)

    return extraer
