# tests/test_f069_servicio_empide.py
"""F-069 · T8 · el ``empide``: Lista → correo → nulo; nunca bloquea (R9–R14).

Dobles de los tres puertos; sin red ni BBDD.

- R9: Entrada con ``empide`` de alta ⇒ Origen ``lista``; si no existe o es de
  baja, Aviso ``empleado_lista_no_valido`` y escalón siguiente.
- R10: con Correo de Ruesma, un único Empleado del correo de alta ⇒ Origen
  ``correo``, sea cual sea el Origen del usuario (también con el Respaldo).
- R11: ambiguo (con cuántos), solo de baja, ninguno; sin Correo de Ruesma, sin
  leer ``dbo.emp``, ``empleado_sin_correo``.
- R12: si nada da empleado, ``empide`` nulo con Aviso ``defecto_sigrid_api``.
- R13: una lectura de ``dbo.emp`` caída deja ``empleado_lectura_fallida`` y
  sigue; ningún caso lleva a ``error``/``revisar``/``no_admitido`` ni impide la
  previa o la grabación.
- R14: primero ``usu``, luego ``empide``, los dos antes de la validación local.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from domain.models.alta_models import EmpleadoSigrid, EstadoAlta, ModoAlta, OrigenEmpleado
from domain.services.usuario_sigrid import (
    AVISO_DEFECTO_SIGRID_API,
    AVISO_EMPLEADO_CORREO_AMBIGUO,
    AVISO_EMPLEADO_CORREO_DE_BAJA,
    AVISO_EMPLEADO_CORREO_SIN_EMPLEADO,
    AVISO_EMPLEADO_LECTURA_FALLIDA,
    AVISO_EMPLEADO_LISTA_NO_VALIDO,
    AVISO_EMPLEADO_SIN_CORREO,
)
from tests import f069_servicio as f
from tests.f053_datos import datos, vinculada
from tests.f053_fakes import RepoFalso, SigridFalso, previa_ok

CORREO = "login1@ruesma.es"
LISTA_EMP = '{"login1": {"empide": 1234567}}'
ALTA = EmpleadoSigrid(1000001, True)
OTRO_ALTA = EmpleadoSigrid(1000002, True)
BAJA = EmpleadoSigrid(2000001, False)


def _resolver(sigrid, approved_by=CORREO, *, lista=""):
    return f.servicio(sigrid, RepoFalso(), lista=lista)._resolver_empleado(approved_by)


def _codigos(avisos) -> list[str]:
    return [a.codigo for a in avisos]


def test_f069_r12_origenes_del_empleado():
    assert [o.value for o in OrigenEmpleado] == ["lista", "correo", "defecto_sigrid_api"]


# ------------------------------------------------------------------ #
# R9 · Entrada con empide
# ------------------------------------------------------------------ #
def test_f069_r9_entrada_de_alta_gana_sin_leer_el_correo():
    sigrid = f.sigrid(empleados_de_alta={1234567}, empleados_por_correo={CORREO: [ALTA]})
    assert _resolver(sigrid, lista=LISTA_EMP) == (1234567, OrigenEmpleado.LISTA, [])
    assert f.lecturas(sigrid, "empleado_de_alta") == [1234567]
    assert f.lecturas(sigrid, "buscar_empleados_por_correo") == []


def test_f069_r9_entrada_no_valida_deja_aviso_y_usa_el_correo():
    sigrid = f.sigrid(empleados_de_alta=set(), empleados_por_correo={CORREO: [ALTA]})
    empide, origen, avisos = _resolver(sigrid, " Login1@Ruesma.ES", lista=LISTA_EMP)
    assert (empide, origen) == (ALTA.ide, OrigenEmpleado.CORREO)
    assert _codigos(avisos) == [AVISO_EMPLEADO_LISTA_NO_VALIDO]
    assert "1234567" in avisos[0].detalle
    assert f.lecturas(sigrid, "buscar_empleados_por_correo") == [CORREO]


def test_f069_r9_entrada_no_valida_y_correo_sin_empleado_es_nulo():
    sigrid = f.sigrid()
    assert _codigos(_resolver(sigrid, lista=LISTA_EMP)[2]) == [
        AVISO_EMPLEADO_LISTA_NO_VALIDO, AVISO_EMPLEADO_CORREO_SIN_EMPLEADO,
        AVISO_DEFECTO_SIGRID_API,
    ]


def test_f069_r9_entrada_solo_con_usu_no_cuenta_para_el_empleado():
    sigrid = f.sigrid(empleados_por_correo={CORREO: [ALTA]})
    assert _resolver(sigrid, lista='{"login1": {"usu": "login1b"}}') == (
        ALTA.ide, OrigenEmpleado.CORREO, [],
    )
    assert f.lecturas(sigrid, "empleado_de_alta") == []


# ------------------------------------------------------------------ #
# R10–R12 · correo y nulo
# ------------------------------------------------------------------ #
def test_f069_r10_un_unico_empleado_de_alta_del_correo():
    sigrid = f.sigrid(empleados_por_correo={CORREO: [ALTA, BAJA]})
    assert _resolver(sigrid, "  LOGIN1@ruesma.es ") == (ALTA.ide, OrigenEmpleado.CORREO, [])
    assert f.lecturas(sigrid, "buscar_empleados_por_correo") == [CORREO]


@pytest.mark.parametrize("filas, codigo", [
    ([ALTA, OTRO_ALTA], AVISO_EMPLEADO_CORREO_AMBIGUO),
    ([BAJA], AVISO_EMPLEADO_CORREO_DE_BAJA),
    ([], AVISO_EMPLEADO_CORREO_SIN_EMPLEADO),
])
def test_f069_r11_correo_que_no_da_empleado_cae_al_nulo(filas, codigo):
    sigrid = f.sigrid(empleados_por_correo={CORREO: filas})
    empide, origen, avisos = _resolver(sigrid)
    assert (empide, origen) == (None, OrigenEmpleado.DEFECTO_SIGRID_API)
    assert _codigos(avisos) == [codigo, AVISO_DEFECTO_SIGRID_API]


def test_f069_r11_ambiguo_dice_cuantos_sin_sus_ide():
    sigrid = f.sigrid(empleados_por_correo={CORREO: [ALTA, OTRO_ALTA]})
    aviso = _resolver(sigrid)[2][0]
    assert aviso.detalle.startswith("2 ")
    assert str(ALTA.ide) not in aviso.detalle and str(OTRO_ALTA.ide) not in aviso.detalle


@pytest.mark.parametrize("approved_by", [None, "", "reviewer", "login1@gmail.com"])
def test_f069_r11_sin_correo_de_ruesma_no_lee_dbo_emp(approved_by):
    sigrid = f.sigrid(empleados_por_correo={CORREO: [ALTA]})
    empide, origen, avisos = _resolver(sigrid, approved_by, lista=LISTA_EMP)
    assert (empide, origen) == (None, OrigenEmpleado.DEFECTO_SIGRID_API)
    assert _codigos(avisos) == [AVISO_EMPLEADO_SIN_CORREO, AVISO_DEFECTO_SIGRID_API]
    assert f.lecturas(sigrid, "buscar_empleados_por_correo") == []
    assert f.lecturas(sigrid, "empleado_de_alta") == []


def test_f069_r12_el_aviso_del_nulo_dice_que_lo_pone_sigrid_api():
    aviso = _resolver(f.sigrid())[2][-1]
    assert aviso.codigo == AVISO_DEFECTO_SIGRID_API and "sigrid-api" in aviso.detalle


# ------------------------------------------------------------------ #
# R13 · lecturas caídas: aviso y sigue
# ------------------------------------------------------------------ #
def test_f069_r13_lectura_de_la_lista_caida_sigue_al_correo():
    sigrid = f.sigrid(fallar_en={"empleado_de_alta"}, empleados_por_correo={CORREO: [ALTA]})
    empide, origen, avisos = _resolver(sigrid, lista=LISTA_EMP)
    assert (empide, origen) == (ALTA.ide, OrigenEmpleado.CORREO)
    assert _codigos(avisos) == [AVISO_EMPLEADO_LECTURA_FALLIDA]
    assert "Explota" in avisos[0].detalle


def test_f069_r13_lectura_del_correo_caida_es_nulo():
    sigrid = f.sigrid(fallar_en={"buscar_empleados_por_correo"})
    empide, origen, avisos = _resolver(sigrid)
    assert (empide, origen) == (None, OrigenEmpleado.DEFECTO_SIGRID_API)
    assert _codigos(avisos) == [AVISO_EMPLEADO_LECTURA_FALLIDA, AVISO_DEFECTO_SIGRID_API]


def test_f069_r13_las_dos_lecturas_caidas():
    sigrid = f.sigrid(fallar_en={"buscar_empleados_por_correo", "empleado_de_alta"})
    assert _codigos(_resolver(sigrid, lista=LISTA_EMP)[2]) == [
        AVISO_EMPLEADO_LECTURA_FALLIDA, AVISO_EMPLEADO_LECTURA_FALLIDA, AVISO_DEFECTO_SIGRID_API,
    ]


@pytest.mark.parametrize("fallar_en", [
    {"buscar_empleados_por_correo"}, {"empleado_de_alta"},
    {"buscar_empleados_por_correo", "empleado_de_alta"},
])
@pytest.mark.parametrize("modo, estado", [
    (ModoAlta.SIMULACION, EstadoAlta.SIMULADO), (ModoAlta.REAL, EstadoAlta.REGISTRADO),
])
def test_f069_r13_nada_del_empleado_impide_la_previa_ni_la_grabacion(fallar_en, modo, estado):
    creado = replace(previa_ok(f.peticion()), estado="creado")
    sigrid = SigridFalso(previa=previa_ok(f.peticion()), grabacion=creado,
                         usuarios={"login1": "login1"}, fallar_en=fallar_en)
    repo, doc, resultado = f.procesar(sigrid, lista=LISTA_EMP, modo=modo)
    assert resultado.estado is estado
    assert sigrid.commits() == ([False, True] if modo is ModoAlta.REAL else [False])
    assert [m.codigo for m in repo.ultimo(doc).motivos] == []


@pytest.mark.parametrize("filas", [[], [BAJA], [ALTA, OTRO_ALTA]])
def test_f069_r13_sin_empleado_el_alta_sigue_en_simulado(filas):
    sigrid = f.sigrid(usuarios={"login1": "login1"}, empleados_por_correo={CORREO: filas})
    repo, _doc, resultado = f.procesar(sigrid)
    assert resultado.estado is EstadoAlta.SIMULADO
    assert not [e for _, e in [(d, r.estado) for d, r in repo.guardados]
                if e in (EstadoAlta.ERROR, EstadoAlta.REVISAR, EstadoAlta.NO_ADMITIDO)]


def test_f069_r13_el_resolver_no_lanza_ni_con_un_fallo_raro():
    class Raro(SigridFalso):
        def buscar_empleados_por_correo(self, correo):
            raise KeyError("inesperado")

        def empleado_de_alta(self, ide):
            raise ZeroDivisionError

    empide, origen, avisos = _resolver(Raro(), lista=LISTA_EMP)
    assert (empide, origen) == (None, OrigenEmpleado.DEFECTO_SIGRID_API)
    assert _codigos(avisos) == [AVISO_EMPLEADO_LECTURA_FALLIDA, AVISO_EMPLEADO_LECTURA_FALLIDA,
                                AVISO_DEFECTO_SIGRID_API]


# ------------------------------------------------------------------ #
# R10 con el Respaldo · R14 orden
# ------------------------------------------------------------------ #
def test_f069_r10_con_usu_del_respaldo_el_empleado_sigue_saliendo_del_correo():
    sigrid = f.sigrid(usuarios={}, empleados_por_correo={CORREO: [ALTA]})
    servicio = f.servicio(sigrid, RepoFalso())
    assert servicio._resolver_usuario("doc", CORREO)[0] == f.RESPALDO
    assert servicio._resolver_empleado(CORREO) == (ALTA.ide, OrigenEmpleado.CORREO, [])


def test_f069_r14_usu_luego_empide_y_los_dos_antes_de_validar():
    sigrid = f.sigrid(usuarios={"login1": "login1"}, empleados_de_alta={1234567})
    no_admitido = datos(vinculada(1), obra_codigo=None)
    _, _, resultado = f.procesar(sigrid, lista=LISTA_EMP, d=no_admitido)
    assert resultado.estado is EstadoAlta.NO_ADMITIDO
    assert sigrid.operaciones() == ["buscar_usuario", "empleado_de_alta"]


def test_f069_r14_orden_completo_en_una_previa():
    sigrid = f.sigrid(usuarios={"login1": "login1"}, empleados_por_correo={CORREO: [ALTA]})
    f.procesar(sigrid)
    assert sigrid.operaciones() == [
        "buscar_usuario", "buscar_empleados_por_correo", "buscar_albaranes", "alta_albaran",
    ]


# ------------------------------------------------------------------ #
# T9 · el empide resuelto es el que se manda (R9, R10, R12)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("lista, sigrid_extra, esperado", [
    (LISTA_EMP, {"empleados_de_alta": {1234567}}, 1234567),                  # R9
    ("", {"empleados_por_correo": {CORREO: [ALTA]}}, ALTA.ide),               # R10
    ("", {"empleados_por_correo": {CORREO: [ALTA, OTRO_ALTA]}}, None),        # R11-R12
    ("", {}, None),                                                           # R12
])
def test_f069_r10_el_empide_resuelto_va_en_la_previa_y_la_grabacion(lista, sigrid_extra, esperado):
    creado = replace(previa_ok(f.peticion()), estado="creado")
    sigrid = SigridFalso(previa=previa_ok(f.peticion()), grabacion=creado,
                         usuarios={"login1": "login1"}, **sigrid_extra)
    repo, doc, resultado = f.procesar(sigrid, lista=lista, modo=ModoAlta.REAL)
    assert resultado.estado is EstadoAlta.REGISTRADO
    assert f.pedidos(sigrid, "empide") == [esperado, esperado]
    assert repo.ultimo(doc).peticion["empide"] == esperado


def test_f069_r9_validar_y_construir_recibe_el_empide():
    from domain.services.validador_alta import ConfigAlta, validar_y_construir
    from tests.f053_datos import CONFIG, HOY

    assert "empide" not in ConfigAlta.__dataclass_fields__
    assert validar_y_construir(f.D, CONFIG, HOY, "u", empide=7).empide == 7
    assert validar_y_construir(f.D, CONFIG, HOY, "u").empide is None
