# tests/test_f070_cod_obra.py
"""F-070 · sv9 da de alta la obra canónica (R14, R15).

Regla del humano: todo código de obra lleva el 0 inicial salvo VAR y POSTV2.
Un merge guardado con ``686`` (anterior a F-070, P3: no se migra) mandaría
``cod_obra = "686"`` y Sigrid no encontraría la obra. El validador canoniza
``cod_obra`` y evalúa sobre él los motivos locales de la obra.

Sin red ni BBDD. Una sola llamada a ``validar_y_construir``: ``_validar``
(design §7, con la firma de la v8 de F-053: ``CONFIG`` sin ``usu`` y ``USU``).
"""
from __future__ import annotations

import pytest
from f053_datos import CONFIG, HOY, USU, datos, vinculada

from domain.models.alta_models import Motivo, PeticionAlbaran
from domain.services.validador_alta import MAX_CODIGO, validar_y_construir


def _validar(d):
    return validar_y_construir(d, CONFIG, HOY, USU)


def _peticion(obra) -> PeticionAlbaran:
    resultado = _validar(datos(vinculada(1), obra_codigo=obra))
    assert isinstance(resultado, PeticionAlbaran), resultado
    return resultado


# ================================================================ #
# R14 — cod_obra canonizado; lo que no encaja, recortado como hoy
# ================================================================ #
@pytest.mark.parametrize(
    ("en_merge", "cod_obra"),
    [
        ("686", "0686"),
        (" 686 ", "0686"),
        ("0686", "0686"),
        ("var", "VAR"),
        (" Var ", "VAR"),
        ("POSTV2", "POSTV2"),
        ("postv2", "POSTV2"),
        ("GG", "GG"),
        (" gg ", "gg"),       # no encaja: tal cual, recortado
        ("1234", "1234"),
    ],
)
def test_f070_r14_cod_obra_canonico(en_merge, cod_obra):
    assert _peticion(en_merge).cod_obra == cod_obra


def test_f070_r14_el_resto_de_la_peticion_no_cambia():
    """Solo cambia ``cod_obra``: la petición con ``686`` es la de ``0686``."""
    con_686 = _peticion("686")
    con_0686 = _peticion("0686")
    assert con_686 == con_0686


# ================================================================ #
# R15 — motivos locales de la obra sobre el código canonizado
# ================================================================ #
@pytest.mark.parametrize("vacia", [None, "", "   "])
def test_f070_r15_sin_obra_falta_obra(vacia):
    resultado = _validar(datos(vinculada(1), obra_codigo=vacia))
    assert resultado == [Motivo("falta_obra")]


def test_f070_r15_la_longitud_se_mide_sobre_el_canonico():
    """``0`` + 23 cifras no encaja (no son 3 ni 4): va tal cual y cabe. El
    límite se evalúa sobre lo que se manda, ya recortado."""
    justo = "9" * MAX_CODIGO
    assert _peticion(f"  {justo}  ").cod_obra == justo
    largo = "9" * (MAX_CODIGO + 1)
    assert _validar(datos(vinculada(1), obra_codigo=largo)) == [
        Motivo("campo_demasiado_largo", "cod_obra"),
    ]


def test_f070_r15_motivos_usan_la_misma_funcion_que_la_peticion():
    """``_cod_obra`` es el único punto de sv9 que lee ``obra_codigo``."""
    import inspect

    from domain.services import validador_alta

    fuente = inspect.getsource(validador_alta)
    assert fuente.count("cab.obra_codigo") == 1
    assert "def _cod_obra(" in fuente
    assert validador_alta._cod_obra(datos().cabecera) == "0404"


@pytest.mark.parametrize(
    "obra",
    [None, "", "   ", "686", " 686 ", "0686", "var", " Postv2 ", "GG", "1234",
     "9" * MAX_CODIGO, "9" * (MAX_CODIGO + 1), " " + "9" * MAX_CODIGO + " ", "900"],
)
def test_f070_r15_motivos_de_obra_equivalentes_a_los_de_antes(obra):
    """RM5 · el mutante «motivos con ``_texto`` en vez de ``_cod_obra``» es
    equivalente en COMPORTAMIENTO: los dos motivos de la obra solo miran si
    queda vacía y si pasa de ``MAX_CODIGO``, y canonizar solo añade un ``0`` a
    3 cifras o cambia la caja de VAR/POSTV2. Lo mata solo el test estructural
    de arriba (un único lector), a propósito."""
    from domain.services.validador_alta import _cod_obra, _texto

    cab = datos(obra_codigo=obra).cabecera
    nuevo, viejo = _cod_obra(cab), _texto(cab.obra_codigo)
    assert (not nuevo) == (not viejo)
    assert (len(nuevo) > MAX_CODIGO) == (len(viejo) > MAX_CODIGO)


def test_f070_r15_control_la_demostracion_distingue_codigos():
    """Control: la petición sí cambia (``686`` ≠ ``0686``)."""
    from domain.services.validador_alta import _cod_obra, _texto

    cab = datos(obra_codigo="686").cabecera
    assert _cod_obra(cab) != _texto(cab.obra_codigo)
