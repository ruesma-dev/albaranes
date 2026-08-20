# tests/test_f012_r1_r5_r11_coordinador.py
"""F-012 · R1, R5 y R11: el coordinador de la campaña paralela.

Ni un solo pytest anidado: los ejecutores son falsos e inyectados, y deciden su
veredicto LEYENDO el fichero del disco. Eso es lo que convierte al falso en
prueba de verdad: si un worker no hubiera escrito la mutación en su propio
worktree, el veredicto no saldría.
"""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path

import pytest

from harness.alcance import Alcance
from harness.mutacion import (
    MUERTO,
    SUPERVIVIENTE,
    EjecutorPytest,
    ejecutar_campania,
    ejecutor_para,
    escribir_informe,
    generar_mutantes,
    lineas_comparables,
)
from harness.mutacion_paralela import (
    clave_estable,
    ejecutar_campania_paralela,
    fabrica_de_ejecutores,
)
from harness.servicios import Servicio

FUENTE = (
    "def evaluar(a, b, c):\n"
    "    if a == b:\n"
    "        return a + b\n"
    "    if a < c:\n"
    "        return a - c\n"
    "    if b > c and a > 0:\n"
    "        return b * c\n"
    "    return not a\n"
)

#: Marca del único mutante que el ejecutor falso deja vivo: la mutación
#: `*` -> `//` de la línea 7.
MARCA_SUPERVIVIENTE = "b // c"


def _git(raiz: Path, *args: str) -> str:
    proceso = subprocess.run(
        ["git", "-C", str(raiz), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return proceso.stdout or ""


def _crear_repo(raiz: Path, ficheros: dict[str, str]) -> Path:
    raiz.mkdir(parents=True, exist_ok=True)
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.email", "arnes@ejemplo.invalid")
    _git(raiz, "config", "user.name", "Arnes")
    for nombre, contenido in ficheros.items():
        destino = raiz / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido, encoding="utf-8")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "inicial")
    return raiz


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _crear_repo(tmp_path / "repo", {"codigo.py": FUENTE})


def _alcance(fichero: str = "codigo.py") -> Alcance:
    return Alcance(
        feature="F-012",
        origen="rama",
        ref_diff=("base", "rama"),
        lineas={fichero: set(range(1, FUENTE.count("\n") + 1))},
    )


class _EjecutorFalso:
    """Juzga el mutante por lo que hay ESCRITO en el árbol que le toca.

    `raiz` es el directorio del worker: si el worker no escribió la mutación
    ahí, este ejecutor lee el fuente original y no hay superviviente que valga.
    """

    def __init__(self, fichero: str, raiz: str, registro: list[tuple[str, str, int]]) -> None:
        self.fichero = fichero
        self.raiz = raiz
        self.registro = registro

    def ejecutar(self, timeout_s: int) -> str:
        contenido = (Path(self.raiz) / self.fichero).read_text(encoding="utf-8")
        self.registro.append((self.fichero, self.raiz, timeout_s))
        return SUPERVIVIENTE if MARCA_SUPERVIVIENTE in contenido else MUERTO


def _fabrica_falsa(registro: list[tuple[str, str, int]]):
    def fabrica(fichero: str, raiz: str) -> _EjecutorFalso:
        return _EjecutorFalso(fichero, raiz, registro)

    return fabrica


# --- R1: la campaña paralela evalúa todo y cuenta bien -----------------------


def test_f012_r1_evalua_todos_los_mutantes_una_sola_vez(repo: Path) -> None:
    registro: list[tuple[str, str, int]] = []

    informe = ejecutar_campania_paralela(
        _alcance(),
        servicios=[],
        raiz=str(repo),
        workers=3,
        fabrica=_fabrica_falsa(registro),
    )

    esperados = generar_mutantes(FUENTE, set(range(1, 9)), "codigo.py")
    assert informe.generados == len(esperados)
    assert informe.evaluados == len(esperados)
    assert [clave_estable(m) for m in informe.mutantes_evaluados] == [
        clave_estable(m) for m in esperados
    ]
    assert len(registro) == len(esperados)
    assert len(informe.supervivientes) == 1
    assert informe.muertos == len(esperados) - 1


def test_f012_r1_reparte_el_trabajo_entre_varios_worktrees(repo: Path) -> None:
    registro: list[tuple[str, str, int]] = []

    ejecutar_campania_paralela(
        _alcance(),
        servicios=[],
        raiz=str(repo),
        workers=3,
        fabrica=_fabrica_falsa(registro),
    )

    raices = {raiz for _, raiz, _ in registro}
    assert len(raices) == 3


def test_f012_r1_el_eco_numera_el_progreso_sobre_el_total_de_la_campania(
    repo: Path,
) -> None:
    lineas: list[str] = []

    informe = ejecutar_campania_paralela(
        _alcance(),
        servicios=[],
        raiz=str(repo),
        workers=2,
        eco=lineas.append,
        fabrica=_fabrica_falsa([]),
    )

    total = informe.evaluados
    # (1.6.0) Cada worker ecoa además su LÍNEA BASE con el prefijo `[base]`:
    # la suite sin mutar corre antes de juzgar a nadie. Ese eco no numera
    # progreso, así que se aparta antes de comprobar la numeración; pero se
    # exige que exista, porque su ausencia significaría que la campaña volvió
    # a arrancar sin comprobar la base, que es el defecto que costó las
    # campañas falsas del 19 y el 20 de agosto.
    base = [linea for linea in lineas if linea.startswith("[base]")]
    mutantes = [linea for linea in lineas if not linea.startswith("[base]")]
    assert base, "sin eco de línea base: la campaña no la está comprobando"

    prefijos = sorted(linea.split("]")[0] + "]" for linea in mutantes)
    assert prefijos == sorted(f"[{numero}/{total}]" for numero in range(1, total + 1))
    assert all("->" in linea for linea in mutantes)  # la descripción llega entera
    assert any("[comparacion]" in linea for linea in mutantes)


def test_f012_r1_sin_pedir_workers_el_coordinador_usa_dos(repo: Path) -> None:
    registro: list[tuple[str, str, int]] = []

    ejecutar_campania_paralela(
        _alcance(), servicios=[], raiz=str(repo), fabrica=_fabrica_falsa(registro)
    )

    raices = {raiz for _, raiz, _ in registro}
    assert len(raices) == 2
    assert str(repo) not in raices


def test_f012_r1_el_reloj_del_informe_es_el_de_la_campania(repo: Path) -> None:
    informe = ejecutar_campania_paralela(
        _alcance(),
        servicios=[],
        raiz=str(repo),
        workers=2,
        fabrica=_fabrica_falsa([]),
    )

    assert 0 < informe.segundos < 600


def test_f012_r1_el_fallo_de_un_worker_se_relanza_en_el_hilo_principal(
    repo: Path,
) -> None:
    """Un worker roto no puede acabar en un informe incompleto y silencioso."""
    cerrojo = threading.Lock()
    llamadas = [0]

    def fabrica(fichero: str, raiz: str) -> _EjecutorFalso:
        with cerrojo:
            llamadas[0] += 1
            primera = llamadas[0] == 1
        if primera:
            raise RuntimeError("ejecutor roto")
        return _EjecutorFalso(fichero, raiz, [])

    with pytest.raises(RuntimeError, match="ejecutor roto"):
        ejecutar_campania_paralela(
            _alcance(), servicios=[], raiz=str(repo), workers=2, fabrica=fabrica
        )

    assert len(_git(repo, "worktree", "list").strip().splitlines()) == 1
    assert (repo / "codigo.py").read_text(encoding="utf-8") == FUENTE


def test_f012_r1_r4_el_informe_paralelo_es_identico_al_de_la_campania_en_serie(
    repo: Path, tmp_path: Path
) -> None:
    alcance = _alcance()

    en_serie = ejecutar_campania(
        alcance,
        EjecutorPytest(raiz=str(repo)),
        raiz=str(repo),
        ejecutor_de=lambda fichero: _EjecutorFalso(fichero, str(repo), []),
    )
    en_paralelo = ejecutar_campania_paralela(
        alcance,
        servicios=[],
        raiz=str(repo),
        workers=4,
        fabrica=_fabrica_falsa([]),
    )

    ruta_serie, ruta_paralelo = tmp_path / "serie.md", tmp_path / "paralelo.md"
    escribir_informe(en_serie, ruta_serie)
    escribir_informe(en_paralelo, ruta_paralelo)

    # Qué filas salen del reloj lo declara `harness.mutacion`, al lado de quien
    # las escribe (F-039 R3/R7). Cuando esta lista se mantenía aquí a mano, la
    # fila que añadió F-038 T5 se quedó fuera y el test quedó flaky: en serie
    # redondeaba a 0.0 y en paralelo a 0.1 según cómo estuviera la máquina.
    assert lineas_comparables(
        ruta_paralelo.read_text(encoding="utf-8")
    ) == lineas_comparables(ruta_serie.read_text(encoding="utf-8"))


# --- R2: el árbol principal no se toca ---------------------------------------


def test_f012_r2_el_arbol_principal_queda_intacto_y_sin_worktrees(repo: Path) -> None:
    registro: list[tuple[str, str, int]] = []

    ejecutar_campania_paralela(
        _alcance(),
        servicios=[],
        raiz=str(repo),
        workers=3,
        fabrica=_fabrica_falsa(registro),
    )

    assert (repo / "codigo.py").read_text(encoding="utf-8") == FUENTE
    assert _git(repo, "status", "--porcelain").strip() == ""
    assert len(_git(repo, "worktree", "list").strip().splitlines()) == 1
    assert all(Path(raiz).resolve() != repo.resolve() for _, raiz, _ in registro)


def test_f012_r9_con_el_arbol_sucio_aborta_sin_crear_worktrees(repo: Path) -> None:
    (repo / "codigo.py").write_text(FUENTE + "\n# sucio\n", encoding="utf-8")

    with pytest.raises(ValueError, match="sin commitear"):
        ejecutar_campania_paralela(
            _alcance(),
            servicios=[],
            raiz=str(repo),
            workers=3,
            fabrica=_fabrica_falsa([]),
        )

    assert len(_git(repo, "worktree", "list").strip().splitlines()) == 1


# --- R5: cada mutante se juzga con la suite de SU servicio -------------------


def test_f012_r5_la_fabrica_ejecuta_en_el_worktree_con_el_venv_del_arbol_principal(
    tmp_path: Path,
) -> None:
    principal = tmp_path / "principal"
    (principal / "entorno" / "Scripts").mkdir(parents=True)
    (principal / "entorno" / "Scripts" / "python.exe").write_text("", encoding="utf-8")
    worktree = tmp_path / "wk_0"
    (worktree / "services" / "svc").mkdir(parents=True)
    servicios = [
        Servicio(nombre="svc", ruta="services/svc", lenguaje="python", venv="entorno")
    ]

    fabrica = fabrica_de_ejecutores(servicios, raiz_venvs=str(principal))
    ejecutor = fabrica("services/svc/modulo.py", str(worktree))

    assert Path(ejecutor.raiz) == worktree / "services" / "svc"
    assert ejecutor.ejecutable == (
        principal / "entorno" / "Scripts" / "python.exe"
    ).resolve().as_posix()


def test_f012_r5_sin_raiz_venvs_el_ejecutor_se_comporta_como_siempre(
    tmp_path: Path,
) -> None:
    raiz = tmp_path / "repo"
    (raiz / "entorno" / "Scripts").mkdir(parents=True)
    (raiz / "entorno" / "Scripts" / "python.exe").write_text("", encoding="utf-8")
    (raiz / "services" / "svc").mkdir(parents=True)
    servicios = [
        Servicio(nombre="svc", ruta="services/svc", lenguaje="python", venv="entorno")
    ]

    ejecutor = ejecutor_para("services/svc/modulo.py", servicios, raiz=str(raiz))

    assert Path(ejecutor.raiz) == raiz / "services" / "svc"
    assert ejecutor.ejecutable == (
        raiz / "entorno" / "Scripts" / "python.exe"
    ).resolve().as_posix()


def test_f012_r5_un_fichero_de_la_raiz_se_juzga_con_la_suite_de_la_raiz(
    tmp_path: Path,
) -> None:
    fabrica = fabrica_de_ejecutores([], raiz_venvs=str(tmp_path / "principal"))

    ejecutor = fabrica("harness/mutacion.py", str(tmp_path / "wk_0"))

    assert Path(ejecutor.raiz) == tmp_path / "wk_0"


# --- R11: un venv declarado que no existe revienta ANTES de crear nada -------


def test_f012_r11_un_venv_inexistente_falla_antes_de_crear_worktrees(
    tmp_path: Path,
) -> None:
    repo = _crear_repo(tmp_path / "repo", {"services/svc/modulo.py": FUENTE})
    servicios = [
        Servicio(
            nombre="svc",
            ruta="services/svc",
            lenguaje="python",
            venv="entorno_que_no_existe",
        )
    ]

    with pytest.raises(ValueError, match="no contiene intérprete"):
        ejecutar_campania_paralela(
            _alcance("services/svc/modulo.py"),
            servicios=servicios,
            raiz=str(repo),
            workers=3,
            fabrica=_fabrica_falsa([]),
        )

    assert len(_git(repo, "worktree", "list").strip().splitlines()) == 1
