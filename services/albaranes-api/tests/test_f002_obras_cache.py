# tests/test_f002_obras_cache.py
"""F-002 · Lista de obras activas para el prompt de IA1 (R1-bis, R3).

La lista se pide a sigrid-api UNA vez por réplica y TTL (R3) y se filtra
con el criterio PROVISIONAL de «obra activa» confirmado por el humano el
2026-08-13: código de 4 dígitos numéricos y mayor que ``cod_min``
(R1-bis, decisión D2).

Sin red: el proveedor es un doble y el filtro se prueba como función.
"""
from __future__ import annotations

import pytest

from config.settings import Settings
from domain.ports.obras_activas_provider import ObraActiva
from infrastructure.sigrid.obras_activas_cache import ObrasActivasCacheTTL
from infrastructure.sigrid.sigrid_api_obras_client import (
    filas_a_obras,
    filtrar_obras_activas,
)


class ProveedorFake:
    """Devuelve la respuesta programada para cada llamada."""

    def __init__(self, *respuestas) -> None:
        self._respuestas = list(respuestas)
        self.llamadas = 0

    def obtener(self):
        self.llamadas += 1
        indice = min(self.llamadas - 1, len(self._respuestas) - 1)
        return self._respuestas[indice]


class RelojFalso:
    def __init__(self) -> None:
        self.ahora = 0.0

    def __call__(self) -> float:
        return self.ahora

    def avanzar(self, segundos: float) -> None:
        self.ahora += segundos


def _obras(*codigos: str) -> list[ObraActiva]:
    return [ObraActiva(codigo=c, nombre=f"OBRA {c}") for c in codigos]


# ---------------------------------------------------------------- #
# R3 — una sola llamada dentro del TTL.
# ---------------------------------------------------------------- #
def test_f002_r3_dentro_del_ttl_solo_se_consulta_una_vez() -> None:
    proveedor = ProveedorFake(_obras("0500", "0600"))
    reloj = RelojFalso()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    resultados = [cache.obtener() for _ in range(10)]

    assert proveedor.llamadas == 1
    assert all(r == _obras("0500", "0600") for r in resultados)


def test_f002_r3_al_expirar_el_ttl_se_refresca() -> None:
    proveedor = ProveedorFake(_obras("0500"), _obras("0500", "0700"))
    reloj = RelojFalso()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    cache.obtener()
    reloj.avanzar(3601)
    segunda = cache.obtener()

    assert proveedor.llamadas == 2
    assert segunda == _obras("0500", "0700")


def test_f002_r3_justo_en_el_borde_del_ttl_no_se_refresca() -> None:
    proveedor = ProveedorFake(_obras("0500"))
    reloj = RelojFalso()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    cache.obtener()
    reloj.avanzar(3600)
    cache.obtener()

    assert proveedor.llamadas == 1


def test_f002_r3_la_cache_no_deja_mutar_lo_cacheado() -> None:
    proveedor = ProveedorFake(_obras("0500"))
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=RelojFalso())

    primera = cache.obtener()
    primera.append(ObraActiva(codigo="9999", nombre="INTRUSA"))

    assert cache.obtener() == _obras("0500")


# ---------------------------------------------------------------- #
# R2 — degradación: sin lista, se sirve la vieja o None.
# ---------------------------------------------------------------- #
def test_f002_r2_si_el_proveedor_falla_se_sirve_la_lista_vieja() -> None:
    proveedor = ProveedorFake(_obras("0500"), None)
    reloj = RelojFalso()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    cache.obtener()
    reloj.avanzar(3601)

    assert cache.obtener() == _obras("0500")


def test_f002_r2_sin_lista_previa_devuelve_none() -> None:
    cache = ObrasActivasCacheTTL(
        ProveedorFake(None), ttl_s=3600, clock=RelojFalso(),
    )

    assert cache.obtener() is None


def test_f002_r2_un_proveedor_que_revienta_no_propaga() -> None:
    class ProveedorRoto:
        def obtener(self):
            raise RuntimeError("sigrid-api 500")

    cache = ObrasActivasCacheTTL(
        ProveedorRoto(), ttl_s=3600, clock=RelojFalso(),
    )

    assert cache.obtener() is None


# ---------------------------------------------------------------- #
# R1-bis — filtro PROVISIONAL de «obra activa».
# ---------------------------------------------------------------- #
def test_f002_r1bis_descarta_codigos_que_no_son_de_4_digitos() -> None:
    entrada = _obras("0500", "500", "05000", "", "  ")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=450)] == [
        "0500",
    ]


def test_f002_r1bis_descarta_codigos_no_numericos() -> None:
    entrada = _obras("0500", "A500", "05.0", "OBRA")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=450)] == [
        "0500",
    ]


def test_f002_r1bis_descarta_los_codigos_por_debajo_del_corte() -> None:
    entrada = _obras("0449", "0450", "0451", "0999")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=450)] == [
        "0451", "0999",
    ]


def test_f002_r1bis_con_corte_cero_no_se_descarta_ninguna_por_valor() -> None:
    entrada = _obras("0001", "0449", "0450", "0451")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=0)] == [
        "0001", "0449", "0450", "0451",
    ]


def test_f002_r1bis_con_corte_cero_sigue_exigiendo_4_digitos() -> None:
    entrada = _obras("0001", "1", "12345", "X001")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=0)] == [
        "0001",
    ]


def test_f002_r1bis_el_corte_es_estricto_mayor_que() -> None:
    """`> 0450`, no `>=`: la obra 0450 queda fuera."""
    assert filtrar_obras_activas(_obras("0450"), cod_min=450) == []


# ---------------------------------------------------------------- #
# Parseo de la respuesta de sigrid-api (sin red).
# ---------------------------------------------------------------- #
def test_f002_r1bis_las_filas_de_sigrid_se_convierten_en_obras() -> None:
    columnas = ["codigo_obra", "nombre_obra"]
    filas = [["0451", "EDIFICIO A"], ["0452", None]]

    assert filas_a_obras(columnas, filas) == [
        ObraActiva(codigo="0451", nombre="EDIFICIO A"),
        ObraActiva(codigo="0452", nombre=None),
    ]


def test_f002_r1bis_las_filas_sin_codigo_se_ignoran() -> None:
    columnas = ["codigo_obra", "nombre_obra"]
    filas = [[None, "SIN CODIGO"], ["", "VACIA"], ["0451", "BUENA"]]

    assert [o.codigo for o in filas_a_obras(columnas, filas)] == ["0451"]


def test_f002_r1bis_los_codigos_se_deduplican_conservando_el_primero() -> None:
    """``con.cod`` se repite en Sigrid (varias filas por obra): el prompt
    no puede listar la misma obra dos veces."""
    columnas = ["codigo_obra", "nombre_obra"]
    filas = [["0451", "EDIFICIO A"], ["0451", "EDIFICIO A (bis)"]]

    assert filas_a_obras(columnas, filas) == [
        ObraActiva(codigo="0451", nombre="EDIFICIO A"),
    ]


# ---------------------------------------------------------------- #
# Configuración: los defaults son parte del contrato (R17, D2, D6).
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "campo,esperado",
    [
        ("obras_activas_enabled", True),
        ("obras_activas_ttl_s", 21600),
        ("obras_activas_max", 300),
        ("obras_activas_cod_min", 450),
        ("sigrid_api_timeout_s", 30.0),
    ],
)
def test_f002_r1bis_defaults_de_configuracion(campo: str, esperado) -> None:
    assert Settings.model_fields[campo].default == esperado
