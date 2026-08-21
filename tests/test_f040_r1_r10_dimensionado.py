# tests/test_f040_r1_r10_dimensionado.py
"""F-040 · R1–R10: la campaña se dimensiona sola en vez de adivinar.

Dos números que el arnés se inventaba, y lo que se mide de verdad en su lugar:

- **El timeout por mutante** era un fijo de `rigor.json`. Ahora sale de la
  LÍNEA BASE que la campaña ya corre dentro de cada worktree, con los W workers
  compitiendo: la medición correcta ya estaba hecha y se tiraba. El valor
  configurado pasa a ser un SUELO.
- **Los workers por defecto** eran `núcleos - 2` con tope 16, que supone que el
  cuello de botella es la CPU. No lo es: cada worker arranca una suite completa
  —intérprete, importaciones, E/S—, así que el recurso escaso es la máquina.

Los dos números salen de la campaña real del 2026-08-21: suite en reposo ~51 s,
97,5 s con 1 worker, 119–122 s con 3, contra un timeout configurado de 120 s.
Con el default de 16 workers no cabía ni una línea base.

Ningún test de este fichero ejecuta una suite: todos usan ejecutores dobles.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from harness.mutacion import (
    TOPE_WORKERS,
    resolver_workers,
    workers_por_defecto,
)
from harness.rigor import RUTA_RIGOR, cargar_rigor, workers_mutacion


# --- R8: el default deja de suponer que el cuello es la CPU -----------------


def test_f040_r8_el_tope_de_workers_calculados_es_cuatro() -> None:
    """El único punto medido y VERDE son 3 workers, y ya ahí la suite sube 25 %.

    4 es un paso sobre lo medido, no un salto. Por encima nadie ha medido, y el
    arnés viaja a máquinas más pequeñas que ésta, donde un tope alto no es
    optimista sino dañino.
    """
    assert TOPE_WORKERS == 4


@pytest.mark.parametrize(
    ("nucleos", "esperados"),
    [
        (1, 1),
        (2, 1),
        (4, 1),
        (6, 2),
        (8, 3),
        (10, 4),
        (22, 4),
        (128, 4),
    ],
)
def test_f040_r8_workers_por_defecto_reservan_dos_nucleos_por_worker(
    nucleos: int, esperados: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`min(max(1, (núcleos - 2) // 2), TOPE_WORKERS)`.

    Los dos primeros núcleos son los de siempre —la máquina y el coordinador—;
    el `// 2` reserva del orden de dos por suite, porque pytest no es monohilo:
    importa, compila y escribe caché mientras corre.
    """
    monkeypatch.setattr("harness.mutacion.os.cpu_count", lambda: nucleos)

    assert workers_por_defecto() == esperados


def test_f040_r8_workers_por_defecto_nunca_bajan_de_uno(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cero workers no es una campaña más barata: es ninguna campaña."""
    monkeypatch.setattr("harness.mutacion.os.cpu_count", lambda: None)

    assert workers_por_defecto() == 1


def test_f040_r8_en_la_maquina_de_la_medicion_el_default_baja_de_16_a_4(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """22 núcleos: el default que hacía la campaña inutilizable, y el nuevo."""
    monkeypatch.setattr("harness.mutacion.os.cpu_count", lambda: 22)

    assert workers_por_defecto() == 4
    assert min(max(1, 22 - 2), 16) == 16, "el default viejo, para que se vea el salto"


# --- R9: el límite de una máquina no se cablea en un arnés que viaja --------


def test_f040_r9_rigor_json_no_declara_la_clave_workers() -> None:
    bloque = json.loads(RUTA_RIGOR.read_text(encoding="utf-8"))["mutacion"]

    assert "workers" not in bloque, (
        "declarar 'mutacion.workers' cablearía el límite de ESTA máquina en un "
        "arnés que se instala en cinco proyectos (decisión del 2026-08-20)"
    )


def test_f040_r9_sin_la_clave_workers_manda_el_default_por_nucleos() -> None:
    assert workers_mutacion(cargar_rigor(RUTA_RIGOR)) is None
    assert resolver_workers(None, None) == workers_por_defecto()


def test_f040_r9_la_precedencia_no_cambia() -> None:
    """`--workers` > `mutacion.workers` > default, intacta."""
    assert resolver_workers(3, 8) == 3
    assert resolver_workers(None, 8) == 8


# --- R10: el tope calculado no limita lo que se pida a mano ----------------


@pytest.mark.parametrize("pedidos", [5, 12, 32])
def test_f040_r10_workers_pedidos_a_mano_no_se_recortan(pedidos: int) -> None:
    """Subir el tope es una decisión CON DATOS, y aquí es donde se producen."""
    assert resolver_workers(pedidos, None) == pedidos
    assert resolver_workers(pedidos, 2) == pedidos


def test_f040_r10_tampoco_se_recorta_lo_declarado_en_rigor_json() -> None:
    """Un proyecto que sí quiera declarar `workers` puede pasarse del tope."""
    assert resolver_workers(None, 12) == 12


# --- R1: el timeout por mutante sale de la línea base ya medida -------------

from harness.mutacion import (  # noqa: E402
    FACTOR_HOLGURA_BASE,
    MARGEN_TIMEOUT,
    timeout_de_linea_base,
    timeout_derivado,
)

#: Los tres tiempos de línea base de la campaña real del 2026-08-21, uno por
#: worktree, con tres workers compitiendo por la misma máquina.
BASE_MEDIDA = {"wk_0": 119.3, "wk_1": 121.6, "wk_2": 119.5}

#: `mutacion.timeout_por_mutante_s` de este repositorio. No se toca: pasa a ser
#: un suelo, y un mutante nunca recibe menos que hoy.
SUELO = 120


def test_f040_r1_el_margen_es_dos() -> None:
    """Dos, no diez: un margen generoso deja pasar mutantes que cuelgan."""
    assert MARGEN_TIMEOUT == 2.0


def test_f040_r1_con_la_medicion_real_el_timeout_sale_244_s() -> None:
    """`max(120, ceil(121,6 × 2)) = 244`. Manda el peor worker, no la media."""
    assert timeout_derivado(SUELO, BASE_MEDIDA) == 244


def test_f040_r1_manda_el_PEOR_de_los_tiempos_medidos() -> None:
    """Un timeout que solo le vale al worker más rápido no le vale a nadie."""
    assert timeout_derivado(SUELO, {"lento": 200.0, "rapido": 1.0}) == 400


def test_f040_r7_el_valor_configurado_es_un_SUELO_y_nunca_un_techo() -> None:
    """Una suite rápida no baja el timeout por debajo de lo configurado."""
    assert timeout_derivado(SUELO, {"wk_0": 3.0}) == SUELO
    assert timeout_derivado(SUELO, {"wk_0": 59.9}) == SUELO
    assert timeout_derivado(SUELO, {"wk_0": 60.1}) > SUELO


def test_f040_r1_sin_medicion_se_queda_el_suelo() -> None:
    """Ejecutores dobles, campaña sin línea base: no hay nada de lo que derivar."""
    assert timeout_derivado(SUELO, {}) == SUELO


def test_f040_r1_el_derivado_se_redondea_HACIA_ARRIBA() -> None:
    """Redondear a la baja regalaría el segundo que faltaba justo al peor caso."""
    assert timeout_derivado(1, {"wk_0": 60.01}) == math.ceil(60.01 * 2) == 121


def test_f040_r1_el_margen_se_puede_inyectar_para_probarlo() -> None:
    assert timeout_derivado(1, {"wk_0": 50.0}, margen=3.0) == 150


def test_f040_r1_el_derivado_siempre_es_un_entero() -> None:
    derivado = timeout_derivado(SUELO, BASE_MEDIDA)

    assert isinstance(derivado, int) and not isinstance(derivado, bool)


# --- R2: la línea base tiene su propio timeout, más holgado ----------------


def test_f040_r2_el_factor_de_holgura_de_la_base_es_cinco() -> None:
    assert FACTOR_HOLGURA_BASE == 5


def test_f040_r2_la_linea_base_recibe_el_suelo_por_el_factor() -> None:
    """Huevo y gallina: la base necesita un timeout para poder medirse.

    Se le concede el suyo, holgado y aparte, y es defendible porque se paga UNA
    VEZ POR WORKER, no una por mutante. Si ni con diez minutos cabe la suite
    limpia, el problema ya no es el reloj.
    """
    assert timeout_de_linea_base(SUELO) == 600


def test_f040_r2_la_base_siempre_recibe_mas_tiempo_que_un_mutante() -> None:
    for suelo in (30, 120, 300):
        assert timeout_de_linea_base(suelo) > suelo
