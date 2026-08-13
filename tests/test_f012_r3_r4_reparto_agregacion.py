# tests/test_f012_r3_r4_reparto_agregacion.py
"""F-012 · R3 y R4: reparto determinista y agregación fiel de los parciales.

Todo lo que se prueba aquí son funciones puras: ni git, ni disco, ni
subprocesos. Son las dos piezas de las que depende que el informe paralelo sea
indistinguible del que produce la campaña en serie.
"""

from __future__ import annotations

from harness.alcance import Alcance
from harness.mutacion import InformeMutacion, Mutante
from harness.mutacion_paralela import clave_estable, fusionar, repartir


def _mutante(fichero: str, linea: int, col: int = 4, operador: str = "comparacion") -> Mutante:
    return Mutante(
        fichero=fichero,
        linea=linea,
        col=col,
        original="if a == b:",
        mutado="if a != b:",
        operador=operador,
        longitud=2,
        sustituto="!=",
    )


def _alcance() -> Alcance:
    return Alcance(
        feature="F-012",
        origen="rama",
        ref_diff=("base", "rama"),
        lineas={"harness/uno.py": {1, 2, 3}, "harness/dos.py": {7}},
    )


def _lote(cuantos: int) -> list[Mutante]:
    return [_mutante("harness/uno.py", numero) for numero in range(1, cuantos + 1)]


# --- R3: reparto ------------------------------------------------------------


def test_f012_r3_reparto_ni_repite_ni_omite_ningun_mutante() -> None:
    mutantes = _lote(7)

    particiones = repartir(mutantes, 3)

    repartidos = [mutante for particion in particiones for mutante in particion]
    assert len(repartidos) == 7
    assert sorted(repartidos, key=clave_estable) == sorted(mutantes, key=clave_estable)
    assert len(set(id(m) for m in repartidos)) == 7


def test_f012_r3_reparto_es_determinista() -> None:
    mutantes = _lote(11)

    assert repartir(mutantes, 4) == repartir(mutantes, 4)


def test_f012_r3_reparto_equilibra_las_particiones() -> None:
    tamanios = [len(particion) for particion in repartir(_lote(10), 4)]

    assert max(tamanios) - min(tamanios) <= 1
    assert sum(tamanios) == 10


def test_f012_r3_reparto_con_un_worker_devuelve_una_sola_particion() -> None:
    mutantes = _lote(5)

    assert repartir(mutantes, 1) == [mutantes]


def test_f012_r3_reparto_con_mas_workers_que_mutantes_deja_particiones_vacias() -> None:
    particiones = repartir(_lote(2), 5)

    assert len(particiones) == 5
    assert [len(particion) for particion in particiones] == [1, 1, 0, 0, 0]


def test_f012_r3_reparto_sin_mutantes_no_revienta() -> None:
    assert repartir([], 3) == [[], [], []]


# --- R4: fusión de los informes parciales -----------------------------------


def test_f012_r4_fusionar_suma_totales_y_ordena_por_clave_estable() -> None:
    alcance = _alcance()
    primero = InformeMutacion(
        feature="F-012",
        alcance=alcance,
        generados=2,
        muertos=1,
        supervivientes=[_mutante("harness/uno.py", 9)],
        mutantes_evaluados=[_mutante("harness/uno.py", 9), _mutante("harness/dos.py", 1)],
        segundos=10.0,
    )
    segundo = InformeMutacion(
        feature="F-012",
        alcance=alcance,
        generados=2,
        muertos=2,
        supervivientes=[_mutante("harness/dos.py", 3)],
        mutantes_evaluados=[_mutante("harness/uno.py", 2), _mutante("harness/dos.py", 3)],
        segundos=12.0,
    )

    informe = fusionar(alcance, [primero, segundo], generados=9, segundos=13.5)

    assert informe.feature == "F-012"
    assert informe.alcance is alcance
    assert informe.generados == 9
    assert informe.muertos == 3
    assert informe.evaluados == 4
    assert informe.segundos == 13.5
    assert [clave_estable(m) for m in informe.mutantes_evaluados] == sorted(
        clave_estable(m) for m in informe.mutantes_evaluados
    )
    assert [(m.fichero, m.linea) for m in informe.supervivientes] == [
        ("harness/dos.py", 3),
        ("harness/uno.py", 9),
    ]


def test_f012_r4_fusionar_agrega_y_ordena_los_timeouts() -> None:
    alcance = _alcance()
    parciales = [
        InformeMutacion(
            feature="F-012",
            alcance=alcance,
            timeouts=[_mutante("harness/uno.py", 8)],
        ),
        InformeMutacion(
            feature="F-012",
            alcance=alcance,
            timeouts=[_mutante("harness/uno.py", 2), _mutante("harness/dos.py", 1)],
        ),
    ]

    informe = fusionar(alcance, parciales, generados=3, segundos=1.0)

    assert [(m.fichero, m.linea) for m in informe.timeouts] == [
        ("harness/dos.py", 1),
        ("harness/uno.py", 2),
        ("harness/uno.py", 8),
    ]


def test_f012_r4_fusionar_conserva_el_muestreo_del_coordinador() -> None:
    alcance = _alcance()

    informe = fusionar(
        alcance,
        [InformeMutacion(feature="F-012", alcance=alcance, generados=1)],
        generados=305,
        segundos=2.0,
        muestreado=True,
        max_mutantes=60,
        semilla=20260813,
    )

    assert informe.generados == 305
    assert informe.muestreado is True
    assert informe.max_mutantes == 60
    assert informe.semilla == 20260813


def test_f012_r4_fusionar_sin_parciales_da_un_informe_vacio() -> None:
    alcance = _alcance()

    informe = fusionar(alcance, [], generados=0, segundos=0.4)

    assert informe.evaluados == 0
    assert informe.muertos == 0
    assert informe.supervivientes == []
    assert informe.timeouts == []
    assert informe.muestreado is False


def test_f012_r4_clave_estable_es_la_del_orden_de_la_campania_en_serie() -> None:
    mutante = _mutante("harness/uno.py", 12, col=7, operador="logico")

    assert clave_estable(mutante) == ("harness/uno.py", 12, 7, "logico")
