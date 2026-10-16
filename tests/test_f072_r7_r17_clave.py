# tests/test_f072_r7_r17_clave.py
"""F-072 · R7–R17: la clave de la caché de suites de un servicio.

La clave reúne todo lo que puede cambiar el resultado de la suite sin cambiar
el árbol del servicio: sus dependencias declaradas, el intérprete, la ruta real
de los módulos que importa y la huella de los ficheros locales (`.env`). Si algo
de eso no se puede fijar, no hay clave y la suite se ejecuta.

Git de verdad, siempre sobre un repositorio diminuto en `tmp_path` y sin las
variables `GIT_*` del entorno (desde un hook, `GIT_DIR` haría que el test operase
sobre el repositorio real). La sonda es falsa: aquí se inyecta el `Sondeo`.
"""

from __future__ import annotations

import builtins
import dataclasses
import hashlib
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from harness import cache_suites
from harness.cache_suites import (
    ErrorDeSonda,
    Sondeo,
    _dentro_de,
    clave_de,
    hash_en_head,
    hay_cambios,
    huella_local,
    raiz_del_repositorio,
    sondear,
    texto_de_clave,
)
from harness.servicios import Servicio

PY = sys.executable


@pytest.fixture(autouse=True)
def _sin_variables_git(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in list(os.environ):
        if variable.startswith("GIT_"):
            monkeypatch.delenv(variable, raising=False)


def _git(raiz: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=Arnes", "-c", "user.email=arnes@ejemplo.invalid",
         "-C", str(raiz), *args],
        capture_output=True, text=True, encoding="utf-8", check=True,
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    ).stdout


def _escribir(raiz: Path, ruta: str, texto: str) -> Path:
    fichero = raiz / ruta
    fichero.parent.mkdir(parents=True, exist_ok=True)
    fichero.write_text(texto, encoding="utf-8")
    return fichero


def _commit(raiz: Path, mensaje: str = "cambio") -> None:
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", mensaje)


@pytest.fixture(scope="module")
def _plantilla(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Se crea una vez por módulo: en Windows, cada proceso git cuesta."""
    raiz = tmp_path_factory.mktemp("plantilla_f072") / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    _escribir(raiz, ".gitignore", ".env\n__pycache__/\nlocal/\n")
    _escribir(raiz, "services/svc/app.py", "X = 1\n")
    _escribir(raiz, "services/comun/pkg/__init__.py", "Y = 1\n")
    _escribir(raiz, "services/otro/otro.py", "Z = 1\n")
    _commit(raiz, "inicial")
    return raiz


@pytest.fixture
def repo(_plantilla: Path, tmp_path: Path) -> Path:
    """Repositorio con `services/svc`, `services/comun` y `services/otro`."""
    raiz = tmp_path / "repo"
    shutil.copytree(_plantilla, raiz)
    return raiz


def _svc(**extra: object) -> Servicio:
    datos: dict = {"nombre": "svc", "ruta": "services/svc", "lenguaje": "python"}
    datos.update(extra)
    return Servicio(**datos)


def _sondeo(**origenes: str | None) -> Sondeo:
    return Sondeo(origenes=dict(origenes), tiene_coverage=False)


def _clave(repo: Path, servicio: Servicio, sondeo: Sondeo | None = None,
           interprete: str = PY) -> str | None:
    clave, _ = clave_de(servicio, str(repo), interprete, sondeo or _sondeo())
    return clave


# --- Piezas de git -----------------------------------------------------------


def test_f072_r7_hash_en_head_de_carpeta_fichero_y_ausente(repo: Path) -> None:
    arbol = _git(repo, "rev-parse", "HEAD:services/svc").strip()

    assert hash_en_head("services/svc", str(repo)) == arbol
    assert hash_en_head(".gitignore", str(repo)) == _git(
        repo, "rev-parse", "HEAD:.gitignore").strip()
    assert hash_en_head("services/no-existe", str(repo)) is None


def test_f072_r11_hay_cambios_ve_modificados_y_no_rastreados(repo: Path) -> None:
    assert hay_cambios(["services/svc", "services/comun"], str(repo)) is False

    _escribir(repo, "services/comun/nuevo.py", "")
    assert hay_cambios(["services/svc"], str(repo)) is False
    assert hay_cambios(["services/svc", "services/comun"], str(repo)) is True


def test_f072_r11_hay_cambios_fuera_de_un_repositorio_es_cambio(tmp_path: Path) -> None:
    """Si git no responde, lo seguro es «no sé»: no hay clave."""
    assert hay_cambios(["x"], str(tmp_path)) is True


def test_f072_r13_raiz_del_repositorio_resuelta(repo: Path) -> None:
    (repo / "services/svc/sub").mkdir()

    assert raiz_del_repositorio(str(repo / "services/svc/sub")) == repo.resolve()


# --- R7 y R8: qué entra en la clave ------------------------------------------


def test_f072_r7_misma_entrada_misma_clave_de_64_hex(repo: Path) -> None:
    servicio = _svc(depende_de=("services/comun",))

    primera = _clave(repo, servicio)

    assert primera == _clave(repo, servicio)
    assert primera is not None and len(primera) == 64
    int(primera, 16)


def test_f072_r7_la_clave_es_el_sha256_del_texto(repo: Path) -> None:
    servicio = _svc()
    texto, _ = texto_de_clave(servicio, str(repo), PY, _sondeo())

    assert texto is not None
    assert _clave(repo, servicio) == hashlib.sha256(texto.encode("utf-8")).hexdigest()


def test_f072_r7_texto_canonico(repo: Path) -> None:
    origen = repo / "services/comun/pkg/__init__.py"
    servicio = _svc(depende_de=("services/comun",), importa=("pkg",))

    texto, avisos = texto_de_clave(servicio, str(repo), PY, _sondeo(pkg=str(origen)))

    assert avisos == []
    hash_svc = _git(repo, "rev-parse", "HEAD:services/svc").strip()
    hash_comun = _git(repo, "rev-parse", "HEAD:services/comun").strip()
    assert texto == "\n".join([
        "formato=cache-suites/2",
        f"servicio=services/svc@{hash_svc}",
        f"depende=services/comun@{hash_comun}",
        f"interprete={os.path.normcase(str(Path(PY).resolve()))}",
        f"modulo=pkg@{os.path.normcase(str(origen.resolve()))}",
        "local=.env@ausente",
        "local=services/svc/.env@ausente",
    ])


def test_f072_r7_un_commit_en_el_servicio_cambia_la_clave(repo: Path) -> None:
    antes = _clave(repo, _svc())
    _escribir(repo, "services/svc/app.py", "X = 2\n")
    _commit(repo)

    assert _clave(repo, _svc()) not in (None, antes)


def test_f072_r7_un_commit_en_la_dependencia_cambia_la_clave(repo: Path) -> None:
    servicio = _svc(depende_de=("services/comun",))
    antes = _clave(repo, servicio)
    _escribir(repo, "services/comun/pkg/__init__.py", "Y = 2\n")
    _commit(repo)

    assert _clave(repo, servicio) not in (None, antes)


def test_f072_r7_un_commit_ajeno_no_cambia_la_clave(repo: Path) -> None:
    servicio = _svc(depende_de=("services/comun",))
    antes = _clave(repo, servicio)
    _escribir(repo, "services/otro/otro.py", "Z = 2\n")
    _escribir(repo, "progress/notas.md", "x\n")
    _commit(repo)

    assert _clave(repo, servicio) == antes


def test_f072_r7_otro_interprete_cambia_la_clave(repo: Path, tmp_path: Path) -> None:
    otro = _escribir(tmp_path, "venv/python.exe", "")

    assert _clave(repo, _svc(), interprete=str(otro)) != _clave(repo, _svc())


def test_f072_r7_otro_origen_del_modulo_cambia_la_clave(repo: Path) -> None:
    servicio = _svc(depende_de=("services/comun",), importa=("pkg",))
    uno = repo / "services/comun/pkg/__init__.py"
    otro = repo / "services/comun/pkg"

    assert _clave(repo, servicio, _sondeo(pkg=str(uno))) != _clave(
        repo, servicio, _sondeo(pkg=str(otro)))


def test_f072_r7_la_huella_de_una_entrada_declarada_cambia_la_clave(repo: Path) -> None:
    servicio = _svc(entradas_no_versionadas=("local/config.ini",))
    antes = _clave(repo, servicio)
    _escribir(repo, "local/config.ini", "a=1\n")

    assert _clave(repo, servicio) not in (None, antes)


# --- R8: el orden de declaración no importa -----------------------------------


def test_f072_r8_clave_independiente_del_orden(repo: Path) -> None:
    _escribir(repo, "services/otro/__init__.py", "")
    _commit(repo)
    origen_pkg = str(repo / "services/comun/pkg/__init__.py")
    origen_otro = str(repo / "services/otro/__init__.py")
    sondeo = _sondeo(pkg=origen_pkg, otro=origen_otro)
    a = _svc(depende_de=("services/comun", "services/otro"), importa=("pkg", "otro"),
             entradas_no_versionadas=("local/b.ini", "local/a.ini"))
    b = _svc(depende_de=("services/otro", "services/comun"), importa=("otro", "pkg"),
             entradas_no_versionadas=("local/a.ini", "local/b.ini"))

    assert _clave(repo, a, sondeo) == _clave(repo, b, sondeo)


# --- R9 y R10: entradas locales por metadatos, nunca por contenido -----------


def test_f072_r9_huella_local_es_nombre_tamano_y_mtime(repo: Path) -> None:
    fichero = _escribir(repo, "services/svc/.env", "CLAVE=1\n")
    os.utime(fichero, ns=(1_700_000_000_000_000_000, 1_700_000_000_123_456_700))

    assert huella_local("services/svc/.env", str(repo)) == (
        f"services/svc/.env@{fichero.stat().st_size}:1700000000123456700")
    assert huella_local("services/svc/no.env", str(repo)) == "services/svc/no.env@ausente"


def test_f072_r9_env_de_la_raiz_y_del_servicio_entran_por_defecto(repo: Path) -> None:
    servicio = _svc()
    antes = _clave(repo, servicio)
    raiz_env = _escribir(repo, ".env", "A=1\n")
    con_raiz = _clave(repo, servicio)
    _escribir(repo, "services/svc/.env", "B=1\n")
    con_los_dos = _clave(repo, servicio)
    os.utime(raiz_env, ns=(1, 1))

    assert len({antes, con_raiz, con_los_dos, _clave(repo, servicio)}) == 4


def test_f072_r9_una_entrada_declarada_igual_que_la_de_defecto_no_se_duplica(
    repo: Path,
) -> None:
    texto, _ = texto_de_clave(_svc(entradas_no_versionadas=(".env",)), str(repo), PY,
                              _sondeo())

    assert texto is not None and texto.count("local=.env@") == 1


def test_f072_r10_el_contenido_del_env_no_esta_en_el_texto_de_la_clave(repo: Path) -> None:
    secreto = "SECRETO=no-me-leas-1234"
    _escribir(repo, ".env", secreto + "\n")
    _escribir(repo, "services/svc/.env", secreto + "\n")

    texto, _ = texto_de_clave(_svc(), str(repo), PY, _sondeo())

    assert texto is not None
    assert "SECRETO" not in texto and "no-me-leas" not in texto
    for algoritmo in ("sha256", "sha1", "md5"):
        for contenido in (secreto, secreto + "\n"):
            digest = hashlib.new(algoritmo, contenido.encode("utf-8")).hexdigest()
            assert digest not in texto


def test_f072_r10_huella_local_nunca_abre_el_fichero(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _escribir(repo, "services/svc/.env", "SECRETO=1\n")

    def _prohibido(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"se intentó abrir {args[:1]}")

    monkeypatch.setattr(builtins, "open", _prohibido)
    monkeypatch.setattr(io, "open", _prohibido)
    monkeypatch.setattr(os, "open", _prohibido)

    assert huella_local("services/svc/.env", str(repo)).startswith("services/svc/.env@")


# --- R11 y R12: sin clave ------------------------------------------------------


def test_f072_r11_servicio_sucio_sin_clave_ni_aviso(repo: Path) -> None:
    _escribir(repo, "services/svc/app.py", "X = 99\n")

    assert texto_de_clave(_svc(), str(repo), PY, _sondeo()) == (None, [])


def test_f072_r11_dependencia_con_no_rastreado_sin_clave_ni_aviso(repo: Path) -> None:
    _escribir(repo, "services/comun/suelto.py", "")

    assert texto_de_clave(_svc(depende_de=("services/comun",)), str(repo), PY,
                          _sondeo()) == (None, [])


def test_f072_r12_servicio_fuera_de_head_sin_clave_ni_aviso(repo: Path) -> None:
    servicio = Servicio(nombre="nuevo", ruta="local/nuevo", lenguaje="python")
    _escribir(repo, "local/nuevo/app.py", "")

    assert texto_de_clave(servicio, str(repo), PY, _sondeo()) == (None, [])


def test_f072_r12_dependencia_fuera_de_head_avisa_y_no_da_clave(repo: Path) -> None:
    _escribir(repo, "local/datos.csv", "a\n")

    texto, avisos = texto_de_clave(_svc(depende_de=("local/datos.csv",)), str(repo), PY,
                                   _sondeo())

    assert texto is None
    assert len(avisos) == 1
    assert "local/datos.csv" in avisos[0]
    assert "no está versionada" in avisos[0]
    assert "entradas_no_versionadas" in avisos[0]


# --- R13–R15: dónde resuelve cada módulo vigilado -------------------------------


def test_f072_r13_modulo_fuera_del_repositorio_avisa_y_no_da_clave(
    repo: Path, tmp_path: Path
) -> None:
    fuera = _escribir(tmp_path, "arbol_principal/pkg/__init__.py", "")

    texto, avisos = texto_de_clave(_svc(importa=("pkg",)), str(repo), PY,
                                   _sondeo(pkg=str(fuera)))

    assert texto is None
    assert len(avisos) == 1
    assert "pkg" in avisos[0] and "svc" in avisos[0]
    assert str(fuera) in avisos[0]
    assert "fuera de este repositorio" in avisos[0]
    assert "ESA copia" in avisos[0] and "no la de este árbol" in avisos[0]


@pytest.mark.parametrize("origen", ["built-in", "frozen"])
def test_f072_r13_origen_que_no_es_ruta_cuenta_como_de_fuera(
    repo: Path, origen: str
) -> None:
    texto, avisos = texto_de_clave(_svc(importa=("pkg",)), str(repo), PY,
                                   _sondeo(pkg=origen))

    assert texto is None
    assert len(avisos) == 1 and origen in avisos[0] and "fuera" in avisos[0]


def test_f072_r13_repositorio_vecino_con_prefijo_comun_es_de_fuera(
    repo: Path, tmp_path: Path
) -> None:
    """`repo-F-072` empieza como `repo`, pero es otro árbol (el caso worktree)."""
    vecino = _escribir(tmp_path, "repo-F-072/services/comun/pkg/__init__.py", "")

    texto, avisos = texto_de_clave(_svc(importa=("pkg",)), str(repo), PY,
                                   _sondeo(pkg=str(vecino)))

    assert texto is None and "fuera de este repositorio" in avisos[0]


def test_f072_r14_modulo_dentro_pero_no_declarado_pide_depende_de(repo: Path) -> None:
    origen = repo / "services/comun/pkg/__init__.py"

    texto, avisos = texto_de_clave(_svc(importa=("pkg",)), str(repo), PY,
                                   _sondeo(pkg=str(origen)))

    assert texto is None
    assert len(avisos) == 1
    assert "services/comun/pkg/__init__.py" in avisos[0]
    assert "depende_de" in avisos[0]


def test_f072_r14_modulo_dentro_de_la_propia_ruta_vale(repo: Path) -> None:
    origen = repo / "services/svc/app.py"

    texto, avisos = texto_de_clave(_svc(importa=("app",)), str(repo), PY,
                                   _sondeo(app=str(origen)))

    assert avisos == [] and texto is not None


def test_f072_r15_modulo_no_encontrado_avisa_y_no_da_clave(repo: Path) -> None:
    texto, avisos = texto_de_clave(_svc(importa=("pkg", "falta")), str(repo), PY,
                                   _sondeo(pkg=None))

    assert texto is None
    assert len(avisos) == 2
    assert all("no se encuentra" in aviso and "svc" in aviso for aviso in avisos)
    assert "`pkg`" in avisos[0] or "`pkg`" in avisos[1]
    assert "`falta`" in avisos[0] or "`falta`" in avisos[1]


def test_f072_r15_sonda_con_salida_ilegible(monkeypatch: pytest.MonkeyPatch,
                                           tmp_path: Path) -> None:
    def _falso(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args, 0, stdout="esto no es json\n", stderr="")

    monkeypatch.setattr(cache_suites.subprocess, "run", _falso)

    with pytest.raises(ErrorDeSonda, match="ilegible"):
        sondear(PY, ("pkg",), tmp_path)


def test_f072_r15_sonda_que_sale_con_error(monkeypatch: pytest.MonkeyPatch,
                                           tmp_path: Path) -> None:
    def _falso(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args, 3, stdout="", stderr="Traceback\nBoom\n")

    monkeypatch.setattr(cache_suites.subprocess, "run", _falso)

    with pytest.raises(ErrorDeSonda) as error:
        sondear(PY, ("pkg",), tmp_path)

    assert "3" in str(error.value) and "Boom" in str(error.value)


def test_f072_r15_sonda_que_tarda_demasiado(monkeypatch: pytest.MonkeyPatch,
                                            tmp_path: Path) -> None:
    vistos: dict = {}

    def _lento(*args: object, **kwargs: object) -> None:
        vistos.update(kwargs)
        raise subprocess.TimeoutExpired(cmd="sonda", timeout=kwargs["timeout"])

    monkeypatch.setattr(cache_suites.subprocess, "run", _lento)

    with pytest.raises(ErrorDeSonda, match="7 s"):
        sondear(PY, ("pkg",), tmp_path, limite_s=7)
    assert vistos["timeout"] == 7


def test_f072_r15_limite_de_la_sonda_por_defecto() -> None:
    assert cache_suites.LIMITE_SONDA_S == 30


def test_f072_r15_interprete_inexistente(tmp_path: Path) -> None:
    with pytest.raises(ErrorDeSonda):
        sondear(str(tmp_path / "no-hay-python.exe"), ("pkg",), tmp_path)


def test_f072_r16_sonda_con_el_interprete_y_la_carpeta_del_servicio(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    vistos: dict = {}

    def _falso(orden: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        vistos["orden"] = orden
        vistos.update(kwargs)
        return subprocess.CompletedProcess(
            orden, 0, stdout='{"origenes": {"pkg": "/x/pkg", "otro.sub": null}, "coverage": true}\n',
            stderr="")

    monkeypatch.setattr(cache_suites.subprocess, "run", _falso)

    sondeo = sondear("/ruta/del/python", ("pkg", "otro.sub"), tmp_path)

    assert sondeo == Sondeo(origenes={"pkg": "/x/pkg", "otro.sub": None},
                            tiene_coverage=True)
    assert vistos["orden"][0] == "/ruta/del/python"
    assert vistos["orden"][1] == "-c"
    assert "-I" not in vistos["orden"]
    assert vistos["orden"][-2:] == ["pkg", "otro.sub"]
    assert Path(vistos["cwd"]) == tmp_path
    assert vistos["stdin"] is subprocess.DEVNULL
    assert vistos["timeout"] == cache_suites.LIMITE_SONDA_S
    # Un código de salida distinto de 0 lo traduce `sondear` (ErrorDeSonda);
    # con check=True escaparía un CalledProcessError que nadie captura.
    assert vistos["check"] is False


def test_f072_r15_sonda_real_que_sale_con_error_da_error_de_sonda(tmp_path: Path) -> None:
    """Un padre que sale del intérprete al importarse (SystemExit no es Exception)
    hace que la sonda real termine con código 3: ErrorDeSonda, no otra excepción."""
    (tmp_path / "sale").mkdir()
    (tmp_path / "sale" / "__init__.py").write_text("raise SystemExit(3)\n", encoding="utf-8")

    with pytest.raises(ErrorDeSonda, match="código 3"):
        sondear(PY, ("sale.hijo",), tmp_path)


def test_f072_r12_git_que_falla_aunque_imprima_algo_no_da_hash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Un `git rev-parse` que sale con error no da hash, imprima lo que imprima."""
    def _git_falso(args: list[str], raiz: str) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args, 128, stdout="a" * 40 + "\n", stderr="")

    monkeypatch.setattr(cache_suites, "_git", _git_falso)

    assert hash_en_head("services/svc", str(tmp_path)) is None


def test_f072_r12_git_que_sale_bien_sin_hash_no_da_hash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _git_falso(args: list[str], raiz: str) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(args, 0, stdout="\n", stderr="")

    monkeypatch.setattr(cache_suites, "_git", _git_falso)

    assert hash_en_head("services/svc", str(tmp_path)) is None


def test_f072_r7_el_sondeo_es_inmutable() -> None:
    """La clave se deriva del sondeo: nadie puede retocarlo a medio cálculo."""
    sondeo = Sondeo(origenes={}, tiene_coverage=False)

    with pytest.raises(dataclasses.FrozenInstanceError):
        sondeo.tiene_coverage = True  # type: ignore[misc]


# --- R17: comparación de rutas ---------------------------------------------------


def test_f072_r17_dentro_de_basico(tmp_path: Path) -> None:
    base = tmp_path / "repo"

    assert _dentro_de(str(base), str(base)) is True
    assert _dentro_de(str(base / "a" / "b.py"), str(base)) is True
    assert _dentro_de(str(tmp_path / "repo2" / "b.py"), str(base)) is False
    assert _dentro_de(str(tmp_path), str(base)) is False


def test_f072_r17_dentro_de_con_rutas_sin_resolver(tmp_path: Path) -> None:
    base = tmp_path / "repo"

    assert _dentro_de(str(base / "x" / ".." / "y.py"), str(base)) is True
    assert _dentro_de(str(base / ".." / "fuera.py"), str(base)) is False


@pytest.mark.skipif(os.name != "nt", reason="mayúsculas y contrabarras: solo Windows")
def test_f072_r17_dentro_de_ignora_mayusculas_y_separadores_en_windows(
    tmp_path: Path,
) -> None:
    base = tmp_path / "Repo"
    ruta = str(base / "Services" / "pkg.py").upper().replace("\\", "/")

    assert _dentro_de(ruta, str(base).lower()) is True
