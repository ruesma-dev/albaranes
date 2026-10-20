# tests/test_f083_comparar_modelos.py
"""F-083 · R11–R19, R24–R26: el comparador de modelos, con `Dependencias` dobles.

Ningún test llama a un LLM ni lanza un subproceso: `ejecutar_sv2`,
`ejecutar_sv5` y `build_sv6` son dobles. En las paradas, los dobles que
llamarían a un LLM revientan si se tocan.
"""

from __future__ import annotations

import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

import pytest

from evals import comparar_modelos as cm
from evals.costes import cargar_tabla
from evals.informe_modelos import gasto_acumulado, tokens_medidos

AHORA = dt.datetime(2026, 10, 19, 12, 0, tzinfo=dt.timezone.utc)
CLAVES = {"ANTHROPIC_API_KEY": "a", "GEMINI_API_KEY": "g", "OPENAI_API_KEY": "o"}


def _prohibido(*args, **kwargs):
    raise AssertionError("no se puede llamar a un LLM en una parada")


def _fixture(fase, caso, tipologia="Generico", tablas=None):
    return {"caso_id": caso, "fase": fase, "tipologia": tipologia, "tablas": tablas or {}}


@pytest.fixture
def banco(tmp_path):
    """Un banco mínimo: IA1 con 3 casos (uno sin albarán), IA2 con 2, INPUTS con 3, IA4 con 2."""
    fixtures = tmp_path / "fixtures"
    albaranes = tmp_path / "albaranes"
    albaranes.mkdir()
    for fase, casos in {
        "IA1": ["GEN-001", "GEN-002", "HOR-001"],
        "IA2": ["HOR-001", "RES-001"],
        "inputs": ["GEN-001", "RES-001", "RES-002"],
        "IA3": ["GEN-001", "RES-001", "RES-002"],
        "IA4": ["RES-001", "COM-009"],
        "final": ["GEN-001", "RES-001", "RES-002"],
    }.items():
        (fixtures / fase).mkdir(parents=True)
        for caso in casos:
            (fixtures / fase / f"{caso}.json").write_text(
                json.dumps(_fixture(fase, caso)), encoding="utf-8"
            )
        (fixtures / fase / "_indice.json").write_text("{}", encoding="utf-8")
    for caso in ("GEN-001", "HOR-001", "RES-001"):
        (albaranes / f"{caso}.pdf").write_bytes(b"%PDF")
    return fixtures, albaranes, tmp_path


def _deps(banco, **cambios):
    fixtures, albaranes, _ = banco
    datos = {
        "ejecutar_sv2": _prohibido,
        "ejecutar_sv5": _prohibido,
        "build_sv6": _prohibido,
        "tabla": cargar_tabla(),
        "fixtures": fixtures,
        "albaranes": albaranes,
        "ahora": lambda: AHORA,
    }
    datos.update(cambios)
    return cm.Dependencias(**datos)


def _argv(banco, *resto):
    _, _, raiz = banco
    return [
        "--resumen", str(raiz / "resumen.md"),
        "--salida", str(raiz / "salida"),
        *resto,
    ]


# --- R11, R12: el plan -------------------------------------------------------------


def _opciones(banco, *argv):
    return cm.analizar(_argv(banco, *argv))


def test_f083_r12_plan_añade_la_referencia_y_la_pone_primera(banco):
    plan = cm.planificar(
        _opciones(banco, "--fase", "IA1", "--modelos", "gpt-6-luna,gemini-4-argon"),
        cargar_tabla(), *banco[:2],
    )
    assert plan.modelos == ["gemini-3.7-flash", "gpt-6-luna", "gemini-4-argon"]
    assert plan.referencia == "gemini-3.7-flash" and plan.referencia_anadida is True
    assert plan.preparacion is None


def test_f083_r12_plan_referencia_pedida_no_se_avisa(banco):
    plan = cm.planificar(
        _opciones(banco, "--fase", "IA1", "--modelos", "gpt-6-luna,gemini-3.7-flash,gpt-6-luna"),
        cargar_tabla(), *banco[:2],
    )
    assert plan.modelos == ["gemini-3.7-flash", "gpt-6-luna"]
    assert plan.referencia_anadida is False


def test_f083_r20_plan_ia1_casos_con_albaran(banco):
    plan = cm.planificar(_opciones(banco, "--fase", "IA1", "--modelos", "gpt-6-luna"),
                         cargar_tabla(), *banco[:2])
    assert plan.casos == ["GEN-001", "HOR-001"]
    assert plan.omitidos == {"GEN-002": "no existe el fichero del albarán"}
    assert plan.proveedores == ["gemini", "openai"]


def test_f083_r21_plan_ia2_con_preparacion_de_ia1(banco):
    plan = cm.planificar(_opciones(banco, "--fase", "IA2", "--modelos", "gpt-5.5"),
                         cargar_tabla(), *banco[:2])
    assert plan.modelos == ["gpt-5.4", "gpt-5.5"]
    assert plan.preparacion == "gemini-3.7-flash"
    assert plan.casos == ["HOR-001", "RES-001"]
    assert plan.proveedores == ["gemini", "openai"]


def test_f083_r22_plan_ia3_todos_los_casos_de_inputs(banco):
    plan = cm.planificar(_opciones(banco, "--fase", "IA3", "--modelos", "claude-opus-5-5"),
                         cargar_tabla(), *banco[:2])
    assert plan.modelos == ["claude-opus-4-8", "claude-opus-5-5"]
    assert plan.casos == ["GEN-001", "RES-001", "RES-002"] and plan.preparacion is None


def test_f083_r23_plan_ia4_casos_del_libro_ia4_con_inputs(banco):
    plan = cm.planificar(_opciones(banco, "--fase", "IA4", "--modelos", "gpt-6.1-sol"),
                         cargar_tabla(), *banco[:2])
    assert plan.preparacion == "claude-opus-4-8"
    assert plan.casos == ["RES-001"]
    assert plan.omitidos == {"COM-009": "sin caso en INPUTS"}
    assert plan.proveedores == ["claude", "openai"]


def test_f083_r11_plan_filtra_por_casos(banco):
    plan = cm.planificar(
        _opciones(banco, "--fase", "IA3", "--modelos", "gpt-5.5", "--casos", "RES-002,XXX-001"),
        cargar_tabla(), *banco[:2],
    )
    assert plan.casos == ["RES-002"]
    assert plan.omitidos == {"XXX-001": "no está en el libro de la fase"}


def test_f083_r25_plan_bloques_intercalados_y_partidas(banco):
    plan = cm.planificar(
        _opciones(banco, "--fase", "IA2", "--modelos", "gpt-5.5", "--repeticiones", "2"),
        cargar_tabla(), *banco[:2],
    )
    assert plan.bloques() == [(1, "gpt-5.4"), (1, "gpt-5.5"), (2, "gpt-5.4"), (2, "gpt-5.5")]
    partidas = plan.partidas()
    assert [(p.modelo, p.etiqueta, p.fase, p.llamadas) for p in partidas] == [
        ("gpt-5.4", "candidato", "IA2", 4),
        ("gpt-5.5", "candidato", "IA2", 4),
        ("gemini-3.7-flash", "preparación", "IA1", 2),
    ]


# --- R13: modelo no válido ---------------------------------------------------------


@pytest.mark.parametrize("modelo", ["gpt-6.1-luna", "gpt-6-astra", "claude-sonnet-5"])
def test_f083_r13_parada_modelo_no_valido(banco, capsys, modelo):
    codigo = cm.main(_argv(banco, "--fase", "IA1", "--modelos", f"gpt-5.5,{modelo}"),
                     entorno=CLAVES, dependencias=_deps(banco))
    error = capsys.readouterr().err
    assert codigo == 2
    assert modelo in error
    assert "gpt-6-luna" in error and "claude-opus-4-8" in error
    assert "gpt-6-astra (" not in error.split("Válidos")[1]


def test_f083_r13_parada_sin_casos(banco, capsys):
    codigo = cm.main(_argv(banco, "--fase", "IA1", "--modelos", "gpt-5.5", "--casos", "GEN-002"),
                     entorno=CLAVES, dependencias=_deps(banco))
    assert codigo == 2
    assert "ningún caso" in capsys.readouterr().err


# --- R4: tabla caducada --------------------------------------------------------------


def test_f083_r4_parada_tabla_caducada_antes_de_estimar(banco, capsys):
    tabla = cargar_tabla()
    argon = tabla.modelo("gemini-4-argon")
    precio = type(argon.precio)(**{**argon.precio.__dict__, "siguiente": None})
    tabla.modelos["gemini-4-argon"] = type(argon)(**{**argon.__dict__, "precio": precio})
    deps = _deps(banco, tabla=tabla, ahora=lambda: dt.datetime(2026, 12, 2, tzinfo=dt.timezone.utc))
    codigo = cm.main(_argv(banco, "--fase", "IA1", "--modelos", "gemini-4-argon", "--estimar"),
                     entorno={}, dependencias=deps)
    salida = capsys.readouterr()
    assert codigo == 2
    assert "caducada" in salida.err and "gemini-4-argon" in salida.err
    assert "Estimación" not in salida.out


def test_f083_r4_parada_tabla_caducada_en_la_preparacion(banco, capsys):
    tabla = cargar_tabla()
    flash = tabla.modelo("gemini-3.7-flash")
    precio = type(flash.precio)(**{**flash.precio.__dict__, "siguiente": None})
    tabla.modelos["gemini-3.7-flash"] = type(flash)(**{**flash.__dict__, "precio": precio})
    deps = _deps(banco, tabla=tabla, ahora=lambda: dt.datetime(2027, 1, 2, tzinfo=dt.timezone.utc))
    codigo = cm.main(_argv(banco, "--fase", "IA2", "--modelos", "gpt-5.5", "--estimar"),
                     entorno={}, dependencias=deps)
    assert codigo == 2
    assert "gemini-3.7-flash" in capsys.readouterr().err


# --- R15, R16: estimación -------------------------------------------------------------


def test_f083_r16_estimar_sin_claves_ni_llamadas(banco, capsys):
    codigo = cm.main(
        _argv(banco, "--fase", "IA2", "--modelos", "gpt-5.5,gpt-6-luna", "--estimar"),
        entorno={}, dependencias=_deps(banco),
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Estimación" in salida
    assert "gemini-3.7-flash · preparación" in salida
    assert "AVISO" in salida and "gpt-5.4" in salida
    assert "por defecto ×1.5" in salida
    assert "Total estimado" in salida
    assert not (banco[2] / "resumen.md").exists()


def test_f083_r15_estimacion_con_tokens_medidos_del_resumen(banco, capsys):
    resumen = banco[2] / "resumen.md"
    resumen.write_text(
        "TOKENS: IA1 · gpt-6-luna · 2000 · 1000\nTOKENS: IA1 · gpt-6-luna · 4000 · 1000\n",
        encoding="utf-8",
    )
    codigo = cm.main(_argv(banco, "--fase", "IA1", "--modelos", "gpt-6-luna", "--estimar"),
                     entorno={}, dependencias=_deps(banco))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "gpt-6-luna · candidato · 2 llamadas · 4000 / 1000 tokens (medido)" in salida
    # 2 × (4.000 × 0,10 + 1.000 × 0,50) / 1e6 = 0,0018.
    assert "≈ 0.0018 USD" in salida


def test_f083_r15_sin_aviso_si_la_referencia_se_pidio(banco, capsys):
    cm.main(_argv(banco, "--fase", "IA3", "--modelos", "claude-opus-4-8", "--estimar"),
            entorno={}, dependencias=_deps(banco))
    assert "AVISO" not in capsys.readouterr().out


def test_f083_r15_la_estimacion_avisa_de_los_omitidos(banco, capsys):
    cm.main(_argv(banco, "--fase", "IA1", "--modelos", "gpt-6-luna", "--estimar"),
            entorno={}, dependencias=_deps(banco))
    assert "Omitidos: 1 (GEN-002: no existe el fichero del albarán)" in capsys.readouterr().out


# --- R14, R17, R18: paradas antes de gastar ----------------------------------------


def test_f083_r14_parada_faltan_claves(banco, capsys):
    codigo = cm.main(_argv(banco, "--fase", "IA2", "--modelos", "gpt-5.5"),
                     entorno={"OPENAI_API_KEY": "secreto-que-no-sale"}, dependencias=_deps(banco))
    captura = capsys.readouterr()
    assert codigo == 2
    assert "GEMINI_API_KEY" in captura.err
    assert "OPENAI_API_KEY" not in captura.err
    assert "secreto-que-no-sale" not in captura.err + captura.out


def test_f083_r14_la_clave_de_la_preparacion_tambien_cuenta(banco, capsys):
    codigo = cm.main(_argv(banco, "--fase", "IA4", "--modelos", "gpt-5.5"),
                     entorno={"OPENAI_API_KEY": "o"}, dependencias=_deps(banco))
    assert codigo == 2
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err


def test_f083_r17_parada_tope_de_la_invocacion(banco, capsys):
    codigo = cm.main(_argv(banco, "--fase", "IA3", "--modelos", "gpt-5.5", "--tope-usd", "0.10"),
                     entorno=CLAVES, dependencias=_deps(banco))
    assert codigo == 2
    assert "--tope-usd" in capsys.readouterr().err


def test_f083_r17_tope_justo_no_para(banco, capsys, monkeypatch):
    llamado = []
    monkeypatch.setattr(cm, "ejecutar_plan", lambda *a, **k: llamado.append(1) or 0)
    cm.main(_argv(banco, "--fase", "IA1", "--modelos", "gemini-3.7-flash", "--estimar"),
            entorno={}, dependencias=_deps(banco))
    total = capsys.readouterr().out.split("Total estimado: ")[1].split(" USD")[0]
    codigo = cm.main(
        _argv(banco, "--fase", "IA1", "--modelos", "gemini-3.7-flash", "--tope-usd", total,
              "--tope-total-usd", total),
        entorno=CLAVES, dependencias=_deps(banco),
    )
    assert codigo == 0 and llamado == [1]


def test_f083_r18_parada_tope_de_la_feature(banco, capsys):
    (banco[2] / "resumen.md").write_text(
        "GASTO: 2026-10-19T10:00:00Z · IA1 · 150.50\nGASTO: 2026-10-19T11:00:00Z · IA3 · 49.40\n",
        encoding="utf-8",
    )
    codigo = cm.main(_argv(banco, "--fase", "IA1", "--modelos", "gpt-5.5"),
                     entorno=CLAVES, dependencias=_deps(banco))
    error = capsys.readouterr().err
    assert codigo == 2
    assert "199.90" in error and "--tope-total-usd" in error


def test_f083_r18_parada_orden_claves_antes_que_topes(banco, capsys):
    codigo = cm.main(_argv(banco, "--fase", "IA3", "--modelos", "gpt-5.5", "--tope-usd", "0"),
                     entorno={}, dependencias=_deps(banco))
    assert codigo == 2
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err


def test_f083_r18_gasto_acumulado_suma_las_lineas_gasto():
    texto = (
        "# resumen\nGASTO: 2026-10-19T10:00:00Z · IA1 · 1.25\n"
        "texto GASTO: 2026 · IA1 · 100\n"
        "GASTO: 2026-10-19T11:00:00Z · IA3 · 0.75\nGASTO: mal\n"
    )
    assert gasto_acumulado(texto) == Decimal("2.00")
    assert gasto_acumulado("") == 0


def test_f083_r15_tokens_medidos_se_queda_con_la_ultima():
    texto = (
        "TOKENS: IA1 · gpt-6-luna · 10 · 5\nTOKENS: IA3 · gpt-6-luna · 7 · 3\n"
        "TOKENS: IA1 · gpt-6-luna · 20 · 6\n TOKENS: IA1 · x · 1 · 1\n"
    )
    assert tokens_medidos(texto) == {("IA1", "gpt-6-luna"): (20, 6), ("IA3", "gpt-6-luna"): (7, 3)}


# --- CLI ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["--fase", "IA5", "--modelos", "gpt-5.5"],
        ["--fase", "IA1"],
        ["--fase", "IA1", "--modelos", "gpt-5.5", "--repeticiones", "0"],
        ["--fase", "IA1", "--modelos", " , "],
    ],
)
def test_f083_r11_parada_uso_incorrecto_del_cli(banco, argv):
    with pytest.raises(SystemExit) as salida:
        cm.main(_argv(banco, *argv), entorno={}, dependencias=_deps(banco))
    assert salida.value.code == 2


def test_f083_r11_plan_valores_por_defecto():
    opciones = cm.analizar(["--fase", "IA1", "--modelos", "gpt-5.5"])
    assert opciones.repeticiones == 1
    assert opciones.tope_usd == Decimal(25)
    assert opciones.tope_total_usd == Decimal(200)
    assert opciones.estimar is False
    assert Path(opciones.resumen) == cm.RUTA_RESUMEN
    assert opciones.salida == ""


# --- T8 · ejecución por bloques (R19, R24–R26) -----------------------------------------

import copy

from evals.conversor import RUTA_FIXTURES
from evals.procesos import sv5_valoracion, sv6_build
from evals.runner import cargar_fixtures

_IA1 = {"cabeceras": [{"numero_albaran": "A-1"}], "lineas": [{"num_linea": 1, "cantidad": 2}]}


@pytest.fixture
def banco_ia1(banco):
    """El banco con tablas IA1 comparables: GEN-001 y HOR-001 esperan cantidad 2."""
    fixtures = banco[0]
    for caso in ("GEN-001", "GEN-002", "HOR-001"):
        (fixtures / "IA1" / f"{caso}.json").write_text(
            json.dumps(_fixture("IA1", caso, tablas=_IA1)), encoding="utf-8"
        )
    return banco


def _documento(cantidad=2):
    return {"cabecera": {"numero_albaran": "A-1"},
            "lineas": [{"concepto": "x", "cantidad": cantidad}]}


def _registro(trabajo, caso, coste, ms=1000):
    return {
        "caso_id": caso, "etiqueta": "preparación" if trabajo["fase"].startswith("prep")
        else "candidato", "proveedor": trabajo["modelo"]["proveedor"],
        "modelo_pedido": trabajo["modelo"]["id"], "modelo_servido": trabajo["modelo"]["id"],
        "duracion_ms": ms, "entrada": 1000, "lectura_cache": 0, "escritura_cache": 0,
        "salida": 100, "uso_incompleto": False, "coste_usd": str(coste),
        "motivo_parada": "STOP", "fallo": False, "con_respuesta": True,
    }


class _Sv2Doble:
    """Contesta cada caso; `cantidades[modelo]` decide si acierta (2) o falla."""

    def __init__(self, coste="0.01", cantidades=None, muere=(), casos_rotos=(), no_ejecuta=()):
        self.coste = Decimal(coste)
        self.cantidades = cantidades or {}
        self.muere = set(muere)
        self.casos_rotos = set(casos_rotos)
        self.no_ejecuta = set(no_ejecuta)
        self.trabajos: list[dict] = []

    def __call__(self, trabajo):
        self.trabajos.append(copy.deepcopy(trabajo))
        modelo = trabajo["modelo"]["id"]
        registros, resultados = [], []
        for caso in trabajo["casos"]:
            caso_id = caso["caso_id"]
            if (modelo, caso_id) in self.no_ejecuta:
                resultados.append({"caso_id": caso_id, "no_ejecutado": True})
                continue
            registros.append(_registro(trabajo, caso_id, self.coste))
            if (modelo, caso_id) in self.casos_rotos:
                resultados.append({"caso_id": caso_id, "error": {
                    "fase": "IA1", "tipo": "ValidationError", "motivo": "ValidationError: json"}})
            else:
                resultados.append({"caso_id": caso_id,
                                   "documento": _documento(self.cantidades.get(modelo, 2))})
        if modelo in self.muere:
            Path(trabajo["registros"]).write_text(
                "".join(json.dumps(r) + "\n" for r in registros), encoding="utf-8"
            )
            raise RuntimeError("el subproceso de sv2 falló con código 1")
        return {"resultados": resultados, "registros": registros}


def _resumen(banco):
    return (banco[2] / "resumen.md").read_text(encoding="utf-8")


def _fila(texto, modelo):
    return next(linea for linea in texto.splitlines() if linea.startswith(f"| `{modelo}`"))


def test_f083_bloque_ia1_completo(banco_ia1, capsys):
    sv2 = _Sv2Doble(cantidades={"gpt-6-luna": 3})
    codigo = cm.main(_argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna"),
                     entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2))
    assert codigo == 0
    assert [t["modelo"]["id"] for t in sv2.trabajos] == ["gemini-3.7-flash", "gpt-6-luna"]
    primero = sv2.trabajos[0]
    assert primero["fase"] == "IA1" and primero["fecha"] == "2026-10-19"
    assert primero["modelo"] == {"id": "gemini-3.7-flash", "proveedor": "gemini",
                                 "herramienta_forzada": None}
    assert [c["caso_id"] for c in primero["casos"]] == ["GEN-001", "HOR-001"]
    assert primero["casos"][0]["fichero"].endswith("GEN-001.pdf")
    assert primero["presupuesto_usd"] == "25"
    texto = _resumen(banco_ia1)
    # 4 llamadas de 0,01 USD.
    assert gasto_acumulado(texto) == Decimal("0.04")
    assert "| `gemini-3.7-flash` | 2 | 0 | 0 | 2 | 0 |" in texto
    assert "| `gpt-6-luna` | 2 | 0 | 0 | 0 | 2 |" in texto
    assert "**mantener** `gemini-3.7-flash`" in texto
    assert "provisional (1 repetición)" in texto
    salida = banco_ia1[2] / "salida"
    assert "detalle CON valores" in (salida / "detalle.md").read_text(encoding="utf-8")
    assert json.loads((salida / "resultados.json").read_text(encoding="utf-8"))["fase"] == "IA1"
    assert "resumen sin valores" in capsys.readouterr().out


def test_f083_bloque_el_presupuesto_restante_pasa_al_siguiente(banco_ia1):
    sv2 = _Sv2Doble(coste="1.5")
    cm.main(_argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna", "--tope-usd", "5"),
            entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2))
    assert [t["presupuesto_usd"] for t in sv2.trabajos] == ["5", "2.0"]


def test_f083_repeticion_bloques_intercalados_y_registros_por_bloque(banco_ia1):
    sv2 = _Sv2Doble()
    cm.main(_argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna", "--repeticiones", "2"),
            entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2))
    assert [t["modelo"]["id"] for t in sv2.trabajos] == [
        "gemini-3.7-flash", "gpt-6-luna", "gemini-3.7-flash", "gpt-6-luna"]
    ficheros = [Path(t["registros"]).name for t in sv2.trabajos]
    assert len(set(ficheros)) == 4
    texto = _resumen(banco_ia1)
    assert "× 2 repeticiones" in texto
    assert "| `gpt-6-luna` | 4 | 0 | 0 | 4 | 0.00 (0–0) |" in texto


def test_f083_repeticion_la_preparacion_se_ejecuta_una_vez(banco):
    sv2 = _Sv2Doble()
    cm.main(_argv(banco, "--fase", "IA2", "--modelos", "gpt-5.5", "--repeticiones", "2"),
            entorno=CLAVES, dependencias=_deps(banco, ejecutar_sv2=sv2))
    fases = [(t["fase"], t["modelo"]["id"]) for t in sv2.trabajos]
    assert fases == [("prep_IA1", "gemini-3.7-flash"), ("IA2", "gpt-5.4"), ("IA2", "gpt-5.5"),
                     ("IA2", "gpt-5.4"), ("IA2", "gpt-5.5")]
    # Cada candidato recibe la IA1 de la preparación.
    assert sv2.trabajos[1]["casos"][0]["ia1"] == _documento()
    texto = _resumen(banco)
    assert "- Preparación (IA1, una vez): `gemini-3.7-flash` · 2 llamadas · 0.0200 USD" in texto
    # 2 de preparación + 8 de candidatos.
    assert gasto_acumulado(texto) == Decimal("0.10")


def test_f083_bloque_preparacion_que_falla_en_un_caso(banco):
    sv2 = _Sv2Doble(casos_rotos={("gemini-3.7-flash", "HOR-001")})
    cm.main(_argv(banco, "--fase", "IA2", "--modelos", "gpt-5.5"),
            entorno=CLAVES, dependencias=_deps(banco, ejecutar_sv2=sv2))
    assert [c["caso_id"] for c in sv2.trabajos[1]["casos"]] == ["RES-001"]
    texto = _resumen(banco)
    assert "- `gpt-5.4` r1 · HOR-001 · falló la preparación · ERROR en IA1 · " in texto
    assert "- `gpt-5.5` r1 · HOR-001 · falló la preparación" in texto
    assert "**sin datos**" in texto


def test_f083_bloque_muerto_pierde_solo_ese_bloque(banco_ia1, capsys):
    sv2 = _Sv2Doble(muere={"gpt-6-luna"})
    codigo = cm.main(_argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna,gpt-5.5"),
                     entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2))
    assert codigo == 0
    assert [t["modelo"]["id"] for t in sv2.trabajos] == [
        "gemini-3.7-flash", "gpt-6-luna", "gpt-5.5"]
    texto = _resumen(banco_ia1)
    assert "| `gpt-6-luna` | 0 | 2 | 0 | 0 | 0 |" in texto
    assert "- `gpt-6-luna` r1 · GEN-001 · ERROR en IA1 · el subproceso del bloque murió" in texto
    # Lo pagado por el bloque muerto se recupera de su fichero de registros (R26).
    assert gasto_acumulado(texto) == Decimal("0.06")
    assert "gpt-6-luna" in capsys.readouterr().err


def test_f083_bloque_que_no_devuelve_un_caso(banco_ia1):
    def sv2(trabajo):
        return {"resultados": [], "registros": []}

    cm.main(_argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna"),
            entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2))
    assert "- `gpt-6-luna` r1 · GEN-001 · el bloque no devolvió el caso" in _resumen(banco_ia1)


def test_f083_tope_alcanzado_no_lanza_mas_bloques(banco_ia1, capsys):
    sv2 = _Sv2Doble(coste="1")
    codigo = cm.main(
        _argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna", "--tope-usd", "2"),
        entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2),
    )
    assert codigo == 3
    assert [t["modelo"]["id"] for t in sv2.trabajos] == ["gemini-3.7-flash"]
    texto = _resumen(banco_ia1)
    assert "**CORTADO**" in texto
    assert "| `gpt-6-luna` | 0 | 0 | 2 | 0 | 0 |" in texto
    assert gasto_acumulado(texto) == Decimal(2)


def test_f083_tope_alcanzado_dentro_de_un_bloque(banco_ia1):
    sv2 = _Sv2Doble(no_ejecuta={("gpt-6-luna", "HOR-001")})
    codigo = cm.main(_argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna"),
                     entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2))
    assert codigo == 3
    assert "| `gpt-6-luna` | 1 | 0 | 1 | 1 | 0 |" in _resumen(banco_ia1)


def test_f083_bloque_ningun_candidato_dio_resultado(banco_ia1):
    sv2 = _Sv2Doble(casos_rotos={(m, c) for m in ("gemini-3.7-flash", "gpt-6-luna")
                                 for c in ("GEN-001", "HOR-001")})
    codigo = cm.main(_argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna"),
                     entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2))
    assert codigo == 1
    assert "ERROR en IA1 · ValidationError: json" in _resumen(banco_ia1)


def test_f083_bloque_el_resumen_se_acumula(banco_ia1):
    for _ in range(2):
        cm.main(_argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna"),
                entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=_Sv2Doble()))
    texto = _resumen(banco_ia1)
    assert gasto_acumulado(texto) == Decimal("0.08")
    assert texto.startswith("<!-- progress/comparar_modelos_F-083.md -->")


def test_f083_bloque_salida_por_defecto_con_fecha(banco_ia1, monkeypatch, tmp_path):
    monkeypatch.setattr(cm, "RUTA_SALIDAS", tmp_path / "salidas")
    argv = ["--resumen", str(tmp_path / "r.md"), "--fase", "IA1", "--modelos", "gpt-6-luna"]
    cm.main(argv, entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=_Sv2Doble()))
    (carpeta,) = (tmp_path / "salidas").iterdir()
    assert (carpeta / "detalle.md").is_file()


# --- T8 · IA3 e IA4 con el build real de sv6 (sin LLM) ------------------------------------

_CASOS_SV5 = ["FER-001", "GEN-001", "RES-001"]


def _deps_reales(banco, sv5):
    return _deps(banco, ejecutar_sv5=sv5, fixtures=RUTA_FIXTURES,
                 build_sv6=sv6_build.ejecutar_en_subproceso)


def test_f083_bloque_ia3_con_la_ia4_del_libro(banco):
    """El candidato devuelve los envelopes del libro IA3: IA3 y E2E, como el modo determinista."""
    inputs = cargar_fixtures(RUTA_FIXTURES, "inputs")
    ia3 = cargar_fixtures(RUTA_FIXTURES, "IA3")
    trabajos = []

    def sv5(trabajo):
        trabajos.append(trabajo)
        resultados = []
        for caso in trabajo["casos"]:
            envelope = sv6_build.construir_envelope_estimulado(
                inputs[caso["caso_id"]], ia3.get(caso["caso_id"], {"tablas": {}}))
            assert caso["contexto"] == sv5_valoracion.construir_contexto(inputs[caso["caso_id"]])
            resultados.append({"caso_id": caso["caso_id"], "envelope": envelope})
        return {"resultados": resultados, "registros": [
            _registro(trabajo, c["caso_id"], "0.01") for c in trabajo["casos"]]}

    codigo = cm.main(
        _argv(banco, "--fase", "IA3", "--modelos", "claude-opus-5-5",
              "--casos", ",".join(_CASOS_SV5)),
        entorno=CLAVES, dependencias=_deps_reales(banco, sv5),
    )
    assert codigo == 0
    assert trabajos[1]["modelo"]["herramienta_forzada"] is False
    deterministas, _ = __import__("evals.runner", fromlist=["x"]).corrida_determinista(
        RUTA_FIXTURES, _CASOS_SV5)
    fallos = {f.nombre: sum(len(c.fallos) for c in f.casos) for f in deterministas}
    texto = _resumen(banco)
    assert "| `claude-opus-5-5` | 3 | 0 | 0 |" in texto
    fila = _fila(texto, "claude-opus-5-5")
    assert fila.split("|")[6].strip() == str(fallos["IA3"])
    e2e = texto.split("### E2E")[1]
    assert _fila(e2e, "claude-opus-5-5").split("|")[6].strip() == str(fallos["E2E"])


def test_f083_bloque_ia4_concilia_sobre_la_preparacion(banco):
    inputs = cargar_fixtures(RUTA_FIXTURES, "inputs")
    ia4 = cargar_fixtures(RUTA_FIXTURES, "IA4")
    trabajos = []

    def sv5(trabajo):
        trabajos.append(copy.deepcopy(trabajo))
        resultados = []
        for caso in trabajo["casos"]:
            caso_id = caso["caso_id"]
            if trabajo["fase"] == "prep_IA3":
                envelope = sv6_build.construir_envelope_estimulado(inputs[caso_id], {"tablas": {}})
                resultados.append({"caso_id": caso_id, "envelope": envelope})
            else:
                conciliaciones = sv5_valoracion.conciliaciones_desde_ground_truth(
                    ia4[caso_id], caso["envelope"])
                if trabajo["modelo"]["id"] == "gpt-6-luna":
                    conciliaciones = []
                resultados.append({"caso_id": caso_id, "conciliaciones": conciliaciones})
        return {"resultados": resultados, "registros": [
            _registro(trabajo, c["caso_id"], "0.01") for c in trabajo["casos"]]}

    codigo = cm.main(
        _argv(banco, "--fase", "IA4", "--modelos", "gpt-6-luna", "--casos", "FER-001,RES-008"),
        entorno=CLAVES, dependencias=_deps_reales(banco, sv5),
    )
    assert codigo == 0
    assert [(t["fase"], t["modelo"]["id"]) for t in trabajos] == [
        ("prep_IA3", "claude-opus-4-8"), ("IA4", "claude-opus-4-8"), ("IA4", "gpt-6-luna")]
    assert trabajos[1]["casos"][0]["envelope"]["meta"] is not None
    texto = _resumen(banco)
    referencia, luna = _fila(texto, "claude-opus-4-8"), _fila(texto, "gpt-6-luna")
    assert referencia.split("|")[6].strip() == "0"
    assert int(luna.split("|")[6].strip()) > 0
    assert "### E2E" in texto


# --- T16 · supervivientes de la mutación ------------------------------------------------


def test_f083_t16_tope_igual_a_la_estimacion_exacta_no_para(banco, monkeypatch):
    from evals.costes import estimar

    llamado = []
    monkeypatch.setattr(cm, "ejecutar_plan", lambda *a, **k: llamado.append(1) or 0)
    argv = _argv(banco, "--fase", "IA1", "--modelos", "gpt-6-luna")
    plan = cm.planificar(cm.analizar(argv), cargar_tabla(), *banco[:2])
    total = str(estimar(plan.partidas(), cargar_tabla(), {}, AHORA.date()).total)
    codigo = cm.main([*argv, "--tope-usd", total, "--tope-total-usd", total],
                     entorno=CLAVES, dependencias=_deps(banco))
    assert codigo == 0 and llamado == [1]


def test_f083_t16_tope_con_menos_de_un_dolar_restante_sigue(banco_ia1):
    sv2 = _Sv2Doble(coste="0.1")
    codigo = cm.main(
        _argv(banco_ia1, "--fase", "IA1", "--modelos", "gpt-6-luna", "--tope-usd", "0.5"),
        entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=sv2),
    )
    assert codigo == 0
    assert [t["presupuesto_usd"] for t in sv2.trabajos] == ["0.5", "0.3"]


def test_f083_t16_el_resumen_crea_su_carpeta_y_el_json_es_legible(banco_ia1):
    _, _, raiz = banco_ia1
    resumen = raiz / "nueva" / "honda" / "resumen.md"
    argv = ["--resumen", str(resumen), "--salida", str(raiz / "salida"),
            "--fase", "IA2", "--modelos", "gpt-5.5"]
    cm.main(argv, entorno=CLAVES, dependencias=_deps(banco_ia1, ejecutar_sv2=_Sv2Doble()))
    assert resumen.is_file()
    texto = (raiz / "salida" / "resultados.json").read_text(encoding="utf-8")
    assert texto.startswith('{\n  "fase": "IA2"')
    assert '"preparación"' in texto


def test_f083_t16_la_fase_es_obligatoria(banco):
    with pytest.raises(SystemExit) as salida:
        cm.analizar(["--modelos", "gpt-5.5"])
    assert salida.value.code == 2
