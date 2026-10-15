# tests/test_f072_r23_r27_init_sh.py
"""F-072 · R23–R27: el pegamento de `harness/init.sh` §7 bis con la caché.

Dos capas. La primera es el contrato estático del texto: la sección decide la
caché solo a través de `python -m harness.cache_suites`, con `</dev/null`, y ya
no compone la clave en bash. La segunda ejecuta la sección DE VERDAD con bash,
extraída del propio `init.sh`, contra un intérprete falso que responde lo que
cada caso necesita: así se comprueba el comportamiento (qué imprime, qué guarda,
que no se come la entrada del bucle) y no solo que unas palabras estén escritas.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

INIT_SH = Path(__file__).resolve().parents[1] / "harness" / "init.sh"


def _texto() -> str:
    return INIT_SH.read_text(encoding="utf-8")


def _seccion_7_bis() -> str:
    lineas = _texto().splitlines()
    inicio = next(i for i, linea in enumerate(lineas) if linea.startswith("# --- 7 bis"))
    fin = next(i for i, linea in enumerate(lineas) if linea.startswith("# --- 7b"))
    return "\n".join(lineas[inicio:fin]) + "\n"


def _cabecera() -> str:
    texto = _texto()
    return texto[: texto.index("set -u")]


# --- Contrato estático -----------------------------------------------------------


def test_f072_r23_la_seccion_llama_al_modulo_de_cache() -> None:
    llamadas = [linea for linea in _seccion_7_bis().splitlines()
                if "-m harness.cache_suites" in linea and not linea.lstrip().startswith("#")]

    assert llamadas, "la §7 bis no llama a python -m harness.cache_suites"
    assert any('--servicio "$NOMBRE"' in linea for linea in llamadas)


def test_f072_r23_la_clave_ya_no_se_compone_en_bash() -> None:
    texto = _texto()

    assert 'git rev-parse "HEAD:$RUTA"' not in texto
    assert "HASH_SRV" not in texto
    assert "SUCIO_SRV" not in texto


def test_f072_r27_la_llamada_no_consume_la_entrada_del_bucle() -> None:
    llamada = next(linea for linea in _seccion_7_bis().splitlines()
                   if "-m harness.cache_suites" in linea and "$(" in linea)

    assert "</dev/null" in llamada


def test_f072_r24_solo_se_guarda_con_clave_no_vacia() -> None:
    seccion = _seccion_7_bis()
    escrituras = [linea for linea in seccion.splitlines() if "suite_${NOMBRE}.ok" in linea
                  and ">" in linea]

    assert len(escrituras) == 1
    assert '[ -n "$CLAVE_SRV" ]' in escrituras[0]
    assert '"$CLAVE_SRV"' in escrituras[0].split("printf", 1)[1]


def test_f072_r24_mensaje_de_cache_con_la_fecha_del_verde() -> None:
    assert ("caché: ni el servicio ni sus dependencias han cambiado desde el verde del "
            "$FECHA_VERDE") in _seccion_7_bis()


def test_f072_r25_sin_cache_en_la_cabecera_y_aviso_unico_fuera_del_bucle() -> None:
    seccion = _seccion_7_bis()
    avisos = [i for i, linea in enumerate(seccion.splitlines())
              if "ARNES_SIN_CACHE=1:" in linea]
    bucle = next(i for i, linea in enumerate(seccion.splitlines())
                 if linea.lstrip().startswith("while IFS='|' read -r NOMBRE"))

    assert 'SIN_CACHE="${ARNES_SIN_CACHE:-0}"' in _cabecera()
    assert len(avisos) == 1
    assert avisos[0] < bucle
    assert "--sin-cache" in seccion


def test_f072_r26_rama_de_fallo_ejecuta_sin_guardar() -> None:
    assert "no se pudo decidir la caché" in _seccion_7_bis()


# --- Comportamiento: la sección ejecutada con bash ----------------------------------


def _bash() -> str | None:
    ruta = shutil.which("bash")
    if ruta is None:
        return None
    if os.name == "nt" and "system32" in ruta.lower():
        return None  # el bash de WSL no ve las rutas de Windows igual
    return ruta


BASH = _bash()

_PY_FALSO = """#!/bin/bash
# Intérprete falso: responde como harness.servicios y harness.cache_suites.
case "$1 $2" in
  "-m harness.servicios")
    if [ "$3" = "--shell" ]; then cat "$DIR_CASO/servicios.txt"; fi
    exit 0 ;;
  "-m harness.cache_suites")
    echo "$*" >> "$DIR_CASO/llamadas.txt"
    cat > /dev/null   # se come la entrada estándar si se la dejan
    shift 3
    cat "$DIR_CASO/respuesta_$1.txt"
    exit "$(cat "$DIR_CASO/codigo_$1.txt" 2>/dev/null || echo 0)" ;;
  "-c import coverage") exit 1 ;;
  "-m pytest")
    nombre=$(basename "$PWD")
    echo "$nombre" >> "$DIR_CASO/suites.txt"
    exit "$(cat "$DIR_CASO/pytest_$nombre.txt" 2>/dev/null || echo 0)" ;;
esac
exit 2
"""


def _caso(tmp_path: Path, respuestas: dict[str, tuple[str, int]],
          sin_cache: str = "0", pytest_rojo: tuple[str, ...] = ()) -> tuple[str, Path]:
    """Ejecuta la §7 bis real con dos servicios y devuelve (salida, dir del caso)."""
    caso = tmp_path / "caso"
    (caso / "harness").mkdir(parents=True)
    (caso / "harness" / "servicios.json").write_text("{}", encoding="utf-8")
    falso = caso / "py_falso"
    falso.write_text(_PY_FALSO, encoding="utf-8", newline="\n")
    falso.chmod(0o755)
    py = falso.as_posix()
    lineas = []
    for nombre, (respuesta, codigo) in respuestas.items():
        (caso / f"svc_{nombre}" / "tests").mkdir(parents=True)
        lineas.append(f"{nombre}|svc_{nombre}|python|{py}|")
        (caso / f"respuesta_{nombre}.txt").write_text(respuesta, encoding="utf-8",
                                                     newline="\n")
        (caso / f"codigo_{nombre}.txt").write_text(str(codigo), encoding="utf-8")
    for nombre in pytest_rojo:
        (caso / f"pytest_svc_{nombre}.txt").write_text("1", encoding="utf-8")
    (caso / "servicios.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8",
                                        newline="\n")
    guion = caso / "seccion.sh"
    guion.write_text(
        "set -u\nFALLOS=0\nSALTAR_SUITES=0\n"
        f"SIN_CACHE={sin_cache}\nPY={py}\n"
        'ok()   { printf "[OK] %s\\n" "$1"; }\n'
        'warn() { printf "[AVISO] %s\\n" "$1"; }\n'
        'ko()   { printf "[KO] %s\\n" "$1"; FALLOS=$((FALLOS + 1)); }\n'
        + _seccion_7_bis() + 'echo "FALLOS=$FALLOS"\n',
        encoding="utf-8", newline="\n",
    )
    proceso = subprocess.run(
        [BASH, guion.name], cwd=caso, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "DIR_CASO": caso.as_posix()}, timeout=60, check=False,
    )
    return proceso.stdout + proceso.stderr, caso


def _leer(caso: Path, fichero: str) -> str:
    ruta = caso / fichero
    return ruta.read_text(encoding="utf-8") if ruta.exists() else ""


necesita_bash = pytest.mark.skipif(BASH is None, reason="sin bash utilizable")


@necesita_bash
def test_f072_r24_r27_avisos_servir_ejecutar_y_guardar(tmp_path: Path) -> None:
    salida, caso = _caso(tmp_path, {
        "a": ("AVISO|importa `x` desde /otro/arbol\nEJECUTAR|clave-a\n", 0),
        "b": ("SERVIR|2026-10-15 09:30\n", 0),
    })

    assert "[AVISO] servicio a (svc_a): importa `x` desde /otro/arbol" in salida
    assert "[OK] servicio a (svc_a): pytest en verde" in salida
    assert ("[OK] servicio b (svc_b): pytest en verde (caché: ni el servicio ni sus "
            "dependencias han cambiado desde el verde del 2026-10-15 09:30)") in salida
    assert _leer(caso, "suites.txt").split() == ["svc_a"]
    assert _leer(caso, ".arnes_cache/suite_a.ok") == "clave-a"
    assert not (caso / ".arnes_cache" / "suite_b.ok").exists()
    assert "FALLOS=0" in salida
    assert "ARNES_SIN_CACHE" not in salida


@necesita_bash
def test_f072_r24_sin_clave_no_se_guarda(tmp_path: Path) -> None:
    salida, caso = _caso(tmp_path, {"a": ("EJECUTAR|\n", 0)})

    assert "[OK] servicio a (svc_a): pytest en verde" in salida
    assert not (caso / ".arnes_cache" / "suite_a.ok").exists()


@necesita_bash
def test_f072_r24_suite_en_rojo_no_se_guarda(tmp_path: Path) -> None:
    salida, caso = _caso(tmp_path, {"a": ("EJECUTAR|clave-a\n", 0)}, pytest_rojo=("a",))

    assert "[KO] servicio a (svc_a): pytest en rojo" in salida
    assert "FALLOS=1" in salida
    assert not (caso / ".arnes_cache" / "suite_a.ok").exists()


@necesita_bash
def test_f072_r25_sin_cache_avisa_una_vez_y_pasa_la_opcion(tmp_path: Path) -> None:
    salida, caso = _caso(tmp_path, {"a": ("EJECUTAR|k1\n", 0), "b": ("EJECUTAR|k2\n", 0)},
                         sin_cache="1")

    assert salida.count("ARNES_SIN_CACHE=1") == 1
    llamadas = _leer(caso, "llamadas.txt").splitlines()
    assert len(llamadas) == 2
    assert all(linea.endswith("--sin-cache") for linea in llamadas)
    assert _leer(caso, ".arnes_cache/suite_b.ok") == "k2"


@necesita_bash
def test_f072_r25_sin_sin_cache_no_se_pasa_la_opcion(tmp_path: Path) -> None:
    _, caso = _caso(tmp_path, {"a": ("EJECUTAR|k1\n", 0)})

    assert "--sin-cache" not in _leer(caso, "llamadas.txt")


@necesita_bash
def test_f072_r26_fallo_del_modulo_avisa_ejecuta_y_no_guarda(tmp_path: Path) -> None:
    salida, caso = _caso(tmp_path, {
        "a": ("SERVIR|2026-10-15 09:30\n", 1),
        "b": ("EJECUTAR|k2\n", 0),
    })

    assert re.search(r"\[AVISO\] servicio a \(svc_a\): no se pudo decidir la caché", salida)
    assert "verde del" not in salida
    assert _leer(caso, "suites.txt").split() == ["svc_a", "svc_b"]
    assert not (caso / ".arnes_cache" / "suite_a.ok").exists()
    assert _leer(caso, ".arnes_cache/suite_b.ok") == "k2"


@necesita_bash
def test_f072_r27_los_tres_servicios_se_procesan(tmp_path: Path) -> None:
    """El falso se come stdin: sin `</dev/null`, el bucle perdería b y c."""
    _, caso = _caso(tmp_path, {
        "a": ("EJECUTAR|k1\n", 0), "b": ("EJECUTAR|k2\n", 0), "c": ("EJECUTAR|k3\n", 0),
    })

    assert len(_leer(caso, "llamadas.txt").splitlines()) == 3
    assert _leer(caso, "suites.txt").split() == ["svc_a", "svc_b", "svc_c"]
