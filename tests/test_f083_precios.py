# tests/test_f083_precios.py
"""F-083 · R1–R3: la tabla de precios versionada `evals/precios_modelos.json`."""

from __future__ import annotations

import copy
import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from evals import costes
from evals.costes import RUTA_PRECIOS, TablaInvalida, cargar_tabla

RAIZ = Path(__file__).resolve().parent.parent

#: Tanda 1 decidida por el humano en la PARADA 1 (design §9).
TANDA_1 = (
    "gemini-3.7-flash",
    "gemini-4-argon",
    "claude-opus-5-5",
    "gpt-5.4",
    "gpt-5.5",
    "gpt-6.1-sol",
    "gpt-6-luna",
    "gpt-5.6-luna",
)

#: Fuera por decisión del humano o por la recomendación de la spec.
EXCLUIDOS = (
    "claude-sonnet-5",
    "claude-haiku-5-5",
    "claude-opus-5",
    "claude-sonnet-5-5",
    "claude-fable-5",
    "claude-fable-5-1",
    "gemini-3.8-flash",
    "gpt-5.6-terra",
    "gpt-5.6-sol",
    "gpt-6-astra",
)


def _crudo() -> dict:
    return json.loads(RUTA_PRECIOS.read_text(encoding="utf-8"))


def _escribir(tmp_path: Path, datos: dict) -> Path:
    ruta = tmp_path / "precios.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


# --- R1 -----------------------------------------------------------------------


def test_f083_r1_la_tabla_real_carga_con_todos_sus_campos():
    tabla = cargar_tabla()
    for modelo_id in (*TANDA_1, *EXCLUIDOS, "claude-opus-4-8"):
        modelo = tabla.modelo(modelo_id)
        assert modelo.id == modelo_id
        assert modelo.proveedor in {"claude", "gemini", "openai"}
        assert modelo.fuente.startswith("https://")
        assert modelo.fecha_consulta.isoformat() == "2026-10-19"
        for precio in (
            modelo.precio.entrada,
            modelo.precio.lectura_cache,
            modelo.precio.escritura_cache,
            modelo.precio.salida,
        ):
            assert isinstance(precio, Decimal) and precio >= 0


def test_f083_r1_papeles_de_la_parada_1():
    tabla = cargar_tabla()
    for modelo_id in TANDA_1:
        assert tabla.modelo(modelo_id).papel in {"candidato", "referencia"}, modelo_id
    for modelo_id in EXCLUIDOS:
        modelo = tabla.modelo(modelo_id)
        assert modelo.papel == "excluido", modelo_id
        assert modelo.motivo.strip(), modelo_id
    # Opus 4.8 solo como referencia de IA3/IA4 (lo añade R12).
    assert tabla.modelo("claude-opus-4-8").papel == "referencia"
    assert set(tabla.validos()) == {*TANDA_1, "claude-opus-4-8"}


def test_f083_r1_herramienta_forzada_solo_en_claude():
    tabla = cargar_tabla()
    assert tabla.modelo("claude-opus-5-5").herramienta_forzada is False
    assert tabla.modelo("claude-opus-4-8").herramienta_forzada is True
    assert tabla.modelo("gpt-6-luna").herramienta_forzada is None
    assert tabla.modelo("gemini-4-argon").herramienta_forzada is None


def test_f083_r1_precios_de_ejemplo_del_inventario():
    tabla = cargar_tabla()
    opus = tabla.modelo("claude-opus-5-5").precio
    assert (opus.entrada, opus.lectura_cache, opus.escritura_cache, opus.salida) == (
        Decimal(4), Decimal("0.20"), Decimal(5), Decimal(20),
    )
    luna = tabla.modelo("gpt-6-luna").precio
    assert (luna.entrada, luna.lectura_cache, luna.escritura_cache, luna.salida) == (
        Decimal("0.10"), Decimal("0.01"), Decimal("0.125"), Decimal("0.50"),
    )
    argon = tabla.modelo("gemini-4-argon").precio
    assert argon.vigente_hasta.isoformat() == "2026-11-30"
    assert argon.siguiente.entrada == Decimal(4)
    assert tabla.modelo("gpt-5.5").tramo_largo.umbral == 272000
    assert tabla.modelo("claude-haiku-5-5").tramo_largo.umbral == 100000
    assert tabla.modelo("gpt-5.4").tramo_largo is None


def test_f083_r1_estimacion_por_defecto_de_cada_fase():
    tabla = cargar_tabla()
    assert tabla.por_defecto("IA1") == (10000, 3000, Decimal("1.5"))
    assert tabla.por_defecto("IA2") == (14000, 4000, Decimal("1.5"))
    assert tabla.por_defecto("IA3") == (12000, 4000, Decimal("1.5"))
    assert tabla.por_defecto("IA4") == (5000, 1500, Decimal("1.5"))


def test_f083_r1_modelo_desconocido_es_keyerror():
    with pytest.raises(KeyError):
        cargar_tabla().modelo("gpt-6.1-luna")


# --- R2 -----------------------------------------------------------------------


def _romper(datos: dict, modelo_id: str, accion) -> dict:
    datos = copy.deepcopy(datos)
    for modelo in datos["modelos"]:
        if modelo["id"] == modelo_id:
            accion(modelo)
    return datos


@pytest.mark.parametrize(
    ("accion", "campo"),
    [
        (lambda m: m.pop("fuente"), "fuente"),
        (lambda m: m.update(fuente="  "), "fuente"),
        (lambda m: m.pop("fecha_consulta"), "fecha_consulta"),
        (lambda m: m["precio"].pop("salida"), "salida"),
        (lambda m: m["precio"].pop("entrada"), "entrada"),
        (lambda m: m["precio"].pop("lectura_cache"), "lectura_cache"),
        (lambda m: m["precio"].pop("escritura_cache"), "escritura_cache"),
        (lambda m: m["precio"].update(salida=-1), "salida"),
        (lambda m: m["precio"].update(entrada="gratis"), "entrada"),
        (lambda m: m.update(proveedor="mistral"), "proveedor"),
        (lambda m: m.update(papel="favorito"), "papel"),
        (lambda m: m.update(papel="excluido", motivo=""), "motivo"),
        (lambda m: m.pop("imagen"), "imagen"),
        (lambda m: m.pop("pdf"), "pdf"),
        (lambda m: m.update(fecha_consulta="ayer"), "fecha_consulta"),
    ],
)
def test_f083_r2_entrada_rota_nombra_modelo_y_campo(tmp_path, accion, campo):
    ruta = _escribir(tmp_path, _romper(_crudo(), "gpt-5.5", accion))
    with pytest.raises(TablaInvalida) as error:
        cargar_tabla(ruta)
    assert "gpt-5.5" in str(error.value)
    assert campo in str(error.value)


def test_f083_r2_precio_siguiente_y_tramo_largo_tambien_se_validan(tmp_path):
    def sin_salida_siguiente(modelo):
        modelo["precio"]["siguiente"].pop("salida")

    ruta = _escribir(tmp_path, _romper(_crudo(), "gemini-4-argon", sin_salida_siguiente))
    with pytest.raises(TablaInvalida, match="gemini-4-argon.*salida"):
        cargar_tabla(ruta)

    def tramo_negativo(modelo):
        modelo["tramo_largo"]["precio"]["entrada"] = -2

    ruta = _escribir(tmp_path, _romper(_crudo(), "gpt-5.5", tramo_negativo))
    with pytest.raises(TablaInvalida, match="gpt-5.5.*entrada"):
        cargar_tabla(ruta)


def test_f083_r2_cero_es_un_precio_valido(tmp_path):
    ruta = _escribir(
        tmp_path, _romper(_crudo(), "gpt-5.5", lambda m: m["precio"].update(lectura_cache=0))
    )
    assert cargar_tabla(ruta).modelo("gpt-5.5").precio.lectura_cache == 0


def test_f083_r2_id_repetido(tmp_path):
    datos = _crudo()
    datos["modelos"].append(copy.deepcopy(datos["modelos"][0]))
    with pytest.raises(TablaInvalida) as error:
        cargar_tabla(_escribir(tmp_path, datos))
    assert datos["modelos"][0]["id"] in str(error.value)
    assert "repetido" in str(error.value)


def test_f083_r2_referencia_que_no_esta_en_la_tabla(tmp_path):
    datos = _crudo()
    datos["referencias"]["IA2"] = "gpt-9"
    with pytest.raises(TablaInvalida, match="gpt-9"):
        cargar_tabla(_escribir(tmp_path, datos))


def test_f083_r2_referencia_excluida(tmp_path):
    datos = _crudo()
    datos["referencias"]["IA2"] = "gpt-6-astra"
    with pytest.raises(TablaInvalida, match="gpt-6-astra"):
        cargar_tabla(_escribir(tmp_path, datos))


def test_f083_r2_falta_la_estimacion_de_una_fase(tmp_path):
    datos = _crudo()
    datos["estimacion_por_defecto"].pop("IA3")
    with pytest.raises(TablaInvalida, match="IA3"):
        cargar_tabla(_escribir(tmp_path, datos))


def test_f083_r2_falta_la_referencia_de_una_fase(tmp_path):
    datos = _crudo()
    datos["referencias"].pop("IA4")
    with pytest.raises(TablaInvalida, match="IA4"):
        cargar_tabla(_escribir(tmp_path, datos))


def test_f083_r2_json_ilegible(tmp_path):
    ruta = tmp_path / "precios.json"
    ruta.write_text("{ no es json", encoding="utf-8")
    with pytest.raises(TablaInvalida, match="JSON"):
        cargar_tabla(ruta)


# --- R3 -----------------------------------------------------------------------


def _modelo_de_infra(variable: str) -> str:
    texto = (RAIZ / "infra" / "create_capps.ps1").read_text(encoding="utf-8-sig")
    encontrado = re.search(rf'^\${variable}\s*=\s*"([^"]+)"', texto, re.MULTILINE)
    assert encontrado, f"{variable} no está en infra/create_capps.ps1"
    return encontrado.group(1)


@pytest.mark.parametrize(
    ("fase", "variable"),
    [
        ("IA1", "GEMINI_MODEL"),
        ("IA2", "OPENAI_MODEL"),
        ("IA3", "ANTHROPIC_MODEL"),
        ("IA4", "ANTHROPIC_MODEL"),
    ],
)
def test_f083_r3_la_referencia_es_la_de_produccion(fase, variable):
    produccion = _modelo_de_infra(variable)
    tabla = cargar_tabla()
    assert tabla.referencia(fase) == produccion, (
        f"{fase}: la tabla dice {tabla.referencia(fase)} e infra/create_capps.ps1 "
        f"({variable}) dice {produccion}"
    )
    assert tabla.modelo(produccion).papel == "referencia"


def test_f083_r3_fase_desconocida():
    with pytest.raises(KeyError):
        cargar_tabla().referencia("IA9")


def test_f083_la_ruta_por_defecto_es_la_versionada():
    assert costes.RUTA_PRECIOS == RAIZ / "evals" / "precios_modelos.json"


@pytest.mark.parametrize("valor", [None, "no"])
def test_f083_r1_claude_declara_si_admite_la_herramienta_forzada(tmp_path, valor):
    datos = _romper(_crudo(), "claude-opus-5-5", lambda m: m.update(herramienta_forzada=valor))
    with pytest.raises(TablaInvalida, match="claude-opus-5-5.*herramienta_forzada"):
        cargar_tabla(_escribir(tmp_path, datos))


def test_f083_r2_modelo_sin_id(tmp_path):
    datos = _crudo()
    datos["modelos"].append({"proveedor": "openai"})
    with pytest.raises(TablaInvalida, match="sin id"):
        cargar_tabla(_escribir(tmp_path, datos))
