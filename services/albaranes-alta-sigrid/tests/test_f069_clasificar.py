# tests/test_f069_clasificar.py
"""F-069 · T2 · clasificar los Empleados del correo (R10, R11).

``clasificar_empleados_correo`` es puro (lo importan el servicio y el script de
medición, R25): un único empleado de alta ⇒ su ``ide``; si no, ``None`` y el
Aviso de resolución de R11. Los de baja no cuentan (E7). El detalle del aviso
ambiguo dice cuántos (hasta «3 o más») sin sus ``ide``. Sin red ni BBDD.
"""
from __future__ import annotations

import pytest

from domain.models.alta_models import AvisoResolucion, EmpleadoSigrid
from domain.services.usuario_sigrid import (
    AVISO_DEFECTO_SIGRID_API,
    AVISO_EMPLEADO_CORREO_AMBIGUO,
    AVISO_EMPLEADO_CORREO_DE_BAJA,
    AVISO_EMPLEADO_CORREO_SIN_EMPLEADO,
    AVISO_EMPLEADO_LECTURA_FALLIDA,
    AVISO_EMPLEADO_LISTA_NO_VALIDO,
    AVISO_EMPLEADO_SIN_CORREO,
    AVISO_USUARIO_LISTA_NO_EXISTE,
    AVISOS_RESOLUCION,
    clasificar_empleados_correo,
)

ALTA_1 = EmpleadoSigrid(ide=1000001, de_alta=True)
ALTA_2 = EmpleadoSigrid(ide=1000002, de_alta=True)
ALTA_3 = EmpleadoSigrid(ide=1000003, de_alta=True)
ALTA_4 = EmpleadoSigrid(ide=1000004, de_alta=True)
BAJA_1 = EmpleadoSigrid(ide=2000001, de_alta=False)
BAJA_2 = EmpleadoSigrid(ide=2000002, de_alta=False)


def test_f069_r11_clasificar_los_codigos_son_los_de_la_spec():
    assert AVISO_USUARIO_LISTA_NO_EXISTE == "usuario_lista_no_existe"
    assert AVISO_EMPLEADO_LISTA_NO_VALIDO == "empleado_lista_no_valido"
    assert AVISO_EMPLEADO_CORREO_AMBIGUO == "empleado_correo_ambiguo"
    assert AVISO_EMPLEADO_CORREO_DE_BAJA == "empleado_correo_de_baja"
    assert AVISO_EMPLEADO_CORREO_SIN_EMPLEADO == "empleado_correo_sin_empleado"
    assert AVISO_EMPLEADO_SIN_CORREO == "empleado_sin_correo"
    assert AVISO_DEFECTO_SIGRID_API == "defecto_sigrid_api"
    assert AVISO_EMPLEADO_LECTURA_FALLIDA == "empleado_lectura_fallida"
    assert AVISOS_RESOLUCION == frozenset({
        "usuario_lista_no_existe", "empleado_lista_no_valido", "empleado_correo_ambiguo",
        "empleado_correo_de_baja", "empleado_correo_sin_empleado", "empleado_sin_correo",
        "defecto_sigrid_api", "empleado_lectura_fallida",
    })


@pytest.mark.parametrize("empleados", [
    [ALTA_1],
    [ALTA_1, BAJA_1],
    [BAJA_1, ALTA_1],
    [BAJA_1, ALTA_1, BAJA_2],
])
def test_f069_r11_clasificar_uno_de_alta_es_su_ide(empleados):
    assert clasificar_empleados_correo(empleados) == (ALTA_1.ide, None)


@pytest.mark.parametrize("empleados, cuantos", [
    ([ALTA_1, ALTA_2], "2"),
    ([ALTA_1, ALTA_2, BAJA_1], "2"),
    ([ALTA_1, ALTA_2, ALTA_3], "3 o más"),
    ([ALTA_1, ALTA_2, ALTA_3, ALTA_4], "3 o más"),
])
def test_f069_r11_clasificar_dos_o_mas_de_alta_es_ambiguo(empleados, cuantos):
    ide, aviso = clasificar_empleados_correo(empleados)
    assert ide is None
    assert aviso.codigo == AVISO_EMPLEADO_CORREO_AMBIGUO
    assert aviso.detalle.startswith(f"{cuantos} empleados de alta")
    for empleado in empleados:  # sin sus ide
        assert str(empleado.ide) not in aviso.detalle


@pytest.mark.parametrize("empleados", [[BAJA_1], [BAJA_1, BAJA_2]])
def test_f069_r11_clasificar_solo_de_baja(empleados):
    ide, aviso = clasificar_empleados_correo(empleados)
    assert ide is None
    assert aviso.codigo == AVISO_EMPLEADO_CORREO_DE_BAJA
    assert aviso.detalle
    for empleado in empleados:
        assert str(empleado.ide) not in aviso.detalle


def test_f069_r11_clasificar_ninguno():
    ide, aviso = clasificar_empleados_correo([])
    assert ide is None
    assert aviso.codigo == AVISO_EMPLEADO_CORREO_SIN_EMPLEADO
    assert aviso.detalle


def test_f069_r11_clasificar_modelos_inmutables_y_a_dict():
    aviso = AvisoResolucion("defecto_sigrid_api", "x")
    assert aviso.a_dict() == {"codigo": "defecto_sigrid_api", "detalle": "x"}
    with pytest.raises(AttributeError):
        aviso.codigo = "y"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        ALTA_1.ide = 3  # type: ignore[misc]
