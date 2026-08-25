# tests/test_f036_r13_tipologia_ler.py
"""F-036 R13 · la regla dura LER -> residuos, tambien en sv5.

sv2 ya la aplica al consolidar la tipologia del documento
(`tipologia_resolver`). sv5 la repite sobre las lineas YA PERSISTIDAS
como defensa en profundidad: si el `tipo_familia` se perdio por el
camino —justo el defecto D2 de esta feature, que dejaba
`contexto_linea` a NULL en el merge— el albaran de residuos acababa
valorandose con el prompt `generico` y ninguna regla de contenedores
llegaba a correr.

El catalogo LER es el de `ruesma_comun.ler` (R14): un unico sitio para
sv2 y sv5, sin copias que diverjan.

Funcion pura: sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from application.services.valuation_extraction_service import (
    _derivar_tipologia_valoracion,
)
from domain.models.contexto_linea import ContextoLinea


@dataclass(frozen=True)
class _Linea:
    """Lo unico que `_derivar_tipologia_valoracion` mira de una linea."""

    codigo: str | None = None
    descripcion: str | None = None
    contexto_linea: ContextoLinea | None = None


@dataclass(frozen=True)
class _Contexto:
    lineas_albaran: list


# ------------------------------------------------------------------ #
# R13 · el LER manda aunque no haya tipo_familia
# ------------------------------------------------------------------ #
def test_f036_r13_un_codigo_ler_en_el_contexto_basta():
    """El caso de SALMEDINA: contexto sin `tipo_familia`, con LER."""
    ctx = _Contexto(
        lineas_albaran=[
            _Linea(
                descripcion="RETIRADA CONTENEDOR",
                contexto_linea=ContextoLinea(codigo_ler="170504"),
            )
        ]
    )

    assert _derivar_tipologia_valoracion(ctx) == "residuos"


def test_f036_r13_basta_con_que_UNA_linea_traiga_ler():
    ctx = _Contexto(
        lineas_albaran=[
            _Linea(descripcion="PORTES"),
            _Linea(contexto_linea=ContextoLinea(codigo_ler="170203")),
        ]
    )

    assert _derivar_tipologia_valoracion(ctx) == "residuos"


def test_f036_r13_el_ler_gana_a_la_familia_hormigon():
    """La regla es DURA: se evalua antes que `tipo_familia`."""
    ctx = _Contexto(
        lineas_albaran=[
            _Linea(contexto_linea=ContextoLinea(tipo_familia="hormigon")),
            _Linea(contexto_linea=ContextoLinea(codigo_ler="170504")),
        ]
    )

    assert _derivar_tipologia_valoracion(ctx) == "residuos"


def test_f036_r13_el_ler_tambien_se_busca_en_el_texto_de_la_linea():
    """Red de seguridad: el LER escrito en el concepto, sin contexto."""
    ctx = _Contexto(
        lineas_albaran=[_Linea(descripcion="GESTION RESIDUO LER 170504")]
    )

    assert _derivar_tipologia_valoracion(ctx) == "residuos"


def test_f036_r13_el_ler_en_la_descripcion_extendida_tambien_cuenta():
    ctx = _Contexto(
        lineas_albaran=[
            _Linea(
                contexto_linea=ContextoLinea(
                    descripcion_extendida="CONTENEDOR RCD 17 05 04"
                )
            )
        ]
    )

    assert _derivar_tipologia_valoracion(ctx) == "residuos"


# ------------------------------------------------------------------ #
# R13 · lo que NO es un LER no dispara residuos
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "codigo_ler",
    [None, "", "   ", "192137", "19213", "990101"],
)
def test_f036_r13_un_ler_invalido_no_dispara_residuos(codigo_ler):
    """`192137` es el codigo de PRODUCTO de un mortero de Prebetong.

    El catalogo lo descarta (el capitulo 19 llega al subcapitulo 13):
    sin esa validacion, un albaran de mortero se valoraba como
    residuos. Mismo blindaje que en sv2.
    """
    ctx = _Contexto(
        lineas_albaran=[
            _Linea(
                descripcion="MORTERO SECO",
                contexto_linea=ContextoLinea(codigo_ler=codigo_ler),
            )
        ]
    )

    assert _derivar_tipologia_valoracion(ctx) == "generico"


def test_f036_r13_un_numero_de_seis_digitos_suelto_no_es_un_ler():
    """Sin contexto de residuos, un 6-digitos pegado es una referencia.

    OJO con el texto de este test: `texto_contiene_ler` busca "ler"
    como SUBCADENA, asi que palabras como "TORNILLERIA" o "ALQUILER"
    la contienen y darian contexto de residuos a cualquier 6-digitos
    valido. Es comportamiento HEREDADO de sv2 (jul 2026), no algo que
    F-036 introduzca; queda anotado como hallazgo en
    progress/impl_F-036_bloque_B.md porque tocarlo cambia el enrutado
    de la fase 2 y exige una pasada de evals.
    """
    ctx = _Contexto(
        lineas_albaran=[_Linea(codigo="170504", descripcion="TUERCA M-8")]
    )

    assert _derivar_tipologia_valoracion(ctx) == "generico"


# ------------------------------------------------------------------ #
# El comportamiento anterior no cambia
# ------------------------------------------------------------------ #
def test_f036_r13_sin_ler_manda_la_familia_como_siempre():
    ctx = _Contexto(
        lineas_albaran=[
            _Linea(contexto_linea=ContextoLinea(tipo_familia="hormigon"))
        ]
    )

    assert _derivar_tipologia_valoracion(ctx) == "hormigon"


def test_f036_r13_la_familia_residuos_sigue_bastando_sin_ler():
    ctx = _Contexto(
        lineas_albaran=[
            _Linea(contexto_linea=ContextoLinea(tipo_familia="residuos"))
        ]
    )

    assert _derivar_tipologia_valoracion(ctx) == "residuos"


def test_f036_r13_sin_lineas_sigue_siendo_generico():
    assert _derivar_tipologia_valoracion(_Contexto(lineas_albaran=[])) == (
        "generico"
    )


def test_f036_r13_una_linea_sin_contexto_no_revienta():
    ctx = _Contexto(lineas_albaran=[_Linea()])

    assert _derivar_tipologia_valoracion(ctx) == "generico"
