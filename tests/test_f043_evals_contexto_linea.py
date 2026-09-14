# tests/test_f043_evals_contexto_linea.py
"""F-043 · el banco de evals alimenta al builder con el `contexto_linea` real.

El camino de PRODUCCIÓN entrega a sv6 el bloque `contexto_linea` entero: sv5
lo lee de `albaran_lines_merge.contexto_linea_json`, lo valida contra el
contrato `ContextoLinea` y lo vuelca al envelope con
`model_dump(exclude_none=True)`. Con `volumen_m3` dentro,
`calcular_contenedores_residuos` cuenta 1 contenedor y la línea vale 120 €.

El banco fabricaba ese bloque con solo tres campos —familia, rol y descripción
extendida— y tiraba el resto. Sin `volumen_m3` la regla de residuos salía por
`residuos_sin_volumen_m3`, el builder caía a la cantidad cruda del albarán y
los importes salían ×6 (×9 en RES-007). Era un defecto del BANCO, no del
producto.

Lo que estos tests fijan:

- que las CONDICIONES del libro `INPUTS` que son campos del contrato viajen al
  `contexto_linea` de cada línea, en los DOS adaptadores (el determinista de
  sv6 y el de la pasada completa de sv5);
- y que no viaje NADA más: `tamano_contenedor_contrato` no es un campo de
  `ContextoLinea` —en producción el tamaño sale de la descripción de la línea
  de contrato o de IA3—, así que colarlo ahí sería regalarle al banco un dato
  que el pipeline real no tiene.
"""

from __future__ import annotations

import json

import pytest

from ruesma_comun.contratos.contexto_linea import ContextoLinea

from evals.conversor import RUTA_FIXTURES
from evals.procesos.sv5_valoracion import construir_contexto
from evals.procesos.sv6_build import (
    CAMPOS_DE_CONTEXTO_LINEA,
    construir_envelope_estimulado,
)


def _fixture(fase: str, caso_id: str) -> dict:
    ruta = RUTA_FIXTURES / fase / f"{caso_id}.json"
    if not ruta.is_file():
        pytest.skip(f"el banco no tiene sembrado {fase}/{caso_id}")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _contextos_de_los_dos_adaptadores(caso_id: str) -> list[dict]:
    """El `contexto_linea` de la línea 1 según cada uno de los dos caminos."""
    inputs = _fixture("inputs", caso_id)
    envelope = construir_envelope_estimulado(inputs, _fixture("IA3", caso_id))
    return [
        envelope["context"]["lineas_albaran"][0]["contexto_linea"],
        construir_contexto(inputs)["lineas_albaran"][0]["contexto_linea"],
    ]


@pytest.mark.parametrize(
    ("caso_id", "codigo_ler", "volumen_m3"),
    [
        ("RES-004", "170604", 6.0),
        ("RES-007", "170802", 9.0),
    ],
)
def test_f043_evals_las_condiciones_llegan_al_contexto_linea(
    caso_id, codigo_ler, volumen_m3
):
    """Sin esto el builder no puede contar contenedores y multiplica ×m³."""
    for contexto in _contextos_de_los_dos_adaptadores(caso_id):
        validado = ContextoLinea(**contexto)

        assert validado.tipo_familia == "residuos"
        assert validado.codigo_ler == codigo_ler
        assert validado.volumen_m3 == pytest.approx(volumen_m3)


def test_f043_evals_el_contexto_linea_no_lleva_nada_que_no_sea_del_contrato():
    """`tamano_contenedor_contrato` es del caso, no de la línea: no se cuela.

    En producción el tamaño del contenedor sale de la descripción de la línea
    de contrato (`CAMBIO CONTENEDOR 6M3`) o del que emite IA3. Metérselo al
    banco por `contexto_linea` sería falsear la entrada.
    """
    for contexto in _contextos_de_los_dos_adaptadores("RES-004"):
        assert "tamano_contenedor_contrato" not in contexto
        assert "numero_albaran" not in contexto
        assert "fecha_albaran" not in contexto
        assert set(contexto) <= CAMPOS_DE_CONTEXTO_LINEA


def test_f043_evals_el_criterio_de_propagacion_es_el_contrato_compartido():
    """La lista de campos que se propagan NO es una copia: sale del contrato.

    Si mañana `ContextoLinea` estrena un campo, el banco lo propaga sin que
    nadie tenga que acordarse de tocar dos sitios (regla del monorepo: la
    lógica compartida vive en `services/albaranes-comun`).
    """
    assert CAMPOS_DE_CONTEXTO_LINEA == frozenset(ContextoLinea.model_fields)
    assert {"codigo_ler", "volumen_m3", "contenedores"} <= CAMPOS_DE_CONTEXTO_LINEA
