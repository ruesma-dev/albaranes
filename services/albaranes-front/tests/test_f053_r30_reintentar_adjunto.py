# tests/test_f053_r30_reintentar_adjunto.py
"""F-053 v8 · T47 (R30, R23; O1 = a) · «Reintentar adjunto».

Un alta ``registrado`` en modo ``real`` cuyo PDF no quedó colgado en Sigrid
(adjunto en error o sin estado) ofrece «Reintentar adjunto»: publica
``accion="alta"`` y sv9, que ya la trata como ``solo_adjunto`` (R7, R23), solo
reintenta el adjunto. Mismas condiciones del documento que «Solicitar alta»
(aprobado, activo, ``approved_at_utc`` ≥ DESDE). R25 no la bloquea: no escribe
en BBDD (solo publica), y el alta registrada ES bloqueante.

Servicio real con dobles; ruta con ``build_app`` real. Sin BBDD ni colas.
"""
from __future__ import annotations

import pytest
from test_f053_t20_rutas import AHORA, DOC, _cliente, _Orq, _RepoAlta, _servicio_alta

from domain.models.alta_sigrid_models import AltaSigridVista, ConfigAltaSigrid
from domain.services.alta_sigrid import puede_reintentar_adjunto


def _registrado(modo="real", adjunto="error", estado="registrado"):
    return AltaSigridVista(estado=estado, modo=modo, sigrid_cod="AC26/7",
                           sigrid_con_ide=7, adjunto_estado=adjunto)


# ------------------------------------------------------------------ #
# Servicio
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("adjunto", ["error", None])
def test_f053_r30_reintentar_adjunto_publica_alta(adjunto):
    orq = _Orq()
    servicio = _servicio_alta(_RepoAlta(_registrado(adjunto=adjunto)), orq)
    assert servicio.puede_reintentar_adjunto(DOC) is True
    assert servicio.reintentar_adjunto_sigrid(document_id=DOC, solicitado_por="ana") == "pedida"
    assert orq.pedidas == [{"document_id": DOC, "accion": "alta", "solicitado_por": "ana"}]


@pytest.mark.parametrize("repo", [
    _RepoAlta(_registrado(adjunto="colgado")),
    _RepoAlta(_registrado(modo="simulacion")),
    _RepoAlta(_registrado(modo=None)),
    _RepoAlta(_registrado(estado="simulado", modo="simulacion")),
    _RepoAlta(_registrado(estado="simulado")),
    _RepoAlta(_registrado(estado="anulado")),
    _RepoAlta(_registrado(estado="incierto")),
    _RepoAlta(None),
    _RepoAlta(_registrado(), aprobado=False),
    _RepoAlta(_registrado(), activo=False),
    _RepoAlta(_registrado(), approved_at="2026-09-30T23:59:59+00:00"),
    _RepoAlta(_registrado(), approved_at=None),
], ids=["colgado", "simulacion", "sin_modo", "simulado", "simulado_real", "anulado",
        "incierto", "sin_alta", "no_aprobado", "papelera", "antes_de_desde", "sin_fecha"])
def test_f053_r30_reintentar_adjunto_cuando_no_procede_no_publica(repo):
    orq = _Orq()
    servicio = _servicio_alta(repo, orq)
    assert servicio.puede_reintentar_adjunto(DOC) is False
    assert servicio.reintentar_adjunto_sigrid(document_id=DOC, solicitado_por="ana") \
        == "no_procede"
    assert orq.pedidas == []


def test_f053_r30_reintentar_adjunto_sin_documento():
    repo = _RepoAlta(_registrado())
    repo.estado = None
    servicio = _servicio_alta(repo, _Orq())
    assert servicio.puede_reintentar_adjunto(DOC) is False
    assert servicio.reintentar_adjunto_sigrid(document_id=DOC, solicitado_por=None) \
        == "no_procede"


def test_f053_r30_reintentar_adjunto_con_desde_vacia_no_publica():
    orq = _Orq()
    servicio = _servicio_alta(_RepoAlta(_registrado()), orq, ConfigAltaSigrid())
    assert servicio.puede_reintentar_adjunto(DOC) is False
    assert servicio.reintentar_adjunto_sigrid(document_id=DOC, solicitado_por="ana") == "apagada"
    assert orq.pedidas == []


def test_f053_r30_reintentar_adjunto_que_no_se_publica_lo_dice():
    servicio = _servicio_alta(_RepoAlta(_registrado()), _Orq(publica=False))
    assert servicio.reintentar_adjunto_sigrid(document_id=DOC, solicitado_por="ana") \
        == "no_publicada"


def test_f053_r23_solicitar_alta_sigue_sin_ofrecerse_en_registrado():
    servicio = _servicio_alta(_RepoAlta(_registrado()), _Orq())
    assert servicio.puede_solicitar_alta(DOC, ahora=AHORA) is False
    assert servicio.puede_reintentar_adjunto(DOC) is True


def test_f053_r23_el_registrado_es_bloqueante_y_aun_asi_se_reintenta():
    """R25 bloquea lo que ESCRIBE; reintentar el adjunto solo publica."""
    alta = _registrado()
    assert alta.bloqueante is True
    orq = _Orq()
    assert _servicio_alta(_RepoAlta(alta), orq).reintentar_adjunto_sigrid(
        document_id=DOC, solicitado_por="ana") == "pedida"


def test_f053_r30_regla_pura_sin_config_activa():
    assert puede_reintentar_adjunto(
        aprobado=True, activo=True, approved_at_utc="2026-10-05T10:00:00+00:00",
        alta=_registrado(), config=ConfigAltaSigrid(),
    ) is False


# ------------------------------------------------------------------ #
# Ruta
# ------------------------------------------------------------------ #
class _ServicioReintento:
    def __init__(self, resultado):
        self.resultado = resultado
        self.llamadas: list[tuple] = []

    def initialize(self):
        return True

    def reintentar_adjunto_sigrid(self, *, document_id, solicitado_por):
        self.llamadas.append((document_id, solicitado_por))
        return self.resultado

    def __getattr__(self, nombre):
        raise AssertionError(f"la ruta no debe llamar a {nombre} (R25 no la bloquea)")


@pytest.mark.parametrize("resultado, texto", [
    ("pedida", "pedido"), ("no_publicada", "no+se+pudo"), ("no_procede", "no+procede"),
    ("apagada", "desactivada"),
])
def test_f053_r30_ruta_reintentar_adjunto(monkeypatch, resultado, texto):
    servicio = _ServicioReintento(resultado)
    cliente, publicador = _cliente(monkeypatch, servicio)
    respuesta = cliente.post(f"/documents/{DOC}/alta-sigrid/reintentar-adjunto",
                             headers={"X-MS-CLIENT-PRINCIPAL-NAME": "ana@ruesma.es"})
    assert respuesta.status_code == 303
    destino = respuesta.headers["location"]
    assert destino.startswith(f"/documents/{DOC}?message=")
    assert texto in destino
    assert servicio.llamadas == [(DOC, "ana@ruesma.es")]
