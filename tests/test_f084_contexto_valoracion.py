# tests/test_f084_contexto_valoracion.py
"""F-084 · C — El contexto de valoración del banco es el de producción.

R12 (las líneas de albarán salen de UNA función, con descuento, precio neto e
importe derivado como el `SELECT` de sv5), R13 (descuento compuesto), R14
(clasificación del documento desde la tipología), R15 (`UnitCategoryPrefilter`
en el subproceso de sv5), R16 (fecha y número desde CONDICIONES), R17
(cabecera del contrato del índice), R32 y R33 (documento del contrato local).

Sin red ni BBDD (R25): sv6 corre en su subproceso con un envelope ya fabricado
y sv5, cuando hace falta, con un doble de LLM.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from evals.procesos import sv6_build
from evals.procesos.sv6_build import (
    MAPA_FAMILIA_DOCUMENTO,
    DescuentoCompuesto,
    clasificacion_de,
    construir_envelope_estimulado,
    lineas_albaran_de,
)

RAIZ = Path(__file__).resolve().parent.parent
FIXTURES = RAIZ / "evals" / "fixtures"


def _fixture(fase: str, caso: str) -> dict:
    return json.loads((FIXTURES / fase / f"{caso}.json").read_text(encoding="utf-8"))


def _inputs(lineas: list[dict], tipologia: str = "Ferreteria", condiciones=None) -> dict:
    return {
        "caso_id": "FER-900",
        "tipologia": tipologia,
        "tablas": {
            "caso": [{"caso_id": "FER-900", "contrato_codigo": "CTSU26/0001", "tipologia": tipologia}],
            "condiciones": condiciones or [],
            "contrato_lineas": [],
            "lineas_albaran": lineas,
        },
    }


def _linea(**cambios) -> dict:
    base = {
        "caso_id": "FER-900",
        "num_linea": 1,
        "descripcion": "DISCO",
        "cantidad": 50,
        "unidad": "UD",
        "precio_unitario": 0.647,
        "descuentos": 40,
        "importe": None,
        "codigo_imputacion": None,
        "observaciones_albaran": None,
    }
    base.update(cambios)
    return base


# --- R12 · descuento, precio neto e importe derivado --------------------------


def test_f084_r12_el_descuento_y_el_precio_neto_viajan_en_la_linea():
    linea = lineas_albaran_de(_inputs([_linea(importe=19.41)]))[0]

    assert linea["descuento_albaran"] == 40.0
    assert linea["precio_neto_albaran"] == 19.41
    assert linea["importe_albaran"] == 19.41


def test_f084_r12_sin_importe_se_deriva_con_la_formula_canonica():
    """`COALESCE(precio_neto, cantidad × precio × (1 − dto/100))` del SELECT de sv5."""
    linea = lineas_albaran_de(_inputs([_linea()]))[0]

    assert linea["importe_albaran"] == 19.41  # 50 × 0,647 × 0,60, sin ruido de float
    assert linea["precio_neto_albaran"] is None


def test_f084_r12_sin_descuento_el_importe_derivado_es_cantidad_por_precio():
    linea = lineas_albaran_de(_inputs([_linea(descuentos=None, cantidad=8, precio_unitario=72.5)]))[0]

    assert linea["importe_albaran"] == 580.0
    assert linea["descuento_albaran"] is None


@pytest.mark.parametrize("cambio", [{"cantidad": None}, {"precio_unitario": None}])
def test_f084_r12_sin_cantidad_o_sin_precio_no_se_deriva(cambio):
    """Como en SQL: un factor NULL deja el importe NULL (caso hormigón)."""
    assert lineas_albaran_de(_inputs([_linea(**cambio)]))[0]["importe_albaran"] is None


def test_f084_r12_el_importe_leido_manda_sobre_el_derivado():
    linea = lineas_albaran_de(_inputs([_linea(importe=20.0)]))[0]

    assert linea["importe_albaran"] == 20.0


def test_f084_r12_un_descuento_de_lista_con_un_valor_vale_ese_valor():
    """El conversor guarda `descuentos` como lista si el libro escribe `a;b`."""
    linea = lineas_albaran_de(_inputs([_linea(descuentos=["40"])]))[0]

    assert linea["descuento_albaran"] == 40.0
    assert linea["importe_albaran"] == 19.41


def test_f084_r12_un_descuento_vacio_o_en_interrogante_es_sin_descuento():
    for vacio in ([], "?", "@@NO_COMPARAR@@", ""):
        linea = lineas_albaran_de(_inputs([_linea(descuentos=vacio)]))[0]
        assert linea["descuento_albaran"] is None, vacio
        assert linea["importe_albaran"] == 32.35


def test_f084_r12_las_lineas_conservan_el_resto_de_campos_de_siempre():
    linea = lineas_albaran_de(
        _inputs([_linea(codigo_imputacion="CI.4.18", observaciones_albaran="nota")])
    )[0]

    assert linea["merge_line_id"] == 1 and linea["line_index"] == 1
    assert linea["descripcion"] == "DISCO" and linea["unidad_medida"] == "UD"
    assert linea["cantidad"] == 50.0 and linea["precio_unitario_albaran"] == 0.647
    assert linea["codigo_partida_albaran"] == "CI.4.18"
    assert linea["unidad_categoria"] == "unknown"
    assert linea["contexto_linea"]["descripcion_extendida"] == "nota"


def test_f084_r12_una_linea_sin_numero_no_entra():
    assert lineas_albaran_de(_inputs([_linea(num_linea=None)])) == []


def test_f084_r12_el_envelope_estimulado_usa_la_misma_funcion():
    inputs = _inputs([_linea()])
    envelope = construir_envelope_estimulado(inputs, {"tablas": {}})

    assert envelope["context"]["lineas_albaran"] == lineas_albaran_de(inputs)


def test_f084_r12_fer001_determinista_valora_19_41():
    """El caso del diagnóstico: hoy 32,35 = 50 × 0,647, sin el 40 % de descuento."""
    inputs, ia3 = _fixture("inputs", "FER-001"), _fixture("IA3", "FER-001")
    envelope = construir_envelope_estimulado(inputs, ia3)

    salida = sv6_build.ejecutar_en_subproceso(
        {"casos": [{"caso_id": "FER-001", "envelope": envelope}]}
    )
    resultado = salida["resultados"][0]
    base = [l for l in resultado["lineas"] if l["line_kind"] == "from_albaran"]

    assert base[0]["importe_calculado"] == pytest.approx(19.41)


# --- R13 · descuento compuesto -----------------------------------------------


@pytest.mark.parametrize("compuesto", [["40", "10"], [40, 10], "40;10"])
def test_f084_r13_un_descuento_compuesto_no_se_representa(compuesto):
    with pytest.raises(DescuentoCompuesto) as error:
        lineas_albaran_de(_inputs([_linea(descuentos=compuesto)]))

    assert "descuento compuesto no representable" in str(error.value)


# --- R14 · clasificación del documento desde la tipología ---------------------


@pytest.mark.parametrize(
    ("tipologia", "familia"),
    [
        ("Residuos", "residuos"),
        ("Hormigon", "hormigon"),
        ("Mortero", "mortero"),
        ("Combustible", "combustible"),
        ("Alquiler", "alquiler_maquinaria"),
        ("Ferreteria", "generico"),
        ("Grava", "generico"),
        ("Generico-Suministros", "generico"),
        ("Bombeo", "generico"),
        ("", "generico"),
    ],
)
def test_f084_r14_la_familia_sale_de_la_tipologia(tipologia, familia):
    clasificacion = clasificacion_de(_inputs([], tipologia=tipologia))

    assert clasificacion["familia"] == familia


def test_f084_r14_la_clasificacion_es_del_banco_y_valida_contra_comun():
    from ruesma_comun.contratos import ClasificacionAlbaran

    clasificacion = clasificacion_de(_inputs([], tipologia="Residuos"))

    assert clasificacion["origen"] == "banco_evals"
    assert clasificacion["confianza_pct"] == 100.0
    assert clasificacion["mixto"] is False
    assert clasificacion["familias_secundarias"] == []
    assert ClasificacionAlbaran.model_validate(clasificacion).familia == "residuos"


def test_f084_r14_las_familias_del_mapa_existen_en_el_catalogo():
    from ruesma_comun.contratos.familias import prompt_valoracion_de

    assert MAPA_FAMILIA_DOCUMENTO == {
        "Residuos": "residuos",
        "Hormigon": "hormigon",
        "Mortero": "mortero",
        "Combustible": "combustible",
        "Alquiler": "alquiler_maquinaria",
    }
    assert prompt_valoracion_de("residuos") == "valuation_residuos"


def test_f084_r14_el_envelope_estimulado_lleva_la_clasificacion_en_context():
    inputs = _inputs([_linea()], tipologia="Residuos")
    envelope = construir_envelope_estimulado(inputs, {"tablas": {}})

    assert envelope["context"]["clasificacion"] == clasificacion_de(inputs)


def test_f084_r14_el_estimulo_de_matches_no_cambia():
    """La clasificación y el descuento se añaden; el estímulo de IA3 es el de siempre."""
    inputs, ia3 = _fixture("inputs", "RES-001"), _fixture("IA3", "RES-001")
    envelope = construir_envelope_estimulado(copy.deepcopy(inputs), ia3)

    por_linea = {l["merge_line_id"]: l for l in envelope["data"]["lineas"] if l["merge_line_id"]}
    for fila in ia3["tablas"]["lineas_valoradas"]:
        linea = por_linea[int(fila["num_linea"])]
        assert linea["match_method"] == (fila["match_method"] or "no_match")
        assert linea["razon_corta"] == "estímulo del eval desde el ground truth de IA3"


# --- T6 · documento local y cabecera del índice (R17, R32, R33) ---------------

import hashlib

from evals.procesos import sv5_valoracion
from evals.procesos.sv5_documentos import nombre_en_cache

_CABECERA = {
    "nombre_contrato": "SUMINISTRO FERRETERIA",
    "cif_proveedor": "A00000000",
    "nombre_proveedor": "FERRETERIA DE PRUEBA SA",
    "codigo_obra": "696",
    "nombre_obra": "OBRA DE PRUEBA",
}


def _indice(tipo: str, contenido: bytes = b"", codigo: str = "CTSU26/0001") -> dict:
    return {codigo: {
        "tipo": tipo,
        "sha256": hashlib.sha256(contenido).hexdigest() if contenido else None,
        "bytes": len(contenido),
        "motivo": "" if contenido else "sin ruta de documento (md ni pdf)",
        **_CABECERA,
        "leido_utc": "2026-10-22T10:00:00Z",
    }}


def test_f084_r32_con_el_fichero_local_y_su_sha256_hay_documento(tmp_path):
    contenido = b"# Contrato"
    (tmp_path / nombre_en_cache("CTSU26/0001", "md")).write_bytes(contenido)

    documento = sv5_valoracion.documento_de("CTSU26/0001", _indice("md", contenido), tmp_path)

    assert documento == {"tipo": "md", "ruta": str(tmp_path / "CTSU26_0001.md")}


def test_f084_r32_un_pdf_local_tambien_vale(tmp_path):
    (tmp_path / "CTSU26_0001.pdf").write_bytes(b"%PDF-1.7")

    documento = sv5_valoracion.documento_de("CTSU26/0001", _indice("pdf", b"%PDF-1.7"), tmp_path)

    assert documento["tipo"] == "pdf"


@pytest.mark.parametrize("indice", [{}, _indice("ninguno")])
def test_f084_r32_sin_documento_en_el_indice_se_valora_sin_el(indice, tmp_path):
    """Como en producción con un contrato sin MD ni PDF: la nota de solo fase 1a."""
    assert sv5_valoracion.documento_de("CTSU26/0001", indice, tmp_path) is None


def test_f084_r33_el_indice_lo_declara_y_el_fichero_no_esta(tmp_path):
    documento = sv5_valoracion.documento_de("CTSU26/0001", _indice("md", b"# C"), tmp_path)

    assert documento == {"falta": "documento del contrato no disponible en local"}


def test_f084_r33_el_fichero_local_no_casa_con_su_sha256(tmp_path):
    (tmp_path / "CTSU26_0001.md").write_bytes(b"# Otro contrato")

    documento = sv5_valoracion.documento_de("CTSU26/0001", _indice("md", b"# C"), tmp_path)

    assert documento == {"falta": "documento del contrato no disponible en local"}


def test_f084_r17_el_contexto_lleva_la_cabecera_y_el_documento_del_indice(tmp_path):
    (tmp_path / "CTSU26_0001.md").write_bytes(b"# C")
    inputs = _inputs([_linea()])

    contexto = sv5_valoracion.construir_contexto(inputs, indice=_indice("md", b"# C"), raiz=tmp_path)

    assert {campo: contexto[campo] for campo in _CABECERA} == _CABECERA
    assert contexto["documento"] == {"tipo": "md", "ruta": str(tmp_path / "CTSU26_0001.md")}


def test_f084_r17_sin_entrada_en_el_indice_la_cabecera_va_vacia(tmp_path):
    contexto = sv5_valoracion.construir_contexto(_inputs([_linea()]), indice={}, raiz=tmp_path)

    assert all(contexto[campo] is None for campo in _CABECERA)
    assert contexto["documento"] is None


def test_f084_r17_sin_indice_explicito_se_lee_el_versionado(tmp_path, monkeypatch):
    ruta = tmp_path / "_indice.json"
    ruta.write_text(json.dumps(_indice("ninguno")), encoding="utf-8")
    monkeypatch.setattr(sv5_valoracion, "RUTA_INDICE", ruta)

    contexto = sv5_valoracion.construir_contexto(_inputs([_linea()]))

    assert contexto["nombre_obra"] == "OBRA DE PRUEBA"


def test_f084_r17_la_cabecera_llega_tambien_con_lineas_de_contrato(tmp_path):
    inputs = _inputs([_linea()])
    inputs["tablas"]["contrato_lineas"] = [
        {"caso_id": "FER-900", "codigo_producto": "P1", "descripcion_recurso": "DISCO",
         "unidad": "UD", "precio_unitario": 0.647, "codigo_partida": None},
    ]

    contexto = sv5_valoracion.construir_contexto(inputs, indice=_indice("ninguno"), raiz=tmp_path)

    assert contexto["nombre_proveedor"] == "FERRETERIA DE PRUEBA SA"
    assert contexto["lineas_contrato"][0]["contrato_line_id"] == 1


# --- T7 · el subproceso de sv5 da a la IA lo que le da producción -------------
#
# sv5 solo se importa en un subproceso (comparte nombres de paquete con sv2 y
# sv6). Este guion lo monta con un DOBLE de LLM —ni red ni claves— por la misma
# puerta que usa `main`, `valorar_casos`, y devuelve lo que vio el «modelo».

import subprocess
import sys

_GUION_SV5 = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from application.services.valuation_extraction_service import ProviderClientSpec
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from evals.procesos import sv5_valoracion

llamadas = []

class Doble:
    def extract_document(self, *, model, instructions, user_text, attachment, response_model):
        llamadas.append({
            "model": model,
            "schema": response_model.__name__,
            "user_text": user_text,
            "instructions": instructions,
            "adjunto": None if attachment is None else [attachment.kind, len(attachment.data)],
        })
        if response_model.__name__ == "DocumentoValoracion":
            return response_model.model_validate({"lineas": []})
        return response_model.model_validate({"conciliaciones": []})

def fabrica(proveedor, modelo=None):
    return ProviderClientSpec(provider=proveedor, model_name=modelo or "sin-modelo", client=Doble())

trabajo = json.loads(sys.stdin.read())
salida = sv5_valoracion.valorar_casos(trabajo, fabrica=fabrica)
prompts = YamlPromptRepository(sv5_valoracion.RAIZ_SV5 / "config" / "prompts.yaml")
sistemas = {clave: prompts.get(clave).system for clave in ("valuation_es", "valuation_residuos")}
for llamada in llamadas:
    sistema = llamada.pop("instructions")
    llamada["prompt"] = next((k for k, v in sistemas.items() if v == sistema), None)
sys.stdout.write("\n@@SALIDA@@" + json.dumps({"salida": salida, "llamadas": llamadas}, ensure_ascii=False))
"""


def _valorar_con_doble(casos: list[dict], modelo: str | None = "modelo-doble") -> dict:
    trabajo = {"proveedor": "openai", "casos": casos}
    if modelo:
        trabajo["modelo"] = modelo
    proceso = subprocess.run(
        [sys.executable, "-c", _GUION_SV5, str(sv5_valoracion.RAIZ_SV5)],
        input=json.dumps(trabajo, ensure_ascii=False), capture_output=True, text=True,
        encoding="utf-8", cwd=str(RAIZ), check=False,
    )
    assert proceso.returncode == 0, proceso.stderr[-3000:]
    return json.loads(proceso.stdout.rsplit("@@SALIDA@@", 1)[1])


def _contexto_res(tmp_path, documento: bytes | None, tipo: str = "md") -> dict:
    inputs = _fixture("inputs", "RES-001")
    codigo = inputs["tablas"]["caso"][0]["contrato_codigo"]
    indice = {}
    if documento is not None:
        (tmp_path / nombre_en_cache(codigo, tipo)).write_bytes(documento)
        indice = _indice(tipo, documento, codigo)
    return sv5_valoracion.construir_contexto(inputs, indice=indice, raiz=tmp_path)


def test_f084_r12_r14_construir_contexto_usa_las_funciones_de_sv6_build():
    inputs = _inputs([_linea()], tipologia="Residuos")

    contexto = sv5_valoracion.construir_contexto(inputs, indice={})

    assert contexto["lineas_albaran"] == lineas_albaran_de(inputs)
    assert contexto["clasificacion"] == clasificacion_de(inputs)


def test_f084_r16_fecha_y_numero_salen_de_condiciones():
    condiciones = [
        {"caso_id": "FER-900", "campo": "fecha_albaran", "valor": "2026-06-05"},
        {"caso_id": "FER-900", "campo": "numero_albaran", "valor": "2139643"},
    ]

    contexto = sv5_valoracion.construir_contexto(_inputs([_linea()], condiciones=condiciones), indice={})

    assert (contexto["fecha_albaran"], contexto["numero_albaran"]) == ("2026-06-05", "2139643")


def test_f084_r14_el_envelope_de_sv5_lleva_la_clasificacion():
    contexto = sv5_valoracion.construir_contexto(_inputs([_linea()], tipologia="Hormigon"), indice={})

    envelope = sv5_valoracion.envelope_desde(contexto, [], "openai", "m")

    assert envelope["context"]["clasificacion"]["familia"] == "hormigon"


def test_f084_r12_r14_r15_r16_r32_el_texto_de_ia3_es_el_de_produccion(tmp_path):
    contexto = _contexto_res(tmp_path, b"# CONTRATO RES-001\nTarifa de contenedores")

    vista = _valorar_con_doble([{"caso_id": "RES-001", "contexto": contexto}])

    (ia3,) = [l for l in vista["llamadas"] if l["schema"] == "DocumentoValoracion"]
    texto = ia3["user_text"]
    assert ia3["prompt"] == "valuation_residuos"
    assert ia3["model"] == "modelo-doble" and ia3["adjunto"] is None
    assert '"descuento_albaran"' in texto and '"precio_neto_albaran"' in texto
    assert '"unidad_categoria": "count"' in texto
    assert '"fecha_albaran": "2024-07-03"' in texto
    assert '"nombre_proveedor": "FERRETERIA DE PRUEBA SA"' in texto
    assert "## CONTRATO (markdown)" in texto and "Tarifa de contenedores" in texto
    assert "NO HAY PDF DE CONTRATO" not in texto


def test_f084_r15_el_envelope_devuelto_lleva_las_categorias_y_el_modelo(tmp_path):
    contexto = _contexto_res(tmp_path, None)

    vista = _valorar_con_doble([{"caso_id": "RES-001", "contexto": contexto}])

    (resultado,) = vista["salida"]["resultados"]
    assert vista["salida"]["modelo"] == "modelo-doble"
    assert resultado["envelope"]["meta"]["model"] == "modelo-doble"
    assert {l["unidad_categoria"] for l in resultado["envelope"]["context"]["lineas_albaran"]} == {"count"}
    assert {l["unidad_categoria"] for l in resultado["envelope"]["context"]["lineas_contrato"]} == {"count"}
    assert resultado["envelope"]["context"]["clasificacion"]["familia"] == "residuos"


def test_f084_r32_sin_documento_ia3_recibe_la_nota_de_solo_fase_1a(tmp_path):
    vista = _valorar_con_doble([{"caso_id": "RES-001", "contexto": _contexto_res(tmp_path, None)}])

    (ia3,) = [l for l in vista["llamadas"] if l["schema"] == "DocumentoValoracion"]
    assert "NO HAY PDF DE CONTRATO" in ia3["user_text"] and ia3["adjunto"] is None


def test_f084_r32_un_pdf_va_como_adjunto_en_la_misma_llamada(tmp_path):
    contexto = _contexto_res(tmp_path, b"%PDF-1.7 contrato", tipo="pdf")

    vista = _valorar_con_doble([{"caso_id": "RES-001", "contexto": contexto}])

    (ia3,) = [l for l in vista["llamadas"] if l["schema"] == "DocumentoValoracion"]
    assert ia3["adjunto"] == ["pdf", len(b"%PDF-1.7 contrato")]
    assert "NO HAY PDF DE CONTRATO" not in ia3["user_text"]


def test_f084_r33_un_documento_que_falta_no_llega_al_llm(tmp_path):
    contexto = _contexto_res(tmp_path, None)
    contexto["documento"] = {"falta": sv5_valoracion.MOTIVO_SIN_DOCUMENTO}

    vista = _valorar_con_doble([{"caso_id": "RES-001", "contexto": contexto}])

    assert vista["llamadas"] == []
    assert vista["salida"]["resultados"][0]["error"]["fase"] == "IA3"


def test_f084_r20_sin_modelo_en_el_trabajo_se_usa_el_de_la_fabrica(tmp_path):
    vista = _valorar_con_doble(
        [{"caso_id": "RES-001", "contexto": _contexto_res(tmp_path, None)}], modelo=None
    )

    assert vista["salida"]["modelo"] == "sin-modelo"
