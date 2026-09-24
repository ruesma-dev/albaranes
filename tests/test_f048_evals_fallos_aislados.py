# tests/test_f048_evals_fallos_aislados.py
"""F-048 · Runner de evals: un caso que falla no tumba la pasada entera.

El 2026-09-24 la pasada `python -m evals.runner --con-llm --feature F-048`
murió a los 50 minutos sin informe: en UN caso, IA2 devolvió un JSON
degenerado (una racha de ceros cortada a 59.877 caracteres), pydantic lanzó
`json_invalid`, el subproceso de sv2 salió con código 1 y el runner no lo
capturaba. Se perdieron los resultados de todos los demás casos y el log no
decía qué caso era.

Lo que fijan estos tests, sin red ni LLM (dobles del extractor):

- En el HIJO, cada caso y cada proveedor van aislados: el error queda en el
  resultado de ESE caso (fase, tipo, motivo corto) y el bucle sigue.
- En el PADRE, un caso con error sale OMITIDO con su motivo y el informe se
  escribe; si el subproceso entero muere, la fase queda NO_EVALUABLE con
  motivo en vez de una traza sin informe.
- El motivo NO lleva valores del albarán (R31 de F-047): el `input_value` de
  pydantic lleva la respuesta del LLM, y aquí va un centinela para probarlo.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pydantic
import pytest

import evals.procesos.sv2_extraccion as sv2
import evals.procesos.sv5_valoracion as sv5
import evals.procesos.sv6_build as sv6
from evals import runner
from evals.modelos import NO_EVALUABLE, OMITIDO
from evals.procesos.errores import describir_error

#: Lo que NUNCA puede aparecer en un motivo: va dentro de la respuesta del LLM.
CENTINELA = "CENTINELA-VALOR-DEL-ALBARAN-7731"


class _Revision(pydantic.BaseModel):
    documento_revisado: dict


class _Linea(pydantic.BaseModel):
    cantidad: float


def _json_degenerado() -> pydantic.ValidationError:
    """Lo que pasó de verdad: JSON cortado a media racha de ceros."""
    # El centinela va al FINAL: pydantic recorta el centro de `input_value`.
    respuesta = '{"documento_revisado": {"nota": "' + "0" * 3000 + CENTINELA
    with pytest.raises(pydantic.ValidationError) as error:
        _Revision.model_validate_json(respuesta)
    # `str()` recorta el centro de `input_value`; `errors()` lo lleva entero.
    assert CENTINELA in str(error.value.errors()[0]["input"]), "el doble debe llevar el valor"
    return error.value


def _tipo_erroneo() -> pydantic.ValidationError:
    with pytest.raises(pydantic.ValidationError) as error:
        _Linea.model_validate({"cantidad": CENTINELA})
    assert CENTINELA in str(error.value.errors()[0]["input"])
    return error.value


# --- La descripción del error: forma, nunca texto --------------------------


def test_f048_evals_el_json_degenerado_se_describe_por_tipo_y_posicion():
    descripcion = describir_error(_json_degenerado(), "IA2")

    assert descripcion["fase"] == "IA2"
    assert descripcion["tipo"] == "ValidationError"
    assert "json_invalid" in descripcion["motivo"]
    assert "línea 1" in descripcion["motivo"]
    assert "columna" in descripcion["motivo"]
    assert CENTINELA not in descripcion["motivo"]
    assert "000" not in descripcion["motivo"]


def test_f048_evals_un_error_de_tipo_da_la_ubicacion_sin_el_valor():
    descripcion = describir_error(_tipo_erroneo(), "IA1")

    assert "float_parsing" in descripcion["motivo"]
    assert "cantidad" in descripcion["motivo"]
    assert CENTINELA not in descripcion["motivo"]


def test_f048_evals_de_una_excepcion_cualquiera_no_se_copia_el_texto():
    descripcion = describir_error(ValueError(f"precio {CENTINELA}"), "IA1")

    assert descripcion["tipo"] == "ValueError"
    assert CENTINELA not in descripcion["motivo"]


def test_f048_evals_un_json_roto_de_la_libreria_estandar_da_su_posicion():
    with pytest.raises(json.JSONDecodeError) as error:
        json.loads('{"a": "' + CENTINELA)

    descripcion = describir_error(error.value, "IA1")

    assert "línea 1" in descripcion["motivo"]
    assert CENTINELA not in descripcion["motivo"]


def test_f048_evals_un_error_http_del_proveedor_da_su_codigo():
    error = RuntimeError(f"cuerpo {CENTINELA}")
    error.status_code = 503

    descripcion = describir_error(error, "IA2")

    assert "HTTP 503" in descripcion["motivo"]
    assert CENTINELA not in descripcion["motivo"]


def test_f048_evals_el_motivo_es_corto_aunque_haya_muchos_errores():
    class _Muchos(pydantic.BaseModel):
        a: int
        b: int
        c: int
        d: int
        e: int

    with pytest.raises(pydantic.ValidationError) as error:
        _Muchos.model_validate({})

    motivo = describir_error(error.value, "IA1")["motivo"]

    assert "(+2 más)" in motivo
    assert len(motivo) <= 200


# --- Hijo de sv2: cada caso y cada proveedor, aislados ---------------------


def _respuesta(documento: dict):
    return SimpleNamespace(parsed=SimpleNamespace(model_dump=lambda: documento))


_DOC_IA1 = {"cabecera": {"numero_albaran": "A-1"}, "lineas": [{"concepto": "x"}]}
_DOC_IA2 = {
    "documento_revisado": {
        "cabecera": {"numero_albaran": "A-1"},
        "lineas": [{"concepto": "x", "contexto_linea": {"tipo_familia": "hormigon"}}],
    }
}


class _ExtractorDoble:
    """sv2 de mentira: IA1 va siempre bien; IA2 revienta en los casos pedidos."""

    def __init__(self, falla_ia1=(), falla_ia2=()):
        self.falla_ia1 = set(falla_ia1)
        self.falla_ia2 = set(falla_ia2)
        self.llamadas: list[tuple[str, str]] = []

    def extract_phase_1(self, attachments, provider, prompt_key):
        self.llamadas.append(("IA1", attachments))
        if attachments in self.falla_ia1:
            raise _tipo_erroneo()
        return _respuesta(_DOC_IA1)

    def review_phase_2(self, attachments, provider, prompt_key, phase_1_json):
        self.llamadas.append(("IA2", attachments))
        if attachments in self.falla_ia2:
            raise _json_degenerado()
        return _respuesta(_DOC_IA2)


def _casos(*ids):
    return [{"caso_id": i, "fichero": f"{i}.pdf", "tipologia": "Hormigon"} for i in ids]


def _adjuntos_de_mentira(ruta):
    """El «adjunto» es el propio caso_id: así el doble sabe en qué caso está."""
    return ruta.stem


def test_f048_evals_sv2_un_ia2_roto_no_se_lleva_por_delante_a_los_demas(capsys):
    extractor = _ExtractorDoble(falla_ia2={"HOR-002"})

    resultados = sv2.procesar_casos(
        _casos("HOR-001", "HOR-002", "HOR-003"), ["openai"], extractor, _adjuntos_de_mentira
    )

    assert [r["caso_id"] for r in resultados] == ["HOR-001", "HOR-002", "HOR-003"]
    assert resultados[0]["proveedores"]["openai"]["ia2"] == _DOC_IA2["documento_revisado"]
    assert "error" not in resultados[0]["proveedores"]["openai"]
    roto = resultados[1]["proveedores"]["openai"]
    assert roto["ia1"] == _DOC_IA1, "IA1 fue bien: su resultado no se pierde"
    assert roto["ia2"] is None
    assert roto["error"]["fase"] == "IA2"
    assert roto["error"]["tipo"] == "ValidationError"
    assert "json_invalid" in roto["error"]["motivo"]
    assert CENTINELA not in json.dumps(resultados)
    assert resultados[2]["proveedores"]["openai"]["ia2"] is not None


def test_f048_evals_sv2_si_falla_ia1_no_se_llama_a_ia2_de_ese_caso():
    extractor = _ExtractorDoble(falla_ia1={"HOR-001"})

    resultados = sv2.procesar_casos(
        _casos("HOR-001", "HOR-002"), ["gemini"], extractor, _adjuntos_de_mentira
    )

    roto = resultados[0]["proveedores"]["gemini"]
    assert roto["error"]["fase"] == "IA1"
    assert roto["ia1"] is None and roto["ia2"] is None
    assert ("IA2", "HOR-001") not in extractor.llamadas
    assert resultados[1]["proveedores"]["gemini"]["ia1"] == _DOC_IA1


def test_f048_evals_sv2_un_proveedor_roto_no_tumba_al_otro_del_mismo_caso():
    class _PorProveedor(_ExtractorDoble):
        def review_phase_2(self, attachments, provider, prompt_key, phase_1_json):
            if provider == "openai":
                raise _json_degenerado()
            return _respuesta(_DOC_IA2)

    resultados = sv2.procesar_casos(
        _casos("HOR-001"), ["gemini", "openai"], _PorProveedor(), _adjuntos_de_mentira
    )

    assert "error" not in resultados[0]["proveedores"]["gemini"]
    assert resultados[0]["proveedores"]["openai"]["error"]["fase"] == "IA2"


def test_f048_evals_sv2_un_albaran_que_no_se_puede_preprocesar_se_aisla():
    def adjuntos(ruta):
        if ruta.stem == "HOR-001":
            raise OSError(f"no se puede leer {CENTINELA}")
        return ruta.stem

    resultados = sv2.procesar_casos(
        _casos("HOR-001", "HOR-002"), ["gemini"], _ExtractorDoble(), adjuntos
    )

    assert resultados[0]["proveedores"] == {}
    assert resultados[0]["error"]["fase"] == "preproceso"
    assert CENTINELA not in json.dumps(resultados)
    assert resultados[1]["proveedores"]["gemini"]["ia1"] == _DOC_IA1


def test_f048_evals_sv2_el_log_dice_que_caso_fallo_y_sin_valores(capsys):
    sv2.procesar_casos(
        _casos("HOR-001", "HOR-002"),
        ["openai"],
        _ExtractorDoble(falla_ia2={"HOR-002"}),
        _adjuntos_de_mentira,
    )

    log = capsys.readouterr().err
    assert "caso HOR-001, proveedor openai: ok" in log
    assert "caso HOR-002, proveedor openai: error en IA2" in log
    assert "json_invalid" in log
    assert CENTINELA not in log


# --- Padre: el caso roto sale OMITIDO con motivo y el informe se escribe ----


def _banco_ia1_ia2(tmp_path, *ids):
    fixtures = tmp_path / "fixtures"
    albaranes = tmp_path / "albaranes"
    albaranes.mkdir()
    for fase in ("IA1", "IA2"):
        (fixtures / fase).mkdir(parents=True)
    for caso_id in ids:
        (albaranes / f"{caso_id}.pdf").write_bytes(b"%PDF-1.4")
        for fase in ("IA1", "IA2"):
            (fixtures / fase / f"{caso_id}.json").write_text(
                json.dumps({"caso_id": caso_id, "tipologia": "Hormigon", "tablas": {}}),
                encoding="utf-8",
            )
    return fixtures, albaranes


def _sv2_en_proceso(extractor):
    """El subproceso de sv2 sustituido por su bucle real con el doble."""

    def ejecutar(trabajo, interprete=None):
        from pathlib import Path

        resultados = sv2.procesar_casos(
            trabajo["casos"],
            trabajo["proveedores"],
            extractor,
            lambda ruta: Path(ruta).stem,
        )
        # Ida y vuelta por JSON, como el canal real.
        return json.loads(json.dumps({"resultados": resultados}))

    return ejecutar


@pytest.fixture
def pasada_con_llm(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("OPENAI_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("IA_PRIMERA_FASE", "openai")
    monkeypatch.setenv("IA_SEGUNDA_FASE", "openai")

    def prohibido(*args, **kwargs):  # pragma: no cover - no debe llamarse
        raise AssertionError("sin inputs no se llama a sv5")

    monkeypatch.setattr(sv5, "ejecutar_en_subproceso", prohibido)


def test_f048_evals_runner_el_caso_roto_sale_omitido_y_el_resto_se_evalua(
    tmp_path, monkeypatch, pasada_con_llm
):
    fixtures, albaranes = _banco_ia1_ia2(tmp_path, "HOR-001", "HOR-002")
    monkeypatch.setattr(
        sv2, "ejecutar_en_subproceso", _sv2_en_proceso(_ExtractorDoble(falla_ia2={"HOR-002"}))
    )

    fases, _ = runner.corrida_completa(fixtures, directorio_albaranes=albaranes)

    ia1 = next(f for f in fases if f.nombre == "IA1")
    ia2 = next(f for f in fases if f.nombre == "IA2")
    assert {c.caso_id: c.estado for c in ia1.casos} == {
        "HOR-001/openai": "VERDE",
        "HOR-002/openai": "VERDE",
    }
    estados = {c.caso_id: c for c in ia2.casos}
    assert estados["HOR-001/openai"].estado == "VERDE"
    roto = estados["HOR-002/openai"]
    assert roto.estado == OMITIDO
    assert roto.motivo.startswith("ERROR en IA2")
    assert "json_invalid" in roto.motivo
    assert CENTINELA not in roto.motivo


def test_f048_evals_runner_si_falla_ia1_ia2_tampoco_se_evalua(
    tmp_path, monkeypatch, pasada_con_llm
):
    fixtures, albaranes = _banco_ia1_ia2(tmp_path, "HOR-001")
    monkeypatch.setattr(
        sv2, "ejecutar_en_subproceso", _sv2_en_proceso(_ExtractorDoble(falla_ia1={"HOR-001"}))
    )

    fases, _ = runner.corrida_completa(fixtures, directorio_albaranes=albaranes)

    ia1 = next(f for f in fases if f.nombre == "IA1")
    ia2 = next(f for f in fases if f.nombre == "IA2")
    assert ia1.casos[0].estado == OMITIDO and ia1.casos[0].motivo.startswith("ERROR en IA1")
    assert ia2.casos[0].estado == OMITIDO and "falló IA1" in ia2.casos[0].motivo


def test_f048_evals_runner_un_caso_que_sv2_no_devuelve_se_declara(
    tmp_path, monkeypatch, pasada_con_llm
):
    fixtures, albaranes = _banco_ia1_ia2(tmp_path, "HOR-001")
    monkeypatch.setattr(sv2, "ejecutar_en_subproceso", lambda *a, **k: {"resultados": []})

    fases, _ = runner.corrida_completa(fixtures, directorio_albaranes=albaranes)

    ia1 = next(f for f in fases if f.nombre == "IA1")
    assert [c.estado for c in ia1.casos] == [OMITIDO]
    assert "sv2 no devolvió resultado" in ia1.casos[0].motivo


def test_f048_evals_runner_si_muere_el_subproceso_de_sv2_la_fase_queda_no_evaluable(
    tmp_path, monkeypatch, pasada_con_llm, capsys
):
    fixtures, albaranes = _banco_ia1_ia2(tmp_path, "HOR-001")

    def muere(trabajo, interprete=None):
        raise RuntimeError(f"el subproceso de sv2 falló con código 1:\n{CENTINELA}")

    monkeypatch.setattr(sv2, "ejecutar_en_subproceso", muere)

    fases, _ = runner.corrida_completa(fixtures, directorio_albaranes=albaranes)

    for nombre in ("IA1", "IA2"):
        fase = next(f for f in fases if f.nombre == nombre)
        assert fase.veredicto() == NO_EVALUABLE
        assert "subproceso de sv2" in fase.motivo
        assert CENTINELA not in fase.motivo
        assert all(CENTINELA not in c.motivo for c in fase.casos)
    assert CENTINELA in capsys.readouterr().err, "el detalle va a la consola, no al informe"


def test_f048_evals_runner_con_un_caso_roto_el_informe_se_escribe_sin_valores(
    tmp_path, monkeypatch, pasada_con_llm
):
    fixtures, albaranes = _banco_ia1_ia2(tmp_path, "HOR-001", "HOR-002")
    monkeypatch.setattr(sv2, "RUTA_ALBARANES", albaranes)
    monkeypatch.setattr(
        sv2, "ejecutar_en_subproceso", _sv2_en_proceso(_ExtractorDoble(falla_ia2={"HOR-001"}))
    )

    codigo = runner.main(
        [
            "--con-llm",
            "--fases",
            "IA1,IA2",
            "--feature",
            "F-999",
            "--fixtures",
            str(fixtures),
            "--informes",
            str(tmp_path / "progress"),
        ]
    )

    informe = (tmp_path / "progress" / "evals_F-999.md").read_text(encoding="utf-8")
    assert codigo in (0, 1, 2)
    assert "HOR-002/openai | VERDE" in informe
    assert "HOR-001/openai | OMITIDO" in informe
    assert "json_invalid" in informe
    assert CENTINELA not in informe


def test_f048_evals_runner_si_muere_sv2_el_informe_se_escribe_igual(
    tmp_path, monkeypatch, pasada_con_llm
):
    fixtures, albaranes = _banco_ia1_ia2(tmp_path, "HOR-001")
    monkeypatch.setattr(sv2, "RUTA_ALBARANES", albaranes)

    def muere(trabajo, interprete=None):
        raise RuntimeError(CENTINELA)

    monkeypatch.setattr(sv2, "ejecutar_en_subproceso", muere)

    codigo = runner.main(
        ["--con-llm", "--fases", "IA1,IA2", "--feature", "F-999", "--fixtures",
         str(fixtures), "--informes", str(tmp_path / "progress")]
    )

    informe = (tmp_path / "progress" / "evals_F-999.md").read_text(encoding="utf-8")
    assert codigo == 2
    assert "VEREDICTO: NO_EVALUABLE" in informe
    assert "subproceso de sv2" in informe
    assert CENTINELA not in informe


# --- sv5 (IA3 + IA4): el mismo agujero, el mismo arreglo --------------------


def test_f048_evals_sv5_un_caso_roto_no_se_lleva_por_delante_a_los_demas(capsys):
    def valorar(contexto):
        if contexto["id"] == "HOR-001":
            raise _json_degenerado()
        return [{"line_id": 1}]

    resultados = sv5.procesar_casos(
        [
            {"caso_id": "HOR-001", "contexto": {"id": "HOR-001"}},
            {"caso_id": "HOR-002", "contexto": {"id": "HOR-002"}},
        ],
        "gemini",
        valorar=valorar,
        construir_envelope=lambda contexto, lineas: {"lineas": lineas},
        conciliar=lambda envelope, contexto: [],
    )

    assert resultados[0]["caso_id"] == "HOR-001"
    assert resultados[0]["error"]["fase"] == "IA3"
    assert "json_invalid" in resultados[0]["error"]["motivo"]
    assert resultados[1]["envelope"] == {"lineas": [{"line_id": 1}]}
    log = capsys.readouterr().err
    assert "caso HOR-001, proveedor gemini: error en IA3" in log
    assert "caso HOR-002, proveedor gemini: ok" in log
    assert CENTINELA not in log + json.dumps(resultados)


def test_f048_evals_sv5_un_ia4_roto_se_declara_como_ia4():
    def conciliar(envelope, contexto):
        raise _tipo_erroneo()

    resultados = sv5.procesar_casos(
        [{"caso_id": "HOR-001", "contexto": {}}],
        "gemini",
        valorar=lambda contexto: [],
        construir_envelope=lambda contexto, lineas: {},
        conciliar=conciliar,
    )

    assert resultados[0]["error"]["fase"] == "IA4"


def _banco_valoracion(tmp_path, *ids):
    fixtures = tmp_path / "fixtures"
    for fase in ("inputs", "IA3", "IA4", "final"):
        (fixtures / fase).mkdir(parents=True)
        for caso_id in ids:
            (fixtures / fase / f"{caso_id}.json").write_text(
                json.dumps({"caso_id": caso_id, "tablas": {}}), encoding="utf-8"
            )
    return fixtures


@pytest.fixture
def valoracion_sin_servicios(monkeypatch):
    """Todo lo que la valoración necesita de sv5/sv6, sin subprocesos."""
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(sv5, "construir_contexto", lambda datos: {"caso": datos["caso_id"]})
    monkeypatch.setattr(sv5, "proyectar_ia4", lambda conciliaciones, envelope: [])
    monkeypatch.setattr(
        sv6,
        "evaluar_caso_determinista",
        lambda **kwargs: SimpleNamespace(discrepancias=[], no_observables=[]),
    )
    monkeypatch.setattr(sv6, "construir_envelope_estimulado", lambda datos, ia3: {})
    monkeypatch.setattr(sv5, "conciliaciones_desde_ground_truth", lambda ia4, env: [])
    monkeypatch.setattr(sv5, "aplicar_conciliacion", lambda env, conc: 0)
    llamadas = {"sv6": []}

    def sv6_doble(trabajo, interprete=None):
        llamadas["sv6"].append([c["caso_id"] for c in trabajo["casos"]])
        return {
            "resultados": [
                {"caso_id": c["caso_id"], "header": {}, "lineas": []} for c in trabajo["casos"]
            ]
        }

    monkeypatch.setattr(sv6, "ejecutar_en_subproceso", sv6_doble)
    return llamadas


def _fase(fases, nombre):
    return next(f for f in fases if f.nombre == nombre)


def test_f048_evals_runner_un_caso_roto_en_sv5_sale_omitido_en_ia3_ia4_y_e2e(
    tmp_path, monkeypatch, valoracion_sin_servicios
):
    fixtures = _banco_valoracion(tmp_path, "HOR-001", "HOR-002")
    monkeypatch.setattr(
        sv5,
        "ejecutar_en_subproceso",
        lambda trabajo, interprete=None: {
            "resultados": [
                {
                    "caso_id": "HOR-001",
                    "error": {"fase": "IA3", "tipo": "ValidationError", "motivo": "ValidationError: json_invalid"},
                },
                {"caso_id": "HOR-002", "envelope": {}, "conciliaciones": []},
            ]
        },
    )

    fases, _ = runner._corrida_valoracion_real(
        *(runner.cargar_fixtures(fixtures, f) for f in ("inputs", "IA3", "IA4", "final")),
        criticidad=runner.cargar_criticidad(),
        proveedores=["gemini"],
    )

    for nombre in ("IA3", "IA4", "E2E"):
        casos = {c.caso_id: c for c in _fase(fases, nombre).casos}
        assert casos["HOR-001"].estado == OMITIDO
        assert "ERROR en IA3" in casos["HOR-001"].motivo
        assert casos["HOR-002"].estado == "VERDE"
    assert valoracion_sin_servicios["sv6"] == [["HOR-002"]], "el caso roto no va a sv6"


def test_f048_evals_runner_si_muere_sv5_la_valoracion_queda_no_evaluable(
    tmp_path, monkeypatch, valoracion_sin_servicios, capsys
):
    fixtures = _banco_valoracion(tmp_path, "HOR-001")

    def muere(trabajo, interprete=None):
        raise RuntimeError(CENTINELA)

    monkeypatch.setattr(sv5, "ejecutar_en_subproceso", muere)

    fases, _ = runner._corrida_valoracion_real(
        *(runner.cargar_fixtures(fixtures, f) for f in ("inputs", "IA3", "IA4", "final")),
        criticidad=runner.cargar_criticidad(),
        proveedores=["gemini"],
    )

    for nombre in ("IA3", "IA4", "E2E"):
        fase = _fase(fases, nombre)
        assert fase.veredicto() == NO_EVALUABLE
        assert "subproceso de sv5" in fase.motivo
        assert CENTINELA not in fase.motivo
    assert valoracion_sin_servicios["sv6"] == []
    assert CENTINELA in capsys.readouterr().err


# --- sv6 (build): el mismo agujero, el mismo arreglo -------------------------


def test_f048_evals_sv6_un_envelope_roto_no_se_lleva_por_delante_a_los_demas(capsys):
    def construir(caso):
        if caso["caso_id"] == "HOR-001":
            raise _tipo_erroneo()
        return {"header": {"ok": True}, "lineas": []}

    resultados = sv6.procesar_casos(
        [{"caso_id": "HOR-001"}, {"caso_id": "HOR-002"}], construir
    )

    assert resultados[0]["error"]["fase"] == "build"
    assert resultados[1] == {"caso_id": "HOR-002", "header": {"ok": True}, "lineas": []}
    log = capsys.readouterr().err
    assert "caso HOR-001: error en build" in log
    assert "caso HOR-002: ok" in log
    assert CENTINELA not in log + json.dumps(resultados)


def test_f048_evals_sv6_real_un_envelope_invalido_no_tumba_el_subproceso():
    """Subproceso REAL de sv6 (sin red): uno inválido y uno válido."""
    valido = {
        "status": "ok",
        "meta": {"document_id": "HOR-002"},
        "data": {"lineas": []},
        "context": {"lineas_albaran": [], "lineas_contrato": []},
    }
    invalido = {**valido, "data": {"lineas": CENTINELA}}

    salida = sv6.ejecutar_en_subproceso(
        {
            "casos": [
                {"caso_id": "HOR-001", "envelope": invalido},
                {"caso_id": "HOR-002", "envelope": valido},
            ]
        }
    )

    roto, bueno = salida["resultados"]
    assert roto["caso_id"] == "HOR-001" and roto["error"]["tipo"] == "ValidationError"
    assert CENTINELA not in json.dumps(roto)
    assert bueno["caso_id"] == "HOR-002" and "header" in bueno


def test_f048_evals_runner_un_build_roto_omite_ia3_y_e2e_pero_no_ia4(
    tmp_path, monkeypatch, valoracion_sin_servicios
):
    fixtures = _banco_valoracion(tmp_path, "HOR-001", "HOR-002")

    def sv6_con_un_roto(trabajo, interprete=None):
        return {
            "resultados": [
                {"caso_id": "HOR-001", "error": {"fase": "build", "tipo": "ValidationError", "motivo": "ValidationError: list_type en data.lineas"}},
                {"caso_id": "HOR-002", "header": {}, "lineas": []},
            ]
        }

    monkeypatch.setattr(sv6, "ejecutar_en_subproceso", sv6_con_un_roto)

    fases, _ = runner.corrida_determinista(fixtures)

    for nombre in ("IA3", "E2E"):
        casos = {c.caso_id: c for c in _fase(fases, nombre).casos}
        assert casos["HOR-001"].estado == OMITIDO
        assert "ERROR en el build de sv6" in casos["HOR-001"].motivo
        assert casos["HOR-002"].estado == "VERDE"
    ia4 = {c.caso_id: c for c in _fase(fases, "IA4").casos}
    assert ia4["HOR-001"].estado == "VERDE", "IA4 no depende del build de sv6"


def test_f048_evals_runner_si_muere_sv6_la_corrida_determinista_no_revienta(
    tmp_path, monkeypatch, valoracion_sin_servicios, capsys
):
    fixtures = _banco_valoracion(tmp_path, "HOR-001")

    def muere(trabajo, interprete=None):
        raise RuntimeError(CENTINELA)

    monkeypatch.setattr(sv6, "ejecutar_en_subproceso", muere)

    fases, _ = runner.corrida_determinista(fixtures)

    for nombre in ("IA3", "E2E"):
        fase = _fase(fases, nombre)
        assert fase.veredicto() == NO_EVALUABLE
        assert "subproceso de sv6" in fase.motivo
        assert CENTINELA not in fase.motivo
    assert CENTINELA in capsys.readouterr().err
