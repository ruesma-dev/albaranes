# tests/test_f069_servicio_usu.py
"""F-069 · T7 · el ``usu``: Lista → login del correo → Respaldo (R5–R8).

Dobles de los tres puertos; sin red ni BBDD.

- R5: con Entrada con ``usu``, el ``cod`` de ``dbo.usu`` para ese ``usu``
  (Origen ``lista``), sin probar el Login.
- R6: si la Entrada no casa, Aviso ``usuario_lista_no_existe`` y escalón siguiente.
- R7: sin Entrada con ``usu`` (o si no casó), el login del correo (``correo``) y,
  si no casa o no hay Correo de Ruesma, el Respaldo (``respaldo``).
- R8: lectura de ``dbo.usu`` caída, o Respaldo vacío cuando hace falta ⇒
  ``error`` ``usuario_no_resuelto`` sin previa ni grabación y sin leer ``dbo.emp``.
"""
from __future__ import annotations

import pytest

from application.alta_sigrid_service import MOTIVO_USUARIO
from domain.models.alta_models import AvisoResolucion, EstadoAlta, OrigenUsuario
from domain.services.usuario_sigrid import AVISO_USUARIO_LISTA_NO_EXISTE
from tests import f069_servicio as f
from tests.f053_fakes import RepoFalso

LISTA_USU = '{"login1": {"usu": "login1b"}}'


def _resolver(sigrid, approved_by, *, lista="", respaldo=f.RESPALDO):
    return f.servicio(sigrid, RepoFalso(), lista=lista, respaldo=respaldo)._resolver_usuario(
        "doc", approved_by,
    )


def test_f069_r5_origenes_del_usuario():
    assert [o.value for o in OrigenUsuario] == ["lista", "correo", "respaldo"]


# ------------------------------------------------------------------ #
# R5 · Entrada con usu
# ------------------------------------------------------------------ #
def test_f069_r5_entrada_con_usu_manda_el_cod_de_sigrid_sin_probar_el_login():
    sigrid = f.sigrid(usuarios={"login1b": "LOGIN1B", "login1": "login1"})
    repo, doc, resultado = f.procesar(sigrid, approved_by=" Login1@Ruesma.es", lista=LISTA_USU)
    assert resultado.estado is EstadoAlta.SIMULADO
    assert f.lecturas(sigrid, "buscar_usuario") == ["login1b"]
    assert f.pedidos(sigrid, "usu") == ["LOGIN1B"]
    assert repo.ultimo(doc).peticion["usu"] == "LOGIN1B"


def test_f069_r5_resolver_devuelve_origen_lista_sin_avisos():
    sigrid = f.sigrid(usuarios={"login1b": "login1b"})
    assert _resolver(sigrid, "login1@ruesma.es", lista=LISTA_USU) == (
        "login1b", OrigenUsuario.LISTA, [],
    )


def test_f069_r5_entrada_solo_con_empide_no_cuenta_para_el_usu():
    sigrid = f.sigrid(usuarios={"login1": "login1"})
    usu, origen, avisos = _resolver(sigrid, "login1@ruesma.es",
                                    lista='{"login1": {"empide": 1234567}}')
    assert (usu, origen, avisos) == ("login1", OrigenUsuario.CORREO, [])
    assert f.lecturas(sigrid, "buscar_usuario") == ["login1"]


def test_f069_r5_entrada_de_otro_login_no_aplica():
    sigrid = f.sigrid(usuarios={"login2": "login2"})
    assert _resolver(sigrid, "login2@ruesma.es", lista=LISTA_USU) == (
        "login2", OrigenUsuario.CORREO, [],
    )
    assert f.lecturas(sigrid, "buscar_usuario") == ["login2"]


# ------------------------------------------------------------------ #
# R6 · Entrada que no casa
# ------------------------------------------------------------------ #
def test_f069_r6_entrada_que_no_existe_deja_aviso_y_prueba_el_login():
    sigrid = f.sigrid(usuarios={"login1": "login1"})
    usu, origen, avisos = _resolver(sigrid, "login1@ruesma.es", lista=LISTA_USU)
    assert (usu, origen) == ("login1", OrigenUsuario.CORREO)
    assert [a.codigo for a in avisos] == [AVISO_USUARIO_LISTA_NO_EXISTE]
    assert "login1b" in avisos[0].detalle and "@" not in avisos[0].detalle
    assert f.lecturas(sigrid, "buscar_usuario") == ["login1b", "login1"]


def test_f069_r6_entrada_que_no_existe_y_login_que_no_casa_va_al_respaldo():
    sigrid = f.sigrid(usuarios={})
    usu, origen, avisos = _resolver(sigrid, "login1@ruesma.es", lista=LISTA_USU)
    assert (usu, origen) == (f.RESPALDO, OrigenUsuario.RESPALDO)
    assert avisos == [AvisoResolucion(
        AVISO_USUARIO_LISTA_NO_EXISTE, avisos[0].detalle)]
    assert f.lecturas(sigrid, "buscar_usuario") == ["login1b", "login1"]


def test_f069_r6_el_aviso_no_impide_la_previa():
    sigrid = f.sigrid(usuarios={"login1": "login1"})
    _, _, resultado = f.procesar(sigrid, lista=LISTA_USU)
    assert resultado.estado is EstadoAlta.SIMULADO
    assert f.pedidos(sigrid, "usu") == ["login1"]


# ------------------------------------------------------------------ #
# R7 · login del correo y Respaldo
# ------------------------------------------------------------------ #
def test_f069_r7_sin_lista_el_login_del_correo():
    sigrid = f.sigrid(usuarios={"login1": "LOGIN1"})
    assert _resolver(sigrid, "Login1@ruesma.es") == ("LOGIN1", OrigenUsuario.CORREO, [])
    assert f.lecturas(sigrid, "buscar_usuario") == ["Login1"]


def test_f069_r7_login_que_no_casa_es_el_respaldo():
    sigrid = f.sigrid(usuarios={})
    assert _resolver(sigrid, "login1@ruesma.es") == (f.RESPALDO, OrigenUsuario.RESPALDO, [])


@pytest.mark.parametrize("approved_by", [None, "", "reviewer", "login1@gmail.com"])
def test_f069_r7_sin_correo_de_ruesma_es_el_respaldo_sin_leer(approved_by):
    sigrid = f.sigrid(usuarios={"login1": "login1", "reviewer": "reviewer"})
    assert _resolver(sigrid, approved_by, lista=LISTA_USU) == (
        f.RESPALDO, OrigenUsuario.RESPALDO, [],
    )
    assert f.lecturas(sigrid, "buscar_usuario") == []


def test_f069_r7_respaldo_recortado():
    assert _resolver(f.sigrid(), "reviewer", respaldo="  pgris \n")[0] == "pgris"


# ------------------------------------------------------------------ #
# R8 · sin usu no se sigue (y no se lee dbo.emp)
# ------------------------------------------------------------------ #
def _sin_usuario(repo, doc, resultado, sigrid, lecturas_usu):
    assert resultado.estado is EstadoAlta.ERROR
    guardado = repo.ultimo(doc)
    assert [m.codigo for m in guardado.motivos] == [MOTIVO_USUARIO]
    assert guardado.peticion is None
    assert f.lecturas(sigrid, "buscar_usuario") == lecturas_usu
    assert f.lecturas(sigrid, "buscar_empleados_por_correo") == []
    assert f.lecturas(sigrid, "empleado_de_alta") == []
    assert sigrid.commits() == []
    assert "buscar_albaranes" not in sigrid.operaciones()


@pytest.mark.parametrize("lista, lecturas_usu", [
    ("", ["login1"]),
    ('{"login1": {"usu": "login1b", "empide": 7}}', ["login1b"]),
])
def test_f069_r8_lectura_caida_es_error_sin_leer_dbo_emp(lista, lecturas_usu):
    sigrid = f.sigrid(fallar_en={"buscar_usuario"}, empleados_de_alta={7})
    repo, doc, resultado = f.procesar(sigrid, lista=lista)
    _sin_usuario(repo, doc, resultado, sigrid, lecturas_usu)


@pytest.mark.parametrize("approved_by, lecturas_usu", [
    ("login1@ruesma.es", ["login1"]), ("reviewer", []),
])
def test_f069_r8_respaldo_vacio_es_error_sin_leer_dbo_emp(approved_by, lecturas_usu):
    sigrid = f.sigrid(usuarios={}, empleados_de_alta={7})
    repo, doc, resultado = f.procesar(sigrid, approved_by=approved_by, respaldo=" ")
    _sin_usuario(repo, doc, resultado, sigrid, lecturas_usu)
    assert "ALTA_SIGRID_USUARIO_RESPALDO" in repo.ultimo(doc).motivos[0].detalle


def test_f069_r8_respaldo_vacio_no_importa_si_la_entrada_casa():
    sigrid = f.sigrid(usuarios={"login1b": "login1b"})
    _, _, resultado = f.procesar(sigrid, lista=LISTA_USU, respaldo="")
    assert resultado.estado is EstadoAlta.SIMULADO
    assert f.pedidos(sigrid, "usu") == ["login1b"]
