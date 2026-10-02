# evals/procesos/sv2_obra.py
"""sv2 montado para comparar la OBRA que lee IA1 con el prompt de `dev` y el de la rama.

Lo usa `evals/comparar_obra.py`. Aquí, y solo aquí, se importa sv2 para esa
comparación, y siempre dentro de las funciones: el módulo se puede importar
desde los tests de la raíz sin arrastrar `application` ni `domain`.

A diferencia de `sv2_extraccion`, esto no va en un subproceso aparte: el
comparador solo usa sv2, así que su propio proceso ya es el intérprete
dedicado que piden los paquetes de primer nivel de los servicios
(`evals/procesos/__init__.py`).

Qué se monta, variante a variante:

- **rama**: el `AlbaranExtractionService` de esta rama con su
  `config/prompts.yaml`, sin correo. El marcador `{contexto_correo}` recibe la
  nota fija de «sin correo», que es lo que ve IA1 en producción cuando el
  albarán no trae correo.
- **dev**: el MISMO código de la rama con el `prompts.yaml` de la BASE (sacado
  con `git show <base>:...`; la base es la rama `dev` salvo que se pida otra
  referencia con `base`) y el schema de respuesta SIN `lectura_correo`. El
  YAML de una base anterior a F-048 no lleva `{contexto_correo}` y sin correo
  el render no añade nada (decisión 2 del bloque C1). El schema hace falta
  recortarlo porque los clientes mandan el JSON Schema del modelo al
  proveedor (`response_json_schema` en gemini): con el de la rama, la
  variante `dev` pediría un campo que esa base no conoce. Con los dos
  recortes, lo que recibe el LLM es byte a byte lo que manda la base; lo fija
  `tests/test_f048_comparar_obra_prompt_dev.py` contra el código de
  `1807e83`, el `dev` de antes de F-048. Desde que F-048 entró en `dev`, la
  rama `dev` ya lleva el prompt nuevo: para medir el antes y el después hay
  que pasar esa referencia como base.

Las dos variantes comparten la MISMA lista de obras activas, consultada una
sola vez a sigrid-api (solo lectura) y congelada en `ObrasFijas`.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from evals.procesos.sv2_extraccion import PROMPT_FASE_1, RAIZ_REPO, RAIZ_SV2

#: Variantes que sabe montar este módulo.
VARIANTES: tuple[str, ...] = ("dev", "rama")

#: Referencia de git de la que sale el prompt de la variante `dev` si no se
#: pide otra, y ruta del YAML de prompts dentro del repositorio.
BASE_POR_DEFECTO = "dev"
RUTA_PROMPTS = "services/albaranes-api/config/prompts.yaml"

#: Campo que la rama añade al schema de fase 1 y que `dev` no conoce.
CAMPO_SOLO_RAMA = "lectura_correo"

#: Variables de sigrid-api que lee sv2 (`config/settings.py`), con sus
#: valores por defecto. Las tres primeras son obligatorias.
VARIABLES_SIGRID_OBLIGATORIAS = (
    "SIGRID_API_BASE_URL",
    "SIGRID_API_FUNCTION_KEY",
    "SIGRID_API_DATABASE",
)
TIMEOUT_SIGRID = ("SIGRID_API_TIMEOUT_S", 30.0)
COD_MIN_OBRAS = ("OBRAS_ACTIVAS_COD_MIN", 450)
MAX_OBRAS = ("OBRAS_ACTIVAS_MAX", 300)


class PromptDevNoDisponible(RuntimeError):
    """`git show <base>:...` no devolvió el YAML de prompts."""


def _con_sv2_en_path() -> None:
    """Pone sv2 al principio de `sys.path` (una vez)."""
    ruta = str(RAIZ_SV2)
    if ruta not in sys.path:
        sys.path.insert(0, ruta)


# --- Prompt de dev -----------------------------------------------------------


def prompt_de_dev(
    directorio: Path | str, raiz: Path = RAIZ_REPO, base: str = BASE_POR_DEFECTO
) -> Path:
    """Escribe en `directorio` el `prompts.yaml` de `base`, tal cual, y devuelve su ruta."""
    proceso = subprocess.run(
        ["git", "-C", str(raiz), "show", f"{base}:{RUTA_PROMPTS}"],
        capture_output=True,
        check=False,
    )
    if proceso.returncode != 0 or not proceso.stdout:
        raise PromptDevNoDisponible(
            f"`git show {base}:{RUTA_PROMPTS}` falló (código {proceso.returncode}): "
            f"{proceso.stderr.decode('utf-8', 'replace').strip()}"
        )
    destino = Path(directorio) / "prompts_dev.yaml"
    destino.write_bytes(proceso.stdout)
    return destino


def prompt_de_rama() -> Path:
    """El `prompts.yaml` de esta rama, el que carga sv2 en producción."""
    return RAIZ_SV2 / "config" / "prompts.yaml"


# --- Obras activas: una consulta, congelada ----------------------------------


class ObrasFijas:
    """Proveedor de obras que devuelve SIEMPRE la misma lista ya consultada.

    Cumple el puerto `ObrasActivasProvider` de sv2. Así las dos variantes y
    todas las repeticiones ven exactamente la misma lista, y sigrid-api se
    consulta una sola vez por corrida.
    """

    def __init__(self, activas: list, todas: list | None = None) -> None:
        self._activas = list(activas)
        self._todas = list(todas) if todas is not None else None

    def obtener(self) -> list:
        return list(self._activas)

    def obtener_todas(self) -> list | None:
        return list(self._todas) if self._todas is not None else None


def faltan_variables_sigrid(entorno: dict) -> list[str]:
    """Las variables obligatorias de sigrid-api que no están (vacías cuentan como ausentes)."""
    return [v for v in VARIABLES_SIGRID_OBLIGATORIAS if not (entorno.get(v) or "").strip()]


def consultar_obras(entorno: dict) -> list | None:  # pragma: no cover - red real
    """Las obras ACTIVAS de Sigrid vía sigrid-api, con el cliente y el corte de producción.

    `None` si sigrid-api no está disponible (sin variables, error de red o
    lista vacía): el cliente de sv2 es best-effort y se traga el error, así
    que quien llama tiene que parar él.
    """
    if faltan_variables_sigrid(entorno):
        return None
    _con_sv2_en_path()
    from infrastructure.sigrid.sigrid_api_obras_client import SigridApiObrasClient

    cliente = SigridApiObrasClient(
        base_url=entorno["SIGRID_API_BASE_URL"],
        function_key=entorno["SIGRID_API_FUNCTION_KEY"],
        database=entorno["SIGRID_API_DATABASE"],
        timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[1]),
        cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[1]),
    )
    catalogo = cliente.obtener_catalogo()
    if catalogo is None or not catalogo.activas:
        return None
    return list(catalogo.activas)


# --- Montaje del servicio ----------------------------------------------------


def modelo_sin_campo(modelo, campo: str = CAMPO_SOLO_RAMA):
    """El mismo modelo pydantic sin `campo`: mismo nombre, base, orden y campos."""
    from pydantic import create_model

    if campo not in modelo.model_fields:
        return modelo
    campos = {
        nombre: (info.annotation, info)
        for nombre, info in modelo.model_fields.items()
        if nombre != campo
    }
    return create_model(
        modelo.__name__,
        __base__=modelo.__base__,
        __module__=modelo.__module__,
        **campos,
    )


class RegistroSinCampo:
    """`SchemaRegistry` que sirve los modelos sin el campo que solo conoce la rama."""

    def __init__(self, base, campo: str = CAMPO_SOLO_RAMA) -> None:
        self._base = base
        self._campo = campo
        self._cache: dict[str, object] = {}

    def get(self, nombre: str):
        if nombre not in self._cache:
            self._cache[nombre] = modelo_sin_campo(self._base.get(nombre), self._campo)
        return self._cache[nombre]


def montar_servicio(
    variante: str,
    ruta_prompts: Path | str,
    especificacion,
    obras_provider,
    obras_max: int = MAX_OBRAS[1],
):
    """El `AlbaranExtractionService` de la variante, con la lista de obras de producción."""
    if variante not in VARIANTES:
        raise ValueError(f"variante desconocida: {variante!r} (valen {', '.join(VARIANTES)})")
    _con_sv2_en_path()
    from application.services.albaran_extraction_service import AlbaranExtractionService
    from application.services.schema_registry import SchemaRegistry
    from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
    from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

    registro = SchemaRegistry()
    if variante == "dev":
        registro = RegistroSinCampo(registro)
    return AlbaranExtractionService(
        providers=[especificacion],
        prompt_repo=YamlPromptRepository(ruta_prompts),
        schema_registry=registro,
        revision_rules_repo=RevisionRulesRepository(
            yaml_path=RAIZ_SV2 / "config" / "revision_rules.yaml"
        ),
        prompt_key_phase_1=PROMPT_FASE_1,
        obras_activas_provider=obras_provider,
        obras_activas_max=obras_max,
    )


def obra_de(documento) -> dict:
    """`obra_codigo` y `obra_nombre` de la cabecera de un `DocumentoAlbaran`."""
    datos = documento.model_dump() if hasattr(documento, "model_dump") else dict(documento)
    cabecera = datos.get("cabecera") or {}
    return {
        "obra_codigo": cabecera.get("obra_codigo"),
        "obra_nombre": cabecera.get("obra_nombre"),
    }


def montar_extractor(
    prompts: dict[str, Path], obras: list, proveedor: str, entorno: dict
) -> Callable[[str, str, Path], dict]:  # pragma: no cover - LLM real
    """La función `extraer(variante, caso_id, ruta)` real: fase 1 de sv2, solo la obra.

    El albarán se preprocesa una vez por caso, con la misma función que el
    pipeline de producción (`sv2_extraccion._adjuntos`).
    """
    from evals.procesos.sv2_extraccion import _adjuntos, _especificacion

    _con_sv2_en_path()
    especificacion = _especificacion(proveedor)
    proveedor_obras = ObrasFijas(obras)
    obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[1])
    servicios = {
        variante: montar_servicio(variante, ruta, especificacion, proveedor_obras, obras_max)
        for variante, ruta in prompts.items()
    }
    material_por_ruta: dict[str, list] = {}

    def extraer(variante: str, caso_id: str, ruta: Path) -> dict:
        clave = str(ruta)
        if clave not in material_por_ruta:
            material_por_ruta[clave] = _adjuntos(Path(ruta))
        resultado = servicios[variante].extract_phase_1(
            attachments=material_por_ruta[clave],
            provider=proveedor,
            prompt_key=PROMPT_FASE_1,
        )
        return obra_de(resultado.parsed)

    return extraer
