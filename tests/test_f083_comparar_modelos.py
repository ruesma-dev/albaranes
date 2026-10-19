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
    assert opciones.tope_usd == Decimal("25")
    assert opciones.tope_total_usd == Decimal("200")
    assert opciones.estimar is False
    assert Path(opciones.resumen) == cm.RUTA_RESUMEN
    assert opciones.salida == ""
