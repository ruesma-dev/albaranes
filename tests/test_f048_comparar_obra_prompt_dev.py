# tests/test_f048_comparar_obra_prompt_dev.py
"""F-048 · la variante `dev` del comparador de obra le manda al LLM lo mismo que `dev`.

El comparador (`evals/comparar_obra.py`) no ejecuta el código de `dev`: monta
el servicio de ESTA rama con el `prompts.yaml` de `dev` (sacado con
`git show`) y el schema sin `lectura_correo`. Eso solo mide el prompt de
`dev` si lo que recibe el LLM es idéntico a lo que manda `dev` de verdad.
Este test lo comprueba byte a byte contra el código de `dev`, extraído con
`git archive` a un temporal y ejecutado en su propio intérprete (sv2 y
`ruesma_comun` de `dev`, no los de la rama).

Se captura lo que llega al cliente LLM —`instructions`, `user_text` y el JSON
Schema del modelo de respuesta, que gemini manda como `response_json_schema`—
con un cliente de mentira: ni red ni LLM. La lista de obras es de mentira y la
misma en los dos lados.
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

MARCA = "<<<CAPTURA-F048>>>"

#: Rutas de `dev` que hacen falta para montar su servicio de extracción.
RUTAS_DEV = (
    "services/albaranes-api/application",
    "services/albaranes-api/domain",
    "services/albaranes-api/infrastructure",
    "services/albaranes-api/config",
    "services/albaranes-comun/ruesma_comun",
)

OBRAS = [["9001", "OBRA DE MENTIRA UNO"], ["9002", "OBRA DE MENTIRA DOS"]]

#: Cliente LLM de mentira y proveedor de obras, comunes a los dos lados.
_COMUN = f"""
import json, sys

CAPTURA = {{}}

class ClienteQueCaptura:
    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        CAPTURA["instructions"] = instructions
        CAPTURA["user_text"] = user_text
        CAPTURA["schema"] = response_model.model_json_schema()
        return response_model.model_validate({{"cabecera": {{}}, "lineas": []}})

def capturar(servicio):
    CAPTURA.clear()
    servicio.extract_phase_1(attachments=[], provider="gemini", prompt_key="albaran_factura_es")
    return dict(CAPTURA)

OBRAS = {OBRAS!r}
"""

#: Lado `dev`: su código, su `ruesma_comun`, su YAML y su `SchemaRegistry`.
_SCRIPT_DEV = _COMUN + """
arbol = sys.argv[1]
sys.path[:0] = [arbol + "/services/albaranes-api", arbol + "/services/albaranes-comun"]
import ruesma_comun
import application.services.albaran_extraction_service as modulo
from application.services.albaran_extraction_service import AlbaranExtractionService, ProviderClientSpec
from application.services.schema_registry import SchemaRegistry
from domain.ports.obras_activas_provider import ObraActiva
from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

class Obras:
    def obtener(self):
        return [ObraActiva(codigo=c, nombre=n) for c, n in OBRAS]

sv2 = arbol + "/services/albaranes-api"
servicio = AlbaranExtractionService(
    providers=[ProviderClientSpec(provider="gemini", model_name="m", client=ClienteQueCaptura())],
    prompt_repo=YamlPromptRepository(sv2 + "/config/prompts.yaml"),
    schema_registry=SchemaRegistry(),
    revision_rules_repo=RevisionRulesRepository(yaml_path=sv2 + "/config/revision_rules.yaml"),
    prompt_key_phase_1="albaran_factura_es",
    obras_activas_provider=Obras(),
)
salida = {"dev": capturar(servicio), "comun": ruesma_comun.__file__, "servicio": modulo.__file__}
print("__MARCA__" + json.dumps(salida, ensure_ascii=False))
""".replace("__MARCA__", MARCA)

#: Lado rama: el montaje REAL del comparador, variante `dev` y variante `rama`.
_SCRIPT_RAMA = _COMUN + """
raiz, temporal = sys.argv[1], sys.argv[2]
sys.path.insert(0, raiz)
from evals.procesos import sv2_obra
sv2_obra._con_sv2_en_path()
from application.services.albaran_extraction_service import ProviderClientSpec
from domain.ports.obras_activas_provider import ObraActiva

spec = ProviderClientSpec(provider="gemini", model_name="m", client=ClienteQueCaptura())
obras = sv2_obra.ObrasFijas([ObraActiva(codigo=c, nombre=n) for c, n in OBRAS])
rutas = {"dev": sv2_obra.prompt_de_dev(temporal), "rama": sv2_obra.prompt_de_rama()}
salida = {v: capturar(sv2_obra.montar_servicio(v, rutas[v], spec, obras)) for v in rutas}
print("__MARCA__" + json.dumps(salida, ensure_ascii=False))
""".replace("__MARCA__", MARCA)


def _arbol_dev(destino: Path) -> Path:
    """El código de `dev` que hace falta, extraído con `git archive` (sin tocar el árbol)."""
    proceso = subprocess.run(
        ["git", "-C", str(RAIZ_REPO), "archive", "--format=tar", "dev", *RUTAS_DEV],
        capture_output=True,
        check=False,
    )
    if proceso.returncode != 0:
        pytest.fail(f"git archive dev falló: {proceso.stderr.decode('utf-8', 'replace')}")
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
    lineas = [l for l in proceso.stdout.splitlines() if l.startswith(MARCA)]
    assert lineas, proceso.stdout[-3000:]
    return json.loads(lineas[-1][len(MARCA):])


@pytest.fixture(scope="module")
def capturas(tmp_path_factory) -> dict:
    arbol = _arbol_dev(tmp_path_factory.mktemp("arbol_dev"))
    temporal = tmp_path_factory.mktemp("prompt_dev")
    dev = _ejecutar(_SCRIPT_DEV, str(arbol))
    rama = _ejecutar(_SCRIPT_RAMA, str(RAIZ_REPO), str(temporal))
    return {"arbol": arbol, "codigo_dev": dev, "rama": rama}


def test_f048_comparar_obra_el_lado_dev_corre_el_codigo_de_dev(capturas):
    """Sin esto el test compararía la rama consigo misma: sv2 y `ruesma_comun` salen del temporal."""
    arbol = capturas["arbol"].resolve()
    assert Path(capturas["codigo_dev"]["comun"]).resolve().is_relative_to(arbol)
    assert Path(capturas["codigo_dev"]["servicio"]).resolve().is_relative_to(arbol)


def test_f048_comparar_obra_variante_dev_instrucciones_identicas_a_dev(capturas):
    """El texto que recibe el LLM (system + task renderizado + schema_hint), byte a byte."""
    esperado = capturas["codigo_dev"]["dev"]
    obtenido = capturas["rama"]["dev"]
    assert obtenido["instructions"] == esperado["instructions"]
    assert obtenido["user_text"] == esperado["user_text"]
    assert "9001 — OBRA DE MENTIRA UNO" in obtenido["instructions"], "la lista de obras llega"


def test_f048_comparar_obra_variante_dev_schema_identico_a_dev(capturas):
    """El JSON Schema de respuesta, que gemini manda al proveedor: sin `lectura_correo`.

    Sin `sort_keys`: byte a byte, también el orden de las propiedades, que a
    Gemini le importa.
    """
    esperado = json.dumps(capturas["codigo_dev"]["dev"]["schema"])
    obtenido = json.dumps(capturas["rama"]["dev"]["schema"])
    assert obtenido == esperado


def test_f048_comparar_obra_variante_rama_es_la_de_la_rama_sin_correo(capturas):
    """La otra variante sí lleva la sección del correo (con la nota de «sin correo») y el campo nuevo."""
    rama = capturas["rama"]["rama"]
    assert rama["instructions"] != capturas["codigo_dev"]["dev"]["instructions"]
    assert "## Correo con el que llegó el albarán" in rama["instructions"]
    assert "{contexto_correo}" not in rama["instructions"]
    assert "9001 — OBRA DE MENTIRA UNO" in rama["instructions"]
    assert "lectura_correo" in rama["schema"]["properties"]
    assert "lectura_correo" not in capturas["rama"]["dev"]["schema"]["properties"]
