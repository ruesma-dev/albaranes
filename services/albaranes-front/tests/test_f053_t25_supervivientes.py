# tests/test_f053_t25_supervivientes.py
"""F-053 · T25 · supervivientes de la campaña de mutación en sv4.

Cada test fija un valor o una rama que la campaña (``progress/mutacion_F-053.md``)
demostró que ningún test leía: modelos inmutables y sus defectos, avisos del
servicio, el cerrojo sobre EL documento pedido, «valorado» con una sola línea o
varias valoraciones, rutas (redirecciones, revisor, recuentos de R27) y que las
rutas de formulario nuevas no salen en el esquema OpenAPI.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

import pytest
from f053_sv4_bbdd import DOC, construir, foto, repositorio
from sqlalchemy import event, text
from sqlalchemy.orm import Session
from test_f053_t18_publicar import _Orquestador, _Repo, _servicio
from test_f053_t20_rutas import _cliente, _RepoBorrado, _ServicioPapelera

from domain.models.alta_sigrid_models import (
    AlbaranSinValorarError,
    AltaSigridVista,
    ConfigAltaSigrid,
    ProductoLinea,
    ResultadoAprobacion,
)
from domain.models.review_models import DocumentListItem
from domain.services.alta_sigrid import puede_solicitar_alta

DESDE = datetime(2026, 10, 1, tzinfo=UTC)
ACTIVA = ConfigAltaSigrid(desde=DESDE)


# ------------------------------------------------------------------ #
# Modelos
# ------------------------------------------------------------------ #
def test_f053_t25_resultados_inmutables():
    from application.services.review_service import (
        ResultadoBorradoMultiple,
        ResultadoGuardado,
    )

    for clase in (ResultadoGuardado, ResultadoBorradoMultiple, ConfigAltaSigrid,
                  ResultadoAprobacion):
        assert clase.__dataclass_params__.frozen is True, clase.__name__


def test_f053_t25_defectos_de_los_modelos():
    assert ProductoLinea(valuation_line_id=1, vinculada=False, a_registrar=True).por_defecto is False
    assert AltaSigridVista(estado="simulado").intentos == 0
    item = DocumentListItem(id="d", source_filename="a", provider_origin="m", created_at_utc="t")
    assert item.valorado is False and item.alta_estado is None


def test_f053_t25_ficha_por_defecto_no_ofrece_solicitar(documento_detalle):
    documento = documento_detalle()
    assert documento.alta_puede_solicitar is False and documento.alta_sigrid_activa is False


# ------------------------------------------------------------------ #
# Servicio
# ------------------------------------------------------------------ #
def test_f053_t25_r4_solo_avisa_en_el_log_si_no_se_pidio(caplog):
    caplog.set_level(logging.WARNING)
    _servicio(_Repo(paso=True), _Orquestador(publica=True)).approve_document(
        document_id=DOC, approved_by="ana")
    assert "NO se pidió" not in caplog.text
    _servicio(_Repo(paso=True), _Orquestador(publica=False)).approve_document(
        document_id=DOC, approved_by="ana")
    assert "NO se pidió" in caplog.text


@pytest.mark.parametrize("producto, texto", [("XA9999", "Producto Sigrid XA9999 · "),
                                             (None, "Producto Sigrid por defecto · ")])
def test_f053_t25_r41_descripcion_del_deshacer(producto, texto):
    from application.services.review_service import ReviewService

    motor = construir()
    ReviewService(repositorio(motor), "r", None, ACTIVA).elegir_producto_sigrid(
        document_id=DOC, valuation_line_id=12, producto=producto)
    with Session(motor) as s:
        descripcion = s.execute(text("SELECT description FROM undo_log")).scalar()
    assert descripcion.startswith(texto)


def test_f053_t25_r30_sin_desde_no_se_puede_solicitar():
    from application.services.review_service import ReviewService

    class _NoLeer:
        def __getattr__(self, nombre):
            raise AssertionError(nombre)

    assert ReviewService(_NoLeer(), "r", None, ConfigAltaSigrid()).puede_solicitar_alta("d") is False


def test_f053_t25_r30_publicar_que_lanza_es_no_publicada():
    from application.services.review_service import ReviewService

    class _Repo30:
        def leer_alta_sigrid(self, document_id):
            return AltaSigridVista(estado="registrado")

    class _Lanza:
        def solicitar_alta_sigrid(self, **kwargs):
            raise RuntimeError("cola caída")

    servicio = ReviewService(_Repo30(), "r", _Lanza(), ACTIVA)
    assert servicio.verificar_anulacion_sigrid(document_id="d", solicitado_por="a") == "no_publicada"


def test_f053_t25_r30_aprobado_justo_en_desde_puede_solicitar():
    assert puede_solicitar_alta(
        aprobado=True, activo=True, approved_at_utc=DESDE.isoformat(), alta=None,
        config=ACTIVA, ahora=DESDE,
    ) is True


def test_f053_t25_r44_espera_cero_admitida():
    from config.settings import Settings

    ajustes = Settings(_env_file=None, PG_PASSWORD="x", PG_ADMIN_PASSWORD="x",
                       ALTA_SIGRID_ESPERA_INCIERTO_MIN="0")
    assert ajustes.alta_sigrid_espera_incierto_min == 0


# ------------------------------------------------------------------ #
# Repositorio
# ------------------------------------------------------------------ #
def _sentencias_de_cerrojo(motor):
    vistas: list[tuple[str, object]] = []

    @event.listens_for(motor, "before_cursor_execute")
    def _anotar(conn, cursor, sentencia, parametros, contexto, varios):
        normal = " ".join(sentencia.split())
        if normal.startswith("SELECT albaran_documents_merge.id FROM"):
            vistas.append((normal, parametros))

    return vistas


@pytest.mark.parametrize("operacion", ["aprobar", "desaprobar"])
def test_f053_t25_r26_el_cerrojo_es_del_documento_pedido(operacion):
    motor = construir(aprobado=operacion == "desaprobar")
    vistas = _sentencias_de_cerrojo(motor)
    repositorio(motor).set_approved(document_id=DOC, approved=operacion == "aprobar",
                                    approved_by="ana")
    sentencia = (
        "SELECT albaran_documents_merge.id FROM albaran_documents_merge "
        "WHERE albaran_documents_merge.id = ?"
    )
    assert vistas == [(sentencia, (DOC,))]


def test_f053_t25_r37_sin_tabla_de_valoracion_no_se_aprueba():
    motor = construir()
    with Session(motor) as s:
        s.execute(text("DROP TABLE albaran_line_valuations"))
        s.execute(text("DROP TABLE albaran_valuations"))
        s.commit()
    with pytest.raises(AlbaranSinValorarError):
        repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")


def test_f053_t25_r37_valoracion_de_una_sola_linea():
    motor = construir(status="ok")
    with Session(motor) as s:
        s.execute(text("DELETE FROM albaran_line_valuations WHERE id <> 11"))
        s.commit()
    assert repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="a") is True


def test_f053_t25_r37_solo_cuentan_las_lineas_de_la_primera_valoracion():
    """Con dos valoraciones del mismo documento (no debería haberlas: sv6
    reemplaza), «valorado» mira la primera por ``id`` y solo sus líneas."""
    motor = construir(status="manual")
    with Session(motor) as s:
        s.execute(text(
            "INSERT INTO albaran_valuations (id, document_id, status, review_required) "
            "VALUES ('zz-otra', :d, 'partial', 0)"), {"d": DOC})
        s.execute(text(
            "INSERT INTO albaran_line_valuations (id, valuation_id, importe_calculado, "
            "importe_source) VALUES (99, 'zz-otra', NULL, 'calculated')"))
        s.commit()
    repo = repositorio(motor)
    with Session(motor) as s:
        assert repo._valorado_in_session(s, DOC) is True
    # (F-065 R20/O2) Aprobar, en cambio, mira TODAS las filas, como sv9 al dar
    # de alta: la 99 (sin línea de contrato ni derivada) lo impide.
    from domain.models.review_models import LineasIncompletasError

    with pytest.raises(LineasIncompletasError):
        repo.set_approved(document_id=DOC, approved=True, approved_by="a")


def test_f053_t25_alta_con_cero_intentos_y_documento_inexistente():
    motor = construir()
    with Session(motor) as s:
        s.execute(text(
            "INSERT INTO albaran_altas_sigrid (document_id, estado, intentos, creado_at_utc) "
            "VALUES (:d, 'error', 0, 't')"), {"d": DOC})
        s.commit()
    repo = repositorio(motor)
    assert repo.leer_alta_sigrid(DOC).intentos == 0
    assert repo.estado_aprobacion("no-existe") is None
    assert repo.estado_aprobacion(DOC) == {
        "approved": False, "approved_at_utc": None, "is_active": True,
    }
    assert foto(motor)  # la BBDD sigue legible


# ------------------------------------------------------------------ #
# Rutas
# ------------------------------------------------------------------ #
class _ServicioRevisor:
    def __init__(self):
        self.revisores: list[str | None] = []

    def initialize(self):
        return True

    def approve_document(self, *, document_id, approved_by):
        self.revisores.append(approved_by)
        return ResultadoAprobacion(paso_a_aprobado=True)

    def delete_document(self, *, document_id, deleted_by):
        self.revisores.append(deleted_by)


@pytest.mark.parametrize("ruta, campo", [("approve", "approved_by"), ("delete", "deleted_by")])
def test_f053_t25_revisor_del_formulario_o_de_la_cabecera(monkeypatch, ruta, campo):
    servicio = _ServicioRevisor()
    cliente, _ = _cliente(monkeypatch, servicio)
    cabecera = {"X-MS-CLIENT-PRINCIPAL-NAME": "ana@ruesma.es"}
    cliente.post(f"/documents/{DOC}/{ruta}", data={campo: "pepe"}, headers=cabecera)
    cliente.post(f"/documents/{DOC}/{ruta}", data={campo: ""}, headers=cabecera)
    assert servicio.revisores == ["pepe", "ana@ruesma.es"]


def test_f053_t25_aprobar_sin_filtros_redirige_con_303(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioRevisor())
    respuesta = cliente.post(f"/documents/{DOC}/approve")
    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/documents?message=Documento+aprobado"


@pytest.mark.parametrize("ids, texto", [
    ("", "Ning%C3%BAn+albar%C3%A1n+seleccionado"),
    ("a,c", "2+albar%C3%A1n%28es%29+movidos+a+la+papelera"),
])
def test_f053_t25_r27_borrado_multiple_sin_saltos(monkeypatch, ids, texto):
    cliente, _ = _cliente(monkeypatch, _ServicioPapelera(set()))
    destino = cliente.post("/documents/bulk-delete", data={"ids": ids}).headers["location"]
    assert destino == f"/documents?message={texto}"


def test_f053_t25_r27_vaciar_papelera_cuenta_bien_los_saltados(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioPapelera({"b"}))
    destino = cliente.post("/documents/trash/empty").headers["location"]
    assert "eliminados.+1+saltado%28s%29" in destino


def test_f053_t25_rutas_de_formulario_fuera_del_esquema(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioRevisor())
    rutas = cliente.app.openapi()["paths"]
    assert "/documents/{document_id}/alta-sigrid/solicitar" not in rutas
    assert "/documents/{document_id}/alta-sigrid/verificar-anulacion" not in rutas
    assert "/api/documents/{document_id}/lineas-valoradas/{valuation_line_id}/producto-sigrid" in rutas


def test_f053_t25_repo_borrado_sigue_igual():
    assert _RepoBorrado(set()).list_trash_document_ids() == ["a", "b", "c"]
