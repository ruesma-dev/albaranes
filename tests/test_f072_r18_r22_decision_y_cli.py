# tests/test_f072_r18_r22_decision_y_cli.py
"""F-072 · R18–R22: la decisión de servir o ejecutar y la CLI que lee init.sh.

`decidir` junta la clave con el fichero de caché (`.arnes_cache/suite_<nombre>.ok`)
y, si el intérprete del servicio tiene `coverage`, con su `coverage.json`. La
CLI lo traduce a un protocolo de líneas: `AVISO|...` y una última línea
`SERVIR|<fecha>` o `EJECUTAR|<clave o vacío>`.

Git de verdad sobre un repositorio en `tmp_path`; la sonda se inyecta en
`decidir` (en `main` corre la real, con el intérprete de este test).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

from harness import cache_suites
from harness.cache_suites import (
    Decision,
    ErrorDeSonda,
    Sondeo,
    clave_de,
    decidir,
    lineas_de_salida,
    main,
)
from harness.servicios import Servicio

PY = sys.executable
SVC = Servicio(nombre="svc", ruta="services/svc", lenguaje="python")


@pytest.fixture(autouse=True)
def _sin_variables_git(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in list(os.environ):
        if variable.startswith("GIT_"):
            monkeypatch.delenv(variable, raising=False)


def _git(raiz: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=Arnes", "-c", "user.email=arnes@ejemplo.invalid",
         "-C", str(raiz), *args],
        capture_output=True, text=True, encoding="utf-8", check=True,
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )


@pytest.fixture(scope="module")
def _plantilla(tmp_path_factory: pytest.TempPathFactory) -> Path:
    raiz = tmp_path_factory.mktemp("plantilla_f072_decision") / "repo"
    (raiz / "services" / "svc").mkdir(parents=True)
    (raiz / "services" / "web").mkdir(parents=True)
    (raiz / "harness").mkdir()
    _git(raiz, "init", "-q")
    (raiz / ".gitignore").write_text(
        ".env\n.arnes_cache/\ncoverage.json\n", encoding="utf-8")
    (raiz / "services" / "svc" / "app.py").write_text("X = 1\n", encoding="utf-8")
    (raiz / "services" / "web" / "index.js").write_text("", encoding="utf-8")
    (raiz / "harness" / "servicios.json").write_text(json.dumps({"servicios": [
        {"nombre": "svc", "ruta": "services/svc", "lenguaje": "python"},
        {"nombre": "web", "ruta": "services/web", "lenguaje": "otro"},
    ]}), encoding="utf-8")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "inicial")
    return raiz


@pytest.fixture
def repo(_plantilla: Path, tmp_path: Path) -> Path:
    raiz = tmp_path / "repo"
    shutil.copytree(_plantilla, raiz)
    return raiz


def _sonda(coverage: bool = False):
    def _falsa(interprete: str, modulos: tuple[str, ...], cwd: Path) -> Sondeo:
        return Sondeo(origenes={}, tiene_coverage=coverage)
    return _falsa


def _clave(repo: Path, coverage: bool = False) -> str:
    clave, _ = clave_de(SVC, str(repo), PY, Sondeo(origenes={}, tiene_coverage=coverage))
    assert clave is not None
    return clave


def _guardar(repo: Path, contenido: str, nombre: str = "svc") -> Path:
    fichero = repo / ".arnes_cache" / f"suite_{nombre}.ok"
    fichero.parent.mkdir(exist_ok=True)
    fichero.write_text(contenido, encoding="utf-8")
    return fichero


# --- R18: servir -------------------------------------------------------------


def test_f072_r18_sirve_con_la_clave_guardada_y_sin_coverage(repo: Path) -> None:
    fichero = _guardar(repo, _clave(repo))
    os.utime(fichero, (1_760_000_000, 1_760_000_000))

    decision = decidir(SVC, str(repo), sondear=_sonda(coverage=False))

    esperada = time.strftime("%Y-%m-%d %H:%M", time.localtime(1_760_000_000))
    assert decision == Decision(servir=True, clave=_clave(repo), fecha_verde=esperada,
                                avisos=())
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", decision.fecha_verde)


def test_f072_r18_tolera_espacios_y_salto_de_linea_en_el_fichero(repo: Path) -> None:
    _guardar(repo, f"  {_clave(repo)}\n")

    assert decidir(SVC, str(repo), sondear=_sonda()).servir is True


def test_f072_r18_con_coverage_hace_falta_su_coverage_json(repo: Path) -> None:
    _guardar(repo, _clave(repo, coverage=True))

    sin_json = decidir(SVC, str(repo), sondear=_sonda(coverage=True))
    (repo / "services" / "svc" / "coverage.json").write_text("{}", encoding="utf-8")
    con_json = decidir(SVC, str(repo), sondear=_sonda(coverage=True))

    assert sin_json.servir is False and sin_json.clave == _clave(repo, coverage=True)
    assert sin_json.fecha_verde is None
    assert con_json.servir is True


def test_f072_r18_el_coverage_json_de_la_raiz_no_cuenta(repo: Path) -> None:
    _guardar(repo, _clave(repo, coverage=True))
    (repo / "coverage.json").write_text("{}", encoding="utf-8")

    assert decidir(SVC, str(repo), sondear=_sonda(coverage=True)).servir is False


# --- R19 y R20: ejecutar --------------------------------------------------------


def test_f072_r19_sin_fichero_de_cache_ejecuta_y_devuelve_la_clave(repo: Path) -> None:
    decision = decidir(SVC, str(repo), sondear=_sonda())

    assert decision == Decision(servir=False, clave=_clave(repo), fecha_verde=None,
                                avisos=())


def test_f072_r19_clave_distinta_ejecuta(repo: Path) -> None:
    _guardar(repo, "0" * 64)

    decision = decidir(SVC, str(repo), sondear=_sonda())

    assert decision.servir is False and decision.clave == _clave(repo)


def test_f072_r19_la_cache_de_otro_servicio_no_vale(repo: Path) -> None:
    _guardar(repo, _clave(repo), nombre="otro")

    assert decidir(SVC, str(repo), sondear=_sonda()).servir is False


def test_f072_r19_sin_clave_ejecuta_con_clave_vacia(repo: Path) -> None:
    _guardar(repo, _clave(repo))
    (repo / "services" / "svc" / "app.py").write_text("X = 2\n", encoding="utf-8")

    decision = decidir(SVC, str(repo), sondear=_sonda())

    assert decision == Decision(servir=False, clave=None, fecha_verde=None, avisos=())


def test_f072_r19_sonda_fallida_avisa_y_ejecuta_sin_clave(repo: Path) -> None:
    def _rota(interprete: str, modulos: tuple[str, ...], cwd: Path) -> Sondeo:
        raise ErrorDeSonda("la sonda tardó más de 30 s")

    _guardar(repo, _clave(repo))

    decision = decidir(SVC, str(repo), sondear=_rota)

    assert decision.servir is False and decision.clave is None
    assert len(decision.avisos) == 1
    assert "la sonda tardó más de 30 s" in decision.avisos[0]


def test_f072_r16_decidir_sondea_con_el_interprete_y_la_carpeta_del_servicio(
    repo: Path,
) -> None:
    vistos: dict = {}

    def _espia(interprete: str, modulos: tuple[str, ...], cwd: Path) -> Sondeo:
        vistos.update(interprete=interprete, modulos=modulos, cwd=cwd)
        return Sondeo(origenes={}, tiene_coverage=False)

    decidir(Servicio(nombre="svc", ruta="services/svc", lenguaje="python"),
            str(repo), sondear=_espia)

    assert vistos["interprete"] == PY
    assert vistos["modulos"] == ()
    assert Path(vistos["cwd"]).resolve() == (repo / "services" / "svc").resolve()


def test_f072_r20_cache_del_formato_anterior_nunca_coincide(repo: Path) -> None:
    arbol = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD:services/svc"],
                           capture_output=True, text=True, check=True).stdout.strip()
    _guardar(repo, arbol)

    decision = decidir(SVC, str(repo), sondear=_sonda())

    assert len(arbol) == 40
    assert decision.servir is False and decision.clave == _clave(repo)


# --- R21: --sin-cache ------------------------------------------------------------


def test_f072_r21_sin_cache_nunca_sirve_pero_devuelve_la_clave(repo: Path) -> None:
    _guardar(repo, _clave(repo))

    decision = decidir(SVC, str(repo), sin_cache=True, sondear=_sonda())

    assert decision == Decision(servir=False, clave=_clave(repo), fecha_verde=None,
                                avisos=())


# --- R22: protocolo de líneas y CLI -----------------------------------------------


def test_f072_r22_lineas_de_salida() -> None:
    assert lineas_de_salida(Decision(True, "a" * 64, "2026-10-15 09:30", ())) == [
        "SERVIR|2026-10-15 09:30"]
    assert lineas_de_salida(Decision(False, "b" * 64, None, ("uno", "dos"))) == [
        "AVISO|uno", "AVISO|dos", f"EJECUTAR|{'b' * 64}"]
    assert lineas_de_salida(Decision(False, None, None, ())) == ["EJECUTAR|"]


def test_f072_r22_un_aviso_con_saltos_de_linea_sigue_siendo_una_linea() -> None:
    lineas = lineas_de_salida(Decision(False, None, None, ("uno\ndos\r\ntres",)))

    assert lineas == ["AVISO|uno dos tres", "EJECUTAR|"]


def test_f072_r22_main_ejecutar_con_clave(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    codigo = main(["--servicio", "svc", "--raiz", str(repo)])

    salida = capsys.readouterr()
    assert codigo == 0
    assert re.fullmatch(r"EJECUTAR\|[0-9a-f]{64}\n", salida.out)
    assert salida.err == ""


def test_f072_r22_main_servir(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["--servicio", "svc", "--raiz", str(repo)])
    clave = capsys.readouterr().out.strip().split("|")[1]
    _guardar(repo, clave)
    (repo / "services" / "svc" / "coverage.json").write_text("{}", encoding="utf-8")

    codigo = main(["--servicio", "svc", "--raiz", str(repo)])

    assert codigo == 0
    assert re.fullmatch(r"SERVIR\|\d{4}-\d{2}-\d{2} \d{2}:\d{2}\n", capsys.readouterr().out)


def test_f072_r22_main_sin_cache(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["--servicio", "svc", "--raiz", str(repo)])
    clave = capsys.readouterr().out.strip().split("|")[1]
    _guardar(repo, clave)
    (repo / "services" / "svc" / "coverage.json").write_text("{}", encoding="utf-8")

    codigo = main(["--servicio", "svc", "--raiz", str(repo), "--sin-cache"])

    assert codigo == 0
    assert capsys.readouterr().out == f"EJECUTAR|{clave}\n"


def test_f072_r22_main_imprime_avisos_antes_de_la_decision(
    repo: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def _rota(interprete: str, modulos: tuple[str, ...], cwd: Path,
              limite_s: int = 30) -> Sondeo:
        raise ErrorDeSonda("motivo de prueba")

    monkeypatch.setattr(cache_suites, "sondear", _rota)

    codigo = main(["--servicio", "svc", "--raiz", str(repo)])

    lineas = capsys.readouterr().out.splitlines()
    assert codigo == 0
    assert len(lineas) == 2
    assert lineas[0].startswith("AVISO|") and "motivo de prueba" in lineas[0]
    assert lineas[1] == "EJECUTAR|"


@pytest.mark.parametrize(
    ("argumentos", "trozo"),
    [
        (["--servicio", "no-existe"], "no-existe"),
        (["--servicio", "web"], "python"),
    ],
)
def test_f072_r22_main_servicio_desconocido_o_no_python_sale_con_1(
    repo: Path, capsys: pytest.CaptureFixture[str], argumentos: list[str], trozo: str
) -> None:
    codigo = main([*argumentos, "--raiz", str(repo)])

    salida = capsys.readouterr()
    assert codigo == 1
    assert salida.out == ""
    assert trozo in salida.err


def test_f072_r22_main_declaracion_invalida_sale_con_1(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "harness" / "servicios.json").write_text(json.dumps({"servicios": [
        {"nombre": "svc", "ruta": "services/svc", "lenguaje": "python",
         "depende_de": ["services/no-existe"]}]}), encoding="utf-8")

    codigo = main(["--servicio", "svc", "--raiz", str(repo)])

    salida = capsys.readouterr()
    assert codigo == 1 and salida.out == "" and "services/no-existe" in salida.err


def test_f072_r22_main_sin_declaracion_sale_con_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo = main(["--servicio", "svc", "--raiz", str(tmp_path)])

    assert codigo == 1 and "svc" in capsys.readouterr().err


def test_f072_r22_main_venv_declarado_que_no_existe_sale_con_1(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "harness" / "servicios.json").write_text(json.dumps({"servicios": [
        {"nombre": "svc", "ruta": "services/svc", "lenguaje": "python",
         "venv": "services/svc/.venv"}]}), encoding="utf-8")

    codigo = main(["--servicio", "svc", "--raiz", str(repo)])

    salida = capsys.readouterr()
    assert codigo == 1 and salida.out == "" and "venv" in salida.err


def test_f072_r22_modulo_ejecutable_con_python_m(repo: Path) -> None:
    """La forma exacta en que lo llama init.sh, en un proceso aparte."""
    raiz_arnes = Path(__file__).resolve().parents[1]
    proceso = subprocess.run(
        [PY, "-m", "harness.cache_suites", "--servicio", "svc", "--raiz", str(repo)],
        cwd=raiz_arnes, capture_output=True, text=True, encoding="utf-8",
        stdin=subprocess.DEVNULL, check=False,
    )

    assert proceso.returncode == 0, proceso.stderr
    assert re.fullmatch(r"EJECUTAR\|[0-9a-f]{64}\n", proceso.stdout)
