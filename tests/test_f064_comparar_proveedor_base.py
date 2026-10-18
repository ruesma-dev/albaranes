# tests/test_f064_comparar_proveedor_base.py
"""F-064 · R15: la variante `base` del comparador del proveedor le manda al LLM lo mismo que su base.

`evals/comparar_proveedor.py` no ejecuta el código de la base: monta el
servicio de ESTA rama con los dos YAML de la base (`prompts.yaml` y
`revision_rules.yaml`, sacados con `git show`). Eso solo mide los prompts de la
base si lo que recibe el LLM es idéntico a lo que manda la base de verdad: el
YAML de la base no lleva `{empresas_cliente}` y, sin marcador, la rama no
añade nada (R7). Aquí se comprueba byte a byte contra el código de la base,
extraído con `git archive` a un temporal y ejecutado en su propio intérprete
(sv2 y `ruesma_comun` de la base, no los de la rama), en IA1 y en IA2.

La base es `BASE`, el `dev` de antes de F-064 (inmutable), y no la rama `dev`,
que se mueve. Cliente LLM de mentira: ni red ni LLM.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

RAIZ_REPO = Path(__file__).resolve().parent.parent

MARCA = "<<<CAPTURA-F064>>>"

#: `dev` de antes de F-064.
BASE = "544113b"

RUTAS_BASE = (
    "services/albaranes-api/application",
    "services/albaranes-api/domain",
    "services/albaranes-api/infrastructure",
    "services/albaranes-api/config",
    "services/albaranes-comun/ruesma_comun",
)

#: Prompts de fase 2 que se capturan: el genérico y uno de familia.
CLAVES_FASE_2 = ("albaran_revision_fase2_es", "albaran_revision_fase2_hormigon")

_COMUN = f"""
import json, sys

CAPTURA = {{}}
FASE_1 = {{"cabecera": {{"proveedor_nombre": "CNES. DEMO", "proveedor_cif": "A81873903"}}, "lineas": []}}

class ClienteQueCaptura:
    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        CAPTURA["instructions"] = instructions
        CAPTURA["user_text"] = user_text
        CAPTURA["schema"] = response_model.model_json_schema()
        if "review_status" in response_model.model_fields:
            return response_model.model_validate(
                {{"review_status": "ok", "documento_revisado": FASE_1, "razonamientos": []}}
            )
        return response_model.model_validate(FASE_1)

def capturar(servicio):
    salida = {{}}
    CAPTURA.clear()
    servicio.extract_phase_1(attachments=[], provider="gemini", prompt_key="albaran_factura_es")
    salida["IA1"] = dict(CAPTURA)
    for clave in {CLAVES_FASE_2!r}:
        CAPTURA.clear()
        servicio.review_phase_2(attachments=[], provider="gemini", prompt_key=clave, phase_1_json=FASE_1)
        salida[clave] = dict(CAPTURA)
    return salida
"""

_SCRIPT_BASE = _COMUN + """
arbol = sys.argv[1]
sys.path[:0] = [arbol + "/services/albaranes-api", arbol + "/services/albaranes-comun"]
import ruesma_comun
import application.services.albaran_extraction_service as modulo
from application.services.albaran_extraction_service import AlbaranExtractionService, ProviderClientSpec
from application.services.schema_registry import SchemaRegistry
from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

sv2 = arbol + "/services/albaranes-api"
servicio = AlbaranExtractionService(
    providers=[ProviderClientSpec(provider="gemini", model_name="m", client=ClienteQueCaptura())],
    prompt_repo=YamlPromptRepository(sv2 + "/config/prompts.yaml"),
    schema_registry=SchemaRegistry(),
    revision_rules_repo=RevisionRulesRepository(yaml_path=sv2 + "/config/revision_rules.yaml"),
    prompt_key_phase_1="albaran_factura_es",
)
salida = {"base": capturar(servicio), "comun": ruesma_comun.__file__, "servicio": modulo.__file__}
print("__MARCA__" + json.dumps(salida, ensure_ascii=False))
""".replace("__MARCA__", MARCA)

#: Lado rama: el montaje REAL del comparador, variante `base` y variante `rama`.
_SCRIPT_RAMA = _COMUN + """
raiz, temporal, base = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, raiz)
from evals.procesos import sv2_proveedor
sv2_proveedor._con_sv2_en_path()
from application.services.albaran_extraction_service import ProviderClientSpec

spec = ProviderClientSpec(provider="gemini", model_name="m", client=ClienteQueCaptura())
ficheros = {"base": sv2_proveedor.ficheros_de_base(temporal, base=base), "rama": sv2_proveedor.ficheros_de_rama()}
salida = {v: capturar(sv2_proveedor.montar_servicio(f, [spec])) for v, f in ficheros.items()}
print("__MARCA__" + json.dumps(salida, ensure_ascii=False))
""".replace("__MARCA__", MARCA)


def _arbol_base(destino: Path) -> Path:
    proceso = subprocess.run(
        ["git", "-C", str(RAIZ_REPO), "archive", "--format=tar", BASE, *RUTAS_BASE],
        capture_output=True,
        check=False,
    )
    if proceso.returncode != 0:
        pytest.fail(f"git archive {BASE} falló: {proceso.stderr.decode('utf-8', 'replace')}")
    with tarfile.open(fileobj=io.BytesIO(proceso.stdout)) as tar:
        tar.extractall(destino, filter="data")
    return destino


def _ejecutar(script: str, *argumentos: str) -> dict:
    proceso = subprocess.run(
        [sys.executable, "-c", script, *argumentos],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(RAIZ_REPO),
        check=False,
    )
    assert proceso.returncode == 0, proceso.stderr[-3000:]
    lineas = [linea for linea in proceso.stdout.splitlines() if linea.startswith(MARCA)]
    assert lineas, proceso.stdout[-3000:]
    return json.loads(lineas[-1][len(MARCA):])


@pytest.fixture(scope="module")
def capturas(tmp_path_factory) -> dict:
    arbol = _arbol_base(tmp_path_factory.mktemp("arbol_base"))
    temporal = tmp_path_factory.mktemp("yaml_base")
    base = _ejecutar(_SCRIPT_BASE, str(arbol))
    rama = _ejecutar(_SCRIPT_RAMA, str(RAIZ_REPO), str(temporal), BASE)
    return {"arbol": arbol, "codigo_base": base, "rama": rama}


def test_f064_r15_el_lado_base_corre_el_codigo_de_la_base(capturas):
    arbol = capturas["arbol"].resolve()
    assert Path(capturas["codigo_base"]["comun"]).resolve().is_relative_to(arbol)
    assert Path(capturas["codigo_base"]["servicio"]).resolve().is_relative_to(arbol)


@pytest.mark.parametrize("fase", ("IA1", *CLAVES_FASE_2))
def test_f064_r15_variante_base_identica_a_la_base(capturas, fase):
    """Instructions, user_text y JSON Schema de respuesta, byte a byte (sin `sort_keys`)."""
    esperado = capturas["codigo_base"]["base"][fase]
    obtenido = capturas["rama"]["base"][fase]
    assert obtenido["instructions"] == esperado["instructions"]
    assert obtenido["user_text"] == esperado["user_text"]
    assert json.dumps(obtenido["schema"]) == json.dumps(esperado["schema"])
    assert "EMPRESAS DEL CLIENTE" not in obtenido["instructions"]


@pytest.mark.parametrize("fase", ("IA1", *CLAVES_FASE_2))
def test_f064_r15_variante_rama_lleva_la_lista_y_el_mismo_schema(capturas, fase):
    rama = capturas["rama"]["rama"][fase]
    base = capturas["codigo_base"]["base"][fase]
    assert rama["instructions"] != base["instructions"]
    assert rama["instructions"].count("EMPRESAS DEL CLIENTE (CIF — razón social):") == 1
    assert json.dumps(rama["schema"]) == json.dumps(base["schema"]), "R11: sin campos nuevos"
    if fase != "IA1":
        assert "proveedor_emisor" in rama["instructions"]
