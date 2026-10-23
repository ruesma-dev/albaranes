# tests/test_f084_runner.py
"""F-084 · D — Runner y veredicto del banco de valoración.

R18 (OMITIDO sin líneas de contrato), R33 (OMITIDO sin el documento local),
R13 en el runner (descuento compuesto = ERROR), R19 (sin sv2 si no se piden
IA1/IA2), R20 (proveedor y modelo de producción por defecto), R21 (modelo en
el informe), R17 (recuento md/pdf/ninguno) y R36 (el determinista declara que
no mide el emparejamiento).

Sin red (R25): los subprocesos de sv2, sv5 y sv6 se sustituyen por dobles.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from evals import runner
from evals.costes import cargar_tabla
from evals.modelos import ERROR, OMITIDO
from evals.procesos import sv2_extraccion, sv5_valoracion, sv6_build

RAIZ = Path(__file__).resolve().parent.parent


def _inputs(caso_id: str, *, lineas_contrato: bool = True, descuentos=None) -> dict:
    return {
        "caso_id": caso_id,
        "fase": "INPUTS",
        "tipologia": "Hormigon",
        "tablas": {
            "caso": [{"caso_id": caso_id, "contrato_codigo": f"CT/{caso_id}"}],
            "condiciones": [],
            "contrato_lineas": (
                [{"caso_id": caso_id, "codigo_producto": "H25", "descripcion_recurso": "HA-25",
                  "unidad": "m3", "precio_unitario": 72.5, "codigo_partida": "01.02"}]
                if lineas_contrato
                else []
            ),
            "lineas_albaran": [
                {"caso_id": caso_id, "num_linea": 1, "descripcion": "HA-25", "cantidad": 8,
                 "unidad": "m3", "precio_unitario": 72.5, "descuentos": descuentos,
                 "importe": None, "codigo_imputacion": "01.02", "observaciones_albaran": None},
            ],
        },
    }


def _ia3(caso_id: str) -> dict:
    return {"caso_id": caso_id, "tablas": {"lineas_valoradas": [
        {"num_linea": 1, "match_method": "exact_code", "codigo_producto_contrato": "H25",
         "codigo_partida_final": "01.02", "precio_unitario_final": 72.5,
         "precio_source": "contrato_db", "importe_calculado": 580.0, "review_required": "NO"},
    ], "sinteticas_esperadas": [], "sinteticas_prohibidas": []}}


def _banco(tmp_path: Path, *inputs: dict, indice: dict | None = None) -> Path:
    fixtures = tmp_path / "fixtures"
    for fase, contenido in (("inputs", inputs), ("IA3", [_ia3(i["caso_id"]) for i in inputs])):
        (fixtures / fase).mkdir(parents=True, exist_ok=True)
        for fixture in contenido:
            (fixtures / fase / f"{fixture['caso_id']}.json").write_text(
                json.dumps(fixture), encoding="utf-8"
            )
    if indice is not None:
        (fixtures / "contratos").mkdir()
        (fixtures / "contratos" / "_indice.json").write_text(json.dumps(indice), encoding="utf-8")
    return fixtures


class _Builds:
    """El subproceso de sv6 sustituido: registra lo que recibe y no construye nada."""

    def __init__(self):
        self.casos: list[str] = []

    def __call__(self, trabajo, interprete=None):
        self.casos += [caso["caso_id"] for caso in trabajo["casos"]]
        return {"resultados": [
            {"caso_id": caso["caso_id"], "header": {}, "lineas": []} for caso in trabajo["casos"]
        ]}


class _Sv5:
    """El subproceso de sv5 sustituido: devuelve un envelope por caso, sin LLM."""

    def __init__(self, modelo: str = "modelo-servido"):
        self.trabajos: list[dict] = []
        self.modelo = modelo

    def __call__(self, trabajo, interprete=None):
        self.trabajos.append(trabajo)
        return {"proveedor": trabajo["proveedor"], "modelo": self.modelo, "resultados": [
            {"caso_id": caso["caso_id"],
             "envelope": sv5_valoracion.envelope_desde(caso["contexto"], [], trabajo["proveedor"], self.modelo),
             "conciliaciones": []}
            for caso in trabajo["casos"]
        ]}


@pytest.fixture
def subprocesos(monkeypatch):
    builds, sv5 = _Builds(), _Sv5()

    def sv2_prohibido(*args, **kwargs):  # pragma: no cover - no debe llamarse
        raise AssertionError("se ha llamado a sv2 sin pedir IA1 ni IA2")

    monkeypatch.setattr(sv6_build, "ejecutar_en_subproceso", builds)
    monkeypatch.setattr(sv5_valoracion, "ejecutar_en_subproceso", sv5)
    monkeypatch.setattr(sv2_extraccion, "ejecutar_en_subproceso", sv2_prohibido)
    for variable in ("IA3_PROVIDER", "OPENAI_MODEL", "ANTHROPIC_MODEL", "GEMINI_MODEL"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "clave-de-prueba")
    return builds, sv5


def _fase(fases, nombre):
    return next(fase for fase in fases if fase.nombre == nombre)


# --- R18 · sin líneas de contrato en INPUTS -----------------------------------


def test_f084_r18_determinista_omite_el_caso_y_no_lo_construye(tmp_path, subprocesos):
    builds, _ = subprocesos
    fixtures = _banco(tmp_path, _inputs("HOR-001"), _inputs("HOR-002", lineas_contrato=False))

    fases, _ = runner.corrida_determinista(fixtures)

    for nombre in ("IA3", "IA4", "E2E"):
        (caso,) = [c for c in _fase(fases, nombre).casos if c.caso_id == "HOR-002"]
        assert (caso.estado, caso.motivo) == (OMITIDO, "sin líneas de contrato en INPUTS")
    assert builds.casos == ["HOR-001"]


def test_f084_r18_con_llm_omite_el_caso_y_no_lo_manda_a_sv5(tmp_path, subprocesos):
    _, sv5 = subprocesos
    fixtures = _banco(tmp_path, _inputs("HOR-001"), _inputs("HOR-002", lineas_contrato=False))

    fases, _ = runner.corrida_completa(fixtures, fases=["IA3", "IA4", "E2E"])

    assert [c["caso_id"] for c in sv5.trabajos[0]["casos"]] == ["HOR-001"]
    for nombre in ("IA3", "IA4", "E2E"):
        (caso,) = [c for c in _fase(fases, nombre).casos if c.caso_id == "HOR-002"]
        assert (caso.estado, caso.motivo) == (OMITIDO, "sin líneas de contrato en INPUTS")


def test_f084_r18_sin_contrato_codigo_no_es_omitido_por_r18(tmp_path, subprocesos):
    """Sin código de contrato, producción da `no_contract`: el banco no lo esconde."""
    caso = _inputs("HOR-003", lineas_contrato=False)
    caso["tablas"]["caso"][0]["contrato_codigo"] = None
    fixtures = _banco(tmp_path, caso)

    fases, _ = runner.corrida_determinista(fixtures)

    assert _fase(fases, "IA3").casos[0].estado != OMITIDO


def test_f084_r18_si_todos_se_omiten_no_se_lanza_sv5(tmp_path, subprocesos):
    _, sv5 = subprocesos
    fixtures = _banco(tmp_path, _inputs("HOR-002", lineas_contrato=False))

    fases, _ = runner.corrida_completa(fixtures, fases=["IA3", "IA4", "E2E"])

    assert sv5.trabajos == []
    assert _fase(fases, "IA3").veredicto() == "NO_EVALUABLE"


# --- R33 · el documento del contrato no está en local --------------------------


def _indice_md(caso_id: str) -> dict:
    return {f"CT/{caso_id}": {"tipo": "md", "sha256": hashlib.sha256(b"# C").hexdigest(),
                              "bytes": 3, "motivo": ""}}


def test_f084_r33_sin_el_documento_local_la_corrida_con_llm_lo_omite(tmp_path, subprocesos, monkeypatch):
    _, sv5 = subprocesos
    monkeypatch.setattr(runner, "RUTA_CACHE", tmp_path / "cache-vacia")
    fixtures = _banco(tmp_path, _inputs("HOR-001"), _inputs("HOR-002"), indice=_indice_md("HOR-002"))

    completa, _ = runner.corrida_completa(fixtures, fases=["IA3", "IA4", "E2E"])

    assert [c["caso_id"] for c in sv5.trabajos[0]["casos"]] == ["HOR-001"]
    for nombre in ("IA3", "IA4", "E2E"):
        (caso,) = [c for c in _fase(completa, nombre).casos if c.caso_id == "HOR-002"]
        assert (caso.estado, caso.motivo) == (
            OMITIDO, "documento del contrato no disponible en local"
        )


def test_f084_r33_el_determinista_no_lee_el_documento_y_no_omite(tmp_path, subprocesos, monkeypatch):
    """(R33, opción a) El determinista no usa el documento: un índice sin caché no le afecta."""
    monkeypatch.setattr(runner, "RUTA_CACHE", tmp_path / "cache-vacia")
    con_indice = _banco(tmp_path / "con", _inputs("HOR-001"), _inputs("HOR-002"),
                        indice=_indice_md("HOR-002"))
    sin_indice = _banco(tmp_path / "sin", _inputs("HOR-001"), _inputs("HOR-002"))

    obtenido, _ = runner.corrida_determinista(con_indice)
    esperado, _ = runner.corrida_determinista(sin_indice)

    assert all(c.motivo != sv5_valoracion.MOTIVO_SIN_DOCUMENTO for f in obtenido for c in f.casos)
    assert [(f.nombre, [(c.caso_id, c.estado, c.motivo, c.fallos) for c in f.casos])
            for f in obtenido] == [
        (f.nombre, [(c.caso_id, c.estado, c.motivo, c.fallos) for c in f.casos]) for f in esperado
    ]


def test_f084_r33_el_comparador_omite_el_caso_sin_documento_local(tmp_path, monkeypatch):
    """(R33) El comparador de F-083 tampoco manda a sv5 un caso con el documento ausente."""
    from evals import comparar_modelos as cm

    fixtures = _banco(tmp_path, _inputs("HOR-001"), _inputs("HOR-002"), indice=_indice_md("HOR-002"))
    (fixtures / "IA4").mkdir()
    for caso_id in ("HOR-001", "HOR-002"):
        (fixtures / "IA4" / f"{caso_id}.json").write_text(
            json.dumps({"caso_id": caso_id, "tablas": {}}), encoding="utf-8")
    monkeypatch.setattr(sv5_valoracion, "RUTA_INDICE", runner.ruta_indice(fixtures))
    monkeypatch.setattr(sv5_valoracion, "RUTA_CACHE", tmp_path / "cache-vacia")

    for fase in ("IA3", "IA4"):
        casos, omitidos = cm.casos_de_fase(fase, fixtures, tmp_path / "albaranes", None)
        assert (casos, omitidos) == (
            ["HOR-001"], {"HOR-002": "documento del contrato no disponible en local"}
        ), fase


def test_f084_r32_con_el_documento_local_el_caso_viaja_con_el(tmp_path, subprocesos, monkeypatch):
    _, sv5 = subprocesos
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "CT_HOR-002.md").write_bytes(b"# C")
    monkeypatch.setattr(runner, "RUTA_CACHE", cache)
    fixtures = _banco(tmp_path, _inputs("HOR-002"), indice=_indice_md("HOR-002"))

    runner.corrida_completa(fixtures, fases=["IA3"])

    (caso,) = sv5.trabajos[0]["casos"]
    assert caso["contexto"]["documento"] == {"tipo": "md", "ruta": str(cache / "CT_HOR-002.md")}


# --- R13 en el runner · descuento compuesto ------------------------------------


def test_f084_r13_un_descuento_compuesto_es_error_de_ese_caso(tmp_path, subprocesos):
    _, sv5 = subprocesos
    fixtures = _banco(tmp_path, _inputs("HOR-001"), _inputs("HOR-002", descuentos=["40", "10"]))

    completa, _ = runner.corrida_completa(fixtures, fases=["IA3", "IA4", "E2E"])
    determinista, _ = runner.corrida_determinista(fixtures)

    assert [c["caso_id"] for c in sv5.trabajos[0]["casos"]] == ["HOR-001"]
    for fases, con_error in ((completa, ("IA3",)), (determinista, ("IA3", "E2E"))):
        for nombre in ("IA3", "IA4", "E2E"):
            (caso,) = [c for c in _fase(fases, nombre).casos if c.caso_id == "HOR-002"]
            assert caso.estado == (ERROR if nombre in con_error else OMITIDO), nombre
            assert "descuento compuesto no representable" in caso.motivo


# --- R19 · sin sv2 si no se piden IA1 ni IA2 -----------------------------------


def test_f084_r19_sin_ia1_ni_ia2_no_se_invoca_sv2_ni_sus_claves(tmp_path, subprocesos, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fixtures = _banco(tmp_path, _inputs("HOR-001"))
    (fixtures / "IA1").mkdir()
    (fixtures / "IA1" / "HOR-001.json").write_text(json.dumps({"caso_id": "HOR-001", "tablas": {}}),
                                                     encoding="utf-8")

    fases, _ = runner.corrida_completa(fixtures, fases=["IA3", "IA4", "E2E"])

    assert _fase(fases, "IA1").casos == [] and _fase(fases, "IA1").proveedores == []
    assert _fase(fases, "IA3").casos[0].caso_id == "HOR-001"


def test_f084_r19_por_cli_tampoco(tmp_path, subprocesos, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    fixtures = _banco(tmp_path, _inputs("HOR-001"))

    codigo = runner.main(["--con-llm", "--fases", "IA3,IA4,E2E", "--fixtures", str(fixtures),
                          "--informes", str(tmp_path / "informes"), "--feature", "F-084-test"])

    assert codigo in (0, 1)


def test_f084_r19_las_claves_de_sv5_se_exigen_antes_de_nada(tmp_path, subprocesos, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fixtures = _banco(tmp_path, _inputs("HOR-001"))

    with pytest.raises(sv5_valoracion.ClavesAusentes, match="OPENAI_API_KEY"):
        runner.corrida_completa(fixtures, fases=["IA3", "IA4", "E2E"])
    assert subprocesos[1].trabajos == []


# --- R20 · proveedor y modelo de producción por defecto ------------------------


def test_f084_r20_sin_nada_se_valora_con_la_referencia_de_produccion():
    tabla = cargar_tabla()
    referencia = tabla.modelo(tabla.referencia("IA3"))

    assert runner.valoracion_por_defecto(None, entorno={}) == (referencia.proveedor, referencia.id)


def test_f084_r20_la_referencia_de_ia3_es_la_de_infra_tras_f085():
    """La misma fuente que vigila R3 de F-083 contra `infra/create_capps.ps1`."""
    assert runner.valoracion_por_defecto(None, entorno={}) == ("openai", "gpt-6.1-sol")


def test_f084_r20_ia3_provider_del_entorno_manda():
    proveedor, modelo = runner.valoracion_por_defecto(None, entorno={"IA3_PROVIDER": " Claude "})

    assert proveedor == "claude"
    assert modelo == sv5_valoracion.MODELOS_POR_PROVEEDOR["claude"][1]


def test_f084_r20_la_variable_de_modelo_del_proveedor_manda_sobre_la_referencia():
    assert runner.valoracion_por_defecto(None, entorno={"OPENAI_MODEL": "gpt-otro"}) == (
        "openai", "gpt-otro",
    )
    assert runner.valoracion_por_defecto(
        None, entorno={"IA3_PROVIDER": "claude", "ANTHROPIC_MODEL": "claude-opus-4-8"}
    ) == ("claude", "claude-opus-4-8")


def test_f084_r20_proveedores_explicitos_mandan_sobre_el_entorno():
    assert runner.valoracion_por_defecto(["gemini"], entorno={"IA3_PROVIDER": "claude"})[0] == "gemini"


def test_f084_r20_un_proveedor_desconocido_es_un_error_de_uso():
    with pytest.raises(runner.UsoIncorrecto, match="IA3_PROVIDER"):
        runner.valoracion_por_defecto(None, entorno={"IA3_PROVIDER": "mistral"})


def test_f084_r20_el_trabajo_de_sv5_lleva_proveedor_y_modelo(tmp_path, subprocesos):
    _, sv5 = subprocesos
    fixtures = _banco(tmp_path, _inputs("HOR-001"))

    fases, _ = runner.corrida_completa(fixtures, fases=["IA3", "IA4", "E2E"])

    assert (sv5.trabajos[0]["proveedor"], sv5.trabajos[0]["modelo"]) == ("openai", "gpt-6.1-sol")
    assert _fase(fases, "IA3").proveedores == ["openai"]


# --- T9 · modelo, documento y emparejamiento en el informe (R17, R21, R36) -----

from evals import informe
from evals.modelos import ResultadoCaso, ResultadoFase, ResultadoPasada


def _bloques(texto: str) -> dict[str, str]:
    """El texto de cada bloque de fase del informe, por su nombre corto."""
    bloques = {}
    for trozo in texto.split("\n## ")[1:]:
        nombre = "E2E" if trozo.startswith("Extremo a extremo") else trozo.split(" ", 1)[0]
        bloques[nombre] = trozo
    return bloques


def _pasada(modo: str, **por_fase) -> ResultadoPasada:
    fases = []
    for nombre in ("IA1", "IA3", "IA4", "E2E"):
        fase = ResultadoFase(nombre=nombre, proveedores=["openai"], **por_fase.get(nombre, {}))
        fase.casos.append(ResultadoCaso(caso_id="HOR-001", fase=nombre))
        fases.append(fase)
    return ResultadoPasada(modo=modo, fases=fases, feature="F-084", commit="abc", fecha="hoy")


def test_f084_r21_el_informe_registra_el_modelo_de_cada_fase_de_valoracion():
    pasada = _pasada(
        informe.MODO_COMPLETA,
        IA3={"modelos": ["gpt-6.1-sol"]}, IA4={"modelos": ["gpt-6.1-sol"]},
        E2E={"modelos": ["gpt-6.1-sol"]},
    )

    bloques = _bloques(informe.render(pasada))

    for nombre in ("IA3", "IA4", "E2E"):
        assert "- Proveedores invocados: openai" in bloques[nombre]
        assert "- Modelo: gpt-6.1-sol" in bloques[nombre]
    assert "- Modelo:" not in bloques["IA1"]


def test_f084_r21_sin_modelo_lo_dice():
    bloques = _bloques(informe.render(_pasada(informe.MODO_DETERMINISTA)))

    assert "- Modelo: (ninguno: sin llamadas LLM)" in bloques["IA3"]


def test_f084_r21_las_lineas_parseables_no_cambian():
    texto = informe.render(_pasada(informe.MODO_COMPLETA, IA3={"modelos": ["m"]}))
    parseable = texto.split("```")[1].strip().splitlines()

    assert parseable == ["MODO: completa", "FASES: IA1,IA3,IA4,E2E", "PROVEEDORES: openai"]
    assert informe.parsear_veredicto(texto) == "VERDE"
    assert texto.rstrip().splitlines()[-1] == "VEREDICTO: VERDE"


def test_f084_r17_el_informe_declara_con_que_documento_se_valoro():
    pasada = _pasada(informe.MODO_COMPLETA, IA3={"documentos": {"md": 2, "ninguno": 1}})

    bloques = _bloques(informe.render(pasada))

    assert "- Documento del contrato: md 2 · pdf 0 · ninguno 1" in bloques["IA3"]


def test_f084_r36_el_determinista_declara_que_no_mide_el_emparejamiento():
    bloques = _bloques(informe.render(_pasada(informe.MODO_DETERMINISTA)))

    for nombre in ("IA3", "IA4", "E2E"):
        assert "NO mide el emparejamiento" in bloques[nombre]
        assert "`?`" in bloques[nombre] and "--con-llm" in bloques[nombre]
    assert "emparejamiento" not in bloques["IA1"]


def test_f084_r36_la_corrida_con_llm_no_lleva_la_advertencia():
    texto = informe.render(_pasada(informe.MODO_COMPLETA))

    assert "NO mide el emparejamiento" not in texto


def test_f084_r21_r17_la_corrida_con_llm_rellena_modelo_y_documentos(tmp_path, subprocesos, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "CT_HOR-002.md").write_bytes(b"# C")
    monkeypatch.setattr(runner, "RUTA_CACHE", cache)
    fixtures = _banco(tmp_path, _inputs("HOR-001"), _inputs("HOR-002"), _inputs("HOR-003", lineas_contrato=False),
                      indice=_indice_md("HOR-002"))

    fases, _ = runner.corrida_completa(fixtures, fases=["IA3", "IA4", "E2E"])

    for nombre in ("IA3", "IA4", "E2E"):
        assert _fase(fases, nombre).modelos == ["modelo-servido"]
        assert _fase(fases, nombre).documentos == {"md": 1, "pdf": 0, "ninguno": 1}


def test_f084_r21_si_sv5_no_dice_el_modelo_vale_el_pedido(tmp_path, subprocesos):
    _, sv5 = subprocesos
    sv5.modelo = None
    fixtures = _banco(tmp_path, _inputs("HOR-001"))

    fases, _ = runner.corrida_completa(fixtures, fases=["IA3"])

    assert _fase(fases, "IA3").modelos == ["gpt-6.1-sol"]


def test_f084_r36_el_informe_determinista_del_runner_lleva_la_advertencia(tmp_path, subprocesos):
    fixtures = _banco(tmp_path, _inputs("HOR-001"))

    runner.main(["--fixtures", str(fixtures), "--informes", str(tmp_path), "--feature", "F-084-t"])

    texto = (tmp_path / "evals_F-084-t.md").read_text(encoding="utf-8")
    assert texto.count("NO mide el emparejamiento") == 3


# --- T11 · R24: los 7 RES siguen igual ------------------------------------------

#: sha256 de lo afirmado por el humano en `tests/datos/afirmado_por_el_humano_RES.json`
#: FUERA de IA1 (INPUTS, IA2, IA3, RESULTADO_FINAL): idéntico en `efd73b7` (la base
#: de la spec) y en `dev` `2721e06`. La corrección del banco IA1 de `dev`
#: (chore/banco-correcciones: CIF añadido y cantidades a «?») solo toca claves
#: `IA1.*`, que F-084 no evalúa; se excluyen para que el guardián mire lo suyo.
_SHA_AFIRMADO_RES_SIN_IA1 = "b7cdb1a899a077eab11bf44a086d27866cfa3fcaa963ee4754c5f1a75bb56d50"

#: Fallos críticos del determinista en `efd73b7`, por caso y fase: el techo.
_FALLOS_BASE_RES = {
    **{(f"RES-00{n}", fase): 0 for n in range(1, 7) for fase in ("IA3", "E2E")},
    ("RES-007", "IA3"): 4,
    ("RES-007", "E2E"): 6,
}


def test_f084_r24_lo_afirmado_por_el_humano_no_cambia():
    datos = json.loads(
        (RAIZ / "tests" / "datos" / "afirmado_por_el_humano_RES.json").read_text(encoding="utf-8")
    )
    fuera_de_ia1 = {k: v for k, v in datos["valores"].items() if not k.startswith("IA1.")}
    huella = json.dumps(fuera_de_ia1, sort_keys=True, ensure_ascii=False).encode("utf-8")

    assert len(fuera_de_ia1) == 419
    assert hashlib.sha256(huella).hexdigest() == _SHA_AFIRMADO_RES_SIN_IA1


def test_f084_r24_el_determinista_de_los_7_res_no_empeora():
    from evals.conversor import RUTA_FIXTURES

    casos = [f"RES-00{n}" for n in range(1, 8)]
    fases, _ = runner.corrida_determinista(RUTA_FIXTURES, casos)

    obtenidos = {
        (caso.caso_id, fase.nombre): len(caso.fallos)
        for fase in fases if fase.nombre in ("IA3", "E2E")
        for caso in fase.casos
    }
    assert set(obtenidos) == set(_FALLOS_BASE_RES)
    for clave, techo in _FALLOS_BASE_RES.items():
        assert obtenidos[clave] <= techo, clave
    assert all(c.estado != OMITIDO for f in fases if f.nombre != "IA4" for c in f.casos)


def test_f084_r33_el_determinista_de_los_7_res_no_depende_de_la_cache(tmp_path, monkeypatch):
    """Un clon limpio tras T13: el índice versionado declara documentos y no hay caché.

    El guardián de R24 y los tests de F-083 sobre RES deben seguir en verde.
    """
    import shutil

    from evals.conversor import RUTA_FIXTURES

    fixtures = tmp_path / "fixtures"
    shutil.copytree(RUTA_FIXTURES, fixtures)
    casos = [f"RES-00{n}" for n in range(1, 8)]
    codigos = {
        json.loads((fixtures / "inputs" / f"{caso}.json").read_text(encoding="utf-8"))
        ["tablas"]["caso"][0]["contrato_codigo"]
        for caso in casos
    }
    runner.ruta_indice(fixtures).parent.mkdir(exist_ok=True)
    runner.ruta_indice(fixtures).write_text(json.dumps(
        {codigo: {"tipo": "md", "sha256": "0" * 64, "bytes": 1, "motivo": ""} for codigo in codigos}
    ), encoding="utf-8")
    monkeypatch.setattr(runner, "RUTA_CACHE", tmp_path / "sin-cache")

    fases, _ = runner.corrida_determinista(fixtures, casos)

    assert all(c.estado != OMITIDO for f in fases if f.nombre != "IA4" for c in f.casos)
    obtenidos = {
        (caso.caso_id, fase.nombre): len(caso.fallos)
        for fase in fases if fase.nombre in ("IA3", "E2E")
        for caso in fase.casos
    }
    assert set(obtenidos) == set(_FALLOS_BASE_RES)
    for clave, techo in _FALLOS_BASE_RES.items():
        assert obtenidos[clave] <= techo, clave
