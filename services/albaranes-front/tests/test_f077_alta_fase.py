# tests/test_f077_alta_fase.py
"""F-077 · B · el panel «Alta en Sigrid»: «Alta en curso…» solo mientras sv9 procesa.

- R14: fase ``en_curso`` / ``sin_respuesta`` / ``resultado`` (función pura con
  ``ahora`` inyectado; instantes comparados como instantes UTC).
- R17: ``no_admitido``, ``revisar`` y ``error`` son un error (``es_error``).
- R18: ``GET /api/documents/{id}/alta-sigrid/fase`` (200 con la fase, 404 sin
  documento; con la feature apagada, ``resultado`` sin leer el alta).
- R20: ni pintar ni sondear escriben el alta ni publican.

Sin red ni BBDD: dobles del repositorio y ``TestClient`` sobre ``build_app``.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from config.settings import Settings
from domain.models.alta_sigrid_models import AltaSigridVista, ConfigAltaSigrid
from domain.services import alta_sigrid as dominio
from interface_adapters.web import app as modulo_app

DESDE = datetime(2026, 10, 1, tzinfo=UTC)
APROBADO = "2026-10-16T10:00:00+00:00"
APROBADO_EN = datetime(2026, 10, 16, 10, 0, tzinfo=UTC)
ANTERIOR = "2026-10-15T09:00:00+00:00"
A_1_MIN = APROBADO_EN + timedelta(minutes=1)
A_6_MIN = APROBADO_EN + timedelta(minutes=6)
REPETIBLES = ("no_admitido", "revisar", "error", "simulado", "anulado")
CONFIG = ConfigAltaSigrid(desde=DESDE)


def _alta(estado: str, approved_at_utc: str | None) -> AltaSigridVista:
    return AltaSigridVista(estado=estado, approved_at_utc=approved_at_utc)


def _fase(alta, ahora=A_1_MIN, *, aprobado=True, activo=True, approved_at_utc=APROBADO, config=CONFIG):
    return dominio.fase_alta(aprobado=aprobado, activo=activo, approved_at_utc=approved_at_utc,
                             alta=alta, config=config, ahora=ahora)


# =================================================================== #
# R14 · tabla de casos de la fase
# =================================================================== #
def test_f077_r14_constantes():
    assert (dominio.FASE_EN_CURSO, dominio.FASE_SIN_RESPUESTA, dominio.FASE_RESULTADO) == (
        "en_curso", "sin_respuesta", "resultado")
    assert dominio.TOPE_RESPUESTA_ALTA == timedelta(minutes=5)


def test_f077_r14_sin_fila_en_curso_y_a_los_5_min_sin_respuesta():
    assert _fase(None, A_1_MIN) == "en_curso"
    assert _fase(None, APROBADO_EN) == "en_curso"
    assert _fase(None, APROBADO_EN + timedelta(minutes=5) - timedelta(seconds=1)) == "en_curso"
    assert _fase(None, APROBADO_EN + timedelta(minutes=5)) == "sin_respuesta"
    assert _fase(None, A_6_MIN) == "sin_respuesta"


@pytest.mark.parametrize("estado", REPETIBLES)
@pytest.mark.parametrize("instante", [ANTERIOR, None, "no es una fecha", ""])
def test_f077_r14_repetible_de_una_aprobacion_anterior_espera(estado, instante):
    assert _fase(_alta(estado, instante), A_1_MIN) == "en_curso"
    assert _fase(_alta(estado, instante), A_6_MIN) == "sin_respuesta"


@pytest.mark.parametrize("estado", ["ya_en_sigrid", "registrado", "incierto", "en_curso"])
def test_f077_r14_no_repetible_anterior_es_la_respuesta(estado):
    """sv9 ignora la aprobación nueva (F-053 R7): esa fila es la respuesta."""
    assert _fase(_alta(estado, ANTERIOR), A_1_MIN) == "resultado"
    assert _fase(_alta(estado, ANTERIOR), A_6_MIN) == "resultado"


def test_f077_r14_en_curso_de_la_vigente_espera_hasta_el_tope():
    assert _fase(_alta("en_curso", APROBADO), A_1_MIN) == "en_curso"
    assert _fase(_alta("en_curso", APROBADO), A_6_MIN) == "sin_respuesta"


def test_f077_r14_se_compara_como_instante_no_como_texto():
    """El mismo instante escrito de otra forma (``Z``, otra zona) es la vigente."""
    for texto in ("2026-10-16T10:00:00Z", "2026-10-16T12:00:00+02:00", "2026-10-16 10:00:00"):
        assert _fase(_alta("en_curso", texto), A_1_MIN) == "en_curso"
        assert _fase(_alta("no_admitido", texto), A_1_MIN) == "resultado"
    # Anterior por instante, aunque su texto ordene después.
    assert _fase(_alta("no_admitido", "2026-10-16T11:30:00+02:00"), A_1_MIN) == "en_curso"


@pytest.mark.parametrize("estado", ["no_admitido", "simulado", "registrado", "revisar", "error",
                                    "ya_en_sigrid", "incierto", "anulado"])
def test_f077_r14_resultado_de_la_vigente(estado):
    assert _fase(_alta(estado, APROBADO), A_1_MIN) == "resultado"
    assert _fase(_alta(estado, APROBADO), A_6_MIN) == "resultado"


def test_f077_r14_alta_posterior_a_la_aprobacion_es_resultado():
    assert _fase(_alta("no_admitido", "2026-10-16T10:00:01+00:00"), A_1_MIN) == "resultado"


@pytest.mark.parametrize("campos", [
    {"config": ConfigAltaSigrid()},                     # feature apagada
    {"aprobado": False},                                # sin aprobar
    {"activo": False},                                  # papelera
    {"approved_at_utc": "2026-09-30T23:59:59+00:00"},   # antes de DESDE
    {"approved_at_utc": None},                          # sin instante de aprobación
    {"approved_at_utc": "ilegible"},
])
def test_f077_r14_documento_que_no_admite_alta_es_resultado(campos):
    assert _fase(None, A_1_MIN, **campos) == "resultado"
    assert _fase(_alta("no_admitido", ANTERIOR), A_6_MIN, **campos) == "resultado"


# =================================================================== #
# R17 · los estados malos son un error
# =================================================================== #
@pytest.mark.parametrize("estado, error", [
    ("no_admitido", True), ("revisar", True), ("error", True),
    ("en_curso", False), ("ya_en_sigrid", False), ("simulado", False), ("incierto", False),
    ("registrado", False), ("anulado", False),
])
def test_f077_r17_es_error(estado, error):
    from domain.models.alta_sigrid_models import ESTADOS_ALTA_ERROR

    assert ESTADOS_ALTA_ERROR == frozenset({"no_admitido", "revisar", "error"})
    assert _alta(estado, APROBADO).es_error is error


# =================================================================== #
# R14, R18, R20 · servicio
# =================================================================== #
class _Repo:
    """Solo lo que la fase puede leer; cualquier otra llamada (escribir el
    alta, publicar…) revienta el test (R20)."""

    def __init__(self, *, estado=None, alta=None, documento=None):
        self.estado = estado
        self.alta = alta
        self.documento = documento
        self.lecturas: list[str] = []

    def estado_aprobacion(self, document_id):
        self.lecturas.append("estado_aprobacion")
        return self.estado

    def leer_alta_sigrid(self, document_id):
        self.lecturas.append("leer_alta_sigrid")
        return self.alta

    def get_document_detail(self, document_id, *, view_mode):
        return self.documento

    def lineas_producto_sigrid(self, document_id):
        return []

    def __getattr__(self, nombre):
        raise AssertionError(f"la fase del alta no debe llamar a {nombre}")


class _Orquestador:
    def __getattr__(self, nombre):
        raise AssertionError(f"la fase del alta no publica ({nombre})")


def _servicio(repo, config=CONFIG):
    from application.services.review_service import ReviewService

    return ReviewService(repo, "r", _Orquestador(), config)


def _estado(approved_at_utc=APROBADO, approved=True, is_active=True):
    return {"approved": approved, "approved_at_utc": approved_at_utc, "is_active": is_active}


def test_f077_r18_servicio_fase_con_el_alta_del_repositorio():
    repo = _Repo(estado=_estado(), alta=_alta("no_admitido", ANTERIOR))
    assert _servicio(repo).fase_alta("d", ahora=A_1_MIN) == "en_curso"
    assert _servicio(repo).fase_alta("d", ahora=A_6_MIN) == "sin_respuesta"
    repo.alta = _alta("no_admitido", APROBADO)
    assert _servicio(repo).fase_alta("d", ahora=A_1_MIN) == "resultado"


def test_f077_r18_servicio_sin_documento_es_none():
    assert _servicio(_Repo(estado=None)).fase_alta("no", ahora=A_1_MIN) is None


def test_f077_r18_servicio_feature_apagada_resultado_sin_leer():
    repo = _Repo(estado=_estado())
    assert _servicio(repo, ConfigAltaSigrid()).fase_alta("d", ahora=A_1_MIN) == "resultado"
    assert repo.lecturas == []


def test_f077_r18_servicio_por_defecto_usa_el_reloj():
    ahora = datetime.now(UTC)
    repo = _Repo(estado=_estado((ahora - timedelta(minutes=1)).isoformat()))
    assert _servicio(repo).fase_alta("d") == "en_curso"
    repo.estado = _estado((ahora - timedelta(minutes=6)).isoformat())
    assert _servicio(repo).fase_alta("d") == "sin_respuesta"


def test_f077_r14_get_document_lleva_la_fase(documento_detalle):
    documento = documento_detalle()
    documento.approved = True
    ahora = datetime.now(UTC)
    repo = _Repo(estado=_estado((ahora - timedelta(minutes=1)).isoformat()), documento=documento)
    ficha = _servicio(repo).get_document(documento.id)
    assert ficha.alta_fase == "en_curso"
    repo.alta = _alta("simulado", (ahora - timedelta(minutes=1)).isoformat())
    repo.estado = _estado(repo.alta.approved_at_utc)
    assert _servicio(repo).get_document(documento.id).alta_fase == "resultado"


def test_f077_r14_alta_fase_por_defecto_es_resultado(documento_detalle):
    assert documento_detalle().alta_fase == "resultado"


# =================================================================== #
# R18, R20 · la ruta
# =================================================================== #
class _Publicador:
    def __init__(self):
        self.publicados: list = []

    def publicar(self, nombre_cola, mensaje):
        self.publicados.append((nombre_cola, mensaje))
        return True


class _ServicioFase:
    def __init__(self, fase):
        self.fase = fase
        self.llamadas: list = []

    def initialize(self):
        return True

    def fase_alta(self, document_id, **kwargs):
        self.llamadas.append(("fase_alta", document_id))
        return self.fase

    def __getattr__(self, nombre):
        raise AssertionError(f"la ruta de la fase no debe llamar a {nombre}")


def _cliente(monkeypatch, servicio):
    publicador = _Publicador()
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: publicador)
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes), follow_redirects=False), publicador


@pytest.mark.parametrize("fase", ["en_curso", "sin_respuesta", "resultado"])
def test_f077_r18_ruta_responde_la_fase(monkeypatch, fase):
    servicio = _ServicioFase(fase)
    cliente, publicador = _cliente(monkeypatch, servicio)
    respuesta = cliente.get("/api/documents/DOC-1/alta-sigrid/fase")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"fase": fase}
    assert servicio.llamadas == [("fase_alta", "DOC-1")]
    assert publicador.publicados == []  # R20


def test_f077_r18_ruta_404_sin_documento(monkeypatch):
    cliente, publicador = _cliente(monkeypatch, _ServicioFase(None))
    assert cliente.get("/api/documents/NO/alta-sigrid/fase").status_code == 404
    assert publicador.publicados == []


def test_f077_r20_la_ruta_es_get_y_solo_lectura():
    from pathlib import Path

    fuente = (Path(modulo_app.__file__)).read_text(encoding="utf-8")
    inicio = fuente.index('"/api/documents/{document_id}/alta-sigrid/fase"')
    bloque = fuente[fuente.rindex("@app.", 0, inicio):fuente.index("@app.", inicio)]
    assert bloque.startswith("@app.get(")
    assert "review_service.fase_alta(" in bloque
    for prohibido in ("publicar", "solicitar", "_publicar_feedback", "guardar", "save"):
        assert prohibido not in bloque
